"""utils — конкретные реализации контрактов и стартовая обвязка бота.

Публичный API
-------------
Commands     : Реестр команд бота (см. ``AbstractCommands``).
Replies      : Фабрика ответов бота (см. ``AbstractReplies``).
setup_bot    : Создаёт и полностью конфигурирует Bot и Dispatcher,
    регистрирует webhook у Telegram. Вызывается из FastAPI lifespan.
teardown_bot : Снимает webhook и закрывает HTTP-сессию бота.
"""

from app.bot.utils.commands import Commands
from app.bot.utils.replies import Replies
from app.bot.utils.setup import setup_bot, teardown_bot

__all__ = ["Commands", "Replies", "setup_bot", "teardown_bot"]
