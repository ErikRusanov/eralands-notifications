"""notification_channel — CRUD-сервис для модели ``NotificationChannel``."""

import uuid

from sqlalchemy import select

from app.models import NotificationChannel
from app.services.db.base import BaseDBService


class NotificationChannelService(BaseDBService[NotificationChannel]):
    """Сервис работы с каналами уведомлений клиентов."""

    model = NotificationChannel

    async def list_for_client(self, client_id: uuid.UUID) -> list[NotificationChannel]:
        """Возвращает каналы клиента, отсортированные по времени создания."""
        stmt = (
            select(NotificationChannel)
            .where(NotificationChannel.client_id == client_id)
            .order_by(NotificationChannel.created_at)
        )
        return list((await self.session.scalars(stmt)).all())
