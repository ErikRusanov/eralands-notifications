"""lifespan — context manager жизненного цикла FastAPI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bot.utils import setup_bot, teardown_bot

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управляет стартом и остановкой сервиса.

    На старте поднимает Telegram-бота и сохраняет ``Bot``/``Dispatcher`` в
    ``app.state`` — оттуда их забирает webhook-эндпоинт. На остановке снимает
    webhook у Telegram и закрывает HTTP-сессию бота.

    Аргументы:
        app: Экземпляр ``FastAPI``, чьим жизненным циклом управляем.

    Yields:
        None: Передаёт управление приложению между фазами старта и остановки.
    """
    logger.info("Backend starting up.")
    bot, dp = await setup_bot()
    app.state.bot = bot
    app.state.dp = dp
    try:
        yield
    finally:
        await teardown_bot(bot)
        logger.info("Backend shutting down.")
