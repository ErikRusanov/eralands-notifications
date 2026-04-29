"""leads — роутер приёма заявок с лендингов по api-токену."""

from fastapi import APIRouter
from fastapi import status as http_status

from app.api.deps import LandingAuthDep, LeadIntakeServiceDep
from app.schemas import LeadAcceptedResponse, LeadCreate

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post(
    "",
    response_model=LeadAcceptedResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Принять заявку с лендинга",
    description=(
        "Аутентификация по ``Authorization: Bearer <api_token>`` лендинга. "
        "Сервис создаёт ``Lead`` с переданным ``payload`` и для каждого "
        "активного маршрута лендинга порождает ``Delivery`` в статусе "
        "``pending``. Сама отправка в каналы — задача воркера."
    ),
)
async def accept_lead(
    data: LeadCreate,
    landing: LandingAuthDep,
    service: LeadIntakeServiceDep,
) -> LeadAcceptedResponse:
    """Принимает заявку и инициирует фан-аут доставок."""
    lead = await service.accept(landing, data.payload, data.source_meta)
    return LeadAcceptedResponse(id=lead.id, accepted_at=lead.created_at)
