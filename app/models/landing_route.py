"""landing_route — связка «лендинг → канал уведомлений» (M:N)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LandingRoute(BaseModel):
    """Маршрут доставки заявок лендинга в конкретный канал.

    Один лендинг может иметь несколько маршрутов (TG владельца + email
    бухгалтера + TG менеджера). Один канал может быть подключён к нескольким
    лендингам одного и того же клиента.

    Атрибуты:
        landing_id: Лендинг, заявки которого маршрутизируются.
        channel_id: Канал доставки.
        is_active: Если ``False``, доставка по маршруту пропускается, но
            запись сохраняется для аудита и быстрой реактивации.
    """

    __tablename__ = "landing_routes"
    __table_args__ = (
        UniqueConstraint(
            "landing_id",
            "channel_id",
            name="uq_landing_routes_landing_channel",
        ),
    )

    landing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("landings.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notification_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
