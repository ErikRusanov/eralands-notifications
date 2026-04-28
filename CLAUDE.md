# Eralands Notifications

REST API на FastAPI для приёма заявок с лендингов. Будущий бот живёт здесь же, в `app/bot/`.

## Стек

- Python 3.12, FastAPI, pydantic-settings
- Менеджер зависимостей: **poetry**
- Линтер/форматтер: ruff
- Запуск: локально (`make run`) или Docker (`make docker-run`)

## Структура

```
app/
  main.py             точка входа (uvicorn)
  core/               фабрика, конфиги, логи, обработчики ошибок
  api/                роутеры (сейчас только /api/health)
  middleware/         мидлвары (логирование запросов)
  schemas/            Pydantic-схемы запросов/ответов
  utils/              утилиты (lifespan)
pyproject.toml        зависимости (uv)
.env.example          шаблон переменных окружения
Dockerfile            uv-based, multi-stage не нужен
docker-compose.yml    один сервис app
Makefile              команды разработчика
```

## Команды

- `make setup` — копирует `.env`, ставит зависимости (`poetry install`)
- `make run` — локально через `python -m app.main`
- `make format` — `ruff format .` + `ruff check --fix .`
- `make update` — обновляет зависимости через poetry

## Конвенции

- Все настройки через переменные окружения с разделителем `__` (например, `APP__HOST`).
  Группа добавляется новым `BaseModel` в `app/core/config.py` и полем в корневом `Settings`.
- Все ошибки уходят через `app/core/errors.py` с унифицированным телом `ErrorResponse`.
- Эндпоинты регистрируются в `app/api/router.py` с префиксом `/api`.
- Docstrings на русском. Технические комментарии в коде минимальны: только когда WHY не очевиден.
- В prod (`APP__ENV=prod`) Swagger/ReDoc отключены.

## Что вне scope сейчас

База данных, Redis, очереди, бот. Подключаются позже отдельными итерациями.
