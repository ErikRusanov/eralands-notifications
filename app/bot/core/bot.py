"""bot — фабрики aiogram Bot и Dispatcher."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings


def create_bot() -> Bot:
    """Создать сконфигурированный экземпляр ``aiogram.Bot``.

    Использует токен из ``settings.telegram.TOKEN``. По умолчанию все
    исходящие сообщения парсятся как HTML — соответствует разметке в
    ``texts.toml``.

    Возвращает:
        Настроенный ``Bot``, готовый к использованию диспатчером.
    """
    return Bot(
        token=settings.telegram.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Создать чистый ``aiogram.Dispatcher``.

    Возвращает:
        Пустой диспатчер. Хендлеры, мидлвары и зависимости подключаются
        в ``setup_bot``.
    """
    return Dispatcher()
