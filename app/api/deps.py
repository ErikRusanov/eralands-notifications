"""deps — зависимости FastAPI: сессия, CRUD-сервисы, доменные сервисы, auth."""

from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_api_token
from app.core.session import get_session
from app.models import Landing
from app.services.db import (
    BaseDBService,
    ClientService,
    DeliveryService,
    LandingRouteService,
    LandingService,
    LeadService,
    LinkingCodeService,
    NotificationChannelService,
)
from app.services.domain import (
    AuthError,
    ClientLifecycleService,
    LandingLifecycleService,
    LeadIntakeService,
    ProvisioningService,
    RoutingService,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]

ServiceT = TypeVar("ServiceT", bound=BaseDBService)


def _service_dep(cls: type[ServiceT]) -> Callable[[SessionDep], ServiceT]:
    """Собирает FastAPI-зависимость, возвращающую CRUD-сервис на сессии запроса.

    Аргументы:
        cls: Класс сервиса, наследник ``BaseDBService``.
    """

    def factory(session: SessionDep) -> ServiceT:
        return cls(session)

    factory.__name__ = f"get_{cls.__name__}"
    return factory


ClientServiceDep = Annotated[ClientService, Depends(_service_dep(ClientService))]
DeliveryServiceDep = Annotated[DeliveryService, Depends(_service_dep(DeliveryService))]
LandingRouteServiceDep = Annotated[
    LandingRouteService,
    Depends(_service_dep(LandingRouteService)),
]
LandingServiceDep = Annotated[LandingService, Depends(_service_dep(LandingService))]
LeadServiceDep = Annotated[LeadService, Depends(_service_dep(LeadService))]
LinkingCodeServiceDep = Annotated[
    LinkingCodeService,
    Depends(_service_dep(LinkingCodeService)),
]
NotificationChannelServiceDep = Annotated[
    NotificationChannelService,
    Depends(_service_dep(NotificationChannelService)),
]


def _provisioning_service(
    clients: ClientServiceDep,
    landings: LandingServiceDep,
    linking_codes: LinkingCodeServiceDep,
) -> ProvisioningService:
    return ProvisioningService(clients, landings, linking_codes)


def _client_lifecycle_service(
    clients: ClientServiceDep,
    landings: LandingServiceDep,
    channels: NotificationChannelServiceDep,
) -> ClientLifecycleService:
    return ClientLifecycleService(clients, landings, channels)


def _landing_lifecycle_service(
    landings: LandingServiceDep,
    linking_codes: LinkingCodeServiceDep,
) -> LandingLifecycleService:
    return LandingLifecycleService(landings, linking_codes)


def _routing_service(routes: LandingRouteServiceDep) -> RoutingService:
    return RoutingService(routes)


def _lead_intake_service(
    leads: LeadServiceDep,
    routes: LandingRouteServiceDep,
    deliveries: DeliveryServiceDep,
) -> LeadIntakeService:
    return LeadIntakeService(leads, routes, deliveries)


ProvisioningServiceDep = Annotated[ProvisioningService, Depends(_provisioning_service)]
ClientLifecycleServiceDep = Annotated[
    ClientLifecycleService, Depends(_client_lifecycle_service)
]
LandingLifecycleServiceDep = Annotated[
    LandingLifecycleService, Depends(_landing_lifecycle_service)
]
RoutingServiceDep = Annotated[RoutingService, Depends(_routing_service)]
LeadIntakeServiceDep = Annotated[LeadIntakeService, Depends(_lead_intake_service)]


_bearer = HTTPBearer(auto_error=False)
_BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def verify_admin_token(creds: _BearerDep) -> None:
    """Проверяет admin bearer-токен. Используется на роутер-уровне.

    Поднимает:
        AuthError: Если заголовок отсутствует или токен не совпадает.
    """
    if creds is None or creds.credentials != settings.api.KEY:
        raise AuthError("Invalid admin credentials.")


async def get_landing_from_token(
    creds: _BearerDep,
    landings: LandingServiceDep,
) -> Landing:
    """Резолвит лендинг по api-токену из заголовка ``Authorization: Bearer``.

    Поднимает:
        AuthError: Если заголовка нет, токен не найден или лендинг отключён.
    """
    if creds is None:
        raise AuthError("Missing API token.")
    landing = await landings.get_by_token_hash(hash_api_token(creds.credentials))
    if landing is None:
        raise AuthError("Invalid API token.")
    return landing


AdminAuth = Depends(verify_admin_token)
LandingAuthDep = Annotated[Landing, Depends(get_landing_from_token)]
