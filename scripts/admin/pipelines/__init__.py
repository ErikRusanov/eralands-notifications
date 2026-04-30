"""pipelines — реестр пайплайнов admin-CLI.

Чтобы добавить новый пайплайн: создать файл с функцией ``run(api)`` и
зарегистрировать его в ``REGISTRY``.
"""

from __future__ import annotations

from collections.abc import Callable

from scripts.admin.api import AdminAPI
from scripts.admin.pipelines import provision_landing

PipelineFn = Callable[[AdminAPI], None]

REGISTRY: dict[str, tuple[PipelineFn, str]] = {
    "provision-landing": (
        provision_landing.run,
        "Создать лендинг (с новым или существующим клиентом) и получить код привязки",
    ),
}
