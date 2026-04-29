"""linking_code — схема ответа с одноразовым кодом привязки."""

from datetime import datetime

from pydantic import BaseModel, Field


class LinkingCodeResponse(BaseModel):
    """Тело ответа с одноразовым кодом привязки канала к лендингу.

    Атрибуты:
        code: Открытый код, который клиент введёт в боте.
        expires_at: Момент протухания кода. После этого ввод не сработает.
    """

    code: str = Field(..., description="Одноразовый код привязки.")
    expires_at: datetime = Field(..., description="Момент протухания кода.")
