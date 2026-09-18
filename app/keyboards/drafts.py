from datetime import datetime

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Post


def drafts_list_keyboard(posts: list[Post]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for post in posts:
        b.button(text=_label(post), callback_data=f"post:open:{post.id}")
    b.adjust(1)
    return b.as_markup()


def _label(post: Post) -> str:
    text = (post.display_text or post.topic or "Без текста").replace("\n", " ").strip()
    preview = text[:40] + ("…" if len(text) > 40 else "")
    try:
        created = datetime.fromisoformat(post.created_at).strftime("%d.%m %H:%M")
    except Exception:
        created = ""
    return f"{preview} ({created})" if created else preview
