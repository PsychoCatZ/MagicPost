from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def content_plan_keyboard(plan: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, (day, topic) in enumerate(plan):
        label = f"{day}: {topic}"
        if len(label) > 60:
            label = label[:57] + "..."
        b.button(text=label, callback_data=f"plan:{i}")
    b.adjust(1)
    return b.as_markup()
