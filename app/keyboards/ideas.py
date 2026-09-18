from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def ideas_keyboard(ideas: list[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, idea in enumerate(ideas):
        label = idea if len(idea) <= 60 else idea[:57] + "..."
        b.button(text=f"{i + 1}. {label}", callback_data=f"idea:{i}")
    b.button(text="🔄 Предложить другие темы", callback_data="idea:more")
    b.adjust(1)
    return b.as_markup()
