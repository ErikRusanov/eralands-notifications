"""main — точка входа Eralands Notifications.

Создаёт FastAPI-приложение через фабрику и запускает uvicorn при прямом
вызове (``python -m app.main``).
"""

import uvicorn

from app.core import Environment, create_app, get_log_config, settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.ENV == Environment.DEV,
        log_config=get_log_config(),
    )
