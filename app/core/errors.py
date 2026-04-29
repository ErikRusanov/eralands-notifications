"""errors — обработчики исключений FastAPI с унифицированным телом ошибки."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi import status as http_status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import ErrorResponse
from app.services.domain import (
    AuthError,
    ConflictError,
    DomainError,
    NotFoundError,
)

_DOMAIN_STATUS_MAP: dict[type[DomainError], int] = {
    AuthError: http_status.HTTP_401_UNAUTHORIZED,
    NotFoundError: http_status.HTTP_404_NOT_FOUND,
    ConflictError: http_status.HTTP_409_CONFLICT,
}

logger = logging.getLogger(__name__)


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Обрабатывает ``HTTPException`` и возвращает унифицированное тело ошибки.

    Аргументы:
        request: Входящий запрос, вызвавший исключение.
        exc: Поднятое ``HTTPException``.

    Возвращает:
        JSONResponse со статусом ``exc.status_code`` и телом ``ErrorResponse``.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=str(exc.detail)).model_dump(),
    )


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обрабатывает ``RequestValidationError`` и возвращает унифицированное тело.

    Форматирует первую ошибку валидации как ``"<location>: <message>"``,
    например ``"body.weight: value is not a valid float"``.

    Аргументы:
        request: Входящий запрос, вызвавший исключение.
        exc: Поднятое ``RequestValidationError``.

    Возвращает:
        JSONResponse со статусом 422 и телом ``ErrorResponse``.
    """
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.get("loc", []))
        msg = first.get("msg", "Validation error.")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Validation error."

    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(detail=detail).model_dump(),
    )


async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Маппит доменное исключение в HTTP-код по таблице ``_DOMAIN_STATUS_MAP``.

    Неизвестные подклассы ``DomainError`` фолбечат на 400.
    """
    status_code = _DOMAIN_STATUS_MAP.get(type(exc), http_status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Обрабатывает любое необработанное исключение и возвращает общее тело ошибки.

    Логирует полный traceback и возвращает 500, чтобы не раскрывать клиенту
    внутренние детали.

    Аргументы:
        request: Входящий запрос, вызвавший исключение.
        exc: Необработанное исключение.

    Возвращает:
        JSONResponse со статусом 500 и телом ``ErrorResponse``.
    """
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(detail="Internal server error.").model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует все обработчики исключений на FastAPI-приложении.

    Устанавливает обработчики для:
    - ``HTTPException`` — возвращает HTTP-статус с унифицированным телом.
    - ``RequestValidationError`` — возвращает 422 с форматированной ошибкой поля.
    - ``Exception`` — возвращает 500 и логирует полный traceback.

    Аргументы:
        app: Экземпляр ``FastAPI``, на котором регистрируются обработчики.
    """
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(DomainError, _domain_error_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
