"""linking — привязка Telegram-чата к лендингу по одноразовому коду.

Закрывает бизнес-кейс 3: клиент получает от Era Lands открытый код, вводит
его в боте через команду ``/link``, и сервис создаёт (или переиспользует)
канал ``NotificationChannel`` и маршрут ``LandingRoute`` лендинг → канал,
после чего гасит код.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChannelType, LinkingCode
from app.services.db import (
    ClientService,
    LandingRouteService,
    LandingService,
    LinkingCodeService,
    NotificationChannelService,
)
from app.services.domain.errors import (
    LinkingCodeExpiredError,
    LinkingCodeNotFoundError,
)


class _ChannelNew(BaseModel):
    """Полный набор полей для INSERT-а ``NotificationChannel``."""

    client_id: uuid.UUID
    type: ChannelType
    address: str
    config: dict = {}
    is_active: bool = True


class _ChannelActivation(BaseModel):
    """Частичный апдейт активности канала."""

    is_active: bool


class _RouteNew(BaseModel):
    """Полный набор полей для INSERT-а ``LandingRoute``."""

    landing_id: uuid.UUID
    channel_id: uuid.UUID
    is_active: bool = True


class _RouteActivation(BaseModel):
    """Частичный апдейт активности маршрута."""

    is_active: bool


class _LinkingCodeRedeem(BaseModel):
    """Частичный апдейт кода: погашение (used_at + used_by_chat_id)."""

    used_at: datetime
    used_by_chat_id: int


@dataclass(slots=True, frozen=True)
class LinkResult:
    """Результат успешной привязки, видимый пользователю в боте.

    Атрибуты:
        landing_name: Имя лендинга (``Landing.name``).
        client_name: Имя владельца лендинга (``Client.name``).
        routes_count: Сколько активных маршрутов теперь у лендинга.
    """

    landing_name: str
    client_name: str
    routes_count: int


class LinkingService:
    """Привязка Telegram-чата к лендингу по одноразовому коду."""

    def __init__(
        self,
        clients: ClientService,
        landings: LandingService,
        linking_codes: LinkingCodeService,
        channels: NotificationChannelService,
        routes: LandingRouteService,
    ) -> None:
        self.clients = clients
        self.landings = landings
        self.linking_codes = linking_codes
        self.channels = channels
        self.routes = routes

    @classmethod
    def from_session(cls, session: AsyncSession) -> "LinkingService":
        """Собирает сервис со всеми CRUD-зависимостями на одной сессии.

        Используется вне FastAPI (например, в боте), где нет ``Depends``.
        Внутри FastAPI сборка идёт через ``app.api.deps``.
        """
        return cls(
            clients=ClientService(session),
            landings=LandingService(session),
            linking_codes=LinkingCodeService(session),
            channels=NotificationChannelService(session),
            routes=LandingRouteService(session),
        )

    async def link_telegram_chat(self, code: str, chat_id: int) -> LinkResult:
        """Привязывает Telegram-чат к лендингу, помечает код погашенным.

        Идемпотентно: если канал и/или маршрут уже существуют, они
        переиспользуются и при необходимости реактивируются.

        Аргументы:
            code: Уже нормализованный (strip+upper) код от пользователя.
            chat_id: ``message.chat.id`` отправителя в Telegram.

        Возвращает:
            ``LinkResult`` для отображения в боте.

        Поднимает:
            LinkingCodeNotFoundError: Кода нет в БД либо он уже погашен.
            LinkingCodeExpiredError: Код есть и не погашен, но протух.
        """
        lc = await self.linking_codes.get_by_code(code)
        if lc is None or lc.used_at is not None:
            raise LinkingCodeNotFoundError("Linking code not found.")

        now = datetime.now(UTC)
        if lc.expires_at <= now:
            raise LinkingCodeExpiredError("Linking code expired.")

        # Штатно лендинг и клиент не могут пропасть «под кодом»: FK от
        # LinkingCode к Landing и от Landing к Client каскадные. Но на гонку
        # с конкурентным DELETE в той же транзакции БД полагаться не стоит —
        # без guard'а упадёт AttributeError → 500. Семантически отсутствующий
        # лендинг/клиент означает, что код больше ни к чему не привязан, так
        # что отдаём «not found».
        landing = await self.landings.get(lc.landing_id)
        if landing is None:
            raise LinkingCodeNotFoundError("Linking code not found.")
        client = await self.clients.get(landing.client_id)
        if client is None:
            raise LinkingCodeNotFoundError("Linking code not found.")

        channel, _created = await self.channels.get_or_create(
            _ChannelNew(
                client_id=client.id,
                type=ChannelType.TELEGRAM,
                address=str(chat_id),
            ),
            by=("client_id", "type", "address"),
        )
        if not channel.is_active:
            await self.channels.update(channel, _ChannelActivation(is_active=True))

        route = await self.routes.get_by_landing_channel(landing.id, channel.id)
        if route is None:
            await self.routes.create(
                _RouteNew(landing_id=landing.id, channel_id=channel.id)
            )
        elif not route.is_active:
            await self.routes.update(route, _RouteActivation(is_active=True))

        await self._redeem(lc, now=now, chat_id=chat_id)

        routes_count = await self.routes.count_active_for_landing(landing.id)

        return LinkResult(
            landing_name=landing.name,
            client_name=client.name,
            routes_count=routes_count,
        )

    async def _redeem(self, lc: LinkingCode, *, now: datetime, chat_id: int) -> None:
        """Помечает код использованным и фиксирует chat_id для аудита."""
        await self.linking_codes.update(
            lc, _LinkingCodeRedeem(used_at=now, used_by_chat_id=chat_id)
        )
