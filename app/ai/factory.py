from __future__ import annotations

from app.ai.base import AIError, AIProvider
from app.config import Settings


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


def get_provider(settings: Settings) -> AIProvider:
    """Builds the configured AIProvider. This is the ONLY place that needs
    to change when a new provider is added. DeepSeek and Qwen both speak the
    OpenAI chat-completions protocol, so they reuse OpenAICompatibleProvider
    with just a different base_url/key — no per-provider class needed.
    """
    from app.ai.openai_compatible_provider import OpenAICompatibleProvider

    provider_name = settings.ai_provider

    if provider_name == "openai":
        return OpenAICompatibleProvider(
            name="openai", api_key=settings.openai_api_key, model=settings.ai_model
        )

    if provider_name == "deepseek":
        return OpenAICompatibleProvider(
            name="deepseek",
            api_key=settings.deepseek_api_key,
            model=settings.ai_model,
            base_url=DEEPSEEK_BASE_URL,
        )

    if provider_name == "qwen":
        return OpenAICompatibleProvider(
            name="qwen",
            api_key=settings.qwen_api_key,
            model=settings.ai_model,
            base_url=QWEN_BASE_URL,
        )

    raise AIError(
        f"Неизвестный AI_PROVIDER: {provider_name!r}. Поддерживается: openai, deepseek, qwen."
    )
