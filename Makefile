.PHONY: setup format run update

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env created from .env.example"; \
	else \
		echo ".env already exists, skipping"; \
	fi
	poetry install

format:
	poetry run ruff format .
	poetry run ruff check --fix .

run:
	poetry run python -m app.main

update:
	poetry update