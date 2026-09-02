"""תזכורת יומית בלי לפתוח את חלון התוכנה."""
from __future__ import annotations


def fire_reminder() -> int:
    from core.nativeos import notify
    from core.profiles import ensure_migrated
    from core.storage import UserStorage

    ensure_migrated()
    storage = UserStorage()
    daily = storage.get_daily_goal() or {}
    if daily.get("is_done"):
        return 0
    student = storage.get_student() or {}
    name = student.get("name") or "תלמיד"
    left = max(0, int(daily.get("target", 15) or 15) - int(daily.get("completed", 0) or 0))
    notify("StudyApp", f"{name}, זמן לתרגול. נשארו עוד {left} שאלות להיום.")
    return 0


def maybe_nudge(storage) -> bool:
    """התראה חד־פעמית בהפעלת החלון, אם היעד היומי עוד לא הושלם."""
    from core.nativeos import notify
    from core.profiles import get_os_pref

    if not get_os_pref("daily_reminder", False):
        return False
    daily = storage.get_daily_goal() or {}
    if daily.get("is_done"):
        return False
    import time

    today = time.strftime("%Y-%m-%d")
    if storage.get_pref("reminder_nudged_on") == today:
        return False
    student = storage.get_student() or {}
    name = student.get("name") or "תלמיד"
    left = max(0, int(daily.get("target", 15) or 15) - int(daily.get("completed", 0) or 0))
    ok = notify("StudyApp", f"{name}, עוד לא סיימת את היעד היומי. נשארו {left} שאלות.")
    if ok:
        storage.set_pref("reminder_nudged_on", today)
    return ok
