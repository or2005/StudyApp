"""סוגי שאלות שקטים: אותה אמריקאית, משימה אחרת."""
from __future__ import annotations

from typing import Any

KICKERS = {
    "tutor": "מצאו את הטעות",
    "estimate": "העריכו, בלי לחשב הכול",
    "headline": "קראו את המקרה",
    "family": "אותו שורש, מילה אחרת",
}

EXHIBIT_LABELS = {
    "tutor": "מה שכתבו",
    "headline": "מקרה",
    "family": "משפחת המילים",
}


def kicker_for(question: dict[str, Any] | None) -> str:
    kind = str((question or {}).get("kind") or "")
    custom = str((question or {}).get("prompt_label") or "").strip()
    if custom:
        return custom
    return KICKERS.get(kind, "")


def exhibit_text(question: dict[str, Any] | None) -> str:
    q = question or {}
    return str(q.get("stem") or q.get("passage") or "").strip()


def exhibit_label(question: dict[str, Any] | None) -> str:
    q = question or {}
    custom = str(q.get("exhibit_label") or "").strip()
    if custom:
        return custom
    kind = str(q.get("kind") or "")
    if q.get("passage") and kind != "tutor":
        return EXHIBIT_LABELS.get(kind, "קטע קריאה")
    return EXHIBIT_LABELS.get(kind, "")
