"""get_app — фабрика FastAPI-приложения."""

from fastapi import FastAPI

from app.api import router
from app.core.config import Environment, settings
from app.core.errors import register_exception_handlers
from app.middleware import LoggingMiddleware
from app.utils.lifespan import lifespan

_DOCS_URL = "/docs"
_REDOC_URL = "/redoc"


def create_app() -> FastAPI:
    """Создаёт и полностью конфигурирует экземпляр FastAPI.

    Регистрирует middleware логирования, унифицированные обработчики ошибок и
    API-роутер. Swagger UI (``/docs``) и ReDoc (``/redoc``) доступны только
    когда ``APP__ENV`` не равно ``"prod"``.

    Возвращает:
        FastAPI: Настроенный экземпляр приложения, готовый к запуску под uvicorn.
    """
    is_prod = settings.app.ENV == Environment.PROD
    app = FastAPI(
        title="Eralands Notifications API",
        description="REST API для приёма заявок с лендингов.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if is_prod else _DOCS_URL,
        redoc_url=None if is_prod else _REDOC_URL,
    )
    app.add_middleware(LoggingMiddleware)
    register_exception_handlers(app)
    app.include_router(router)
    return app
