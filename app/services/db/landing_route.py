"""landing_route — CRUD-сервис для модели ``LandingRoute``."""

import uuid

from sqlalchemy import select

from app.models import LandingRoute
from app.services.db.base import BaseDBService


class LandingRouteService(BaseDBService[LandingRoute]):
    """Сервис работы с маршрутами доставки лендингов в каналы уведомлений."""

    model = LandingRoute

    async def list_active_for_landing(
        self, landing_id: uuid.UUID
    ) -> list[LandingRoute]:
        """Возвращает активные маршруты лендинга для fan-out доставки."""
        stmt = select(LandingRoute).where(
            LandingRoute.landing_id == landing_id,
            LandingRoute.is_active.is_(True),
        )
        return list((await self.session.scalars(stmt)).all())

    async def get_by_landing_channel(
        self, landing_id: uuid.UUID, channel_id: uuid.UUID
    ) -> LandingRoute | None:
        """Возвращает маршрут по уникальной паре ``(landing_id, channel_id)``."""
        stmt = select(LandingRoute).where(
            LandingRoute.landing_id == landing_id,
            LandingRoute.channel_id == channel_id,
        )
        return (await self.session.scalars(stmt)).one_or_none()
