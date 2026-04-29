"""client — CRUD-сервис для модели ``Client``."""

from sqlalchemy import select

from app.models import Client
from app.services.db.base import BaseDBService


class ClientService(BaseDBService[Client]):
    """Сервис работы с клиентами Era Lands."""

    model = Client

    async def list_all(self) -> list[Client]:
        """Возвращает всех клиентов, отсортированных по времени создания."""
        stmt = select(Client).order_by(Client.created_at)
        return list((await self.session.scalars(stmt)).all())
