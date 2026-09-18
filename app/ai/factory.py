from __future__ import annotations

from app.ai.base import AIError, AIProvider
from app.config import Settings


def get_provider(settings: Settings) -> AIProvider:
    """Builds the configured AIProvider. This is the ONLY place that needs
    to change when a new provider (Claude, DeepSeek, Gemini, ...) is added.
    """
    provider_name = settings.ai_provider

    if provider_name == "openai":
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.ai_model)

    # Задел на будущее, например:
    # if provider_name == "deepseek":
    #     from app.ai.deepseek_provider import DeepSeekProvider
    #     return DeepSeekProvider(api_key=settings.deepseek_api_key, model=settings.ai_model)

    raise AIError(
        f"Неизвестный AI_PROVIDER: {provider_name!r}. Поддерживается: openai."
    )
