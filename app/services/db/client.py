"""client — CRUD-сервис для модели ``Client``."""

from app.models import Client
from app.services.db.base import BaseDBService


class ClientService(BaseDBService[Client]):
    """Сервис работы с клиентами Era Lands."""

    model = Client
