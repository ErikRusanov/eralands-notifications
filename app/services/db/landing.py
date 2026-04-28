"""landing — CRUD-сервис для модели ``Landing``."""

from app.models import Landing
from app.services.db.base import BaseDBService


class LandingService(BaseDBService[Landing]):
    """Сервис работы с лендингами клиента."""

    model = Landing
