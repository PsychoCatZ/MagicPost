from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.keyboards.texts import MenuText


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MenuText.CREATE_POST)],
            [KeyboardButton(text=MenuText.SUGGEST_IDEAS)],
            [KeyboardButton(text=MenuText.FROM_BULLETS)],
            [KeyboardButton(text=MenuText.REWRITE)],
            [KeyboardButton(text=MenuText.DRAFTS), KeyboardButton(text=MenuText.SCHEDULED)],
            [KeyboardButton(text=MenuText.CONTENT_PLAN)],
            [KeyboardButton(text=MenuText.SETTINGS)],
        ],
        resize_keyboard=True,
    )
