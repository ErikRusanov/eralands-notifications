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

    def link_prompt(self) -> str:
        """Текст приглашения ввести код после команды ``/link``."""
        return self._msg("link_prompt")

    def link_success(
        self,
        *,
        landing: str,
        client: str,
        routes_count: int,
    ) -> str:
        """Сформировать ответ об успешной привязке чата к лендингу.

        Аргументы:
            landing: Имя лендинга (``Landing.name``).
            client: Имя клиента (``Client.name``).
            routes_count: Сколько активных каналов теперь у лендинга.

        Возвращает:
            HTML-строка для ``message.answer``.
        """
        return self._msg("link_success").format(
            **self._escape(landing=landing, client=client),
            routes_count=routes_count,
        )

    def link_not_found(self) -> str:
        """Ответ когда код не найден или уже погашен."""
        return self._msg("link_not_found")

    def link_expired(self) -> str:
        """Ответ когда код существует, не использован, но протух."""
        return self._msg("link_expired")

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
