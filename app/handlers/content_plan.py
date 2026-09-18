from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.base import AIError
from app.ai.content_service import ContentService
from app.keyboards.content_plan import content_plan_keyboard
from app.keyboards.texts import MenuText
from app.services.post_service import AI_ERROR_TEXT, generate_and_show

router = Router(name="content_plan")


@router.message(F.text == MenuText.CONTENT_PLAN)
async def show_content_plan(
    message: Message, state: FSMContext, content_service: ContentService
) -> None:
    status_msg = await message.answer("⏳ Формирую контент-план…")
    try:
        plan = await content_service.suggest_content_plan()
    except AIError:
        await status_msg.edit_text(AI_ERROR_TEXT)
        return
    if not plan:
        await status_msg.edit_text(AI_ERROR_TEXT)
        return

    await state.update_data(plan=plan)
    await status_msg.delete()
    summary = "\n".join(f"{day} — {topic}" for day, topic in plan)
    await message.answer(
        "Контент-план на неделю:\n\n" + summary + "\n\nВыберите тему, чтобы сразу создать пост:",
        reply_markup=content_plan_keyboard(plan),
    )


@router.callback_query(F.data.startswith("plan:"))
async def pick_plan_topic(
    callback: CallbackQuery, state: FSMContext, content_service: ContentService
) -> None:
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    plan = data.get("plan", [])
    if idx < 0 or idx >= len(plan):
        await callback.answer("Тема больше недоступна", show_alert=True)
        return
    _, topic = plan[idx]
    await callback.answer()
    await generate_and_show(callback.message, content_service, mode="topic", topic=topic)
