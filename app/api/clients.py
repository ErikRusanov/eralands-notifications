"""clients — роутер по клиентам и их лендингам."""

import uuid

from fastapi import APIRouter, Response
from fastapi import status as http_status

from app.api.deps import (
    AdminAuth,
    ClientLifecycleServiceDep,
    ProvisioningServiceDep,
)
from app.schemas import (
    ClientCreate,
    ClientResponse,
    LandingCreate,
    LandingResponse,
    LinkingCodeResponse,
    ProvisionedLandingResponse,
)

router = APIRouter(prefix="/clients", tags=["Clients"], dependencies=[AdminAuth])


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


@router.post(
    "/{client_id}/disable",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Отключить уведомления у всех лендингов клиента",
    description=(
        "Используется при прекращении услуг. Все лендинги клиента переходят "
        "в ``is_active=False``, заявки на них отклоняются. Каналы и маршруты "
        "сохраняются для быстрой реактивации."
    ),
)
async def disable_client(
    client_id: uuid.UUID, service: ClientLifecycleServiceDep
) -> Response:
    """Гасит уведомления на всех лендингах клиента."""
    await service.disable(client_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


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
