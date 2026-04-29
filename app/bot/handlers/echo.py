"""echo — catch-all обработчик любых входящих сообщений.

Временная заглушка: на любое сообщение пользователя (текст, фото, голос,
стикер, документ и пр.) бот отвечает случайным вариантом из набора текстов
``[messages.echo].variants`` в ``texts.toml``. Подключается в роутер-цепочку
после обработчиков команд, чтобы не перехватывать ``/start`` и подобные.
"""

from aiogram import Router
from aiogram.types import Message

from app.bot.utils.replies import Replies

router = Router(name="echo")


@router.message()
async def handle_any(message: Message, replies: Replies) -> None:
    """Ответить случайной заглушкой на любое входящее сообщение.

    Аргументы:
        message: Любое входящее сообщение Telegram.
        replies: Фабрика ответов, инжектируемая через ``dp["replies"]``.
    """
    await message.answer(replies.echo())
