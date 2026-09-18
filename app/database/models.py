from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Post:
    id: int
    status: str
    creation_mode: str
    topic: str | None
    source_text: str | None
    generated_text: str | None
    final_text: str | None
    image_file_id: str | None
    created_at: str
    updated_at: str
    published_at: str | None
    scheduled_at: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Post":
        return cls(**{key: row[key] for key in row.keys()})

    @property
    def display_text(self) -> str:
        return self.final_text or self.generated_text or ""
