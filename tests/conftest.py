"""conftest — общие фикстуры для pipeline-тестов."""

import os

# Переменные окружения должны быть выставлены ДО импорта app.*, потому что
# app.core.config.settings читает их при импорте.
os.environ.setdefault("DB__NAME", "notifications_test")
os.environ.setdefault("DB__PASSWORD", "notifications")
os.environ.setdefault("DB__HOST", "localhost")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "notifications")
os.environ.setdefault("API__KEY", "test-admin-key")
os.environ.setdefault("APP__ENV", "dev")
os.environ.setdefault("APP__LOGGING_LEVEL", "WARNING")

import asyncio  # noqa: E402
import logging  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import asyncpg  # noqa: E402
import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.api import router as api_router  # noqa: E402
from app.bot.utils.replies import Replies  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.errors import register_exception_handlers  # noqa: E402
from app.core.session import get_session  # noqa: E402
from app.models import Base  # noqa: E402

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeBot:
    """Заглушка ``aiogram.Bot.send_message`` для пайплайн-тестов.

    Накапливает вызовы ``send_message`` в ``calls``. Чтобы в тесте проверить
    failure-ветку доставки, можно положить ``chat_id`` в ``fail_chat_ids`` —
    отправка в этот чат бросит ``RuntimeError``, который ``DispatchService``
    поймает и переведёт ``Delivery`` в ``failed``.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail_chat_ids: set[int] = set()
        self.fail_message: str = "forced telegram failure"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        **_: Any,
    ) -> None:
        if chat_id in self.fail_chat_ids:
            raise RuntimeError(self.fail_message)
        self.calls.append({"chat_id": chat_id, "text": text})


def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавить флаг ``--logs`` для пошагового вывода пайплайнов в консоль."""
    parser.addoption(
        "--logs",
        action="store_true",
        default=False,
        help="Печатать INFO-логи в консоль во время тестов (видно шаги пайплайна).",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Включить log_cli, если передан ``--logs``.

    По умолчанию тесты молчат. ``log_cli_level`` и ``log_cli_format`` уже
    выставлены в ``pyproject.toml``, здесь остаётся только переключить флаг
    ``log_cli`` и поднять уровень root + ``pipeline`` логгеров до INFO.
    """
    if config.getoption("--logs"):
        config.option.log_cli_level = "INFO"
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger("pipeline").setLevel(logging.INFO)


def _build_test_app(session_override, fake_bot: FakeBot) -> FastAPI:
    """Собрать FastAPI без lifespan, без реального бота и без LoggingMiddleware.

    - Реального ``aiogram.Bot`` не поднимаем: ``setup_bot`` без валидного
      TELEGRAM_TOKEN роняет старт, и Telegram API в тестах не дёргаем. Вместо
      бота в ``app.state.bot`` кладём ``FakeBot``, который ``DispatchService``
      использует так же, как и настоящего бота. Линковка чата проверяется
      прямым вызовом ``LinkingService.from_session``.
    - ``Replies`` — реальный, читает ``texts.toml`` один раз. Это позволяет
      пайплайну ассертить итоговый текст уведомления.
    - LoggingMiddleware (Starlette ``BaseHTTPMiddleware``) исключён: в связке
      с ``ASGITransport`` он создаёт TaskGroup в собственном loop, и asyncpg
      падает с «attached to a different loop». В проде с uvicorn проблема
      не воспроизводится.
    - ``get_session`` подменяется на тестовый, который сидит на engine с
      NullPool (см. фикстуру ``_test_session_maker``).
    """
    app = FastAPI(title="notifications-test")
    register_exception_handlers(app)
    app.include_router(api_router)
    app.dependency_overrides[get_session] = session_override
    app.state.bot = fake_bot
    app.state.replies = Replies()
    return app


@pytest.fixture(scope="session")
def _prepared_database() -> None:
    """Создать тестовую БД (если её нет) и накатить миграции один раз на сессию.

    Сделано синхронно через ``asyncio.run`` намеренно: pytest-asyncio тесты
    работают на function-scope loop, и async session-scope фикстура жила бы в
    отдельном loop, что ломает asyncpg-коннекшены при teardown.
    """

    async def _ensure_db() -> None:
        conn = await asyncpg.connect(
            host=settings.db.HOST,
            port=settings.db.PORT,
            user=settings.db.USER,
            password=settings.db.PASSWORD,
            database="postgres",
        )
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", settings.db.NAME
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{settings.db.NAME}"')
        finally:
            await conn.close()

    asyncio.run(_ensure_db())

    # Конфиг без alembic.ini, чтобы env.py не дёрнул ``fileConfig`` —
    # он бы перетёр root logger в WARN и отключил все user-loggers (в т.ч.
    # ``pipeline``), после чего флаг ``--logs`` ничего бы не показал.
    cfg = Config()
    cfg.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", "")
    command.upgrade(cfg, "head")


@pytest.fixture
async def _test_engine(_prepared_database) -> AsyncIterator:
    """Свежий async-engine на каждый тест с NullPool.

    Function-scope + NullPool — самый простой способ избежать «attached to a
    different loop»: каждый запрос открывает и закрывает свой коннект внутри
    того же loop'а, что и тест.
    """
    engine = create_async_engine(settings.db.url, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def _test_session_maker(_test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _clean_database(_test_engine) -> None:
    """Очищать таблицы перед каждым тестом.

    Транзакционная изоляция не подходит: ``get_session`` коммитит на выходе
    из запроса, поэтому состояние всё равно «утечёт» между тестами.
    """
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    async with _test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def fake_bot() -> FakeBot:
    """Per-test ``FakeBot``, доступный и в фикстуре ``app``, и в самом тесте."""
    return FakeBot()


@pytest.fixture
def app(_test_session_maker, fake_bot: FakeBot) -> FastAPI:
    async def _override() -> AsyncIterator[AsyncSession]:
        async with _test_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    return _build_test_app(_override, fake_bot)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def session(_test_session_maker) -> AsyncIterator[AsyncSession]:
    """Сессия для прямой работы с БД из теста.

    Используется, чтобы дёрнуть доменные сервисы без HTTP-уровня (например,
    ``LinkingService.from_session(session)`` вместо реального бот-вебхука) и
    для проверок состояния БД в конце пайплайна.
    """
    async with _test_session_maker() as s:
        yield s


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.api.KEY}"}
