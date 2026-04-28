"""delivery — CRUD-сервис для модели ``Delivery``."""

from app.models import Delivery
from app.services.db.base import BaseDBService


class DeliveryService(BaseDBService[Delivery]):
    """Сервис работы с доставками заявок в каналы уведомлений."""

    model = Delivery
