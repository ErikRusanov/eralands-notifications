"""notification_channel — схемы ответов по каналам уведомлений."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import ChannelType


class NotificationChannelResponse(BaseModel):
    """Описание канала уведомлений в API-ответах.

    Атрибуты:
        id: Идентификатор канала. Используется в ``DELETE
            /landings/{landing_id}/routes/{channel_id}``.
        client_id: Владелец канала.
        type: Тип канала (например, ``telegram``).
        address: Адресная часть: ``chat_id`` для Telegram, email для почты
            и т. п. Хранится строкой для единообразия между типами.
        config: Дополнительные параметры, специфичные для типа канала.
        is_active: Активен ли канал.
        created_at: Момент создания записи.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    type: ChannelType
    address: str
    config: dict[str, Any]
    is_active: bool
    created_at: datetime
