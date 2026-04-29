"""Отключение конкретного лендинга, соседний лендинг того же клиента жив.

У клиента два лендинга, к каждому привязан свой канал. Era Lands отключает
один лендинг через PATCH. Заявки по его токену должны отбиваться 409, а
заявки по соседнему — приниматься как обычно и порождать ``Delivery``.
"""

import logging

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Delivery, Lead, NotificationChannel
from app.services.domain import LinkingService

log = logging.getLogger("pipeline")


async def test_only_target_landing_stops_accepting_leads(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    log.info("→ Era Lands заводит клиента с двумя лендингами")
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": "ООО Двухдомные"},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    landings = []
    for slug, name, chat in (
        ("roofs-a", "Лендинг A", 300101),
        ("roofs-b", "Лендинг B", 300102),
    ):
        resp = await client.post(
            f"/api/clients/{client_id}/landings",
            headers=admin_headers,
            json={"slug": slug, "name": name},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        linking = LinkingService.from_session(session)
        await linking.link_telegram_chat(body["linking_code"]["code"], chat)
        await session.commit()
        landings.append(
            {
                "id": body["landing"]["id"],
                "token": body["api_token"],
                "chat": chat,
                "name": name,
            }
        )

    target, neighbour = landings
    log.info(
        "  target=%s (%s), neighbour=%s (%s)",
        target["id"],
        target["name"],
        neighbour["id"],
        neighbour["name"],
    )

    log.info("→ Era Lands отключает только target-лендинг")
    resp = await client.patch(
        f"/api/landings/{target['id']}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is False

    log.info("→ Заявка по target отбивается 409")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {target['token']}"},
        json={"payload": {"name": "Никто"}},
    )
    assert resp.status_code == 409, resp.text

    log.info("→ Заявка по соседнему лендингу проходит и порождает доставку")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {neighbour['token']}"},
        json={"payload": {"name": "Соседский"}},
    )
    assert resp.status_code == 202, resp.text
    neighbour_lead_id = resp.json()["id"]

    log.info("→ В БД ровно один Lead, и доставка ушла в канал соседа")
    leads = (await session.execute(select(Lead))).scalars().all()
    assert [str(lead.id) for lead in leads] == [neighbour_lead_id]
    assert leads[0].landing_id.hex == neighbour["id"].replace("-", "")

    deliveries = (
        (await session.execute(select(Delivery).where(Delivery.lead_id == leads[0].id)))
        .scalars()
        .all()
    )
    assert len(deliveries) == 1

    channel = await session.get(NotificationChannel, deliveries[0].channel_id)
    assert channel is not None
    assert channel.address == str(neighbour["chat"])
    log.info("  доставка пошла в канал=%s", channel.address)
