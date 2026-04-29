"""schemas — Pydantic-схемы запросов и ответов API."""

from app.schemas.client import ClientCreate, ClientResponse
from app.schemas.error import ErrorResponse
from app.schemas.health import HealthResponse
from app.schemas.landing import (
    LandingCreate,
    LandingResponse,
    ProvisionedLandingResponse,
)
from app.schemas.lead import LeadAcceptedResponse, LeadCreate
from app.schemas.linking_code import LinkingCodeResponse

__all__ = [
    "ClientCreate",
    "ClientResponse",
    "ErrorResponse",
    "HealthResponse",
    "LandingCreate",
    "LandingResponse",
    "LeadAcceptedResponse",
    "LeadCreate",
    "LinkingCodeResponse",
    "ProvisionedLandingResponse",
]
