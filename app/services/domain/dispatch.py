"""dispatch — синхронная отправка свежесозданных доставок в каналы клиента.

Закрывает второй шаг бизнес-кейса 5: после ``LeadIntakeService`` создал
``Delivery`` в ``pending`` для каждого активного маршрута, ``DispatchService``
параллельно дёргает Telegram (``asyncio.gather``) и обновляет статусы:

- успех → ``status=sent``, ``sent_at=now``
- ошибка → ``status=failed``, ``last_error=<message>``

Каждый канал на своей корутине, поэтому ``send_message`` не блокирует event
loop, и сбой одного канала не валит остальные. Транзакцию закрывает
``get_session`` — мы только мутируем attached ORM-объекты.
"""

import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot

from app.bot.utils.replies import Replies
from app.models import (
    ChannelType,
    Delivery,
    DeliveryStatus,
    Landing,
    Lead,
    NotificationChannel,
)
from app.services.db import NotificationChannelService

logger = logging.getLogger(__name__)

_LAST_ERROR_MAX_LEN = 500


class DispatchService:
    """Параллельная отправка набора ``Delivery`` в их каналы."""

    def __init__(
        self,
        bot: Bot,
        channels: NotificationChannelService,
        replies: Replies,
    ) -> None:
        self.bot = bot
        self.channels = channels
        self.replies = replies

    async def dispatch_lead(
        self,
        landing: Landing,
        lead: Lead,
        deliveries: list[Delivery],
    ) -> None:
        """Параллельно отправляет ``deliveries`` в свои каналы и обновляет статусы.

        Метод не валит транзакцию: исключения каждого канала ловятся
        внутри корутины и пишутся в ``last_error`` соответствующего
        ``Delivery``. Считается, что все ``deliveries`` только что созданы и
        находятся в ``pending``.

        Аргументы:
            landing: Лендинг, с которого пришла заявка. Имя используется в
                тексте уведомления.
            lead: Сама заявка. ``payload`` рендерится в HTML-сообщение.
            deliveries: Только что созданные доставки, для которых нужно
                выполнить попытку отправки.
        """
        if not deliveries:
            return

        channels = await self.channels.list_by_ids(d.channel_id for d in deliveries)
        channels_by_id = {channel.id: channel for channel in channels}

        text = self.replies.lead_notification(
            landing=landing.name,
            payload=lead.payload,
        )

        # return_exceptions=True страхует от непредусмотренных рейзов в одной
        # из корутин: каждая ветка уже ловит Exception и пишет в last_error,
        # но если произойдёт что-то совсем неожиданное (например, KeyError при
        # поиске канала), остальные доставки всё равно получат свою попытку.
        results = await asyncio.gather(
            *(
                self._dispatch_one(delivery, channels_by_id[delivery.channel_id], text)
                for delivery in deliveries
            ),
            return_exceptions=True,
        )
        for delivery, result in zip(deliveries, results, strict=True):
            if isinstance(result, BaseException):
                delivery.status = DeliveryStatus.FAILED
                delivery.last_error = str(result)[:_LAST_ERROR_MAX_LEN]
                logger.exception(
                    "Unhandled dispatch error: delivery=%s",
                    delivery.id,
                    exc_info=result,
                )

    async def _dispatch_one(
        self,
        delivery: Delivery,
        channel: NotificationChannel,
        text: str,
    ) -> None:
        delivery.attempts += 1
        if channel.type != ChannelType.TELEGRAM:
            delivery.status = DeliveryStatus.FAILED
            delivery.last_error = f"Unsupported channel type: {channel.type.value}"
            logger.warning(
                "Unsupported channel type for delivery=%s type=%s",
                delivery.id,
                channel.type.value,
            )
            return
        try:
            await self.bot.send_message(chat_id=int(channel.address), text=text)
        except Exception as exc:
            delivery.status = DeliveryStatus.FAILED
            delivery.last_error = str(exc)[:_LAST_ERROR_MAX_LEN]
            logger.warning(
                "Telegram send failed: delivery=%s chat_id=%s err=%s",
                delivery.id,
                channel.address,
                exc,
            )
        else:
            delivery.status = DeliveryStatus.SENT
            delivery.sent_at = datetime.now(UTC)
            logger.info(
                "Delivery sent: delivery=%s chat_id=%s",
                delivery.id,
                channel.address,
            )
