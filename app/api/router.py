"""router — корневой API-роутер, агрегирующий все суб-роутеры."""

from fastapi import APIRouter

from app.api.bot import router as bot_router
from app.api.clients import router as clients_router
from app.api.health import router as health_router
from app.api.landings import router as landings_router
from app.api.leads import router as leads_router

router = APIRouter(prefix="/api")
router.include_router(health_router)
router.include_router(bot_router)
router.include_router(clients_router)
router.include_router(landings_router)
router.include_router(leads_router)
