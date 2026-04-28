"""lead — CRUD-сервис для модели ``Lead``."""

from app.models import Lead
from app.services.db.base import BaseDBService


class LeadService(BaseDBService[Lead]):
    """Сервис работы с заявками лендингов."""

    model = Lead
