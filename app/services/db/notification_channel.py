"""notification_channel — CRUD-сервис для модели ``NotificationChannel``."""

import uuid
from collections.abc import Iterable

from sqlalchemy import select

from app.models import NotificationChannel
from app.services.db.base import BaseDBService


class NotificationChannelService(BaseDBService[NotificationChannel]):
    """Сервис работы с каналами уведомлений клиентов."""

    model = NotificationChannel

    async def list_for_client(self, client_id: uuid.UUID) -> list[NotificationChannel]:
        """Возвращает каналы клиента, отсортированные по времени создания."""
        stmt = (
            select(NotificationChannel)
            .where(NotificationChannel.client_id == client_id)
            .order_by(NotificationChannel.created_at)
        )
        return list((await self.session.scalars(stmt)).all())

    async def list_by_ids(self, ids: Iterable[uuid.UUID]) -> list[NotificationChannel]:
        """Возвращает каналы по списку идентификаторов (одним SELECT-ом).

        Используется при fan-out отправки лида: набор каналов известен по
        свежесозданным ``Delivery``, и подгрузка одним запросом избавляет от
        N+1 на стороне ``DispatchService``.
        """
        ids_list = list({*ids})
        if not ids_list:
            return []
        stmt = select(NotificationChannel).where(NotificationChannel.id.in_(ids_list))
        return list((await self.session.scalars(stmt)).all())
