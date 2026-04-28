"""schemas — Pydantic-схемы запросов и ответов бота.

Публичный API
-------------
WebhookResponse : Тело ответа эндпоинта ``POST /api/bot/webhook``.
"""

from app.bot.schemas.webhook import WebhookResponse

__all__ = ["WebhookResponse"]
