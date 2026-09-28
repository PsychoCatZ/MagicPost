from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from aiogram import Bot

from app.config import settings
from app.database import repository
from app.database.db import run_sync
from app.database.models import Post
from app.utils.markdown_html import markdown_to_html

logger = logging.getLogger(__name__)

PHOTO_CAPTION_LIMIT = 1024
SITE_NOTIFY_TIMEOUT = 10.0

TARGET_CHANNEL = "channel"
TARGET_SITE = "site"
TARGET_BOTH = "both"
VALID_TARGETS = (TARGET_CHANNEL, TARGET_SITE, TARGET_BOTH)


class PublishError(RuntimeError):
    """Raised when a post could not be published to any of the requested targets."""


async def _send_to_site(post: Post) -> None:
    async with httpx.AsyncClient(timeout=SITE_NOTIFY_TIMEOUT) as client:
        response = await client.post(
            settings.site_news_api_url,
            headers={"Authorization": f"Bearer {settings.site_news_api_key}"},
            json={"text": post.display_text, "topic": post.topic},
        )
        response.raise_for_status()


async def _send_to_channel(bot: Bot, post: Post, text: str) -> None:
    chat_id = settings.target_channel_id
    if post.image_file_id:
        if len(text) <= PHOTO_CAPTION_LIMIT:
            await bot.send_photo(chat_id, photo=post.image_file_id, caption=text, parse_mode="HTML")
        else:
            await bot.send_photo(chat_id, photo=post.image_file_id)
            await bot.send_message(chat_id, text=text, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text=text, parse_mode="HTML")


async def publish_post(bot: Bot, post_id: int, targets: str | None = None) -> list[str]:
    """Publishes a post to the channel, the site, or both.

    Returns the targets that failed after another target already succeeded
    (only possible for 'both': channel ok, site failed). In that case the post
    goes back to 'draft' so it can be re-sent to the failed target alone.
    Raises PublishError when nothing was published.
    """
    post = await run_sync(repository.get_post, post_id)
    if post is None:
        raise PublishError("Пост не найден")

    targets = targets or post.targets
    if targets not in VALID_TARGETS:
        raise PublishError(f"Неизвестное назначение публикации: {targets}")

    if not post.display_text.strip():
        raise PublishError("Текст поста пуст")

    to_channel = targets in (TARGET_CHANNEL, TARGET_BOTH)
    to_site = targets in (TARGET_SITE, TARGET_BOTH)
    if to_site and not settings.site_enabled:
        if targets == TARGET_SITE:
            raise PublishError("Публикация на сайт не настроена (нет SITE_NEWS_API_URL/KEY)")
        to_site = False

    if to_channel:
        try:
            await _send_to_channel(bot, post, markdown_to_html(post.display_text))
        except Exception as exc:
            logger.exception(
                "Не удалось опубликовать пост %s в канал %s", post_id, settings.target_channel_id
            )
            raise PublishError(str(exc)) from exc
        logger.info("Пост %s опубликован в канал %s", post_id, settings.target_channel_id)

    if to_site:
        try:
            await _send_to_site(post)
        except Exception as exc:
            logger.exception("Не удалось отправить пост %s на сайт", post_id)
            if not to_channel:
                raise PublishError(str(exc)) from exc
            await run_sync(repository.set_status, post_id, "draft")
            return [TARGET_SITE]
        logger.info("Пост %s отправлен на сайт", post_id)

    now = datetime.now(timezone.utc).isoformat()
    await run_sync(repository.set_published, post_id, now)
    return []
