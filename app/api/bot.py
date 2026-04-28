"""bot — роутер с эндпоинтом приёма обновлений Telegram через webhook."""

from aiogram.types import Update
from fastapi import APIRouter, Request
from fastapi import status as http_status

from app.bot.schemas import WebhookResponse

router = APIRouter(prefix="/bot", tags=["Bot"])


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Webhook Telegram",
    description=(
        "Принимает обновление от Telegram, валидирует его в ``aiogram.Update`` "
        "и передаёт в диспатчер для обработки. Должен быть зарегистрирован у "
        "Telegram через ``set_webhook`` — это делает ``setup_bot`` при старте "
        "сервиса, если задан ``TELEGRAM__WEBHOOK_URL``."
    ),
    responses={
        http_status.HTTP_200_OK: {
            "description": "Обновление принято и передано в диспатчер."
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
    """
    bot = request.app.state.bot
    dp = request.app.state.dp

    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)

    return WebhookResponse(ok=True)
