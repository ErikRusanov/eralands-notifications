"""logging — мидлвара логирования HTTP-запросов без персональных данных."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Логирует метод, путь, статус и длительность каждого запроса.

    Персональные данные не логируются: только HTTP-метод, путь URL (без
    query-string), статус ответа и время выполнения в миллисекундах.

    Пример вывода::

        INFO  GET /api/health -> 200 (5ms)
        WARNING POST /api/foo -> 404 (2ms)
        ERROR GET /api/bar -> 500 (1ms)

    Уровень лога выбирается по диапазону статус-кода:
    - 5xx → ``ERROR``
    - 4xx → ``WARNING``
    - остальное → ``INFO``
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Логирует запрос и ответ, прокидывая управление дальше по цепочке.

        Аргументы:
            request: Входящий HTTP-запрос.
            call_next: Колбэк, вызывающий следующий мидлвар или эндпоинт.

        Возвращает:
            HTTP-ответ от нижестоящего обработчика.
        """
        start = time.monotonic()
        response: Response = await call_next(request)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        status = response.status_code
        msg = "%s %s -> %d (%dms)", request.method, request.url.path, status, elapsed_ms

        if status >= 500:
            logger.error(*msg)
        elif status >= 400:
            logger.warning(*msg)
        else:
            logger.info(*msg)

        return response
