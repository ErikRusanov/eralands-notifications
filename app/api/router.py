"""router — корневой API-роутер, агрегирующий все суб-роутеры."""

from fastapi import APIRouter

from app.api.health import router as health_router

router = APIRouter(prefix="/api")
router.include_router(health_router)
