from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.base import AIError
from app.ai.content_service import ContentService
from app.keyboards.ideas import ideas_keyboard
from app.keyboards.texts import MenuText
from app.services.post_service import AI_ERROR_TEXT, generate_and_show
from app.states.generation import PostCreation

router = Router(name="generate")


@router.message(F.text == MenuText.CREATE_POST)
async def start_create_post(message: Message, state: FSMContext) -> None:
    await state.set_state(PostCreation.waiting_topic)
    await message.answer("О чём должен быть пост?\nНапишите тему своими словами.")


@router.message(PostCreation.waiting_topic)
async def receive_topic(
    message: Message, state: FSMContext, content_service: ContentService
) -> None:
    await state.clear()
    await generate_and_show(message, content_service, mode="topic", topic=message.text)


@router.message(F.text == MenuText.FROM_BULLETS)
async def start_from_bullets(message: Message, state: FSMContext) -> None:
    await state.set_state(PostCreation.waiting_bullets)
    await message.answer(
        "Пришлите тезисы одним сообщением — по одному на строку.\n\n"
        "Например:\n"
        "— ошибки в SEO\n"
        "— слишком много ключей\n"
        "— нет нормального заголовка"
    )


@router.message(PostCreation.waiting_bullets)
async def receive_bullets(
    message: Message, state: FSMContext, content_service: ContentService
) -> None:
    await state.clear()
    await generate_and_show(message, content_service, mode="bullets", source_text=message.text)


@router.message(F.text == MenuText.REWRITE)
async def start_rewrite(message: Message, state: FSMContext) -> None:
    await state.set_state(PostCreation.waiting_source_text)
    await message.answer("Пришлите текст, который нужно переработать.")


@router.message(PostCreation.waiting_source_text)
async def receive_source_text(
    message: Message, state: FSMContext, content_service: ContentService
) -> None:
    await state.clear()
    await generate_and_show(message, content_service, mode="rewrite", source_text=message.text)


async def _show_ideas(message: Message, state: FSMContext, content_service: ContentService) -> None:
    status_msg = await message.answer("⏳ Подбираю темы…")
    try:
        ideas = await content_service.suggest_ideas()
    except AIError:
        await status_msg.edit_text(AI_ERROR_TEXT)
        return
    if not ideas:
        await status_msg.edit_text(AI_ERROR_TEXT)
        return
    await state.update_data(ideas=ideas)
    await status_msg.delete()
    await message.answer("Вот несколько тем на выбор:", reply_markup=ideas_keyboard(ideas))


@router.message(F.text == MenuText.SUGGEST_IDEAS)
async def suggest_ideas(
    message: Message, state: FSMContext, content_service: ContentService
) -> None:
    await _show_ideas(message, state, content_service)


@router.callback_query(F.data == "idea:more")
async def more_ideas(
    callback: CallbackQuery, state: FSMContext, content_service: ContentService
) -> None:
    await callback.answer()
    await _show_ideas(callback.message, state, content_service)


@router.callback_query(F.data.startswith("idea:"))
async def pick_idea(
    callback: CallbackQuery, state: FSMContext, content_service: ContentService
) -> None:
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    ideas = data.get("ideas", [])
    if idx < 0 or idx >= len(ideas):
        await callback.answer("Тема больше недоступна", show_alert=True)
        return
    topic = ideas[idx]
    await callback.answer()
    await generate_and_show(callback.message, content_service, mode="topic", topic=topic)
