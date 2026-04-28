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
    """Открывает async-сессию БД и закрывает её после завершения запроса.

    Yields:
        AsyncSession: Активная сессия SQLAlchemy.
    """
    async with async_session_maker() as session:
        yield session
