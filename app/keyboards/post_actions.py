from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Post


def post_preview_keyboard(post: Post) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Опубликовать", callback_data=f"post:publish:{post.id}")
    b.button(text="🕒 Запланировать", callback_data=f"post:schedule:{post.id}")
    b.button(text="🔄 Перегенерировать", callback_data=f"post:regenerate:{post.id}")
    b.button(text="✏️ Изменить текст", callback_data=f"post:edit:{post.id}")
    if post.image_file_id:
        b.button(text="🖼 Заменить изображение", callback_data=f"post:image_add:{post.id}")
        b.button(text="🗑 Удалить изображение", callback_data=f"post:image_remove:{post.id}")
    else:
        b.button(text="🖼 Добавить изображение", callback_data=f"post:image_add:{post.id}")
    b.button(text="💾 В черновики", callback_data=f"post:save_draft:{post.id}")
    b.button(text="🗑 Удалить", callback_data=f"post:delete:{post.id}")
    b.adjust(2)
    return b.as_markup()


def confirm_publish_keyboard(post_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Да", callback_data=f"post:publish_confirm:{post_id}")
    b.button(text="◀️ Назад", callback_data=f"post:open:{post_id}")
    b.adjust(2)
    return b.as_markup()


def confirm_delete_keyboard(post_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🗑 Да, удалить", callback_data=f"post:delete_confirm:{post_id}")
    b.button(text="◀️ Назад", callback_data=f"post:open:{post_id}")
    b.adjust(2)
    return b.as_markup()
