from __future__ import annotations

import logging
import re

from app.ai.base import AIError, AIProvider
from app.ai.prompts import load_prompt
from app.config import Settings
from app.database import repository
from app.database.db import run_sync

logger = logging.getLogger(__name__)


class ContentService:
    """Turns raw provider text generation into the operations the bot needs
    (posts, ideas, content plan), using prompt templates from app/prompts/.

    This is the only layer that knows about prompts and content shape.
    Handlers never build prompts themselves and never call an AIProvider
    directly — that keeps provider swaps and prompt tuning independent of
    the Telegram-facing code.
    """

    def __init__(self, provider: AIProvider, settings: Settings):
        self._provider = provider
        self._settings = settings
        self._system_prompt = load_prompt("system").format(author=settings.author_name)

    async def _run(self, operation: str, template_name: str, **kwargs: str) -> str:
        template = load_prompt(template_name)
        user_prompt = template.format(**kwargs)
        try:
            result = await self._provider.generate_text(
                system_prompt=self._system_prompt, user_prompt=user_prompt
            )
        except AIError:
            logger.exception("AI-запрос не выполнен: operation=%s", operation)
            await run_sync(
                repository.log_ai_usage,
                provider=self._provider.name,
                model=self._settings.ai_model,
                operation=operation,
                success=False,
            )
            raise

        usage = result.usage
        await run_sync(
            repository.log_ai_usage,
            provider=self._provider.name,
            model=self._settings.ai_model,
            operation=operation,
            success=True,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
        )
        return result.text

    async def generate_post(self, topic: str) -> str:
        return await self._run("generate_post", "generate_post", topic=topic)

    async def generate_from_bullets(self, bullets: str) -> str:
        return await self._run("from_bullets", "from_bullets", bullets=bullets)

    async def rewrite_text(self, source_text: str) -> str:
        return await self._run("rewrite", "rewrite", source_text=source_text)

    async def generate_for_post(
        self, *, mode: str, topic: str | None, source_text: str | None
    ) -> str:
        """Dispatches to the right generator based on a post's creation_mode."""
        if mode == "topic":
            return await self.generate_post(topic or "")
        if mode == "bullets":
            return await self.generate_from_bullets(source_text or "")
        if mode == "rewrite":
            return await self.rewrite_text(source_text or "")
        return await self.generate_post(topic or source_text or "")

    async def suggest_ideas(self) -> list[str]:
        text = await self._run("ideas", "ideas")
        return self._parse_numbered_list(text)

    async def suggest_content_plan(self) -> list[tuple[str, str]]:
        text = await self._run("content_plan", "content_plan")
        return self._parse_plan(text)

    @staticmethod
    def _parse_numbered_list(text: str) -> list[str]:
        ideas = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^\d+[.)]\s*(.+)$", line)
            ideas.append(match.group(1).strip() if match else line.lstrip("-•— ").strip())
        return ideas

    @staticmethod
    def _parse_plan(text: str) -> list[tuple[str, str]]:
        plan = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "—" in line:
                day, topic = line.split("—", 1)
            elif " - " in line:
                day, topic = line.split(" - ", 1)
            else:
                continue
            plan.append((day.strip(), topic.strip()))
        return plan
