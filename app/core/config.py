"""config — конфигурация сервиса, читаемая из переменных окружения.

Настройки разбиты на логические группы и собираются в корневой объект
``Settings``, который читает ``.env`` из корня проекта. Вложенные переменные
используют разделитель ``__``, например ``APP__HOST``, ``APP__PORT``.
"""

from enum import StrEnum
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import BaseModel, computed_field
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


class DatabaseSettings(BaseModel):
    """Настройки подключения к PostgreSQL.

    Атрибуты:
        HOST: Адрес сервера БД.
        PORT: TCP-порт.
        NAME: Имя БД.
        USER: Пользователь.
        PASSWORD: Пароль. Обязательное поле, фейлим на старте, если пусто.
    """

    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "notifications"
    USER: str = "notifications"
    PASSWORD: str

    @computed_field
    @property
    def url(self) -> str:
        """Async-URL подключения для asyncpg (с URL-кодированием логина и пароля)."""
        return (
            f"postgresql+asyncpg://{quote_plus(self.USER)}:{quote_plus(self.PASSWORD)}"
            f"@{self.HOST}:{self.PORT}/{self.NAME}"
        )


class TelegramSettings(BaseModel):
    """Настройки Telegram-бота.

    Атрибуты:
        TOKEN: Bot API токен, выданный BotFather. Пустая строка отключает бота
            на старте: webhook не регистрируется, но сервис продолжает работать.
        WEBHOOK_URL: Публичный базовый URL сервиса (без пути), на который
            Telegram будет слать обновления. Пустая строка пропускает регистрацию
            вебхука у Telegram (полезно в локальной разработке без туннеля).
        WEBHOOK_PATH: Путь, на котором смонтирован FastAPI-эндпоинт вебхука.
            Используется при сборке итогового URL для ``set_webhook``.
    """

    TOKEN: str = ""
    WEBHOOK_URL: str = ""
    WEBHOOK_PATH: str = "/api/bot/webhook"


class ApiSettings(BaseModel):
    """Настройки административной аутентификации API.

    Атрибуты:
        KEY: Bearer-ключ для эндпоинтов управления клиентами и лендингами.
            Обязательное поле, фейлим на старте, если пусто, чтобы случайно не
            открыть админку публично.
    """

    KEY: str


class LinkingCodeSettings(BaseModel):
    """Настройки одноразовых кодов привязки.

    Атрибуты:
        TTL_MINUTES: Сколько минут код считается валидным после выдачи.
        LENGTH: Длина кода в символах. Алфавит фиксирован
            в ``utils/tokens.py``.
    """

    TTL_MINUTES: int = 60
    LENGTH: int = 8


class Settings(BaseSettings):
    """Корневой объект настроек. Читает все переменные из ``.env``.

    Переменные сгруппированы префиксами с разделителем ``__``:
    - ``APP__ENV``, ``APP__HOST``, ``APP__PORT``, ``APP__LOGGING_LEVEL``
    - ``DB__HOST``, ``DB__PORT``, ``DB__NAME``, ``DB__USER``, ``DB__PASSWORD``
    - ``TELEGRAM__TOKEN``, ``TELEGRAM__WEBHOOK_URL``, ``TELEGRAM__WEBHOOK_PATH``
    - ``API__KEY``
    - ``LINKING_CODE__TTL_MINUTES``, ``LINKING_CODE__LENGTH``

    Атрибуты:
        app: Базовые настройки приложения.
        db: Настройки подключения к PostgreSQL.
        telegram: Настройки Telegram-бота.
        api: Настройки админской аутентификации.
        linking_code: Настройки одноразовых кодов привязки.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = AppSettings()
    db: DatabaseSettings
    telegram: TelegramSettings = TelegramSettings()
    api: ApiSettings
    linking_code: LinkingCodeSettings = LinkingCodeSettings()


settings = Settings()
