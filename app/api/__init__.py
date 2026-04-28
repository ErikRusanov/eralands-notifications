"""api — роутеры и обработчики эндпоинтов сервиса.

Публичный API
-------------
router : Корневой APIRouter, который монтируется на FastAPI-приложение.
"""

from app.api.router import router

__all__ = ["router"]
