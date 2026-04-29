"""replies — конкретная фабрика ответов бота."""

import random

from app.bot.abstracts import AbstractReplies


class Replies(AbstractReplies):
    """Фабрика готовых текстов ответов бота.

    Каждый метод соответствует записи ``[messages.<key>]`` в ``texts.toml``.
    Подстановка значений идёт через ``str.format`` с предварительным
    HTML-экранированием через ``_escape``.
    """

    def start_welcome(self, name: str | None = None) -> str:
        """Сформировать приветственный ответ на команду ``/start``.

        Аргументы:
            name: Имя пользователя из Telegram (``first_name``). Если ``None``
                или пустая строка, отдаётся обезличенный вариант.

        Возвращает:
            Готовая HTML-строка для ``message.answer``.
        """
        if name:
            return self._msg("start_welcome_named").format(**self._escape(name=name))
        return self._msg("start_welcome")

    def echo(self) -> str:
        """Вернуть случайную заглушку-ответ на любое сообщение пользователя.

        Варианты текстов хранятся в ``[messages.echo].variants`` в
        ``texts.toml``. Используется catch-all хендлером, пока полноценная
        логика бота не реализована.

        Возвращает:
            Случайно выбранная HTML-строка для ``message.answer``.
        """
        variants: list[str] = self._messages["echo"]["variants"]
        return random.choice(variants)
