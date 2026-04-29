"""lead_intake — приём заявки с лендинга и fan-out по каналам.

Закрывает бизнес-кейс 5: по api-токену лендинга прилетает заявка со
свободным payload-ом. Сервис создаёт ``Lead`` и для каждого активного
маршрута лендинга создаёт ``Delivery`` в статусе ``pending``. Сама
отправка в канал — задача воркера, который пока не реализован.
"""

import uuid
from typing import Any

from pydantic import BaseModel

from app.models import Landing, Lead
from app.services.db import (
    DeliveryService,
    LandingRouteService,
    LeadService,
)
from app.services.domain.errors import ConflictError


class _LeadNew(BaseModel):
    """Полный набор полей для INSERT-а ``Lead``."""

    landing_id: uuid.UUID
    payload: dict[str, Any]
    source_meta: dict[str, Any]


class _DeliveryNew(BaseModel):
    """Полный набор полей для INSERT-а ``Delivery``."""

    lead_id: uuid.UUID
    channel_id: uuid.UUID


class LeadIntakeService:
    """Приём заявки и фан-аут доставок по активным маршрутам."""

    def __init__(
        self,
        leads: LeadService,
        routes: LandingRouteService,
        deliveries: DeliveryService,
    ) -> None:
        self.leads = leads
        self.routes = routes
        self.deliveries = deliveries

    async def accept(
        self,
        landing: Landing,
        payload: dict[str, Any],
        source_meta: dict[str, Any],
    ) -> Lead:
        """Создаёт лид и доставки в статусе ``pending``.

        Аргументы:
            landing: Лендинг, который аутентифицировал запрос. Должен быть
                активным: на отключённый лендинг заявку не принимаем.
            payload: Данные формы.
            source_meta: Технические метаданные.

        Поднимает:
            ConflictError: Если лендинг отключён.
        """
        if not landing.is_active:
            raise ConflictError("Landing is disabled.")

        lead = await self.leads.create(
            _LeadNew(
                landing_id=landing.id,
                payload=payload,
                source_meta=source_meta,
            )
        )

        active_routes = await self.routes.list_active_for_landing(landing.id)
        for route in active_routes:
            await self.deliveries.create(
                _DeliveryNew(lead_id=lead.id, channel_id=route.channel_id)
            )
        # TODO(worker): дёргать воркер на отправку pending-доставок.
        return lead
