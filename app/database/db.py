from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.config import settings

T = TypeVar("T")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL DEFAULT 'draft',
    creation_mode TEXT NOT NULL,
    topic TEXT,
    source_text TEXT,
    generated_text TEXT,
    final_text TEXT,
    image_file_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    published_at TEXT,
    scheduled_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS ai_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    operation TEXT NOT NULL,
    success INTEGER NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    created_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


async def run_sync(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Runs a blocking sqlite3 call off the event loop thread."""
    return await asyncio.to_thread(fn, *args, **kwargs)
