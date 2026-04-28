"""notification_channel — канал доставки уведомлений (Telegram, в будущем email/sms)."""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ChannelType(str, enum.Enum):
    """Тип канала доставки."""

    TELEGRAM = "telegram"


class NotificationChannel(BaseModel):
    """Канал уведомлений, к которому подключаются лендинги клиента.

    Канал привязан к клиенту, а не к лендингу: клиент один раз подключает,
    например, свой Telegram-чат, и потом любое количество его лендингов могут
    маршрутизировать уведомления в этот канал через ``LandingRoute``.

    Атрибуты:
        client_id: Владелец канала.
        type: Тип канала, определяет интерпретацию ``address`` и ``config``.
        address: Адресная часть канала: ``chat_id`` для Telegram, email для
            почты и т. п. Хранится строкой для единообразия между типами.
        config: Дополнительные параметры, специфичные для типа (username
            чата, локаль, шаблон сообщения и т. п.).
        is_active: Если ``False``, доставка в канал пропускается.
    """

    __tablename__ = "notification_channels"
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "type",
            "address",
            name="uq_notification_channels_client_type_address",
        ),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[ChannelType] = mapped_column(
        Enum(
            ChannelType,
            name="channel_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(nullable=False)
    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
