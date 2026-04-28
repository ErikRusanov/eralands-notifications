"""deps — зависимости FastAPI."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Открывает async-сессию БД и закрывает её после завершения запроса.

    Yields:
        AsyncSession: Активная сессия SQLAlchemy.
    """
    async with async_session_maker() as session:
        yield session
