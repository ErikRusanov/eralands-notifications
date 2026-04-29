"""bot — роутер с эндпоинтом приёма обновлений Telegram через webhook."""

import secrets

from aiogram.types import Update
from fastapi import APIRouter, Request
from fastapi import status as http_status

from app.bot.schemas import WebhookResponse
from app.core.config import settings
from app.services.domain import AuthError

router = APIRouter(prefix="/bot", tags=["Bot"])

_TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Webhook Telegram",
    description=(
        "Принимает обновление от Telegram, валидирует его в ``aiogram.Update`` "
        "и передаёт в диспатчер для обработки. Должен быть зарегистрирован у "
        "Telegram через ``set_webhook`` — это делает ``setup_bot`` при старте "
        "сервиса, если задан ``TELEGRAM__WEBHOOK_URL``. Если задан "
        "``TELEGRAM__WEBHOOK_SECRET``, ожидается совпадающий заголовок "
        "``X-Telegram-Bot-Api-Secret-Token``; иначе 401."
    ),
    responses={
        http_status.HTTP_200_OK: {
            "description": "Обновление принято и передано в диспатчер."
        },
        http_status.HTTP_401_UNAUTHORIZED: {
            "description": "Заголовок секрета отсутствует или не совпадает."
        },
        http_status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Тело запроса не похоже на корректное обновление Telegram."
        },
    },
)
async def webhook(request: Request) -> WebhookResponse:
    """Принять обновление Telegram и передать его в aiogram-диспатчер.

    Bot и Dispatcher хранятся в ``app.state`` — там их инициализирует
    ``setup_bot`` через FastAPI lifespan.

    Аргументы:
        request: Входящий HTTP-запрос. Тело — JSON-обновление Telegram.

    Возвращает:
        WebhookResponse: ``{"ok": true}`` после успешной передачи в диспатчер.

    Поднимает:
        AuthError: Если задан ``TELEGRAM__WEBHOOK_SECRET``, но заголовок
            ``X-Telegram-Bot-Api-Secret-Token`` отсутствует или не совпадает.
    """
    expected = settings.telegram.WEBHOOK_SECRET
    if expected:
        provided = request.headers.get(_TELEGRAM_SECRET_HEADER, "")
        if not secrets.compare_digest(provided, expected):
            raise AuthError("Invalid Telegram webhook secret.")

    bot = request.app.state.bot
    dp = request.app.state.dp

    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)

    return WebhookResponse(ok=True)
