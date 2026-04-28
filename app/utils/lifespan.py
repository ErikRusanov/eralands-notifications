"""lifespan — context manager жизненного цикла FastAPI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управляет стартом и остановкой сервиса.

    Аргументы:
        app: Экземпляр ``FastAPI``, чьим жизненным циклом управляем.

    Yields:
        None: Передаёт управление приложению между фазами старта и остановки.
    """
    logger.info("Backend starting up.")
    yield
    logger.info("Backend shutting down.")
