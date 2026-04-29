"""Отвязка маршрута: DELETE ``(landing_id, channel_id)`` оставляет канал жить.

К одному лендингу привязаны два канала. Era Lands отвязывает один из них
через DELETE. Канал остаётся в БД (для аудита и быстрой реактивации), но
следующая заявка идёт только в оставшийся маршрут.
"""

import logging

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Delivery, NotificationChannel
from app.services.domain import LinkingService

log = logging.getLogger("pipeline")


async def test_unlinked_route_drops_out_of_fanout(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    log.info("→ Era Lands заводит клиента с лендингом и двумя каналами")
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": "ООО Двухканалка"},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    resp = await client.post(
        f"/api/clients/{client_id}/landings",
        headers=admin_headers,
        json={"slug": "two-routes", "name": "Лендинг с двумя каналами"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    landing_id = body["landing"]["id"]
    api_token = body["api_token"]
    first_code = body["linking_code"]["code"]

    linking = LinkingService.from_session(session)
    owner_chat = 400111
    await linking.link_telegram_chat(first_code, owner_chat)
    await session.commit()

    resp = await client.post(
        f"/api/landings/{landing_id}/linking-codes",
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    second_code = resp.json()["code"]

    employee_chat = 400222
    await linking.link_telegram_chat(second_code, employee_chat)
    await session.commit()

    log.info("→ Прилетает первая заявка, доставки идут в оба канала")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "До отвязки"}},
    )
    assert resp.status_code == 202, resp.text
    first_lead_id = resp.json()["id"]
    deliveries = (
        (
            await session.execute(
                select(Delivery).where(Delivery.lead_id == first_lead_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(deliveries) == 2

    resp = await client.get(
        f"/api/clients/{client_id}/channels",
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    channels_by_address = {c["address"]: c["id"] for c in resp.json()}
    assert set(channels_by_address) == {str(owner_chat), str(employee_chat)}
    employee_channel_id = channels_by_address[str(employee_chat)]

    log.info("→ Era Lands отвязывает канал сотрудника от лендинга")
    resp = await client.delete(
        f"/api/landings/{landing_id}/routes/{employee_channel_id}",
        headers=admin_headers,
    )
    assert resp.status_code == 204, resp.text

    log.info("→ Следующая заявка должна уйти только в канал владельца")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "После отвязки"}},
    )
    assert resp.status_code == 202, resp.text
    second_lead_id = resp.json()["id"]

    second_deliveries = (
        (
            await session.execute(
                select(Delivery).where(Delivery.lead_id == second_lead_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(second_deliveries) == 1
    delivery_channel = await session.get(
        NotificationChannel, second_deliveries[0].channel_id
    )
    assert delivery_channel is not None
    assert delivery_channel.address == str(owner_chat)

    log.info("→ Канал сотрудника остался в БД и активен (для реактивации)")
    employee_channel = await session.get(NotificationChannel, employee_channel_id)
    assert employee_channel is not None
    assert employee_channel.is_active is True
