.PHONY: setup format run update migration migrate db-up db-down run-vpn test \
        admin provision-landing

VPN_HOST ?= root@89.19.213.102
VPN_REMOTE_PORT ?= 8000
VPN_LOCAL_PORT ?= 8000

# Admin CLI (scripts/admin/). URL и KEY можно переопределить из cli:
#   make provision-landing URL=https://api.example.com KEY=secret
URL ?= http://localhost:8000
KEY ?=
ADMIN_RUN = ADMIN_URL=$(URL) $(if $(strip $(KEY)),ADMIN_KEY=$(KEY)) \
            poetry run python -m scripts.admin

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

test: db-up
	poetry run pytest $(args)

# --- Admin CLI костыли (scripts/admin/) ----------------------------------
# Передать произвольную команду: `make admin args="provision-landing"`.
admin:
	@$(ADMIN_RUN) $(args)

# Пайплайн: клиент (выбор/создание) -> лендинг -> код привязки.
provision-landing:
	@$(ADMIN_RUN) provision-landing
