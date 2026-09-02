"""מושב מימ״ד מלא: שלושה פרקים, שעון לכל פרק, ציון לפי פרק.

זה לא המבחן הכללי של כל שמונת המקצועות, כאן רק עברית, אנגלית וחשבון,
כמו ישיבה אמיתית במאל״ו.
"""
from __future__ import annotations

import random
from typing import Any, Callable

from core.config import MEIMAD_SUBJECTS, subject_label

PER_SECTION = 10
SECTION_SECONDS = 12 * 60  # 12 דקות לפרק, ניהול זמן, לא רק ידע
SECTIONS: list[tuple[str, str, int, int]] = [
    ("hebrew", "עברית", PER_SECTION, SECTION_SECONDS),
    ("english", "אנגלית", PER_SECTION, SECTION_SECONDS),
    ("math", "חשבון", PER_SECTION, SECTION_SECONDS),
]


def _pick(pool: list[dict], count: int, rng: random.Random) -> list[dict]:
    if not pool:
        return []
    passages = [q for q in pool if q.get("kind") == "passage" or q.get("passage")]
    rest = [q for q in pool if q not in passages]
    picked: list[dict] = []

    # אם יש קטע קריאה, לוקחים בלוק שלם מאותו passage_id, עד 4 שאלות.
    by_id: dict[str, list[dict]] = {}
    for item in passages:
        by_id.setdefault(str(item.get("passage_id") or item.get("id")), []).append(item)
    groups = list(by_id.values())
    rng.shuffle(groups)
    for group in groups:
        if len(picked) >= count:
            break
        room = count - len(picked)
        if len(group) <= room:
            picked.extend(group)
        elif room >= 3:
            picked.extend(group[:room])

    leftover = [q for q in rest if q not in picked]
    rng.shuffle(leftover)
    for item in leftover:
        if len(picked) >= count:
            break
        picked.append(item)
    return picked[:count]


def build_meimad_exam(load_subject: Callable[[str], dict | None], seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    questions: list[dict] = []
    chapters: list[dict] = []
    cursor = 0
    for key, name, count, seconds in SECTIONS:
        data = load_subject(key) or {}
        pool = [q for q in (data.get("questions") or []) if q.get("kind") != "trick"]
        chunk = _pick(pool, count, rng)
        if len(chunk) < count:
            extra = [q for q in pool if q not in chunk]
            rng.shuffle(extra)
            chunk.extend(extra[: count - len(chunk)])
        for item in chunk:
            row = dict(item)
            row["section"] = key
            row["section_name"] = name
            questions.append(row)
        end = cursor + len(chunk)
        chapters.append(
            {
                "key": key,
                "name": name,
                "start": cursor,
                "end": end,
                "seconds": seconds,
            }
        )
        cursor = end
    return {
        "questions": questions,
        "chapters": chapters,
        "total_limit_sec": sum(ch["seconds"] for ch in chapters),
        "size": len(questions),
    }


def can_take_meimad(storage) -> bool:
    """אחרי אבחון, אפשר לשבת. בלי נעילה ארוכה: המבחן הזה הוא אימון, לא תעודה."""
    return bool(getattr(storage, "get_diagnostic", lambda: None)())


def section_names() -> list[str]:
    return [subject_label(key) for key in MEIMAD_SUBJECTS]
