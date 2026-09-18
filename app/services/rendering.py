from __future__ import annotations

from aiogram.types import Message

from app.database.models import Post
from app.keyboards.post_actions import post_preview_keyboard
from app.keyboards.scheduled import scheduled_actions_keyboard
from app.utils.markdown_html import markdown_to_html

PHOTO_CAPTION_LIMIT = 1024


def _keyboard_for(post: Post):
    if post.status == "scheduled":
        return scheduled_actions_keyboard(post)
    return post_preview_keyboard(post)


async def render_post_preview(message: Message, post: Post) -> None:
    """Shows the full post (text + optional image) with its action buttons.

    Never publishes anything — this is only ever a preview screen. Text is
    converted to Telegram HTML the same way as at publish time, so the
    preview always looks exactly like the final post (bold, lists, line
    breaks and special characters render identically, not as raw markdown).
    """
    raw_text = post.display_text or "(текст пока пуст — попробуйте перегенерировать)"
    text = markdown_to_html(raw_text)
    keyboard = _keyboard_for(post)

    if post.image_file_id:
        if len(text) <= PHOTO_CAPTION_LIMIT:
            await message.answer_photo(
                post.image_file_id, caption=text, parse_mode="HTML", reply_markup=keyboard
            )
        else:
            await message.answer_photo(post.image_file_id)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
