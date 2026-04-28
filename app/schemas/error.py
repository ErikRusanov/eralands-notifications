"""error — Pydantic-схема унифицированного тела ошибки API."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Унифицированное тело ошибки, возвращаемое всеми обработчиками исключений.

    Атрибуты:
        detail: Человекочитаемое описание того, что пошло не так.
    """

    detail: str = Field(
        ...,
        description="Человекочитаемое описание ошибки.",
        examples=["Not found.", "Internal server error."],
    )
