"""סכמת המחשה לימודית — נפרדת מהטקסט, ניתנת למחיקה."""
from __future__ import annotations

from typing import Any


VISUAL_KEY = "visual"


def make_visual(
    *,
    kind: str,
    title: str,
    caption: str,
    alt: str,
    accent: str = "",
    years: list[str] | None = None,
    labels: list[str] | None = None,
    reveal_note: str = "",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "title": title,
        "caption": caption,
        "alt": alt,
        "accent": accent,
        "years": list(years or []),
        "labels": list(labels or []),
        "reveal_note": reveal_note or caption,
        "subject": "history",
    }


def get_visual(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    visual = item.get(VISUAL_KEY)
    return visual if isinstance(visual, dict) and visual.get("kind") else None
