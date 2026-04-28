"""handlers — обработчики обновлений Telegram.

Публичный API
-------------
register_handlers : Подключает все роутеры бота к диспатчеру в нужном порядке.
"""

from aiogram import Dispatcher

from app.bot.handlers.commands import register_commands

__all__ = ["register_handlers"]


def register_handlers(dp: Dispatcher) -> None:
    """Подключить все роутеры бота к диспатчеру.

    Порядок имеет значение: aiogram перебирает роутеры в порядке регистрации
    и отдаёт обновление первому подходящему. Команды регистрируются раньше
    catch-all обработчиков (когда такие появятся).

    Аргументы:
        dp: Диспатчер aiogram, к которому подключаются роутеры.
    """
    register_commands(dp)
