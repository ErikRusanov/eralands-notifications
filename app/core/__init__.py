"""core — фабрика приложения, конфиги и стартовая обвязка.

Публичный API
-------------
Environment    : Перечисление допустимых окружений.
settings       : Синглтон ``Settings``, заполненный из переменных окружения.
create_app     : Фабрика, собирающая сконфигурированный экземпляр ``FastAPI``.
get_log_config : Возвращает словарь настроек логирования для uvicorn.
"""

from app.core.config import Environment, settings
from app.core.get_app import create_app
from app.core.logging import get_log_config

__all__ = ["Environment", "create_app", "get_log_config", "settings"]
