from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import repository
from app.database.db import run_sync
from app.services.publishing import PublishError, publish_post

logger = logging.getLogger(__name__)


class PostScheduler:
    """Thin wrapper around APScheduler. SQLite (the `posts` table) is the
    source of truth for what is scheduled — jobs are (re)created from it on
    every startup, so a restart never loses a pending publication.
    """

    def __init__(self, bot: Bot):
        self._bot = bot
        self._tz = ZoneInfo(settings.app_timezone)
        self._scheduler = AsyncIOScheduler(timezone=self._tz)

    def start(self) -> None:
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    @staticmethod
    def _job_id(post_id: int) -> str:
        return f"post_{post_id}"

    def schedule_post(self, post_id: int, run_at: datetime) -> None:
        self._scheduler.add_job(
            self._run_publish,
            trigger="date",
            run_date=run_at,
            args=[post_id],
            id=self._job_id(post_id),
            replace_existing=True,
            misfire_grace_time=3600,
        )

    def cancel(self, post_id: int) -> None:
        job = self._scheduler.get_job(self._job_id(post_id))
        if job:
            job.remove()

    async def _run_publish(self, post_id: int) -> None:
        try:
            await publish_post(self._bot, post_id)
            logger.info("Запланированный пост %s опубликован по расписанию", post_id)
        except PublishError:
            logger.exception("Ошибка публикации запланированного поста %s", post_id)

    async def load_pending(self) -> None:
        """Reloads every 'scheduled' post from SQLite into APScheduler.
        Call this once on startup, after the scheduler has started.
        """
        posts = await run_sync(repository.list_scheduled)
        now = datetime.now(self._tz)
        for post in posts:
            if not post.scheduled_at:
                continue
            try:
                run_at = datetime.fromisoformat(post.scheduled_at)
            except ValueError:
                logger.warning("Некорректная дата scheduled_at у поста %s", post.id)
                continue
            if run_at <= now:
                # Публикация должна была случиться, пока бот был выключен.
                await self._run_publish(post.id)
            else:
                self.schedule_post(post.id, run_at)
        logger.info("Загружено запланированных публикаций: %s", len(posts))
