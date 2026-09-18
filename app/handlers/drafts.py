from aiogram import F, Router
from aiogram.types import Message

from app.database import repository
from app.database.db import run_sync
from app.keyboards.drafts import drafts_list_keyboard
from app.keyboards.texts import MenuText

router = Router(name="drafts")


@router.message(F.text == MenuText.DRAFTS)
async def list_drafts(message: Message) -> None:
    posts = await run_sync(repository.list_drafts)
    if not posts:
        await message.answer("Черновиков пока нет.")
        return
    await message.answer("Ваши черновики:", reply_markup=drafts_list_keyboard(posts))
