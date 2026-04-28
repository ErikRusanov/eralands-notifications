"""core — фабрики низкоуровневых объектов бота.

Публичный API
-------------
create_bot        : Возвращает сконфигурированный экземпляр ``aiogram.Bot``.
create_dispatcher : Возвращает чистый ``aiogram.Dispatcher``.
"""

from app.bot.core.bot import create_bot, create_dispatcher

__all__ = ["create_bot", "create_dispatcher"]
