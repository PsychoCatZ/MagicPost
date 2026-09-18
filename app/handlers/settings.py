from aiogram import F, Router
from aiogram.types import Message

from app.config import settings
from app.keyboards.texts import MenuText

router = Router(name="settings")


@router.message(F.text == MenuText.SETTINGS)
async def show_settings(message: Message) -> None:
    text = (
        "⚙️ Настройки\n\n"
        f"Автор публикаций: {settings.author_name}\n"
        f"Канал для публикации: {settings.target_channel_id}\n"
        f"Часовой пояс: {settings.app_timezone}\n"
        "Помощник ИИ: подключён ✅"
    )
    await message.answer(text)
