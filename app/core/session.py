"""session — async движок SQLAlchemy и фабрика сессий."""

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
