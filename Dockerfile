FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=1

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --without dev --no-root

COPY . .

RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
