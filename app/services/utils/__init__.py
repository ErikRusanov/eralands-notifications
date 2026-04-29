"""utils — общие утилиты, которые используются доменными сервисами."""

from app.services.utils.tokens import generate_api_token, generate_linking_code

__all__ = ["generate_api_token", "generate_linking_code"]
