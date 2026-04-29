"""Онбординг клиента: создание → лендинг → привязка чата → лид → доставка.

Эталонный пайплайн для всех остальных тестов сервиса. Один тест —
один полный бизнес-сценарий, как живой клиент его проживает.
"""

import logging

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ChannelType,
    Delivery,
    DeliveryStatus,
    Lead,
    NotificationChannel,
)
from app.services.domain import LinkingService
from tests.conftest import FakeBot

log = logging.getLogger("pipeline")


async def test_onboarding_through_first_lead(
    client: AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
    fake_bot: FakeBot,
) -> None:
    log.info("→ Era Lands заводит нового клиента «ООО Ромашка»")
    resp = await client.post(
        "/api/clients",
        headers=admin_headers,
        json={"name": "ООО Ромашка"},
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]
    log.info("  клиент создан, id=%s", client_id)

    log.info("→ Выдаём ему первый лендинг с api-токеном и одноразовым кодом")
    resp = await client.post(
        f"/api/clients/{client_id}/landings",
        headers=admin_headers,
        json={"slug": "roofs-msk", "name": "Кровля под ключ — Москва"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    landing_id = body["landing"]["id"]
    api_token = body["api_token"]
    code = body["linking_code"]["code"]
    log.info(
        "  лендинг id=%s, api_token=%s..., linking_code=%s",
        landing_id,
        api_token[:8],
        code,
    )

    log.info("→ Сотрудник клиента вводит код в боте, чат привязывается")
    chat_id = 100500
    linking = LinkingService.from_session(session)
    link_result = await linking.link_telegram_chat(code, chat_id)
    await session.commit()
    log.info(
        "  привязка ок, маршрутов на лендинге: %d (клиент: %s)",
        link_result.routes_count,
        link_result.client_name,
    )

    assert link_result.routes_count == 1
    assert link_result.client_name == "ООО Ромашка"

    log.info("→ С лендинга прилетает первая заявка")
    resp = await client.post(
        "/api/leads",
        headers={"Authorization": f"Bearer {api_token}"},
        json={
            "payload": {"name": "Иван", "phone": "+7-999-000-00-00"},
            "source_meta": {"utm_source": "yandex"},
        },
    )
    assert resp.status_code == 202, resp.text
    lead_id = resp.json()["id"]
    log.info("  заявка принята, lead_id=%s", lead_id)

    log.info("→ Проверяем, что в БД лежит лид и доставка отправлена")
    lead = await session.get(Lead, lead_id)
    assert lead is not None
    assert lead.landing_id.hex == landing_id.replace("-", "")
    assert lead.payload == {"name": "Иван", "phone": "+7-999-000-00-00"}

    deliveries = (
        (await session.execute(select(Delivery).where(Delivery.lead_id == lead.id)))
        .scalars()
        .all()
    )
    assert len(deliveries) == 1
    delivery = deliveries[0]
    assert delivery.status == DeliveryStatus.SENT
    assert delivery.attempts == 1
    assert delivery.sent_at is not None
    assert delivery.last_error is None

    channel = await session.get(NotificationChannel, delivery.channel_id)
    assert channel is not None
    assert channel.type == ChannelType.TELEGRAM
    assert channel.address == str(chat_id)
    assert channel.is_active is True
    log.info(
        "  delivery_id=%s status=%s -> канал TG chat_id=%s",
        delivery.id,
        delivery.status.value,
        channel.address,
    )

    log.info("→ В Telegram ушло одно сообщение в этот чат с реальным payload-ом")
    assert len(fake_bot.calls) == 1
    sent = fake_bot.calls[0]
    assert sent["chat_id"] == chat_id
    assert "Кровля под ключ — Москва" in sent["text"]
    assert "Иван" in sent["text"]
    assert "+7-999-000-00-00" in sent["text"]
