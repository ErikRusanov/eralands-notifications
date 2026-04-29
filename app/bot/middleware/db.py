"""db — мидлвара, инжектит ``LinkingService`` на готовой async-сессии.

Открывает одну сессию на одно сообщение, собирает доменный сервис через
``LinkingService.from_session`` и инжектит в ``data``:

- ``linking_service`` — собранный сервис
- ``session`` — та же ``AsyncSession``, чтобы хендлер мог явно сделать
  ``rollback`` при пойманной доменной ошибке (когда нужно ответить
  пользователю, но не коммитить partial-state)

Коммитит при успешном возврате хендлера, откатывает при пробросе
исключения — симметрично HTTP-зависимости ``get_session``.

Подключается точечно к роутеру, которому нужна БД (см. ``handlers.commands.link``),
а не глобально на ``Dispatcher``: иначе сессия открывалась бы для каждого
``/start`` и echo-сообщения зря.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.core.session import async_session_maker
from app.services.domain import LinkingService


class DbSessionMiddleware(BaseMiddleware):
    """Открывает сессию БД и собирает ``LinkingService`` для хендлера."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Обернуть вызов хендлера в одну транзакцию БД."""
        async with async_session_maker() as session:
            data["session"] = session
            data["linking_service"] = LinkingService.from_session(session)
            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            await session.commit()
            return result
