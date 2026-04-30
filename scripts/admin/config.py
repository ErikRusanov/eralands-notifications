"""config — резолв URL и API-ключа для admin-CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_URL = "http://localhost:8000"
ENV_FILE = Path(".env")


@dataclass(frozen=True)
class Config:
    """Параметры подключения к API.

    Атрибуты:
        url: Базовый URL без хвостового слэша.
        key: Bearer-токен админки.
    """

    url: str
    key: str


def resolve(url: str | None, key: str | None) -> Config:
    """Собирает Config из CLI-аргументов с фолбэком в env и .env.

    Приоритет URL: CLI ``--url`` → env ``ADMIN_URL`` → ``DEFAULT_URL``.
    Приоритет KEY: CLI ``--key`` → env ``ADMIN_KEY`` → ``API__KEY`` из .env.

    Поднимает:
        SystemExit: Если ключ не удалось получить ни одним способом.
    """
    resolved_url = (url or os.environ.get("ADMIN_URL") or DEFAULT_URL).rstrip("/")
    resolved_key = key or os.environ.get("ADMIN_KEY") or _read_key_from_env_file()
    if not resolved_key:
        raise SystemExit(
            "Не задан API-ключ. Передайте --key, выставьте ADMIN_KEY "
            "или пропишите API__KEY в .env"
        )
    return Config(url=resolved_url, key=resolved_key)


def _read_key_from_env_file() -> str | None:
    """Достаёт ``API__KEY`` из локального .env, если он есть."""
    if not ENV_FILE.exists():
        return None
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, _, value = line.partition("=")
        if name.strip() == "API__KEY":
            return value.strip().strip('"').strip("'") or None
    return None
