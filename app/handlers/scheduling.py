from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.database import repository
from app.database.db import run_sync
from app.keyboards.scheduled import confirm_schedule_keyboard, scheduled_list_keyboard
from app.keyboards.texts import MenuText
from app.services.scheduler import PostScheduler
from app.states.generation import Scheduling

router = Router(name="scheduling")


def _post_id(callback_data: str) -> int:
    return int(callback_data.split(":")[-1])


@router.callback_query(F.data.startswith("post:schedule:"))
async def start_schedule(callback: CallbackQuery, state: FSMContext) -> None:
    post_id = _post_id(callback.data)
    await state.set_state(Scheduling.waiting_date)
    await state.update_data(post_id=post_id)
    await callback.answer()
    await callback.message.answer("Введите дату публикации в формате ДД.ММ.ГГГГ\nНапример: 24.09.2026")


@router.callback_query(F.data.startswith("sched:change:"))
async def change_schedule(callback: CallbackQuery, state: FSMContext) -> None:
    post_id = _post_id(callback.data)
    await state.set_state(Scheduling.waiting_date)
    await state.update_data(post_id=post_id)
    await callback.answer()
    await callback.message.answer("Введите новую дату публикации в формате ДД.ММ.ГГГГ")


@router.message(Scheduling.waiting_date)
async def receive_date(message: Message, state: FSMContext) -> None:
    try:
        date_value = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Не получилось распознать дату. Формат: ДД.ММ.ГГГГ, например 24.09.2026")
        return
    await state.update_data(date=date_value.isoformat())
    await state.set_state(Scheduling.waiting_time)
    await message.answer("Введите время публикации в формате ЧЧ:ММ\nНапример: 15:00")


@router.message(Scheduling.waiting_time)
async def receive_time(message: Message, state: FSMContext) -> None:
    try:
        time_value = datetime.strptime(message.text.strip(), "%H:%M").time()
    except ValueError:
        await message.answer("Не получилось распознать время. Формат: ЧЧ:ММ, например 15:00")
        return

    data = await state.get_data()
    date_value = datetime.fromisoformat(data["date"]).date()
    tz = ZoneInfo(settings.app_timezone)
    run_at = datetime.combine(date_value, time_value, tzinfo=tz)

    if run_at <= datetime.now(tz):
        await message.answer(
            "Указанное время уже прошло. Введите дату заново в формате ДД.ММ.ГГГГ"
        )
        await state.set_state(Scheduling.waiting_date)
        return

    await state.update_data(run_at=run_at.isoformat())
    post_id = data["post_id"]
    pretty = run_at.strftime("%d.%m.%Y %H:%M")
    await message.answer(
        f"Запланировать публикацию на {pretty} ({settings.app_timezone})?",
        reply_markup=confirm_schedule_keyboard(post_id),
    )


@router.callback_query(F.data.startswith("sched:confirm:"))
async def confirm_schedule(
    callback: CallbackQuery, state: FSMContext, scheduler: PostScheduler
) -> None:
    post_id = _post_id(callback.data)
    data = await state.get_data()
    run_at = datetime.fromisoformat(data["run_at"])
    await state.clear()

    await run_sync(repository.set_scheduled, post_id, run_at.isoformat())
    scheduler.schedule_post(post_id, run_at)

    await callback.answer()
    pretty = run_at.strftime("%d.%m.%Y %H:%M")
    await callback.message.answer(f"🕒 Публикация запланирована на {pretty}.")


@router.message(F.text == MenuText.SCHEDULED)
async def list_scheduled(message: Message) -> None:
    posts = await run_sync(repository.list_scheduled)
    if not posts:
        await message.answer("Пока нет запланированных публикаций.")
        return
    await message.answer("Запланированные публикации:", reply_markup=scheduled_list_keyboard(posts))


@router.callback_query(F.data.startswith("sched:cancel:"))
async def cancel_schedule(callback: CallbackQuery, scheduler: PostScheduler) -> None:
    post_id = _post_id(callback.data)
    scheduler.cancel(post_id)
    await run_sync(repository.set_status, post_id, "draft")
    await callback.answer("Публикация отменена")
    await callback.message.answer("Публикация отменена. Пост возвращён в черновики.")
