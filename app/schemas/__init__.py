"""schemas — Pydantic-схемы запросов и ответов API.

Публичный API
-------------
ErrorResponse  : Унифицированное тело ошибки для всех обработчиков исключений.
HealthResponse : Тело ответа health-check эндпоинта.
"""

from app.schemas.error import ErrorResponse
from app.schemas.health import HealthResponse

__all__ = ["ErrorResponse", "HealthResponse"]
