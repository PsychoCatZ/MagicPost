from __future__ import annotations

from openai import AsyncOpenAI

from app.ai.base import AIError, AIProvider, AIResult, AIUsage


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str | None, model: str):
        if not api_key:
            raise AIError("OPENAI_API_KEY не задан в .env")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate_text(
        self, *, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> AIResult:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
        except Exception as exc:  # SDK raises several distinct error types
            raise AIError(f"Ошибка OpenAI API: {exc}") from exc

        choice = response.choices[0] if response.choices else None
        text = (choice.message.content or "").strip() if choice else ""
        if not text:
            raise AIError("OpenAI вернул пустой ответ")

        usage = None
        if response.usage:
            usage = AIUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return AIResult(text=text, usage=usage)
