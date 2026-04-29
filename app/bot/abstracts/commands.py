"""commands — абстрактный реестр команд и совместимый с aiogram BotCommand."""

from abc import ABC
from pathlib import Path
from typing import Any

import tomllib
from aiogram.filters import Command
from aiogram.types import BotCommand as TelegramBotCommand

# texts.toml лежит рядом с пакетом bot: app/bot/abstracts/commands.py → ../texts.toml
_TEXTS_FILE = Path(__file__).resolve().parents[1] / "texts.toml"


class BotCommand(Command):
    """Описание команды бота и одновременно фильтр для aiogram-роутера.

    Наследует ``aiogram.filters.Command``, поэтому экземпляр можно передать
    напрямую в ``@router.message(...)`` — фильтр среагирует на сообщение,
    начинающееся с ``/<name>``.

    Атрибуты:
        cmd_name: Имя команды без слэша. Совпадает с ключом в ``texts.toml``
            (``[commands.<cmd_name>]``).
        in_menu: Показывать ли команду в дефолтном меню Telegram. Команды
            вроде ``/start``, которые пользователь не вводит руками, в меню
            не нужны.
    """

    def __init__(self, name: str, *, in_menu: bool = False) -> None:
        """Создать команду с заданным именем.

        Аргументы:
            name: Имя команды без слэша (например, ``"start"``).
            in_menu: Если ``True``, команда попадёт в список ``set_my_commands``
                и будет видна в дефолтном меню Telegram.
        """
        super().__init__(name)
        self.cmd_name = name
        self.in_menu = in_menu


class AbstractCommands(ABC):  # noqa: B024
    """Базовый реестр команд бота.

    Конкретные сабклассы определяют команды как атрибуты класса:

        class Commands(AbstractCommands):
            start = BotCommand("start")

    При инициализации читает ``app/bot/texts.toml`` и кеширует секцию
    ``[commands.*]`` — оттуда берутся описания команд для Telegram-меню.
    """

    def __init__(self) -> None:
        """Загрузить описания команд из ``texts.toml`` в память."""
        with open(_TEXTS_FILE, "rb") as fh:
            data = tomllib.load(fh)
        self._commands: dict[str, dict[str, Any]] = data.get("commands", {})

    def all(self) -> list[BotCommand]:
        """Вернуть все команды, объявленные в сабклассе.

        Возвращает:
            Список ``BotCommand`` в порядке объявления атрибутов класса.
        """
        return [v for v in vars(type(self)).values() if isinstance(v, BotCommand)]

    def as_telegram(self) -> list[TelegramBotCommand]:
        """Сформировать список команд для дефолтного меню Telegram.

        Включает только команды с ``in_menu=True``. Описание подставляется
        из секции ``[commands.<cmd_name>]`` файла ``texts.toml``. Результат
        передаётся в ``bot.set_my_commands``.

        Возвращает:
            Список ``aiogram.types.BotCommand`` в порядке объявления атрибутов.

        Поднимает:
            KeyError: Если для команды нет записи в ``texts.toml``.
        """
        return [
            TelegramBotCommand(
                command=cmd.cmd_name,
                description=self._commands[cmd.cmd_name]["description"],
            )
            for cmd in self.all()
            if cmd.in_menu
        ]
