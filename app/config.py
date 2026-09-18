from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Не задана обязательная переменная окружения: {name}")
    return value


def _required_int(name: str) -> int:
    value = _required(name)
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"Переменная {name} должна быть целым числом, получено: {value!r}") from exc


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_telegram_id: int
    target_channel_id: int
    app_timezone: str
    database_path: str
    author_name: str
    ai_provider: str
    ai_model: str
    openai_api_key: str | None
    deepseek_api_key: str | None


def load_settings() -> Settings:
    return Settings(
        bot_token=_required("BOT_TOKEN"),
        owner_telegram_id=_required_int("OWNER_TELEGRAM_ID"),
        target_channel_id=_required_int("TARGET_CHANNEL_ID"),
        app_timezone=os.getenv("APP_TIMEZONE", "Asia/Krasnoyarsk"),
        database_path=os.getenv("DATABASE_PATH", "data/bot.db"),
        author_name=os.getenv("AUTHOR_NAME", "Анна"),
        ai_provider=os.getenv("AI_PROVIDER", "openai").strip().lower(),
        ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
    )


settings = load_settings()
