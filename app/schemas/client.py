"""client — схемы запросов и ответов для управления клиентами."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.landing import LandingResponse


class ClientCreate(BaseModel):
    """Тело запроса ``POST /api/clients``.

    Атрибуты:
        name: Произвольное имя клиента, видимое только в админке.
    """

    name: str = Field(
        ...,
        min_length=1,
        description="Имя клиента в админке.",
        examples=["ООО Ромашка"],
    )


class ClientUpdate(BaseModel):
    """Тело запроса ``PATCH /api/clients/{client_id}``.

    Применяется массово: ``is_active`` каскадно проставляется на всех
    лендингах клиента. Сама запись клиента не имеет такого флага.

    Атрибуты:
        is_active: Активны ли лендинги клиента.
    """

    is_active: bool = Field(
        ...,
        description="Активны ли все лендинги клиента.",
    )


class ClientResponse(BaseModel):
    """Тело ответа на операции с клиентом.

    Атрибуты:
        id: Идентификатор клиента (UUIDv7).
        name: Имя клиента.
        created_at: Момент создания записи.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


class ClientWithLandingsResponse(BaseModel):
    """Карточка клиента вместе со списком его лендингов.

    Атрибуты:
        id: Идентификатор клиента.
        name: Имя клиента.
        created_at: Момент создания записи.
        landings: Лендинги клиента, отсортированные по времени создания.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    landings: list[LandingResponse]
