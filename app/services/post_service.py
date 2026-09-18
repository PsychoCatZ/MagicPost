from __future__ import annotations

from aiogram.types import Message

from app.ai.base import AIError
from app.ai.content_service import ContentService
from app.database import repository
from app.database.db import run_sync
from app.services.rendering import render_post_preview

AI_ERROR_TEXT = "⚠️ Не удалось получить ответ от AI.\nПопробуйте повторить позже."


async def generate_and_show(
    message: Message,
    content_service: ContentService,
    *,
    mode: str,
    topic: str | None = None,
    source_text: str | None = None,
) -> None:
    """Creates a draft row, asks the AI to fill it in, then shows the
    preview. On AI failure the draft (and the topic/source text the owner
    already typed) is kept, and the preview still shows up so the owner can
    retry with "Перегенерировать" instead of losing their input.
    """
    post = await run_sync(
        repository.create_post, creation_mode=mode, topic=topic, source_text=source_text
    )
    status_msg = await message.answer("⏳ Готовлю черновик…")

    try:
        text = await content_service.generate_for_post(
            mode=mode, topic=topic, source_text=source_text
        )
    except AIError:
        await status_msg.edit_text(AI_ERROR_TEXT)
        post = await run_sync(repository.get_post, post.id)
        if post is not None:
            await render_post_preview(message, post)
        return

    post = await run_sync(
        repository.update_post_text, post.id, generated_text=text, final_text=text
    )
    await status_msg.delete()
    if post is not None:
        await render_post_preview(message, post)
