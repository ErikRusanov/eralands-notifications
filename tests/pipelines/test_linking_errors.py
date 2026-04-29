"""Ошибки линковки: бот аккуратно реагирует на плохой код, БД не меняется.

Покрываем три ветки ``LinkingService.link_telegram_chat``:
- кода нет в БД (или его кто-то выдумал) → ``LinkingCodeNotFoundError``;
- код есть, не использован, но протух → ``LinkingCodeExpiredError``;
- код уже погашен — внешне неотличим от несуществующего → ``LinkingCodeNotFoundError``.

В каждом случае: канал и маршрут из-за неудачной попытки не появляются,
а ранее существовавшее состояние не «съезжает».
"""

import logging
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LandingRoute, LinkingCode, NotificationChannel
from app.services.domain import LinkingService
from app.services.domain.errors import (
    LinkingCodeExpiredError,
    LinkingCodeNotFoundError,
)

log = logging.getLogger("pipeline")


async def _create_landing_with_code(
    client: AsyncClient,
    admin_headers: dict[str, str],
    *,
    client_name: str,
    slug: str,
) -> tuple[str, str]:
    """Создаёт клиента и лендинг, возвращает ``(landing_id, code)``."""
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": client_name},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    resp = await client.post(
        f"/api/clients/{client_id}/landings",
        headers=admin_headers,
        json={"slug": slug, "name": f"Лендинг {slug}"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["landing"]["id"], body["linking_code"]["code"]


async def test_invalid_code_does_not_change_state(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    log.info("→ Заводим лендинг с настоящим кодом, чтобы было что не трогать")
    landing_id, real_code = await _create_landing_with_code(
        client,
        admin_headers,
        client_name="ООО Невалидный",
        slug="bad-code",
    )

    log.info("→ Бот получает выдуманный код, которого нет в БД")
    linking = LinkingService.from_session(session)
    with pytest.raises(LinkingCodeNotFoundError):
        await linking.link_telegram_chat("NOSUCHCODE", 500111)
    await session.rollback()

    log.info("→ Каналов и маршрутов не появилось, настоящий код всё ещё активен")
    channels = (await session.execute(select(NotificationChannel))).scalars().all()
    assert channels == []
    routes = (await session.execute(select(LandingRoute))).scalars().all()
    assert routes == []
    real = await session.scalar(
        select(LinkingCode).where(LinkingCode.code == real_code)
    )
    assert real is not None
    assert real.used_at is None
    assert real.landing_id.hex == landing_id.replace("-", "")


async def test_expired_code_does_not_change_state(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    log.info("→ Заводим лендинг с кодом и принудительно протухаем его в БД")
    _, code = await _create_landing_with_code(
        client,
        admin_headers,
        client_name="ООО Просрочка",
        slug="expired-code",
    )
    past = datetime.now(UTC) - timedelta(minutes=1)
    await session.execute(
        update(LinkingCode).where(LinkingCode.code == code).values(expires_at=past)
    )
    await session.commit()

    log.info("→ Бот вводит протухший код")
    linking = LinkingService.from_session(session)
    with pytest.raises(LinkingCodeExpiredError):
        await linking.link_telegram_chat(code, 500222)
    await session.rollback()

    log.info("→ Код не погашен, каналов и маршрутов нет")
    channels = (await session.execute(select(NotificationChannel))).scalars().all()
    assert channels == []
    routes = (await session.execute(select(LandingRoute))).scalars().all()
    assert routes == []
    lc = await session.scalar(select(LinkingCode).where(LinkingCode.code == code))
    assert lc is not None
    assert lc.used_at is None
    assert lc.used_by_chat_id is None


async def test_used_code_does_not_link_again(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    log.info("→ Сотрудник честно вводит код в первый раз — привязка проходит")
    landing_id, code = await _create_landing_with_code(
        client,
        admin_headers,
        client_name="ООО Повтор",
        slug="reused-code",
    )
    first_chat = 500333
    linking = LinkingService.from_session(session)
    await linking.link_telegram_chat(code, first_chat)
    await session.commit()

    channels_before = (
        (await session.execute(select(NotificationChannel))).scalars().all()
    )
    routes_before = (await session.execute(select(LandingRoute))).scalars().all()
    assert len(channels_before) == 1
    assert len(routes_before) == 1
    used_at_before = (
        await session.scalar(select(LinkingCode).where(LinkingCode.code == code))
    ).used_at
    assert used_at_before is not None

    log.info("→ Второй сотрудник пробует тот же код — должна быть ошибка")
    with pytest.raises(LinkingCodeNotFoundError):
        await linking.link_telegram_chat(code, 500444)
    await session.rollback()

    log.info("→ Состояние БД ровно такое же, как после первой привязки")
    session.expire_all()
    channels_after = (
        (await session.execute(select(NotificationChannel))).scalars().all()
    )
    routes_after = (await session.execute(select(LandingRoute))).scalars().all()
    assert {c.id for c in channels_after} == {c.id for c in channels_before}
    assert {r.id for r in routes_after} == {r.id for r in routes_before}
    assert channels_after[0].address == str(first_chat)

    lc = await session.scalar(select(LinkingCode).where(LinkingCode.code == code))
    assert lc is not None
    assert lc.used_at == used_at_before
    assert lc.used_by_chat_id == first_chat
    assert lc.landing_id.hex == landing_id.replace("-", "")
