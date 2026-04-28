"""utils — общие хелперы и утилиты сервиса.

Публичный API
-------------
lifespan : Async context manager жизненного цикла FastAPI.
"""

from app.utils.lifespan import lifespan

__all__ = ["lifespan"]
