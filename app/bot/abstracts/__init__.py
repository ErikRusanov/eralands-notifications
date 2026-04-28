"""abstracts — абстрактные базовые классы доменного слоя бота.

Публичный API
-------------
AbstractCommands : Базовый реестр команд. Сабкласс описывает команды как
    атрибуты класса типа ``BotCommand``.
AbstractReplies  : Базовая фабрика ответов. Загружает тексты из ``texts.toml``
    и предоставляет хелперы ``_msg`` и ``_escape`` для конкретных реализаций.
BotCommand       : Описание команды + готовый фильтр ``aiogram``. Используется
    как декоратор: ``@router.message(Commands.start)``.
"""

from app.bot.abstracts.commands import AbstractCommands, BotCommand
from app.bot.abstracts.replies import AbstractReplies

__all__ = ["AbstractCommands", "AbstractReplies", "BotCommand"]
