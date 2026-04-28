"""health — схема ответа health-check эндпоинта."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Тело ответа эндпоинта ``GET /api/health``.

    Атрибуты:
        status: Человекочитаемый операционный статус сервиса.
            Всегда ``"ok"`` после успешного старта.
    """

    status: str = Field(
        ...,
        description="Операционный статус сервиса.",
        examples=["ok"],
    )
