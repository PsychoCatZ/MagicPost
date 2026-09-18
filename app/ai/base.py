from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class AIError(RuntimeError):
    """Raised whenever a provider fails to produce a usable result."""


@dataclass
class AIUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class AIResult:
    text: str
    usage: AIUsage | None = None


class AIProvider(ABC):
    """Common interface every AI backend must implement.

    Business logic (handlers, drafts, publishing, scheduler) only ever talks
    to this interface, never to a concrete SDK — that is what makes swapping
    OpenAI for Claude/DeepSeek/etc. a matter of adding one new class here.
    """

    name: str = "base"

    @abstractmethod
    async def generate_text(
        self, *, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> AIResult:
        """Produces text from a system + user prompt pair."""
        raise NotImplementedError
