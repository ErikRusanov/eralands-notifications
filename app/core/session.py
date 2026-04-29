"""session — async движок SQLAlchemy, фабрика сессий и провайдер сессии."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Environment, settings

engine = create_async_engine(
    settings.db.url,
    echo=settings.app.ENV == Environment.DEV,
)

async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Открывает async-сессию БД, коммитит при успехе и откатывает при ошибке.

    Транзакция привязана к жизни запроса: один HTTP-запрос — одна сессия —
    один коммит. Доменные сервисы flush-ят свои изменения внутри запроса, а
    окончательная фиксация происходит здесь после возврата из обработчика.

    Yields:
        AsyncSession: Активная сессия SQLAlchemy.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
