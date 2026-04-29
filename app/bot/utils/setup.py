"""setup — стартовая обвязка бота для FastAPI lifespan."""

import logging

from aiogram import Bot, Dispatcher

from app.core.config import settings

logger = logging.getLogger(__name__)


async def setup_bot() -> tuple[Bot, Dispatcher]:
    """Поднять бота: создать Bot/Dispatcher, подключить хендлеры, поставить webhook.

    Webhook у Telegram регистрируется только если задан
    ``settings.telegram.WEBHOOK_URL``. Иначе сервис стартует, но обновления от
    Telegram не приходят (полезно в локальной разработке без публичного URL).

    Возвращает:
        Кортеж ``(bot, dp)``, готовый к использованию вебхук-эндпоинтом.

    Поднимает:
        aiogram.exceptions.TelegramAPIError: Если регистрация вебхука у
            Telegram провалилась.
    """
    # Импорты отложены, чтобы развязать круг через app.core.__init__ ↔ app.bot.*.
    from app.bot.core import create_bot, create_dispatcher
    from app.bot.handlers import register_handlers
    from app.bot.middleware import LoggingMiddleware
    from app.bot.utils.commands import Commands
    from app.bot.utils.replies import Replies

    bot = create_bot()
    dp = create_dispatcher()

    replies = Replies()
    commands = Commands()

    dp["replies"] = replies
    dp["commands"] = commands

    dp.update.middleware(LoggingMiddleware())

    register_handlers(dp)

    await bot.set_my_commands(commands.as_telegram())

    if settings.telegram.WEBHOOK_URL:
        base = settings.telegram.WEBHOOK_URL.rstrip("/")
        webhook_url = f"{base}{settings.telegram.WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logger.info("Webhook set to %s", webhook_url)
    else:
        logger.warning(
            "TELEGRAM__WEBHOOK_URL is not set — skipping webhook registration."
        )

    logger.info("Bot started.")
    return bot, dp


async def teardown_bot(bot: Bot) -> None:
    """Снять webhook у Telegram и закрыть HTTP-сессию бота.

    Аргументы:
        bot: Экземпляр ``Bot``, созданный через ``setup_bot``.
    """
    if settings.telegram.WEBHOOK_URL:
        await bot.delete_webhook()
        logger.info("Webhook removed.")
    await bot.session.close()
    logger.info("Bot stopped.")
