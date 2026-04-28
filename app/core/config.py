"""config — конфигурация сервиса, читаемая из переменных окружения.

Настройки разбиты на логические группы и собираются в корневой объект
``Settings``, который читает ``.env`` из корня проекта. Вложенные переменные
используют разделитель ``__``, например ``APP__HOST``, ``APP__PORT``.
"""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env в корне проекта: app/core/config.py → ../../ → корень.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Environment(StrEnum):
    """Допустимые идентификаторы окружения.

    Атрибуты:
        DEV: Локальная разработка. Включает auto-reload и API-доки.
        PROD: Прод. Отключает auto-reload и API-доки.
    """

    DEV = "dev"
    PROD = "prod"


class AppSettings(BaseModel):
    """Базовые настройки приложения.

    Атрибуты:
        ENV: Окружение. Влияет на reload и видимость API-док.
        HOST: Сетевой интерфейс, на который биндится uvicorn.
        PORT: TCP-порт, на котором слушает uvicorn.
        LOGGING_LEVEL: Уровень логирования для логгера ``app``.
    """

    ENV: Environment = Environment.DEV
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOGGING_LEVEL: str = "INFO"


class Settings(BaseSettings):
    """Корневой объект настроек. Читает все переменные из ``.env``.

    Переменные сгруппированы префиксами с разделителем ``__``:
    - ``APP__ENV``, ``APP__HOST``, ``APP__PORT``, ``APP__LOGGING_LEVEL``

    Атрибуты:
        app: Базовые настройки приложения.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = AppSettings()


settings = Settings()
