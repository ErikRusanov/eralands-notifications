"""domain — сервисы бизнес-процессов поверх per-model CRUD.

Каждый доменный сервис отвечает за один бизнес-процесс и оркестрирует
несколько ``BaseDBService``-наследников. Сервисы не управляют транзакцией:
flush делает вызванный CRUD, commit делает ``get_session`` после возврата
из обработчика. Доменные ошибки (``app.services.domain.errors``) маппятся
в HTTP-коды в ``app.core.errors``.
"""

from app.services.domain.client_lifecycle import (
    ClientLifecycleService,
    ClientWithLandings,
)
from app.services.domain.dispatch import DispatchService
from app.services.domain.errors import (
    AuthError,
    ConflictError,
    DomainError,
    LinkingCodeExpiredError,
    LinkingCodeNotFoundError,
    NotFoundError,
)
from app.services.domain.landing_lifecycle import LandingLifecycleService
from app.services.domain.lead_intake import LeadIntakeService
from app.services.domain.linking import LinkingService, LinkResult
from app.services.domain.provisioning import (
    ProvisionedLanding,
    ProvisioningService,
)
from app.services.domain.routing import RoutingService

__all__ = [
    "AuthError",
    "ClientLifecycleService",
    "ClientWithLandings",
    "ConflictError",
    "DispatchService",
    "DomainError",
    "LandingLifecycleService",
    "LeadIntakeService",
    "LinkResult",
    "LinkingCodeExpiredError",
    "LinkingCodeNotFoundError",
    "LinkingService",
    "NotFoundError",
    "ProvisionedLanding",
    "ProvisioningService",
    "RoutingService",
]
