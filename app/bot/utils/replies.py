"""replies — конкретная фабрика ответов бота."""

import random
from typing import Any

from aiogram.utils.text_decorations import html_decoration

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

    def lead_notification(self, *, landing: str, payload: dict[str, Any]) -> str:
        """Сформировать уведомление о новой заявке для отправки в канал клиента.

        Шаблон ``[messages.lead_notification]`` ожидает плейсхолдеры
        ``{landing}`` и ``{fields}``. Поля payload собираются в
        ``<b>key:</b> value``-строки. И заголовок, и каждое поле проходят
        через HTML-quote, чтобы пользовательский ввод не ломал разметку.

        Аргументы:
            landing: Имя лендинга (``Landing.name``).
            payload: Свободный JSON-payload формы.

        Возвращает:
            HTML-строка для ``Bot.send_message``.
        """
        fields = "\n".join(
            f"<b>{html_decoration.quote(str(key))}:</b> "
            f"{html_decoration.quote(str(value))}"
            for key, value in payload.items()
        )
        return self._msg("lead_notification").format(
            **self._escape(landing=landing),
            fields=fields,
        )

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
