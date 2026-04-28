"""lead — заявка, прилетевшая на лендинг."""

import uuid

from sqlalchemy import ForeignKey, Index, desc, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Lead(BaseModel):
    """Заявка с лендинга.

    Поля формы у каждого лендинга свои, поэтому ``payload`` хранится JSONB.
    Метаданные источника (utm-метки, ip, user-agent, реферер) изолированы в
    отдельном ``source_meta``, чтобы не смешивать с бизнес-полями формы.

    Атрибуты:
        landing_id: Лендинг, на который пришла заявка.
        payload: Данные формы как есть (имя, телефон, текст и т. п.).
        source_meta: Технические метаданные запроса.
    """

    __tablename__ = "leads"
    __table_args__ = (
        # Hot path админки: «последние заявки лендинга». Композитный индекс
        # покрывает и фильтр по landing_id, и сортировку по времени, поэтому
        # отдельный индекс на landing_id здесь не нужен.
        Index(
            "ix_leads_landing_id_created_at",
            "landing_id",
            desc("created_at"),
        ),
    )

    landing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("landings.id", ondelete="CASCADE"),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    source_meta: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
