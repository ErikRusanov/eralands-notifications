"""landings — роутер по лендингам, их кодам привязки и маршрутам."""

import uuid

from fastapi import APIRouter, Response
from fastapi import status as http_status

from app.api.deps import (
    AdminAuth,
    LandingLifecycleServiceDep,
    RoutingServiceDep,
)
from app.schemas import LandingResponse, LandingUpdate, LinkingCodeResponse

router = APIRouter(prefix="/landings", tags=["Landings"], dependencies=[AdminAuth])


@router.patch(
    "/{landing_id}",
    response_model=LandingResponse,
    summary="Включить или отключить лендинг",
    description=(
        "Меняет ``is_active`` у конкретного лендинга. При ``false`` заявки "
        "отклоняются и доставки не создаются, но маршруты и каналы "
        "сохраняются для быстрой реактивации."
    ),
)
async def update_landing(
    landing_id: uuid.UUID,
    data: LandingUpdate,
    service: LandingLifecycleServiceDep,
) -> LandingResponse:
    """Обновляет флаг активности лендинга и возвращает свежий объект."""
    landing = await service.set_active(landing_id, is_active=data.is_active)
    return LandingResponse.model_validate(landing)


@router.post(
    "/{landing_id}/linking-codes",
    response_model=LinkingCodeResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Выдать одноразовый код привязки канала",
    description=(
        "Используется, когда клиент хочет подключить ещё один канал "
        "(например, добавить TG-аккаунт сотрудника). Код вводится в боте, "
        "после чего к лендингу добавляется новый маршрут."
    ),
)
async def issue_linking_code(
    landing_id: uuid.UUID, service: LandingLifecycleServiceDep
) -> LinkingCodeResponse:
    """Возвращает свежий одноразовый код привязки для лендинга."""
    return await service.issue_linking_code(landing_id)


@router.delete(
    "/{landing_id}/routes/{channel_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Отвязать канал от лендинга",
    description=(
        "Деактивирует маршрут лендинга в указанный канал: TG-аккаунт "
        "перестанет получать уведомления именно с этого лендинга. Сам канал "
        "и его маршруты на других лендингах остаются активными."
    ),
)
async def unlink_channel(
    landing_id: uuid.UUID,
    channel_id: uuid.UUID,
    service: RoutingServiceDep,
) -> Response:
    """Деактивирует маршрут ``(landing_id, channel_id)``."""
    await service.unlink_channel(landing_id, channel_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
