"""delivery — попытка доставки заявки в конкретный канал уведомлений."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DeliveryStatus(str, enum.Enum):
    """Статус доставки заявки в канал."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Delivery(BaseModel):
    """Доставка заявки в канал.

    Один лид может породить несколько доставок (по одной на каждый активный
    маршрут лендинга). Запись хранится отдельно от ``Lead``, чтобы можно было
    повторять отправку и видеть историю по каждому каналу независимо.

    Атрибуты:
        lead_id: Заявка, которую доставляем.
        channel_id: Канал, в который идёт отправка.
        status: Текущий статус доставки.
        attempts: Сколько попыток отправки уже было сделано.
        last_error: Текст последней ошибки, если попытка зафейлилась.
        sent_at: Момент успешной отправки, ``None`` пока не доставлено.
    """

    __tablename__ = "deliveries"
    __table_args__ = (
        UniqueConstraint(
            "lead_id",
            "channel_id",
            name="uq_deliveries_lead_channel",
        ),
        # Воркер забирает pending по очереди (FIFO по created_at). Partial-индекс
        # хранит только ждущие отправки строки и не разрастается после успехов.
        Index(
            "ix_deliveries_pending_created_at",
            "created_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notification_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(
            DeliveryStatus,
            name="delivery_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=DeliveryStatus.PENDING,
        server_default=DeliveryStatus.PENDING.value,
    )
    attempts: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
