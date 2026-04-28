"""deps — зависимости FastAPI."""

from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_session
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

SessionDep = Annotated[AsyncSession, Depends(get_session)]

ServiceT = TypeVar("ServiceT", bound=BaseDBService)


def _service_dep(cls: type[ServiceT]) -> Callable[[SessionDep], ServiceT]:
    """Собирает FastAPI-зависимость, возвращающую сервис на сессии запроса.

    Аргументы:
        cls: Класс сервиса, наследник ``BaseDBService``.

    Возвращает:
        Функцию, пригодную для ``Depends``, которая принимает сессию из
        ``get_session`` и инстанцирует переданный сервис.
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
