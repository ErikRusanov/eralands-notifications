"""landings — роутер по лендингам, их кодам привязки и маршрутам."""

import uuid

from fastapi import APIRouter, Response
from fastapi import status as http_status

from app.api.deps import (
    AdminAuth,
    LandingLifecycleServiceDep,
    RoutingServiceDep,
)
from app.schemas import LinkingCodeResponse

router = APIRouter(prefix="/landings", tags=["Landings"], dependencies=[AdminAuth])


@router.post(
    "/{landing_id}/disable",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Отключить уведомления у конкретного лендинга",
    description=(
        "Лендинг переходит в ``is_active=False``: заявки на него отклоняются, "
        "доставки не создаются. Маршруты и каналы сохраняются."
    ),
)
async def disable_landing(
    landing_id: uuid.UUID, service: LandingLifecycleServiceDep
) -> Response:
    """Гасит уведомления конкретного лендинга."""
    await service.disable(landing_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


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
