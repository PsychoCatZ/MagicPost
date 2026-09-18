from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.database.db import get_connection
from app.database.models import Post


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_post(
    *, creation_mode: str, topic: Optional[str] = None, source_text: Optional[str] = None
) -> Post:
    now = _now()
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO posts (status, creation_mode, topic, source_text, created_at, updated_at)
               VALUES ('draft', ?, ?, ?, ?, ?)""",
            (creation_mode, topic, source_text, now, now),
        )
        conn.commit()
        post_id = cur.lastrowid
    finally:
        conn.close()
    return get_post(post_id)  # type: ignore[return-value]


def get_post(post_id: int) -> Optional[Post]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return Post.from_row(row) if row else None
    finally:
        conn.close()


def update_post_text(
    post_id: int, *, generated_text: Optional[str] = None, final_text: Optional[str] = None
) -> Optional[Post]:
    conn = get_connection()
    try:
        fields = []
        params: list = []
        if generated_text is not None:
            fields.append("generated_text = ?")
            params.append(generated_text)
        if final_text is not None:
            fields.append("final_text = ?")
            params.append(final_text)
        fields.append("updated_at = ?")
        params.append(_now())
        params.append(post_id)
        conn.execute(f"UPDATE posts SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    finally:
        conn.close()
    return get_post(post_id)


def set_image(post_id: int, file_id: str) -> Optional[Post]:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE posts SET image_file_id = ?, updated_at = ? WHERE id = ?",
            (file_id, _now(), post_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_post(post_id)


def remove_image(post_id: int) -> Optional[Post]:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE posts SET image_file_id = NULL, updated_at = ? WHERE id = ?",
            (_now(), post_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_post(post_id)


def set_status(post_id: int, status: str) -> Optional[Post]:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE posts SET status = ?, updated_at = ? WHERE id = ?", (status, _now(), post_id)
        )
        conn.commit()
    finally:
        conn.close()
    return get_post(post_id)


def set_scheduled(post_id: int, scheduled_at_iso: str) -> Optional[Post]:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE posts SET status = 'scheduled', scheduled_at = ?, updated_at = ? WHERE id = ?",
            (scheduled_at_iso, _now(), post_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_post(post_id)


def set_published(post_id: int, published_at_iso: str) -> Optional[Post]:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE posts SET status = 'published', published_at = ?, updated_at = ? WHERE id = ?",
            (published_at_iso, _now(), post_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_post(post_id)


def delete_post(post_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    finally:
        conn.close()


def list_drafts() -> list[Post]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = 'draft' ORDER BY updated_at DESC"
        ).fetchall()
        return [Post.from_row(r) for r in rows]
    finally:
        conn.close()


def list_scheduled() -> list[Post]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = 'scheduled' ORDER BY scheduled_at ASC"
        ).fetchall()
        return [Post.from_row(r) for r in rows]
    finally:
        conn.close()


def log_ai_usage(
    *,
    provider: str,
    model: str,
    operation: str,
    success: bool,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO ai_usage_log
               (provider, model, operation, success, prompt_tokens, completion_tokens, total_tokens, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                provider,
                model,
                operation,
                int(success),
                prompt_tokens,
                completion_tokens,
                total_tokens,
                _now(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
