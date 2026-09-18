from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app.ai.content_service import ContentService
from app.ai.factory import get_provider
from app.config import settings
from app.database.db import init_db
from app.handlers import register_handlers
from app.logging_config import setup_logging
from app.services.access import OwnerOnlyMiddleware
from app.services.scheduler import PostScheduler

logger = logging.getLogger(__name__)


async def _check_channel_rights(bot: Bot) -> None:
    """Warns loudly on startup if the bot can't actually publish — this is
    a very common setup mistake and better caught here than at publish time.
    """
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(settings.target_channel_id, me.id)
    except Exception:
        logger.exception(
            "Не удалось проверить права бота в канале %s. Убедитесь, что "
            "TARGET_CHANNEL_ID указан верно и бот добавлен в канал.",
            settings.target_channel_id,
        )
        return

    is_admin = getattr(member, "status", None) == "administrator"
    can_post = getattr(member, "can_post_messages", True)
    if not is_admin or not can_post:
        logger.warning(
            "Бот НЕ является администратором канала %s с правом публикации сообщений. "
            "Публикация постов не будет работать, пока это не исправлено.",
            settings.target_channel_id,
        )
    else:
        logger.info("Права бота в канале проверены: публикация доступна.")


async def main() -> None:
    setup_logging()
    logger.info("Запуск бота. AI_PROVIDER=%s, AI_MODEL=%s", settings.ai_provider, settings.ai_model)

    init_db()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.outer_middleware(OwnerOnlyMiddleware())
    dp.callback_query.outer_middleware(OwnerOnlyMiddleware())

    provider = get_provider(settings)
    content_service = ContentService(provider, settings)
    scheduler = PostScheduler(bot)

    dp["content_service"] = content_service
    dp["scheduler"] = scheduler

    register_handlers(dp)

    await _check_channel_rights(bot)

    scheduler.start()
    await scheduler.load_pending()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())
