"""landing — лендинг клиента, на который прилетают заявки."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Landing(BaseModel):
    """Лендинг клиента.

    Атрибуты:
        client_id: Владелец лендинга.
        slug: Человеко-читаемый идентификатор для URL и логов.
        name: Отображаемое имя в админке и в уведомлениях.
        api_token_hash: SHA-256 hex-хеш токена, которым лендинг
            аутентифицирует входящие заявки. Открытый токен не хранится.
        is_active: Если ``False``, заявки отвергаются, доставка не создаётся.
    """

    __tablename__ = "landings"

    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    api_token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
