"""commands — абстрактный реестр команд и совместимый с aiogram BotCommand."""

from abc import ABC

from aiogram.filters import Command


class BotCommand(Command):
    """Описание команды бота и одновременно фильтр для aiogram-роутера.

    Наследует ``aiogram.filters.Command``, поэтому экземпляр можно передать
    напрямую в ``@router.message(...)`` — фильтр среагирует на сообщение,
    начинающееся с ``/<name>``.

    Атрибуты:
        cmd_name: Имя команды без слэша. Совпадает с ключом в ``texts.toml``
            (``[commands.<cmd_name>]``).
    """

    def __init__(self, name: str) -> None:
        """Создать команду с заданным именем.

        Аргументы:
            name: Имя команды без слэша (например, ``"start"``).
        """
        super().__init__(name)
        self.cmd_name = name


class AbstractCommands(ABC):  # noqa: B024
    """Базовый реестр команд бота.

    Конкретные сабклассы определяют команды как атрибуты класса:

        class Commands(AbstractCommands):
            start = BotCommand("start")

    Метод ``all`` возвращает список всех ``BotCommand``-атрибутов сабкласса —
    удобно для регистрации команд в Telegram через ``set_my_commands`` (если
    понадобится в будущем).
    """

    def all(self) -> list[BotCommand]:
        """Вернуть все команды, объявленные в сабклассе.

        Возвращает:
            Список ``BotCommand`` в порядке объявления атрибутов класса.
        """
        return [v for v in vars(type(self)).values() if isinstance(v, BotCommand)]
