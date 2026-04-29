"""client_lifecycle — операции над жизненным циклом клиента и read-проекции.

Закрывает бизнес-кейс 3 (массовое включение/отключение лендингов клиента)
и админские listing-операции по клиентам.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass

from app.models import Client, Landing, NotificationChannel
from app.services.db import (
    ClientService,
    LandingService,
    NotificationChannelService,
)
from app.services.domain.errors import NotFoundError


@dataclass(slots=True)
class ClientWithLandings:
    """Клиент в паре со списком его лендингов."""

    client: Client
    landings: list[Landing]


class ClientLifecycleService:
    """Управление активностью клиента и его лендингов плюс админский read."""

    def __init__(
        self,
        clients: ClientService,
        landings: LandingService,
        channels: NotificationChannelService,
    ) -> None:
        self.clients = clients
        self.landings = landings
        self.channels = channels

    async def set_active(
        self, client_id: uuid.UUID, is_active: bool
    ) -> ClientWithLandings:
        """Каскадно ставит ``is_active`` на всех лендингах клиента.

        Сама запись клиента не имеет такого флага: при возобновлении услуг
        лендинги и каналы реактивируются массово, без повторной выдачи
        токенов и кодов.

        Возвращает свежую карточку клиента с обновлёнными лендингами.

        Поднимает:
            NotFoundError: Если клиент не найден.
        """
        client = await self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Client not found.")
        await self.landings.set_active_by_client(client_id, is_active=is_active)
        landings = await self.landings.list_by_client_ids([client_id])
        return ClientWithLandings(client=client, landings=landings)

    async def list_with_landings(self) -> list[ClientWithLandings]:
        """Возвращает всех клиентов вместе с их лендингами одним батчем.

        Делается двумя запросами без relationship-а: один на клиентов,
        второй — на их лендинги по ``IN (client_ids)``. Группировка в
        Python тривиальна и не требует ORM-связи.
        """
        clients = await self.clients.list_all()
        if not clients:
            return []

        landings = await self.landings.list_by_client_ids([c.id for c in clients])
        by_client: dict[uuid.UUID, list[Landing]] = defaultdict(list)
        for landing in landings:
            by_client[landing.client_id].append(landing)

        return [
            ClientWithLandings(client=client, landings=by_client.get(client.id, []))
            for client in clients
        ]

    async def list_channels(self, client_id: uuid.UUID) -> list[NotificationChannel]:
        """Возвращает каналы клиента.

        Поднимает:
            NotFoundError: Если клиент не найден.
        """
        client = await self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Client not found.")
        return await self.channels.list_for_client(client_id)
