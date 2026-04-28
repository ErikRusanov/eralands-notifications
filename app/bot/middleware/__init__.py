"""middleware — aiogram-мидлвары бота.

Публичный API
-------------
LoggingMiddleware : Логирует тип каждого обработанного обновления
    (без персональных данных).
"""

from app.bot.middleware.logging import LoggingMiddleware

__all__ = ["LoggingMiddleware"]
