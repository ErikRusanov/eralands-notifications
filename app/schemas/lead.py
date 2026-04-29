"""lead — схемы запроса и ответа приёма заявок с лендингов."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LeadCreate(BaseModel):
    """Тело запроса ``POST /api/leads``.

    Поля формы у каждого лендинга свои, поэтому ``payload`` принимаем как
    свободный словарь. Технические метаданные источника (utm, ip, ua) клиент
    может прислать в ``source_meta`` либо мы их соберём на стороне бэкенда
    в будущем.

    Атрибуты:
        payload: Поля формы как есть.
        source_meta: Технические метаданные запроса.
    """

    model_config = ConfigDict(extra="forbid")

    payload: dict[str, Any] = Field(
        default_factory=dict, description="Поля формы лендинга."
    )
    source_meta: dict[str, Any] = Field(
        default_factory=dict, description="Технические метаданные запроса."
    )


class LeadAcceptedResponse(BaseModel):
    """Ответ ``POST /api/leads`` после принятия заявки.

    Атрибуты:
        id: Идентификатор созданного лида.
        accepted_at: Момент создания записи.
    """

    id: uuid.UUID
    accepted_at: datetime
