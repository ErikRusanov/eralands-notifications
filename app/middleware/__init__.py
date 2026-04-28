"""middleware — Starlette-мидлвары сервиса.

Публичный API
-------------
LoggingMiddleware : Логирует метод, путь, статус и длительность каждого запроса.
"""

from app.middleware.logging import LoggingMiddleware

__all__ = ["LoggingMiddleware"]
