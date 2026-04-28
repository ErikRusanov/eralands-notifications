"""replies — конкретная фабрика ответов бота."""

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
