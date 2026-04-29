"""schemas — Pydantic-схемы запросов и ответов API."""

from app.schemas.client import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    ClientWithLandingsResponse,
)
from app.schemas.error import ErrorResponse
from app.schemas.health import HealthResponse
from app.schemas.landing import (
    LandingCreate,
    LandingResponse,
    LandingUpdate,
    ProvisionedLandingResponse,
)
from app.schemas.lead import LeadAcceptedResponse, LeadCreate
from app.schemas.linking_code import LinkingCodeResponse
from app.schemas.notification_channel import NotificationChannelResponse

__all__ = [
    "ClientCreate",
    "ClientResponse",
    "ClientUpdate",
    "ClientWithLandingsResponse",
    "ErrorResponse",
    "HealthResponse",
    "LandingCreate",
    "LandingResponse",
    "LandingUpdate",
    "LeadAcceptedResponse",
    "LeadCreate",
    "LinkingCodeResponse",
    "NotificationChannelResponse",
    "ProvisionedLandingResponse",
]
