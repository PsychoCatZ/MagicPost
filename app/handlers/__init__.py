from aiogram import Dispatcher

from app.handlers import content_plan, drafts, generate, post_actions, scheduling, settings, start


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(generate.router)
    dp.include_router(post_actions.router)
    dp.include_router(drafts.router)
    dp.include_router(scheduling.router)
    dp.include_router(content_plan.router)
    dp.include_router(settings.router)
