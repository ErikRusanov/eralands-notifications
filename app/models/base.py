"""base — декларативная база и абстрактный миксин для ORM-моделей."""

import uuid
from datetime import datetime

import uuid_utils
from sqlalchemy import UUID, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid7() -> uuid.UUID:
    """Возвращает UUIDv7 как стандартный ``uuid.UUID``.

    UUIDv7 монотонен по времени, что даёт почти-апенд-вставки в B-tree
    PK-индекса и снимает фрагментацию, типичную для случайных UUIDv4.
    """

    return uuid.UUID(bytes=uuid_utils.uuid7().bytes)


class Base(DeclarativeBase):
    """Корневая декларативная база SQLAlchemy.

    Все ORM-модели наследуются от неё, чтобы ``Base.metadata`` собрал все
    таблицы для автогенерации миграций.
    """


class BaseModel(Base):
    """Абстрактный миксин с общими аудит-полями.

    Атрибуты:
        id: UUIDv7, генерируется на стороне приложения при вставке.
        created_at: Метка времени с TZ, выставляется БД при вставке.
        updated_at: Метка времени с TZ, обновляется БД при каждом write.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid7,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
