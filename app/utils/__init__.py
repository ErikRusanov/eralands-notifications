"""utils — общие хелперы и утилиты сервиса.

Публичный API
-------------
generate_api_token : Генератор открытого API-токена лендинга.
generate_linking_code : Генератор одноразового кода привязки.

``lifespan`` импортируется напрямую из ``app.utils.lifespan``, чтобы избежать
циклического импорта через ``app.bot`` → ``app.core`` → ``app.services``.
"""

from app.utils.tokens import generate_api_token, generate_linking_code

__all__ = ["generate_api_token", "generate_linking_code"]
