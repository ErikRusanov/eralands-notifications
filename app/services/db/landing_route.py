"""landing_route — CRUD-сервис для модели ``LandingRoute``."""

from app.models import LandingRoute
from app.services.db.base import BaseDBService


class LandingRouteService(BaseDBService[LandingRoute]):
    """Сервис работы с маршрутами доставки лендингов в каналы уведомлений."""

    model = LandingRoute
