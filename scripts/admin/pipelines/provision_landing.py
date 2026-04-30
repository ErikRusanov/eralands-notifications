"""provision_landing — пайплайн создания лендинга и выдачи кода привязки.

Шаги:
    1. Выбрать существующего клиента из списка или создать нового.
    2. Ввести slug и имя лендинга.
    3. Получить от API одноразовый код привязки и api-токен лендинга.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.admin import ui
from scripts.admin.api import AdminAPI

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


def run(api: AdminAPI) -> None:
    """Прогоняет пайплайн целиком."""
    client = _choose_or_create_client(api)
    landing_slug = ui.ask_text("Slug лендинга:", validate=_validate_slug)
    landing_name = ui.ask_text("Имя лендинга:", validate=_validate_nonempty)

    provisioned = api.provision_landing(client["id"], landing_slug, landing_name)
    landing = provisioned["landing"]
    code = provisioned["linking_code"]

    ui.heading("Лендинг создан")
    ui.kv("name:", landing["name"])
    ui.kv("slug:", landing["slug"])
    ui.kv("id:", landing["id"])
    ui.kv("api token:", provisioned["api_token"])
    ui.kv("код:", code["code"])
    ui.kv("истечёт:", code["expires_at"])


def _choose_or_create_client(api: AdminAPI) -> dict[str, Any]:
    clients = api.list_clients()
    clients.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    if not clients:
        ui.heading("Клиентов пока нет, создаём первого")
        return _create_client(api)

    selected = ui.select_or_create(
        title="Клиент:",
        items=clients,
        display=_format_client,
    )
    if selected is ui.CREATE_NEW:
        return _create_client(api)
    return selected  # type: ignore[return-value]


def _create_client(api: AdminAPI) -> dict[str, Any]:
    name = ui.ask_text("Имя нового клиента:", validate=_validate_nonempty)
    client = api.create_client(name)
    ui.heading(f"Клиент создан: {client['name']}")
    return client


def _format_client(client: dict[str, Any]) -> str:
    landings_count = len(client.get("landings") or [])
    suffix = "лендинг" if landings_count == 1 else "лендингов"
    return f"{client['name']}  ({landings_count} {suffix})"


def _validate_slug(value: str) -> bool | str:
    if not value:
        return "не пусто"
    if len(value) > 64:
        return "до 64 символов"
    if not SLUG_RE.match(value):
        return "латиница в нижнем регистре, цифры, дефисы"
    return True


def _validate_nonempty(value: str) -> bool | str:
    return True if value.strip() else "не пусто"
