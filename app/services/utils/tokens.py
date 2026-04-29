"""tokens — генераторы токенов лендинга и одноразовых кодов привязки."""

import secrets

# 32 байта энтропии, url-safe base64 даёт ~43 печатных символа.
_API_TOKEN_BYTES = 32

# Алфавит без визуально похожих 0/O, 1/I/L: код вводится человеком в боте.
_LINKING_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_api_token() -> str:
    """Возвращает url-safe токен лендинга на ``_API_TOKEN_BYTES`` байт энтропии.

    Возвращаемое значение — открытый токен, который кладётся на лендинг и
    больше нигде не сохраняется в БД (хранится только SHA-256 хеш).
    """
    return secrets.token_urlsafe(_API_TOKEN_BYTES)


def generate_linking_code(length: int) -> str:
    """Возвращает короткий человеко-набираемый код привязки.

    Аргументы:
        length: Длина кода в символах. Берётся из ``LinkingCodeSettings.LENGTH``.

    Возвращает:
        Строку из заглавных букв и цифр без визуально похожих символов.
    """
    return "".join(secrets.choice(_LINKING_CODE_ALPHABET) for _ in range(length))
