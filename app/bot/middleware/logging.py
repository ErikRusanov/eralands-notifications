"""logging — мидлвара логирования обновлений aiogram без персональных данных."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

logger = logging.getLogger(__name__)


def _describe(update: Update) -> tuple[int | str, str]:
    """Извлечь loggable-метку и идентификатор пользователя из обновления.

    Текстовое содержимое сообщений не логируется, чтобы не утекали персональные
    данные. Для текстовых команд (``/<cmd>``) возвращается сама команда,
    для прочих сообщений — тип контента.

    Аргументы:
        update: Входящее обновление Telegram.

    Возвращает:
        Кортеж ``(user_id, label)``. ``user_id`` равен ``"unknown"`` если
        пользователя извлечь не удалось.
    """
    if isinstance(msg := update.message, Message):
        user_id = msg.from_user.id if msg.from_user else "unknown"
        if msg.text and msg.text.startswith("/"):
            return user_id, msg.text.split()[0]
        return user_id, f"[{msg.content_type}]"

    if isinstance(cb := update.callback_query, CallbackQuery):
        user_id = cb.from_user.id if cb.from_user else "unknown"
        return user_id, f"[callback:{cb.data or 'unknown'}]"

    return "unknown", f"[{update.event_type}]"


class LoggingMiddleware(BaseMiddleware):
    """Логирует факт обработки каждого обновления.

    Уровень ``INFO`` для успешных вызовов, ``ERROR`` если хендлер кинул
    исключение. Само исключение пробрасывается дальше — глобальный
    обработчик ошибок aiogram им займётся.
    """

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        """Залогировать тип обновления, выполнить хендлер, залогировать исход."""
        user_id, label = _describe(event)

        try:
            result = await handler(event, data)
        except Exception as exc:
            logger.error("[%s] -> %s [ERROR: %s]", user_id, label, exc)
            raise

        logger.info("[%s] -> %s [OK]", user_id, label)
        return result
