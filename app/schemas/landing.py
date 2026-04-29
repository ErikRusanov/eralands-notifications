"""landing — схемы запросов и ответов для управления лендингами."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.linking_code import LinkingCodeResponse


class LandingCreate(BaseModel):
    """Тело запроса ``POST /api/clients/{client_id}/landings``.

    Атрибуты:
        slug: Человеко-читаемый идентификатор лендинга, уникальный глобально.
        name: Отображаемое имя в админке и в текстах уведомлений.
    """

    slug: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
        description="Slug лендинга: латиница в нижнем регистре, цифры, дефисы.",
        examples=["roofs-msk"],
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Отображаемое имя лендинга.",
        examples=["Кровля под ключ — Москва"],
    )


class LandingResponse(BaseModel):
    """Описание лендинга в API-ответах.

    Атрибуты:
        id: Идентификатор лендинга.
        client_id: Владелец лендинга.
        slug: Уникальный slug.
        name: Отображаемое имя.
        is_active: Активен ли лендинг.
        created_at: Момент создания записи.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    slug: str
    name: str
    is_active: bool
    created_at: datetime


class ProvisionedLandingResponse(BaseModel):
    """Расширенный ответ при создании лендинга.

    Содержит открытый api-токен и одноразовый код привязки. Клиент видит эти
    значения один раз в момент провиженинга, после чего токен живёт только
    на лендинге, а код — у владельца до ввода в боте.

    Атрибуты:
        landing: Сам лендинг.
        api_token: Открытый токен лендинга для аутентификации заявок.
        linking_code: Одноразовый код привязки канала к лендингу.
    """

    landing: LandingResponse
    api_token: str = Field(..., description="Открытый токен лендинга, без хеширования.")
    linking_code: LinkingCodeResponse
