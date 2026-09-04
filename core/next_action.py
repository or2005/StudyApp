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
    goal: str | None = None,
    preferred_subject: str | None = None,
) -> dict:
    """מחזיר id, title, detail, cta, ו־subject אם רלוונטי."""
    weak_keys = list(weak_keys or [])
    _ = has_saved  # סשן פתוח לא תופס כרטיס בדשבורד
    if due_now > 0:
        n = min(int(due_now), review_batch)
        return {
            "id": "review",
            "title": f"יש {n} שאלות לחזרה",
            "detail": "חזרה קצרה על מה שכבר ראיתם.",
            "cta": "לחזרה",
            "subject": None,
        }
    if mistakes > 0:
        return {
            "id": "mistakes",
            "title": f"{mistakes} טעויות פתוחות",
            "detail": "רק מה שפספסת, בלי סיבוב ארוך.",
            "cta": "לתקן",
            "subject": None,
        }
    if weak_keys:
        key = weak_keys[0]
        name = subject_label(key)
        return {
            "id": "weak",
            "title": f"{name} קצת חלש עכשיו",
            "detail": "תרגול קצר שם מזיז יותר מהשאר.",
            "cta": f"לתרגל {name}",
            "subject": key,
        }
    if unpracticed_key:
        name = subject_label(unpracticed_key)
        return {
            "id": "unpracticed",
            "title": f"עוד לא נגענו ב{name}",
            "detail": "פתיחה רגועה, בלי לחץ של מבחן.",
            "cta": f"לפתוח {name}",
            "subject": unpracticed_key,
        }
    if goal == "meimad":
        return {
            "id": "meimad",
            "title": "היום: תרגול לקראת מימ״ד",
            "detail": "עברית, אנגלית וחשבון — קצב קצר לפני ישיבה מלאה.",
            "cta": "למימ״ד",
            "subject": None,
        }
    if goal == "general":
        key = preferred_subject or (weak_keys[0] if weak_keys else unpracticed_key)
        if key:
            name = subject_label(key)
            return {
                "id": "weak" if key in weak_keys else "unpracticed",
                "title": f"היום: חיזוק לקראת מבחן כללי — {name}",
                "detail": "עדיף מקצוע אחד היום, לא שלושה.",
                "cta": f"לתרגל {name}",
                "subject": key,
            }
        return {
            "id": "general_exam",
            "title": "היום: הכנה למבחן כללי",
            "detail": "בחרו מקצוע חלש למטה, או פתחו מבחן כללי כשמוכנים.",
            "cta": "למבחן הכללי",
            "subject": None,
        }
    return {
        "id": "subjects",
        "title": "מה בא לך היום?",
        "detail": "בחרו מקצוע למטה והמשיכו משם.",
        "cta": "למקצועות",
        "subject": None,
    }
