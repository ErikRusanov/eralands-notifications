"""api — тонкая httpx-обёртка над admin-эндпоинтами.

Сюда добавляются ровно те методы, которые нужны пайплайнам в
``scripts/admin/pipelines/``. Бизнес-логики здесь нет: один метод равен
одному вызову API.
"""

from __future__ import annotations

from typing import Any

import httpx

from scripts.admin.config import Config


class AdminAPIError(RuntimeError):
    """Ошибка API: статус-код плюс тело ответа в человеческом виде."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


class AdminAPI:
    """Sync-клиент админских эндпоинтов.

    Используется как контекстный менеджер: ``with AdminAPI(cfg) as api: ...``.
    """

    def __init__(self, cfg: Config) -> None:
        self._client = httpx.Client(
            base_url=cfg.url,
            headers={"Authorization": f"Bearer {cfg.key}"},
            timeout=10.0,
        )

    def __enter__(self) -> AdminAPI:
        return self

    def __exit__(self, *_exc: object) -> None:
        self._client.close()

    def list_clients(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/clients")

    def create_client(self, name: str) -> dict[str, Any]:
        return self._request("POST", "/api/clients", json={"name": name})

    def provision_landing(self, client_id: str, slug: str, name: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/clients/{client_id}/landings",
            json={"slug": slug, "name": name},
        )

    def issue_linking_code(self, landing_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/landings/{landing_id}/linking-codes")

    def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> Any:
        try:
            response = self._client.request(method, path, json=json)
        except httpx.RequestError as exc:
            raise AdminAPIError(0, f"не удалось подключиться: {exc}") from exc
        if response.is_success:
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        raise AdminAPIError(response.status_code, _format_error(response))


def _format_error(response: httpx.Response) -> str:
    """Достаёт человекочитаемую строку из ответа с ошибкой."""
    try:
        body = response.json()
    except ValueError:
        return response.text or response.reason_phrase
    if isinstance(body, dict):
        if "detail" in body:
            return str(body["detail"])
        if "message" in body:
            return str(body["message"])
    return str(body)
