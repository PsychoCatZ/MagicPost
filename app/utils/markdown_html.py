from __future__ import annotations

import html
import re

# Telegram HTML only understands a small, fixed set of tags. We never trust
# the AI (or a manually edited draft) to emit HTML directly — instead every
# post always goes through this converter, which:
#   1. escapes the raw text first, so any literal <, >, & (or an attempted
#      HTML/script injection) can never be parsed as markup;
#   2. only then re-introduces tags, and only for markdown syntax WE detect
#      and construct ourselves — never from unescaped user/AI input.
# This is the single place responsible for turning whatever the AI or the
# owner typed into a consistent Telegram parse_mode="HTML" string, for both
# the preview and the published message.

_CODE_BLOCK_RE = re.compile(r"```(?:[ \t]*\w+[ \t]*\n)?(.*?)```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_HEADING_RE = re.compile(r"^[ \t]*#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_STRIKE_RE = re.compile(r"~~(.+?)~~")
# Single-* / single-_ italics. Guarded so a bullet list marker like "* item"
# or "_" inside a word (snake_case) is never mistaken for emphasis.
_ITALIC_STAR_RE = re.compile(r"(?<![\*\w])\*(?!\*)(?!\s)(.+?)(?<!\s)\*(?!\*)")
_ITALIC_UNDERSCORE_RE = re.compile(r"(?<![_\w])_(?!_)(?!\s)(.+?)(?<!\s)_(?!_)")

_PLACEHOLDER = "\x00{}\x00"


def markdown_to_html(text: str) -> str:
    """Converts a small, safe subset of Markdown to Telegram HTML.

    Anything that isn't recognized markdown is treated as plain text and
    escaped, so raw '**', '###', backticks etc. never leak into what the
    user sees, and arbitrary HTML the AI/owner typed can never inject tags.
    """
    if not text:
        return ""

    placeholders: list[str] = []

    def _store(fragment: str) -> str:
        placeholders.append(fragment)
        return _PLACEHOLDER.format(len(placeholders) - 1)

    working = text

    # 1. Pull code out first and escape its content immediately — nothing
    # below is allowed to re-interpret markdown characters inside code.
    def _code_block(m: re.Match) -> str:
        code = m.group(1).strip("\n")
        return _store(f"<pre>{html.escape(code, quote=False)}</pre>")

    working = _CODE_BLOCK_RE.sub(_code_block, working)
    working = _INLINE_CODE_RE.sub(
        lambda m: _store(f"<code>{html.escape(m.group(1), quote=False)}</code>"),
        working,
    )

    # 2. Escape everything that's left. After this point no raw <, >, & can
    # possibly survive into the output as markup.
    working = html.escape(working, quote=False)

    # 3. Headings have no Telegram equivalent — fold them into bold text.
    working = _HEADING_RE.sub(lambda m: f"<b>{m.group(1)}</b>", working)

    # 4. Inline emphasis.
    working = _BOLD_RE.sub(lambda m: f"<b>{m.group(1) or m.group(2)}</b>", working)
    working = _STRIKE_RE.sub(lambda m: f"<s>{m.group(1)}</s>", working)
    working = _ITALIC_STAR_RE.sub(lambda m: f"<i>{m.group(1)}</i>", working)
    working = _ITALIC_UNDERSCORE_RE.sub(lambda m: f"<i>{m.group(1)}</i>", working)

    # 5. Restore code fragments (already safely escaped in step 1).
    for i, fragment in enumerate(placeholders):
        working = working.replace(_PLACEHOLDER.format(i), fragment)

    return working
