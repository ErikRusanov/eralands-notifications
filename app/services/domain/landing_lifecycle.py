"""landing_lifecycle — операции над жизненным циклом отдельного лендинга.

Закрывает бизнес-кейсы 4 и 6: отключение конкретного лендинга и выдача
дополнительного одноразового кода для подключения нового канала
(например, добавление сотрудника клиента).
"""

import uuid
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.core.config import settings
from app.models import Landing
from app.schemas import LinkingCodeResponse
from app.services.db import LandingService, LinkingCodeService
from app.services.domain.errors import NotFoundError
from app.utils import generate_linking_code


class _LandingActivation(BaseModel):
    """Частичный апдейт активности лендинга."""

    is_active: bool


class _LinkingCodeNew(BaseModel):
    """Полный набор полей для INSERT-а ``LinkingCode``."""

    landing_id: uuid.UUID
    code: str
    expires_at: datetime


class LandingLifecycleService:
    """Операции отключения и выдачи кодов привязки для лендинга."""

    def __init__(
        self,
        landings: LandingService,
        linking_codes: LinkingCodeService,
    ) -> None:
        self.landings = landings
        self.linking_codes = linking_codes

    async def set_active(self, landing_id: uuid.UUID, is_active: bool) -> Landing:
        """Меняет флаг активности конкретного лендинга и возвращает его.

        Поднимает:
            NotFoundError: Если лендинг не найден.
        """
        landing = await self.landings.get(landing_id)
        if landing is None:
            raise NotFoundError("Landing not found.")
        return await self.landings.update(
            landing, _LandingActivation(is_active=is_active)
        )

    async def issue_linking_code(self, landing_id: uuid.UUID) -> LinkingCodeResponse:
        """Выдаёт новый одноразовый код привязки для лендинга.

        Поднимает:
            NotFoundError: Если лендинг не найден.
        """
        landing = await self.landings.get(landing_id)
        if landing is None:
            raise NotFoundError("Landing not found.")

        plain_code = generate_linking_code(settings.linking_code.LENGTH)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.linking_code.TTL_MINUTES
        )
        await self.linking_codes.create(
            _LinkingCodeNew(
                landing_id=landing.id,
                code=plain_code,
                expires_at=expires_at,
            )
        )
        return LinkingCodeResponse(code=plain_code, expires_at=expires_at)
