"""provisioning — провижининг клиента и лендинга.

Закрывает бизнес-кейсы 1 и 2: новый клиент с лендингом и уже существующий
клиент с дополнительным лендингом. В обоих случаях операция выдаёт открытый
api-токен лендинга и одноразовый код привязки канала.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.core.config import settings
from app.core.security import hash_api_token
from app.models import Client, Landing
from app.schemas import ClientCreate, LandingCreate
from app.services.db import (
    ClientService,
    LandingService,
    LinkingCodeService,
)
from app.services.domain.errors import ConflictError, NotFoundError
from app.utils import generate_api_token, generate_linking_code


class _LandingNew(BaseModel):
    """Полный набор полей для INSERT-а ``Landing``."""

    client_id: uuid.UUID
    slug: str
    name: str
    api_token_hash: str


class _LinkingCodeNew(BaseModel):
    """Полный набор полей для INSERT-а ``LinkingCode``."""

    landing_id: uuid.UUID
    code: str
    expires_at: datetime


@dataclass(slots=True)
class ProvisionedLanding:
    """Результат провижининга лендинга, видимый владельцу один раз.

    Атрибуты:
        landing: Свежесозданный ORM-объект лендинга.
        api_token: Открытый api-токен. В БД хранится только его SHA-256 хеш.
        linking_code: Открытый одноразовый код привязки канала.
        code_expires_at: До какого момента код валиден.
    """

    landing: Landing
    api_token: str
    linking_code: str
    code_expires_at: datetime


class ProvisioningService:
    """Сервис провижининга клиентов и лендингов."""

    def __init__(
        self,
        clients: ClientService,
        landings: LandingService,
        linking_codes: LinkingCodeService,
    ) -> None:
        self.clients = clients
        self.landings = landings
        self.linking_codes = linking_codes

    async def create_client(self, data: ClientCreate) -> Client:
        """Создаёт нового клиента Era Lands."""
        return await self.clients.create(data)

    async def provision_landing(
        self, client_id: uuid.UUID, data: LandingCreate
    ) -> ProvisionedLanding:
        """Создаёт лендинг и одноразовый код для подключения канала.

        Аргументы:
            client_id: Владелец лендинга. Должен существовать.
            data: Входные данные лендинга от админа.

        Возвращает:
            ``ProvisionedLanding`` с открытым api-токеном и кодом привязки.

        Поднимает:
            NotFoundError: Если клиент не найден.
            ConflictError: Если ``slug`` уже занят другим лендингом.
        """
        client = await self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Client not found.")

        existing_by_slug = await self.landings.get_by_slug(data.slug)
        if existing_by_slug is not None:
            raise ConflictError("Landing with this slug already exists.")

        plain_api_token = generate_api_token()
        landing = await self.landings.create(
            _LandingNew(
                client_id=client_id,
                slug=data.slug,
                name=data.name,
                api_token_hash=hash_api_token(plain_api_token),
            )
        )

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

        return ProvisionedLanding(
            landing=landing,
            api_token=plain_api_token,
            linking_code=plain_code,
            code_expires_at=expires_at,
        )
