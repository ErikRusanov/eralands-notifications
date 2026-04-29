"""Добавление сотрудника: второй чат привязывается к тому же лендингу.

Один маршрут уже есть. Era Lands выдаёт ещё один одноразовый код, второй
сотрудник вводит его в боте, чат привязывается. Следующая заявка с того же
лендинга должна породить ``Delivery`` в оба канала.
"""

import logging

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ChannelType,
    Delivery,
    DeliveryStatus,
    NotificationChannel,
)
from app.services.domain import LinkingService
from tests.conftest import FakeBot

log = logging.getLogger("pipeline")


async def test_second_employee_attached_to_same_landing(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
    fake_bot: FakeBot,
) -> None:
    log.info("→ Era Lands заводит клиента «ООО Кровельщики» с лендингом")
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": "ООО Кровельщики"},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    resp = await client.post(
        f"/api/clients/{client_id}/landings",
        headers=admin_headers,
        json={"slug": "roofs-spb", "name": "Кровля СПб"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    landing_id = body["landing"]["id"]
    api_token = body["api_token"]
    first_code = body["linking_code"]["code"]
    log.info("  лендинг id=%s, первый код=%s", landing_id, first_code)

    log.info("→ Первый сотрудник (chat=100501) вводит код в боте")
    owner_chat = 100501
    linking = LinkingService.from_session(session)
    first_link = await linking.link_telegram_chat(first_code, owner_chat)
    await session.commit()
    assert first_link.routes_count == 1

    log.info("→ Era Lands выдаёт второй одноразовый код для того же лендинга")
    resp = await client.post(
        f"/api/landings/{landing_id}/linking-codes",
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    second_code = resp.json()["code"]
    log.info("  второй код=%s", second_code)

    log.info("→ Второй сотрудник (chat=100502) вводит этот код")
    employee_chat = 100502
    second_link = await linking.link_telegram_chat(second_code, employee_chat)
    await session.commit()
    log.info("  привязка ок, активных маршрутов: %d", second_link.routes_count)
    assert second_link.routes_count == 2
    assert second_link.client_name == "ООО Кровельщики"

    log.info("→ С лендинга прилетает заявка")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "Пётр", "phone": "+7-900-111-22-33"}},
    )
    assert resp.status_code == 202, resp.text
    lead_id = resp.json()["id"]

    log.info("→ Проверяем, что заявка ушла в оба канала")
    deliveries = (
        (await session.execute(select(Delivery).where(Delivery.lead_id == lead_id)))
        .scalars()
        .all()
    )
    assert len(deliveries) == 2
    assert all(d.status == DeliveryStatus.SENT for d in deliveries)
    assert all(d.attempts == 1 for d in deliveries)
    assert all(d.sent_at is not None for d in deliveries)

    channels = (
        (
            await session.execute(
                select(NotificationChannel).where(
                    NotificationChannel.id.in_([d.channel_id for d in deliveries])
                )
            )
        )
        .scalars()
        .all()
    )
    addresses = sorted(c.address for c in channels)
    assert addresses == [str(owner_chat), str(employee_chat)]
    assert all(c.type == ChannelType.TELEGRAM for c in channels)
    assert all(c.is_active for c in channels)
    log.info("  каналы: %s", addresses)

    log.info("→ В Telegram ушло два сообщения, по одному в каждый чат")
    sent_chat_ids = sorted(call["chat_id"] for call in fake_bot.calls)
    assert sent_chat_ids == [owner_chat, employee_chat]
    assert all("Пётр" in call["text"] for call in fake_bot.calls)
