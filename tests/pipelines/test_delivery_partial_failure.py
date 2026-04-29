"""Частичный сбой fan-out: один канал упал, остальные дошли.

К одному лендингу привязаны два чата. На отправке в один из них
``Bot.send_message`` бросает ошибку. ``DispatchService`` должен:

- перевести упавшую доставку в ``failed`` с ``last_error``;
- успешно отправить во второй канал и оставить его доставку ``sent``;
- не пробросить исключение наружу, иначе вся транзакция откатится.
"""

import logging

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Delivery, DeliveryStatus, NotificationChannel
from app.services.domain import LinkingService
from tests.conftest import FakeBot

log = logging.getLogger("pipeline")


async def test_one_channel_failure_does_not_affect_others(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
    fake_bot: FakeBot,
) -> None:
    log.info("→ Era Lands заводит клиента с лендингом и двумя каналами")
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": "ООО Двухканалка-2"},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    resp = await client.post(
        f"/api/clients/{client_id}/landings",
        headers=admin_headers,
        json={"slug": "fail-mix", "name": "Лендинг с одним битым каналом"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    landing_id = body["landing"]["id"]
    api_token = body["api_token"]
    first_code = body["linking_code"]["code"]

    linking = LinkingService.from_session(session)
    healthy_chat = 500111
    broken_chat = 500222
    await linking.link_telegram_chat(first_code, healthy_chat)
    await session.commit()

    resp = await client.post(
        f"/api/landings/{landing_id}/linking-codes",
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    second_code = resp.json()["code"]

    await linking.link_telegram_chat(second_code, broken_chat)
    await session.commit()

    log.info("→ Заставляем Telegram падать на отправке во второй чат")
    fake_bot.fail_chat_ids.add(broken_chat)
    fake_bot.fail_message = "Bad Request: chat not found"

    log.info("→ Прилетает заявка")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"payload": {"name": "Партиал", "phone": "+7-900-555-44-33"}},
    )
    assert resp.status_code == 202, resp.text
    lead_id = resp.json()["id"]

    log.info("→ В БД ровно две доставки: одна sent, другая failed")
    deliveries = (
        (await session.execute(select(Delivery).where(Delivery.lead_id == lead_id)))
        .scalars()
        .all()
    )
    assert len(deliveries) == 2
    by_status = {d.status: d for d in deliveries}
    assert set(by_status) == {DeliveryStatus.SENT, DeliveryStatus.FAILED}

    sent = by_status[DeliveryStatus.SENT]
    failed = by_status[DeliveryStatus.FAILED]

    sent_channel = await session.get(NotificationChannel, sent.channel_id)
    assert sent_channel is not None
    assert sent_channel.address == str(healthy_chat)
    assert sent.attempts == 1
    assert sent.sent_at is not None
    assert sent.last_error is None

    failed_channel = await session.get(NotificationChannel, failed.channel_id)
    assert failed_channel is not None
    assert failed_channel.address == str(broken_chat)
    assert failed.attempts == 1
    assert failed.sent_at is None
    assert failed.last_error is not None
    assert "chat not found" in failed.last_error

    log.info(
        "  sent -> chat=%s, failed -> chat=%s, last_error=%s",
        sent_channel.address,
        failed_channel.address,
        failed.last_error,
    )

    log.info("→ В Telegram реально ушло одно сообщение, в здоровый чат")
    sent_chat_ids = [call["chat_id"] for call in fake_bot.calls]
    assert sent_chat_ids == [healthy_chat]
