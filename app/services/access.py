from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings

DENIED_TEXT = "Этот бот является внутренним инструментом управления каналом."


class OwnerOnlyMiddleware(BaseMiddleware):
    """Blocks every update from anyone other than OWNER_TELEGRAM_ID.

    All content-creation and publishing features are for the channel owner
    only — this is the single choke point that enforces it.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None or user.id != settings.owner_telegram_id:
            if isinstance(event, Message):
                await event.answer(DENIED_TEXT)
            elif isinstance(event, CallbackQuery):
                await event.answer(DENIED_TEXT, show_alert=True)
            return None
        return await handler(event, data)
