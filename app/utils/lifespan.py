"""lifespan — context manager жизненного цикла FastAPI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управляет стартом и остановкой сервиса.

    На старте проверяет коннект к БД (``SELECT 1``), затем поднимает Telegram-бота
    и сохраняет ``Bot``/``Dispatcher`` в ``app.state`` — оттуда их забирает
    webhook-эндпоинт. На остановке снимает webhook у Telegram, закрывает HTTP-сессию
    бота и освобождает пул соединений БД.

    Аргументы:
        app: Экземпляр ``FastAPI``, чьим жизненным циклом управляем.

    Yields:
        None: Передаёт управление приложению между фазами старта и остановки.
    """
    # Отложенный импорт: на module-import-time он создал бы цикл
    # app.api.deps -> app.bot.utils -> app.core.config -> app.core.__init__
    # -> app.core.get_app -> app.utils.lifespan -> app.bot.utils.
    from app.bot.utils import setup_bot, teardown_bot

    logger.info("Backend starting up.")
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection OK.")
    bot, dp = await setup_bot()
    app.state.bot = bot
    app.state.dp = dp
    app.state.replies = dp["replies"]
    try:
        yield
    finally:
        await teardown_bot(bot)
        await engine.dispose()
        logger.info("Backend shutting down.")
