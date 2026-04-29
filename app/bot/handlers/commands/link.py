"""link — обработчик команды ``/link`` и ввода одноразового кода привязки."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.bot.middleware import DbSessionMiddleware
from app.bot.utils.commands import Commands
from app.bot.utils.replies import Replies
from app.services.domain import (
    LinkingCodeExpiredError,
    LinkingCodeNotFoundError,
    LinkingService,
)


class LinkStates(StatesGroup):
    """Состояния FSM для команды ``/link``."""

    awaiting_code = State()


router = Router(name=Commands.link.cmd_name)
router.message.middleware(DbSessionMiddleware())


@router.message(Commands.link)
async def handle_link_entry(
    message: Message, state: FSMContext, replies: Replies
) -> None:
    """Запросить у пользователя одноразовый код после команды ``/link``."""
    await state.set_state(LinkStates.awaiting_code)
    await message.answer(replies.link_prompt())


@router.message(LinkStates.awaiting_code, F.text)
async def handle_link_code(
    message: Message,
    state: FSMContext,
    replies: Replies,
    linking_service: LinkingService,
) -> None:
    """Принять код от пользователя и попытаться привязать чат к лендингу."""
    code = (message.text or "").strip().upper().replace(" ", "")
    chat_id = message.chat.id

    try:
        result = await linking_service.link_telegram_chat(code, chat_id)
    except LinkingCodeNotFoundError:
        await message.answer(replies.link_not_found())
    except LinkingCodeExpiredError:
        await message.answer(replies.link_expired())
    else:
        await message.answer(
            replies.link_success(
                landing=result.landing_name,
                client=result.client_name,
                routes_count=result.routes_count,
            )
        )
    finally:
        await state.clear()
