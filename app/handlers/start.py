from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu import main_menu_keyboard

router = Router(name="start")

WELCOME = (
    "✨ Контент-помощник\n\n"
    "Помогу быстро готовить посты для канала: по теме, из тезисов "
    "или переработать готовый текст. Выберите действие в меню ниже."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu_keyboard())
