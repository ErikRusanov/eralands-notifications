"""routing — операции над маршрутами доставки лендинг → канал.

Закрывает бизнес-кейс 7: отвязать конкретный канал (TG-аккаунт) от
лендинга. Сам канал и другие маршруты в нём остаются активными.
"""

import uuid

from pydantic import BaseModel

from app.services.db import LandingRouteService
from app.services.domain.errors import ConflictError, NotFoundError


class _RouteActivation(BaseModel):
    """Частичный апдейт активности маршрута."""

    is_active: bool


class RoutingService:
    """Управление активностью маршрутов лендинга."""

    def __init__(self, routes: LandingRouteService) -> None:
        self.routes = routes

    async def unlink_channel(
        self, landing_id: uuid.UUID, channel_id: uuid.UUID
    ) -> None:
        """Деактивирует маршрут по паре ``(landing_id, channel_id)``.

        Запись маршрута не удаляется: остаётся след для аудита и быстрой
        реактивации, если клиент вернётся.

        Поднимает:
            NotFoundError: Если маршрут не найден.
            ConflictError: Если маршрут уже отключён.
        """
        route = await self.routes.get_by_landing_channel(landing_id, channel_id)
        if route is None:
            raise NotFoundError("Route not found.")
        if not route.is_active:
            raise ConflictError("Route is already inactive.")
        await self.routes.update(route, _RouteActivation(is_active=False))
