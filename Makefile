.PHONY: setup format run update migration migrate db-up db-down

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env created from .env.example"; \
	else \
		echo ".env already exists, skipping"; \
	fi
	poetry install
	poetry run pre-commit install

format:
	poetry run ruff format .
	poetry run ruff check --fix .

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose stop postgres

run: db-up
	poetry run python -m app.main

update:
	poetry update

migration:
	poetry run alembic revision --autogenerate -m "$(m)"

migrate:
	poetry run alembic upgrade head
