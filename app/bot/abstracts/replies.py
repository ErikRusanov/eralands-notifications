"""replies — базовая фабрика ответов бота с загрузкой текстов из TOML."""

from abc import ABC
from pathlib import Path
from typing import Any

import tomllib
from aiogram.utils.text_decorations import html_decoration

# texts.toml лежит рядом с пакетом bot: app/bot/abstracts/replies.py → ../texts.toml
_TEXTS_FILE = Path(__file__).resolve().parents[1] / "texts.toml"


class AbstractReplies(ABC):  # noqa: B024
    """Базовая фабрика ответов.

    При инициализации читает ``app/bot/texts.toml`` и кеширует секцию
    ``[messages.*]``. Конкретные сабклассы определяют методы для каждого
    логического ответа и собирают строки через хелперы ``_msg`` и ``_escape``.

    Тексты грузятся один раз при старте сервиса — экземпляр живёт на всё
    время работы и переинжектируется в хендлеры через ``dp["replies"]``.
    """

    def __init__(self) -> None:
        """Загрузить тексты из ``texts.toml`` в память."""
        with open(_TEXTS_FILE, "rb") as fh:
            data = tomllib.load(fh)
        self._messages: dict[str, dict[str, Any]] = data.get("messages", {})

    def _msg(self, key: str) -> str:
        """Вернуть шаблон сообщения по ключу.

        Аргументы:
            key: Ключ из секции ``[messages.<key>]`` в ``texts.toml``.

        Возвращает:
            Содержимое поля ``text`` соответствующей записи.

        Поднимает:
            KeyError: Если ключ отсутствует в TOML.
        """
        return self._messages[key]["text"]

    @staticmethod
    def _escape(**kwargs: str) -> dict[str, str]:
        """Экранировать спецсимволы HTML в значениях для подстановки.

        Используется перед ``str.format`` на шаблонах с HTML-разметкой,
        чтобы пользовательский ввод не сломал теги в финальном сообщении.

        Аргументы:
            **kwargs: Пары имя-значение для подстановки в шаблон.

        Возвращает:
            Те же ключи со значениями, прошедшими через HTML-экранирование.
        """
        return {k: html_decoration.quote(v) for k, v in kwargs.items()}
