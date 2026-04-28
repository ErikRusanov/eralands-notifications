"""env — окружение Alembic для сервиса notifications.

Запускает миграции в async online-режиме через драйвер asyncpg.
URL подключения и метаданные моделей берутся из настроек приложения и
реестра SQLAlchemy соответственно.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import settings
from app.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запускает миграции в offline-режиме (без живого подключения к БД).

    Генерирует SQL-скрипт вместо прямого исполнения. Удобно для ревью или
    ручного применения миграций.
    """
    context.configure(
        url=settings.db.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Применяет миграции на переданном синхронном соединении.

    Аргументы:
        connection: Активное синхронное соединение SQLAlchemy.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Создаёт async-движок и применяет миграции онлайн."""
    connectable = create_async_engine(settings.db.url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Точка входа для online-режима — делегирует async-раннеру."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
