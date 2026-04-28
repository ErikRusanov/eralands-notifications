"""notification_channel — CRUD-сервис для модели ``NotificationChannel``."""

from app.models import NotificationChannel
from app.services.db.base import BaseDBService


class NotificationChannelService(BaseDBService[NotificationChannel]):
    """Сервис работы с каналами уведомлений клиентов."""

    model = NotificationChannel
