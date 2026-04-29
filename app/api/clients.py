"""clients — роутер по клиентам и их лендингам."""

import uuid

from fastapi import APIRouter
from fastapi import status as http_status

from app.api.deps import (
    AdminAuth,
    ClientLifecycleServiceDep,
    ProvisioningServiceDep,
)
from app.schemas import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    ClientWithLandingsResponse,
    LandingCreate,
    LandingResponse,
    LinkingCodeResponse,
    NotificationChannelResponse,
    ProvisionedLandingResponse,
)

router = APIRouter(prefix="/clients", tags=["Clients"], dependencies=[AdminAuth])


@router.get(
    "",
    response_model=list[ClientWithLandingsResponse],
    summary="Список клиентов с их лендингами",
    description=(
        "Возвращает всех клиентов вместе со списком их лендингов одним "
        "запросом для админки. Лендинги отсортированы по времени создания."
    ),
)
async def list_clients(
    service: ClientLifecycleServiceDep,
) -> list[ClientWithLandingsResponse]:
    """Возвращает клиентов и их лендинги."""
    items = await service.list_with_landings()
    return [
        ClientWithLandingsResponse(
            id=item.client.id,
            name=item.client.name,
            created_at=item.client.created_at,
            landings=[
                LandingResponse.model_validate(landing) for landing in item.landings
            ],
        )
        for item in items
    ]


@router.post(
    "",
    response_model=ClientResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Создать клиента",
    description="Регистрирует нового клиента Era Lands в системе.",
)
async def create_client(
    data: ClientCreate, service: ProvisioningServiceDep
) -> ClientResponse:
    """Создаёт клиента и возвращает его карточку."""
    client = await service.create_client(data)
    return ClientResponse.model_validate(client)


@router.patch(
    "/{client_id}",
    response_model=ClientWithLandingsResponse,
    summary="Включить или отключить лендинги клиента",
    description=(
        "Каскадно ставит ``is_active`` на всех лендингах клиента: "
        "``false`` отключает заявки, ``true`` возвращает их в работу. "
        "Каналы и маршруты сохраняются для быстрой реактивации. "
        "Возвращает свежий список лендингов клиента."
    ),
)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    service: ClientLifecycleServiceDep,
) -> ClientWithLandingsResponse:
    """Меняет активность всех лендингов клиента и возвращает их свежий срез."""
    item = await service.set_active(client_id, is_active=data.is_active)
    return ClientWithLandingsResponse(
        id=item.client.id,
        name=item.client.name,
        created_at=item.client.created_at,
        landings=[LandingResponse.model_validate(landing) for landing in item.landings],
    )


@router.get(
    "/{client_id}/channels",
    response_model=list[NotificationChannelResponse],
    summary="Каналы уведомлений клиента",
    description=(
        "Возвращает все каналы клиента: TG-чаты, email-адреса и т. п. "
        "Используется, чтобы узнать ``channel_id`` для ``DELETE "
        "/landings/{landing_id}/routes/{channel_id}``."
    ),
)
async def list_client_channels(
    client_id: uuid.UUID,
    service: ClientLifecycleServiceDep,
) -> list[NotificationChannelResponse]:
    """Возвращает каналы клиента."""
    channels = await service.list_channels(client_id)
    return [NotificationChannelResponse.model_validate(channel) for channel in channels]


@router.post(
    "/{client_id}/landings",
    response_model=ProvisionedLandingResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Создать лендинг клиенту",
    description=(
        "Создаёт лендинг и в той же операции выдаёт открытый api-токен и "
        "одноразовый код привязки канала. Открытый токен видно только в "
        "ответе и больше нигде не сохраняется."
    ),
)
async def provision_landing(
    client_id: uuid.UUID,
    data: LandingCreate,
    service: ProvisioningServiceDep,
) -> ProvisionedLandingResponse:
    """Провижинит лендинг клиенту: лендинг + токен + код привязки."""
    result = await service.provision_landing(client_id, data)
    return ProvisionedLandingResponse(
        landing=LandingResponse.model_validate(result.landing),
        api_token=result.api_token,
        linking_code=LinkingCodeResponse(
            code=result.linking_code,
            expires_at=result.code_expires_at,
        ),
    )
