"""logging — конфигурация логирования сервиса."""

import copy

from uvicorn.config import LOGGING_CONFIG

from app.core import settings


def get_log_config() -> dict:
    """Собирает конфиг логирования, расширяющий дефолты uvicorn.

    Добавляет таймстамп и имя логгера в дефолтный форматтер и регистрирует
    логгер ``app``, чтобы он использовал тот же цветной вывод, что и uvicorn.

    Возвращает:
        Словарь, совместимый с ``logging.config.dictConfig``.
    """
    config = copy.deepcopy(LOGGING_CONFIG)
    config["formatters"]["default"]["fmt"] = (
        "%(levelprefix)s %(asctime)s  %(name)s: %(message)s"
    )
    config["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    config["loggers"]["app"] = {
        "handlers": ["default"],
        "level": settings.app.LOGGING_LEVEL,
        "propagate": False,
    }
    return config
