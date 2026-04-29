"""client — схемы запросов и ответов для управления клиентами."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
