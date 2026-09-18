from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.base import AIError
from app.ai.content_service import ContentService
from app.database import repository
from app.database.db import run_sync
from app.keyboards.post_actions import confirm_delete_keyboard, confirm_publish_keyboard
from app.services.publishing import PublishError, publish_post
from app.services.rendering import render_post_preview
from app.states.generation import PostEditing

router = Router(name="post_actions")

AI_ERROR_TEXT = "⚠️ Не удалось получить ответ от AI.\nПопробуйте повторить позже."


def _post_id(callback_data: str) -> int:
    return int(callback_data.split(":")[-1])


@router.callback_query(F.data.startswith("post:open:"))
async def open_post(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    post = await run_sync(repository.get_post, post_id)
    await callback.answer()
    if post is None:
        await callback.message.answer("Пост не найден — возможно, он уже был удалён.")
        return
    await render_post_preview(callback.message, post)


@router.callback_query(F.data.startswith("post:publish:"))
async def ask_publish_confirm(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    await callback.answer()
    await callback.message.answer(
        "Опубликовать пост в канал сейчас?",
        reply_markup=confirm_publish_keyboard(post_id),
    )


@router.callback_query(F.data.startswith("post:publish_confirm:"))
async def do_publish(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    try:
        await publish_post(callback.bot, post_id)
    except PublishError:
        await callback.answer()
        await callback.message.answer(
            "⚠️ Не удалось опубликовать пост. Проверьте, что бот всё ещё "
            "администратор канала с правом публикации, и попробуйте снова."
        )
        return
    await callback.answer()
    await callback.message.answer("✅ Пост опубликован.")


@router.callback_query(F.data.startswith("post:regenerate:"))
async def regenerate(callback: CallbackQuery, content_service: ContentService) -> None:
    post_id = _post_id(callback.data)
    post = await run_sync(repository.get_post, post_id)
    if post is None:
        await callback.answer("Пост не найден", show_alert=True)
        return

    await callback.answer("Генерирую новый вариант…")
    status_msg = await callback.message.answer("⏳ Готовлю новый вариант…")
    try:
        text = await content_service.generate_for_post(
            mode=post.creation_mode, topic=post.topic, source_text=post.source_text
        )
    except AIError:
        await status_msg.edit_text(AI_ERROR_TEXT + "\nПредыдущий вариант поста сохранён.")
        return

    post = await run_sync(repository.update_post_text, post_id, generated_text=text, final_text=text)
    await status_msg.delete()
    await render_post_preview(callback.message, post)


@router.callback_query(F.data.startswith("post:edit:"))
async def ask_edit_text(callback: CallbackQuery, state: FSMContext) -> None:
    post_id = _post_id(callback.data)
    await state.set_state(PostEditing.waiting_new_text)
    await state.update_data(post_id=post_id)
    await callback.answer()
    await callback.message.answer("Пришлите новый текст поста целиком.")


@router.message(PostEditing.waiting_new_text)
async def receive_new_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    post_id = data.get("post_id")
    await state.clear()
    post = await run_sync(repository.update_post_text, post_id, final_text=message.text)
    if post is not None:
        await render_post_preview(message, post)


@router.callback_query(F.data.startswith("post:image_add:"))
async def ask_image(callback: CallbackQuery, state: FSMContext) -> None:
    post_id = _post_id(callback.data)
    await state.set_state(PostEditing.waiting_image)
    await state.update_data(post_id=post_id)
    await callback.answer()
    await callback.message.answer("Пришлите фото или скриншот для этого поста.")


@router.message(PostEditing.waiting_image, F.photo)
async def receive_image(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    post_id = data.get("post_id")
    await state.clear()
    file_id = message.photo[-1].file_id
    post = await run_sync(repository.set_image, post_id, file_id)
    if post is not None:
        await render_post_preview(message, post)


@router.message(PostEditing.waiting_image)
async def image_wrong_type(message: Message) -> None:
    await message.answer("Пришлите изображение (фото или скриншот).")


@router.callback_query(F.data.startswith("post:image_remove:"))
async def remove_image(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    post = await run_sync(repository.remove_image, post_id)
    await callback.answer("Изображение удалено")
    if post is not None:
        await render_post_preview(callback.message, post)


@router.callback_query(F.data.startswith("post:save_draft:"))
async def save_draft(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    await run_sync(repository.set_status, post_id, "draft")
    await callback.answer("Сохранено в черновики")
    await callback.message.answer("💾 Пост сохранён в черновиках.")


@router.callback_query(F.data.startswith("post:delete:"))
async def ask_delete(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    await callback.answer()
    await callback.message.answer(
        "Удалить этот пост без возможности восстановления?",
        reply_markup=confirm_delete_keyboard(post_id),
    )


@router.callback_query(F.data.startswith("post:delete_confirm:"))
async def do_delete(callback: CallbackQuery) -> None:
    post_id = _post_id(callback.data)
    await run_sync(repository.delete_post, post_id)
    await callback.answer("Удалено")
    await callback.message.answer("🗑 Пост удалён.")
