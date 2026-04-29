"""client_lifecycle — операции над жизненным циклом клиента.

Закрывает бизнес-кейс 3: клиент перестал платить, нужно отключить
уведомления для всех его лендингов.
"""

import uuid

from app.services.db import ClientService, LandingService
from app.services.domain.errors import NotFoundError


class ClientLifecycleService:
    """Управление активностью клиента и его лендингов."""

    def __init__(
        self,
        clients: ClientService,
        landings: LandingService,
    ) -> None:
        self.clients = clients
        self.landings = landings

    async def disable(self, client_id: uuid.UUID) -> None:
        """Отключает уведомления на всех лендингах клиента.

        Сама запись клиента сохраняется: при возобновлении услуг лендинги
        и каналы переактивируются массово, без повторной выдачи токенов.

        Поднимает:
            NotFoundError: Если клиент не найден.
        """
        client = await self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Client not found.")
        await self.landings.set_active_by_client(client_id, is_active=False)
