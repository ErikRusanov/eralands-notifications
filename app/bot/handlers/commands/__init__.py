"""commands — обработчики команд бота.

Публичный API
-------------
register_commands : Подключает все роутеры команд к диспатчеру.
"""

from aiogram import Dispatcher

from app.bot.handlers.commands.link import router as link_router
from app.bot.handlers.commands.start import router as start_router

__all__ = ["register_commands"]


def register_commands(dp: Dispatcher) -> None:
    """Подключить все роутеры команд к диспатчеру.

    Аргументы:
        dp: Диспатчер aiogram.
    """
    dp.include_router(start_router)
    dp.include_router(link_router)
