"""webhook — схема ответа эндпоинта приёма обновлений Telegram."""

from pydantic import BaseModel, Field


class WebhookResponse(BaseModel):
    """Тело ответа после приёма обновления Telegram.

    Атрибуты:
        ok: Флаг успешной передачи обновления в aiogram-диспатчер. Всегда
            ``True`` при успешной обработке. Ошибки отдаются через
            унифицированный ``ErrorResponse``.
    """

    ok: bool = Field(
        ...,
        description="Признак успешного приёма обновления.",
        examples=[True],
    )
