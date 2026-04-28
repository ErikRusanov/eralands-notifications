"""health — роутер для health-check эндпоинта."""

from fastapi import APIRouter
from fastapi import status as http_status

from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Проверка состояния сервиса",
    description=(
        "Возвращает текущий операционный статус сервиса. Используется для "
        "liveness-проб и мониторинга аптайма."
    ),
    responses={
        http_status.HTTP_200_OK: {"description": "Сервис здоров и работает."},
    },
)
async def health() -> HealthResponse:
    """Возвращает операционный статус сервиса.

    Возвращает:
        HealthResponse: Ответ с ``status="ok"`` пока сервис работает нормально.
    """
    return HealthResponse(status="ok")
