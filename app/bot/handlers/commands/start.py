"""start — обработчик команды ``/start``."""

from aiogram import Router
from aiogram.types import Message

from app.bot.utils.commands import Commands
from app.bot.utils.replies import Replies

router = Router(name=Commands.start.cmd_name)


@router.message(Commands.start)
async def handle_start(message: Message, replies: Replies) -> None:
    """Поприветствовать пользователя в ответ на команду ``/start``.

    Аргументы:
        message: Входящее сообщение Telegram, содержащее команду.
        replies: Фабрика ответов, инжектируемая через ``dp["replies"]``.
    """
    name = message.from_user.first_name if message.from_user else None
    await message.answer(replies.start_welcome(name=name))
