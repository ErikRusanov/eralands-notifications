.PHONY: setup format run update migration migrate db-up db-down run-vpn

VPN_HOST ?= root@89.19.213.102
VPN_REMOTE_PORT ?= 8000
VPN_LOCAL_PORT ?= 8000

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

run-vpn:
	@command -v autossh >/dev/null 2>&1 || { echo "autossh не установлен. Поставь: sudo apt install autossh"; exit 1; }
	autossh -M 0 -N \
		-o "ServerAliveInterval 30" \
		-o "ServerAliveCountMax 3" \
		-o "ExitOnForwardFailure yes" \
		-R $(VPN_REMOTE_PORT):127.0.0.1:$(VPN_LOCAL_PORT) \
		$(VPN_HOST)

update:
	poetry update

migration:
	poetry run alembic revision --autogenerate -m "$(m)"

migrate:
	poetry run alembic upgrade head
