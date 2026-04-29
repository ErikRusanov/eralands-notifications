"""Уход клиента и возврат: PATCH ``is_active`` каскадирует на лендинги.

Активный клиент → принимает заявки. После PATCH ``is_active=false`` тот же
лендинг отдаёт 409 и не порождает ``Delivery``. После PATCH ``is_active=true``
лендинг снова принимает заявки и фан-аут восстанавливается.
"""

import logging

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Delivery, Lead
from app.services.domain import LinkingService

log = logging.getLogger("pipeline")


async def test_client_disabled_then_reenabled(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    log.info("→ Era Lands заводит клиента «ООО Уход» с лендингом и каналом")
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": "ООО Уход"},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    resp = await client.post(
        f"/api/clients/{client_id}/landings",
        headers=admin_headers,
        json={"slug": "leaving-msk", "name": "Уходящий клиент"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    api_token = body["api_token"]
    code = body["linking_code"]["code"]

    chat_id = 200300
    linking = LinkingService.from_session(session)
    await linking.link_telegram_chat(code, chat_id)
    await session.commit()

    log.info("→ Пока активен, заявка проходит и порождает доставку")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "Анна"}},
    )
    assert resp.status_code == 202, resp.text
    first_lead_id = resp.json()["id"]
    first_deliveries = (
        (
            await session.execute(
                select(Delivery).where(Delivery.lead_id == first_lead_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(first_deliveries) == 1

    log.info("→ Era Lands отключает клиента целиком")
    resp = await client.patch(
        f"/api/clients/{client_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert resp.status_code == 200, resp.text
    landings = resp.json()["landings"]
    assert all(landing["is_active"] is False for landing in landings)

    log.info("→ Заявка с того же токена должна отбиться 409")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "Игнор"}},
    )
    assert resp.status_code == 409, resp.text

    log.info("→ Проверяем, что в БД нет ни нового Lead, ни новых Delivery")
    leads = (await session.execute(select(Lead))).scalars().all()
    assert [str(lead.id) for lead in leads] == [first_lead_id]
    deliveries_total = (await session.execute(select(Delivery))).scalars().all()
    assert len(deliveries_total) == 1

    log.info("→ Era Lands возвращает клиента в работу")
    resp = await client.patch(
        f"/api/clients/{client_id}",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert resp.status_code == 200, resp.text
    landings = resp.json()["landings"]
    assert all(landing["is_active"] is True for landing in landings)

    log.info("→ Заявка снова принимается и порождает доставку")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "Сергей"}},
    )
    assert resp.status_code == 202, resp.text
    third_lead_id = resp.json()["id"]
    third_deliveries = (
        (
            await session.execute(
                select(Delivery).where(Delivery.lead_id == third_lead_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(third_deliveries) == 1
    log.info(
        "  возврат ок: lead=%s, доставка=%s", third_lead_id, third_deliveries[0].id
    )
