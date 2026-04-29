"""landing — CRUD-сервис для модели ``Landing``."""

import uuid

from sqlalchemy import select, update

from app.models import Landing
from app.services.db.base import BaseDBService


class LandingService(BaseDBService[Landing]):
    """Сервис работы с лендингами клиента."""

    model = Landing

    async def get_by_slug(self, slug: str) -> Landing | None:
        """Возвращает лендинг по уникальному ``slug`` или ``None``."""
        stmt = select(Landing).where(Landing.slug == slug)
        return (await self.session.scalars(stmt)).one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> Landing | None:
        """Возвращает лендинг по SHA-256 хешу api-токена или ``None``."""
        stmt = select(Landing).where(Landing.api_token_hash == token_hash)
        return (await self.session.scalars(stmt)).one_or_none()

    async def list_by_client_ids(self, client_ids: list[uuid.UUID]) -> list[Landing]:
        """Возвращает лендинги для нескольких клиентов одним запросом.

        Используется в админских listing-эндпоинтах, чтобы не делать
        N+1 запрос на каждого клиента.
        """
        if not client_ids:
            return []
        stmt = (
            select(Landing)
            .where(Landing.client_id.in_(client_ids))
            .order_by(Landing.client_id, Landing.created_at)
        )
        return list((await self.session.scalars(stmt)).all())

    async def set_active_by_client(self, client_id: uuid.UUID, is_active: bool) -> None:
        """Массово выставляет ``is_active`` на всех лендингах клиента.

        Делается одним UPDATE без выгрузки строк в сессию: при отказе клиента
        от услуг лендингов может быть много, и итерация в Python тут лишняя.
        """
        stmt = (
            update(Landing)
            .where(Landing.client_id == client_id)
            .values(is_active=is_active)
        )
        await self.session.execute(stmt)
        await self.session.flush()
