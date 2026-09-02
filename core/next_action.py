"""בחירת הפעולה הבאה בדשבורד, פעולה אחת ברורה."""
from __future__ import annotations

from core.config import subject_label


def pick_next_action(
    *,
    has_saved: bool,
    due_now: int,
    mistakes: int,
    weak_keys: list[str] | None = None,
    unpracticed_key: str | None = None,
    review_batch: int = 20,
) -> dict:
    """מחזיר id, title, detail, ו־subject אם רלוונטי."""
    weak_keys = list(weak_keys or [])
    _ = has_saved  # סשן פתוח לא תופס כרטיס בדשבורד
    if due_now > 0:
        n = min(int(due_now), review_batch)
        return {
            "id": "review",
            "title": f"להתחיל חזרה ({n} שאלות)",
            "detail": "שאלות שכבר פגשת, בדיוק כשהמוח מתחיל לשכוח.",
            "subject": None,
        }
    if mistakes > 0:
        return {
            "id": "mistakes",
            "title": f"תרגול טעויות ({mistakes})",
            "detail": "חוזרים רק למה שפספסת.",
            "subject": None,
        }
    if weak_keys:
        key = weak_keys[0]
        return {
            "id": "weak",
            "title": f"לחזק {subject_label(key)}",
            "detail": "המקצוע הכי חלש עכשיו. תרגול קצר שם מזיז הכי הרבה.",
            "subject": key,
        }
    if unpracticed_key:
        return {
            "id": "unpracticed",
            "title": f"להתחיל {subject_label(unpracticed_key)}",
            "detail": "עוד לא נגענו במקצוע הזה.",
            "subject": unpracticed_key,
        }
    return {
        "id": "subjects",
        "title": "למקצועות",
        "detail": "בחרו מקצוע והתחילו שיעור או תרגול.",
        "subject": None,
    }
