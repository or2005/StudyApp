# -*- coding: utf-8 -*-
"""העדפות לומד אחרי הרשמה: מקצועות, רמה, תקנון, יעד — מקומי בלבד."""
from __future__ import annotations

from typing import Any

from core.config import ALL_SUBJECTS, HOME_SUBJECTS, subject_key

# מפתחות פנימיים ↔ עברית (5 רמות)
LEVEL_KEYS = ("starter", "easy", "intermediate", "advanced", "elite")
LEVEL_LABELS_HE = {
    "starter": "מתחיל",
    "easy": "קל",
    "intermediate": "בינוני",
    "advanced": "מתקדם",
    "elite": "רמה גבוהה",
}
# מיפוי רמות ישנות (3) → חדשות (5)
LEGACY_LEVEL = {
    "beginner": "starter",
    "starter": "starter",
    "easy": "easy",
    "intermediate": "intermediate",
    "advanced": "advanced",
    "elite": "elite",
    "מתחיל": "starter",
    "קל": "easy",
    "בינוני": "intermediate",
    "מתקדם": "advanced",
    "רמה גבוהה": "elite",
}

GOAL_KEYS = ("practice_only", "meimad", "general")
GOAL_LABELS_HE = {
    "practice_only": "תרגול יומי לפי מקצועות",
    "meimad": "הכנה למימ״ד",
    "general": "מבחן כללי",
}


def normalize_level(raw: Any) -> str:
    text = str(raw or "").strip()
    if text in LEVEL_KEYS:
        return text
    return LEGACY_LEVEL.get(text) or LEGACY_LEVEL.get(text.casefold()) or "starter"


def level_he(raw: Any) -> str:
    return LEVEL_LABELS_HE.get(normalize_level(raw), "מתחיל")


def selected_subjects(storage) -> list[str]:
    raw = []
    if hasattr(storage, "get_pref"):
        raw = storage.get_pref("selected_subjects") or []
    if not isinstance(raw, list) or not raw:
        return list(ALL_SUBJECTS)
    out = []
    seen = set()
    for item in raw:
        key = subject_key(str(item))
        if key in ALL_SUBJECTS and key not in seen:
            out.append(key)
            seen.add(key)
    return out or list(HOME_SUBJECTS)


def preferred_level(storage) -> str:
    if hasattr(storage, "get_pref"):
        return normalize_level(storage.get_pref("preferred_level") or "starter")
    return "starter"


def exam_goal(storage) -> str:
    if hasattr(storage, "get_pref"):
        goal = str(storage.get_pref("exam_goal") or "practice_only")
        if goal in GOAL_KEYS:
            return goal
    return "practice_only"


def onboarding_complete(storage) -> bool:
    if not hasattr(storage, "get_pref"):
        return bool(getattr(storage, "has_profile", lambda: False)())
    if storage.get_pref("onboarding_complete"):
        return True
    # פרופיל ישן עם אבחון נחשב הושלם
    if getattr(storage, "has_profile", lambda: False)() and getattr(storage, "get_diagnostic", lambda: None)():
        return True
    return False


def save_onboarding_choices(
    storage,
    *,
    subjects: list[str],
    level: str,
    goal: str = "practice_only",
    terms_accepted: bool = True,
) -> None:
    clean = []
    seen = set()
    for item in subjects or []:
        key = subject_key(str(item))
        if key in ALL_SUBJECTS and key not in seen:
            clean.append(key)
            seen.add(key)
    if not clean:
        clean = list(HOME_SUBJECTS)
    lvl = normalize_level(level)
    g = goal if goal in GOAL_KEYS else "practice_only"
    storage.set_pref("selected_subjects", clean)
    storage.set_pref("preferred_level", lvl)
    storage.set_pref("exam_goal", g)
    storage.set_pref("onboarding_complete", True)
    if terms_accepted:
        import time

        storage.set_pref("terms_accepted_at", time.strftime("%Y-%m-%d %H:%M"))


def apply_preferred_levels(storage, engine) -> None:
    """מאתחל רמת מקצוע לכל מקצוע שנבחר לפי בחירת המשתמש."""
    lvl = preferred_level(storage)
    for key in selected_subjects(storage):
        if hasattr(engine, "set_level"):
            engine.set_level(key, lvl)
        else:
            rec = engine.record_for(key)
            rec["level"] = lvl
            rec["answers_at_level"] = int(rec.get("answers_at_level") or 0)
            engine._save(key, rec)
