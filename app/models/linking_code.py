"""linking_code — одноразовый код для привязки канала уведомлений к лендингу."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LinkingCode(BaseModel):
    """Одноразовый код привязки.

    Era Lands создаёт код для лендинга и отдаёт клиенту. Клиент в боте вводит
    код, мы создаём (или переиспользуем) канал и маршрут лендинг → канал, после
    чего код считается погашенным и повторно не используется.

    Атрибуты:
        landing_id: Лендинг, к которому привяжется канал.
        code: Короткий уникальный код, выдаваемый клиенту.
        expires_at: До какого момента код валиден.
        used_at: Момент погашения, ``None`` пока код не использован.
        used_by_chat_id: Telegram chat_id, который ввёл код, для аудита.
    """

    __tablename__ = "linking_codes"
    __table_args__ = (
        # Cleanup-job ходит по протухшим неиспользованным кодам. Partial-индекс
        # хранит только активные коды, не разрастается после погашения.
        Index(
            "ix_linking_codes_active_expires_at",
            "expires_at",
            postgresql_where=text("used_at IS NULL"),
        ),
    )

    landing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("landings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    used_by_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
