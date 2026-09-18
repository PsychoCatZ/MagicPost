from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot

from app.config import settings
from app.database import repository
from app.database.db import run_sync
from app.utils.markdown_html import markdown_to_html

logger = logging.getLogger(__name__)

PHOTO_CAPTION_LIMIT = 1024


class PublishError(RuntimeError):
    """Raised when a post could not be sent to the channel."""


async def publish_post(bot: Bot, post_id: int) -> None:
    post = await run_sync(repository.get_post, post_id)
    if post is None:
        raise PublishError("Пост не найден")

    if not post.display_text.strip():
        raise PublishError("Текст поста пуст")
    text = markdown_to_html(post.display_text)

    chat_id = settings.target_channel_id
    try:
        if post.image_file_id:
            if len(text) <= PHOTO_CAPTION_LIMIT:
                await bot.send_photo(
                    chat_id, photo=post.image_file_id, caption=text, parse_mode="HTML"
                )
            else:
                await bot.send_photo(chat_id, photo=post.image_file_id)
                await bot.send_message(chat_id, text=text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, text=text, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Не удалось опубликовать пост %s в канал %s", post_id, chat_id)
        raise PublishError(str(exc)) from exc

    now = datetime.now(timezone.utc).isoformat()
    await run_sync(repository.set_published, post_id, now)
    logger.info("Пост %s опубликован в канал %s", post_id, chat_id)
