from datetime import datetime

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Post


def scheduled_actions_keyboard(post: Post) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🕒 Изменить дату", callback_data=f"sched:change:{post.id}")
    b.button(text="✅ Опубликовать сейчас", callback_data=f"post:publish:{post.id}")
    b.button(text="❌ Отменить и вернуть в черновики", callback_data=f"sched:cancel:{post.id}")
    b.adjust(1)
    return b.as_markup()


def confirm_schedule_keyboard(post_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить", callback_data=f"sched:confirm:{post_id}")
    b.button(text="✖️ Отмена", callback_data=f"post:open:{post_id}")
    b.adjust(2)
    return b.as_markup()


def scheduled_list_keyboard(posts: list[Post]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for post in posts:
        b.button(text=_label(post), callback_data=f"post:open:{post.id}")
    b.adjust(1)
    return b.as_markup()


def _label(post: Post) -> str:
    try:
        dt_str = datetime.fromisoformat(post.scheduled_at).strftime("%d.%m %H:%M")
    except Exception:
        dt_str = "?"
    topic = (post.topic or post.display_text or "Без темы").replace("\n", " ").strip()[:30]
    return f"{dt_str} — {topic}"
