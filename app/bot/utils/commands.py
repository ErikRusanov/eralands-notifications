"""commands — конкретный реестр команд бота."""

from app.bot.abstracts import AbstractCommands, BotCommand


class Commands(AbstractCommands):
    """Реестр всех команд бота.

    Каждая команда описывается как атрибут класса типа ``BotCommand``.
    Имя атрибута и аргумент конструктора должны совпадать с ключом в
    секции ``[commands.<name>]`` файла ``app/bot/texts.toml``.

    Чтобы добавить новую команду:
    1. Объявить здесь атрибут: ``help = BotCommand("help")``.
    2. Добавить запись ``[commands.help]`` в ``texts.toml``.
    3. Создать хендлер в ``app/bot/handlers/commands/help.py`` и подключить
       его роутер в ``app/bot/handlers/commands/__init__.py``.
    """

    start = BotCommand("start")
