"""מושב מימ״ד בסגנון מאל״ו: שלושה פרקים ארוכים, שעון לכל פרק.

עברית מילולית, אנגלית והשלמות, וחשבון כמותי. לא 10–12 שאלות קצרות.
השאלות מקוריות, לא הועתקו משאלון רשמי.
"""
from __future__ import annotations

import random
from typing import Any, Callable

from core.adaptive_engine import normalize_difficulty, pick_by_mix
from core.config import MEIMAD_SUBJECTS, subject_label

# ישיבה קרובה למאל״ו: פרק מילולי, פרק אנגלית, פרק כמותי.
SECTIONS: list[tuple[str, str, int, int]] = [
    ("hebrew", "עברית, חשיבה מילולית", 20, 20 * 60),
    ("english", "אנגלית", 22, 20 * 60),
    ("math", "חשבון, חשיבה כמותית", 20, 20 * 60),
]
MEIMAD_MIX = {"Easy": 0.22, "Medium": 0.53, "Hard": 0.25}


def section_count(key: str) -> int:
    for item in SECTIONS:
        if item[0] == key:
            return item[2]
    return 20


def sitting_size() -> int:
    return sum(row[2] for row in SECTIONS)


def sitting_minutes() -> int:
    return sum(row[3] for row in SECTIONS) // 60


def describe_sitting() -> str:
    parts = [f"{name}: {count} שאלות, {seconds // 60} דקות" for _, name, count, seconds in SECTIONS]
    return " · ".join(parts)


def _score(question: dict, subject: str) -> float:
    tags = [str(item) for item in (question.get("tags") or [])]
    topic = str(question.get("topic") or "")
    blob = f"{topic} {' '.join(tags)} {question.get('category') or ''}"
    value = 0.0
    if question.get("kind") == "passage" or question.get("passage"):
        value += 45
    if question.get("level") in {"3units", "4units"}:
        value += 18
    if any(mark in blob.lower() for mark in ("meimad", "מימ", "bagrut", "בגרות")):
        value += 16
    if subject == "math" and any(
        word in topic for word in ("אחוז", "יחס", "ממוצע", "בעי", "סדרה", "פרופור", "דרך", "מימ")
    ):
        value += 12
    if subject == "hebrew" and any(
        word in topic for word in ("נרדפ", "הפך", "הבנת", "אנלוג", "השלמ", "מימ", "לשון בהקשר")
    ):
        value += 12
    if subject == "english" and any(
        word in topic.lower() for word in ("unseen", "perfect", "grammar", "meimad", "module", "restat")
    ):
        value += 12
    if normalize_difficulty(question.get("difficulty")) == "Easy" and "כתיב" in topic:
        value -= 8
    return value


def _pick(pool: list[dict], count: int, rng: random.Random, subject: str) -> list[dict]:
    if not pool or count <= 0:
        return []
    fresh = [q for q in pool if q.get("kind") != "trick"]
    picked: list[dict] = []

    passages = [q for q in fresh if q.get("kind") == "passage" or q.get("passage")]
    by_id: dict[str, list[dict]] = {}
    for item in passages:
        by_id.setdefault(str(item.get("passage_id") or item.get("id")), []).append(item)
    groups = list(by_id.values())
    rng.shuffle(groups)
    # פרק מילולי/אנגלית אמיתי כולל קטע קריאה עם כמה שאלות עליו.
    if subject in {"hebrew", "english"} and groups:
        group = max(groups, key=len)
        take = min(len(group), 5 if subject == "english" else 4, count)
        if take >= 3:
            picked.extend(group[:take])

    rest = [q for q in fresh if q not in picked]
    need = count - len(picked)
    if need > 0:
        more = pick_by_mix(
            rest,
            MEIMAD_MIX,
            need,
            rng=rng,
            scorer=lambda q: _score(q, subject) + rng.random() * 4,
        )
        picked.extend(more)
    if len(picked) < count:
        leftover = [q for q in rest if q not in picked]
        rng.shuffle(leftover)
        picked.extend(leftover[: count - len(picked)])
    return picked[:count]


def build_meimad_exam(load_subject: Callable[[str], dict | None], seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    questions: list[dict] = []
    chapters: list[dict] = []
    cursor = 0
    for key, name, count, seconds in SECTIONS:
        data = load_subject(key) or {}
        pool = [q for q in (data.get("questions") or []) if q.get("kind") != "trick"]
        chunk = _pick(pool, count, rng, key)
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
