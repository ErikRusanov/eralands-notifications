# Eralands Notifications

REST API на FastAPI для приёма заявок с лендингов. Будущий бот живёт здесь же, в `app/bot/`.

## Стек

- Python 3.12, FastAPI, pydantic-settings
- PostgreSQL 17, SQLAlchemy 2 (async), Alembic, asyncpg
- Менеджер зависимостей: **poetry**
- Линтер/форматтер: ruff
- Запуск: локально (`make run`) или Docker (`make docker-run`)

## Структура

```
app/
  main.py             точка входа (uvicorn)
  core/               фабрика, конфиги, логи, обработчики ошибок, движок БД
  api/                роутеры и зависимости (сейчас /api/health, deps.get_session)
  middleware/         мидлвары (логирование запросов)
  models/             ORM-модели и декларативная база
  schemas/            Pydantic-схемы запросов/ответов
  utils/              утилиты (lifespan)
alembic/              окружение и версии миграций
alembic.ini           конфигурация Alembic
pyproject.toml        зависимости (poetry)
.env.example          шаблон переменных окружения
Dockerfile            uv-based, multi-stage не нужен
docker-compose.yml    сервисы app + postgres
Makefile              команды разработчика
```

## Команды

- `make setup` — копирует `.env`, ставит зависимости (`poetry install`)
- `make run` — поднимает postgres (`db-up --wait`) и запускает сервис локально через `python -m app.main`
- `make db-up` / `make db-down` — поднять/остановить контейнер postgres
- `make format` — `ruff format .` + `ruff check --fix .`
- `make update` — обновляет зависимости через poetry
- `make migration m="..."` — создаёт авто-миграцию по diff моделей
- `make migrate` — применяет миграции до head

## Конвенции

- Все настройки через переменные окружения с разделителем `__` (например, `APP__HOST`).
  Группа добавляется новым `BaseModel` в `app/core/config.py` и полем в корневом `Settings`.
- Все ошибки уходят через `app/core/errors.py` с унифицированным телом `ErrorResponse`.
- Эндпоинты регистрируются в `app/api/router.py` с префиксом `/api`.
- Модели наследуются от `app.models.base.BaseModel` и регистрируются импортом в `app/models/__init__.py`, иначе их не увидит Alembic autogenerate.
- Docstrings на русском. Технические комментарии в коде минимальны: только когда WHY не очевиден.
- В prod (`APP__ENV=prod`) Swagger/ReDoc отключены.

## Что вне scope сейчас

Redis, очереди. Подключаются позже отдельными итерациями.
