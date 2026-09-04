"""אנליסט רמה לפי מקצוע.

כל מקצוע מתחיל ברמת מתחילים (שאלות קלות, שיעורים בסיסיים, מבחן רגוע).
כשהתלמיד מצליח באופן יציב, הרמה עולה לבינוני ואז למתקדם, והחומר נהיה רציני יותר.
ירידה ברמה רק אם יש ממש קושי מתמשך, כדי לא לקפוץ הלוך־ושוב.
"""
from __future__ import annotations

import random
import re
import time
from typing import Any

from core.config import subject_key, subject_label

_LESSON_NUM_TITLE = re.compile(r"^\s*(\d+)\s*[\.\)]\s*")
_LESSON_NUM_ID = re.compile(r"(\d+)\s*$")
_DIFF_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}

LEVELS = ("starter", "easy", "intermediate", "advanced", "elite")
LEVEL_HE = {
    "starter": "מתחיל",
    "easy": "קל",
    "intermediate": "בינוני",
    "advanced": "מתקדם",
    "elite": "רמה גבוהה",
}
LEVEL_EMOJI = {
    "starter": "",
    "easy": "",
    "intermediate": "",
    "advanced": "",
    "elite": "",
}
DIFFICULTY_HE = {"Easy": "קל", "Medium": "בינוני", "Hard": "קשה"}

# פרופילים / אבחונים ישנים (3 רמות) → 5 רמות
_LEGACY_LEVEL = {
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

_DIFF_ALIASES = {
    "easy": "Easy",
    "קל": "Easy",
    "beginner": "Easy",
    "starter": "Easy",
    "בסיסי": "Easy",
    "1": "Easy",
    "medium": "Medium",
    "בינוני": "Medium",
    "intermediate": "Medium",
    "2": "Medium",
    "hard": "Hard",
    "קשה": "Hard",
    "advanced": "Hard",
    "elite": "Hard",
    "מתקדם": "Hard",
    "3": "Hard",
    "bagrut": "Hard",
    "בגרות": "Hard",
}

PRACTICE_MIX = {
    "starter": {"Easy": 0.92, "Medium": 0.08, "Hard": 0.0},
    "easy": {"Easy": 0.70, "Medium": 0.28, "Hard": 0.02},
    "intermediate": {"Easy": 0.18, "Medium": 0.64, "Hard": 0.18},
    "advanced": {"Easy": 0.08, "Medium": 0.32, "Hard": 0.60},
    "elite": {"Easy": 0.02, "Medium": 0.23, "Hard": 0.75},
}

EXAM_MIX = {
    "starter": {"Easy": 0.85, "Medium": 0.15, "Hard": 0.0},
    "easy": {"Easy": 0.60, "Medium": 0.35, "Hard": 0.05},
    "intermediate": {"Easy": 0.12, "Medium": 0.63, "Hard": 0.25},
    "advanced": {"Easy": 0.0, "Medium": 0.30, "Hard": 0.70},
    "elite": {"Easy": 0.0, "Medium": 0.18, "Hard": 0.82},
}

# כמה שאלות / כמה זמן לכל רמה. מבחן אמיתי נהיה ארוך ורציני יותר.
SESSION_SHAPE = {
    "starter": {
        "practice": 12,
        "guided": 5,
        "compose": 8,
        "mock": 10,
        "timed": 10,
        "final": 16,
        "seconds": 100,
        "mock_timed": False,
    },
    "easy": {
        "practice": 14,
        "guided": 6,
        "compose": 10,
        "mock": 12,
        "timed": 12,
        "final": 20,
        "seconds": 90,
        "mock_timed": False,
    },
    "intermediate": {
        "practice": 16,
        "guided": 6,
        "compose": 12,
        "mock": 15,
        "timed": 15,
        "final": 30,
        "seconds": 75,
        "mock_timed": False,
    },
    "advanced": {
        "practice": 18,
        "guided": 8,
        "compose": 14,
        "mock": 20,
        "timed": 20,
        "final": 35,
        "seconds": 55,
        "mock_timed": True,
    },
    "elite": {
        "practice": 20,
        "guided": 8,
        "compose": 16,
        "mock": 22,
        "timed": 22,
        "final": 40,
        "seconds": 50,
        "mock_timed": True,
    },
}

PROMOTE = {
    "starter": {"window": 7, "accuracy": 0.78, "min_at_level": 7},
    "easy": {"window": 8, "accuracy": 0.80, "min_at_level": 8},
    "intermediate": {"window": 10, "accuracy": 0.78, "min_at_level": 10},
    "advanced": {"window": 12, "accuracy": 0.80, "min_at_level": 12},
}
DEMOTE = {
    "easy": {"window": 7, "accuracy": 0.40, "min_at_level": 7},
    "intermediate": {"window": 8, "accuracy": 0.42, "min_at_level": 8},
    "advanced": {"window": 8, "accuracy": 0.48, "min_at_level": 8},
    "elite": {"window": 10, "accuracy": 0.50, "min_at_level": 10},
}

RECENT_KEEP = 60
RETENTION_HALF_LIFE_H = 72.0
BAGRUT_MARKERS = ("בגרות", "מימ״ד", "מימד", "מימ\"ד")


def normalize_difficulty(raw: Any) -> str:
    text = str(raw or "Easy").strip()
    if text in {"Easy", "Medium", "Hard"}:
        return text
    return _DIFF_ALIASES.get(text.lower(), _DIFF_ALIASES.get(text, "Easy"))


def lesson_sort_key(lesson: dict) -> tuple:
    """מספר שיעור מהכותרת (1. נושא) או מהמזהה — לסדר בסיס → בינוני → קשה."""
    title = str(lesson.get("title") or "")
    match = _LESSON_NUM_TITLE.match(title)
    if match:
        return (0, int(match.group(1)), title)
    match = _LESSON_NUM_ID.search(str(lesson.get("id") or ""))
    if match:
        return (1, int(match.group(1)), title)
    return (2, 10**9, title)


def sort_lessons(lessons: list[dict]) -> list[dict]:
    return sorted(lessons, key=lesson_sort_key)


def sort_questions_progressive(questions: list[dict]) -> list[dict]:
    """קל → בינוני → קשה, כדי שהתרגול יתחיל מבסיס ויתקדם."""
    return sorted(
        questions,
        key=lambda q: (
            _DIFF_ORDER.get(normalize_difficulty(q.get("difficulty")), 0),
            str(q.get("topic") or ""),
            str(q.get("id") or ""),
        ),
    )


def normalize_level(level: str | None) -> str:
    raw = str(level or "").strip()
    mapped = _LEGACY_LEVEL.get(raw) or _LEGACY_LEVEL.get(raw.casefold())
    if mapped in LEVELS:
        return mapped
    return "starter"


def next_level(level: str) -> str | None:
    lvl = normalize_level(level)
    try:
        i = LEVELS.index(lvl)
    except ValueError:
        return "easy"
    return LEVELS[i + 1] if i + 1 < len(LEVELS) else None


def prev_level(level: str) -> str | None:
    lvl = normalize_level(level)
    try:
        i = LEVELS.index(lvl)
    except ValueError:
        return None
    return LEVELS[i - 1] if i > 0 else None


def level_he(level: str) -> str:
    return LEVEL_HE.get(normalize_level(level), "מתחיל")


def mix_for(level: str, exam: bool = False) -> dict[str, float]:
    table = EXAM_MIX if exam else PRACTICE_MIX
    lvl = normalize_level(level)
    return dict(table.get(lvl) or table["starter"])


DIFF_WEIGHT = {"Easy": 0.75, "Medium": 1.0, "Hard": 1.35}
RUSH_SEC = 2.8


def _accuracy(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get("correct")) / len(rows)


def wilson_lower(successes: int, n: int, z: float = 1.2816) -> float:
    """גבול תחתון של Wilson — כמה באמת אפשר לסמוך על אחוז מדגם קטן."""
    if n <= 0:
        return 0.0
    p = max(0.0, min(1.0, successes / n))
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p + z2 / (2.0 * n)
    inner = p * (1.0 - p) / n + z2 / (4.0 * n * n)
    margin = z * (inner ** 0.5)
    return max(0.0, (centre - margin) / denom)


def weighted_accuracy(rows: list[dict], half_life: float = 12.0) -> float:
    """דיוק עם דעיכת זמן ומשקל קושי: הצלחה קשה שווה יותר מהצלחה קלה."""
    if not rows:
        return 0.0
    num = den = 0.0
    n = len(rows)
    span = max(float(half_life), 1.0)
    for i, row in enumerate(rows):
        recency = 0.5 ** ((n - 1 - i) / span)
        weight = recency * DIFF_WEIGHT.get(normalize_difficulty(row.get("difficulty")), 1.0)
        den += weight
        if row.get("correct"):
            num += weight
    return num / den if den else 0.0


def _stable_tail(rows: list[dict], need: int = 2) -> bool:
    """לא מעלים רמה אחרי קריסה בסוף החלון, גם אם הממוצע עדיין גבוה."""
    tail = rows[-3:] if len(rows) >= 3 else rows
    if not tail:
        return False
    return sum(1 for row in tail if row.get("correct")) >= min(need, len(tail))


def _mostly_guessing(rows: list[dict]) -> bool:
    times = [float(row["time_sec"]) for row in rows if row.get("time_sec") is not None]
    if len(times) < 5:
        return False
    rushed = sum(1 for item in times if item < RUSH_SEC)
    return (rushed / len(times) >= 0.6) and _accuracy(rows) < 0.92


def _showed_depth(rows: list[dict]) -> bool:
    return sum(
        1
        for row in rows
        if row.get("correct") and normalize_difficulty(row.get("difficulty")) in {"Medium", "Hard"}
    ) >= 2


def _round_targets(mix: dict[str, float], count: int) -> dict[str, int]:
    raw = {key: mix.get(key, 0.0) * count for key in ("Easy", "Medium", "Hard")}
    targets = {key: int(value) for key, value in raw.items()}
    remainder = count - sum(targets.values())
    if remainder:
        order = sorted(raw, key=lambda key: raw[key] - targets[key], reverse=remainder > 0)
        step = 1 if remainder > 0 else -1
        for key in order:
            if remainder == 0:
                break
            nxt = targets[key] + step
            if nxt < 0:
                continue
            targets[key] = nxt
            remainder -= step
    return targets


def pick_by_mix(
    pool: list[dict],
    mix: dict[str, float],
    count: int,
    rng: random.Random | None = None,
    scorer=None,
    avoid_ids=None,
) -> list[dict]:
    """בוחר שאלות לפי תמהיל קושי. כל סשן מערבב מחדש ונמנע משאלות שזה עתה הופיעו."""
    if not pool or count <= 0:
        return []
    count = min(int(count), len(pool))
    roller = rng or random.Random()
    avoid = {str(item) for item in (avoid_ids or []) if item}
    buckets: dict[str, list[dict]] = {"Easy": [], "Medium": [], "Hard": []}
    for question in pool:
        buckets[normalize_difficulty(question.get("difficulty"))].append(question)

    def order_bucket(items: list[dict]) -> list[dict]:
        items = list(items)
        roller.shuffle(items)
        if avoid:
            fresh = [q for q in items if str(q.get("id") or "") not in avoid]
            used = [q for q in items if str(q.get("id") or "") in avoid]
            roller.shuffle(fresh)
            roller.shuffle(used)
            items = fresh + used
        if scorer:
            items.sort(
                key=lambda q: (
                    0 if str(q.get("id") or "") in avoid else 1,
                    scorer(q) + roller.random() * 18,
                ),
                reverse=True,
            )
        return items

    buckets = {key: order_bucket(value) for key, value in buckets.items()}
    targets = _round_targets(mix, count)
    picked: list[dict] = []
    leftover: list[dict] = []
    neighbor = {"Easy": ("Medium", "Hard"), "Medium": ("Easy", "Hard"), "Hard": ("Medium", "Easy")}

    for diff in ("Easy", "Medium", "Hard"):
        take = min(targets[diff], len(buckets[diff]))
        picked.extend(buckets[diff][:take])
        leftover.extend(buckets[diff][take:])

    if len(picked) < count:
        # מילוי מכוון: קודם השכן הקרוב למה שחסר
        missing = []
        for diff in ("Easy", "Medium", "Hard"):
            have = sum(1 for q in picked if normalize_difficulty(q.get("difficulty")) == diff)
            gap = max(0, targets[diff] - have)
            missing.extend([diff] * gap)
        for diff in missing:
            if len(picked) >= count:
                break
            for alt in neighbor[diff]:
                found = next(
                    (q for q in leftover if normalize_difficulty(q.get("difficulty")) == alt),
                    None,
                )
                if found:
                    leftover.remove(found)
                    picked.append(found)
                    break

    while len(picked) < count and leftover:
        picked.append(leftover.pop(0))

    return sort_questions_progressive(picked[:count])


def infer_lesson_difficulty(lesson: dict, topic_diff: dict[str, str] | None = None) -> str:
    category = str(lesson.get("category") or "")
    title = str(lesson.get("title") or "")
    blob = f"{category} {title}"
    if any(marker in blob for marker in BAGRUT_MARKERS) or "מתקדם" in blob:
        return "Hard"
    if "בינוני" in blob:
        return "Medium"
    if "מתחיל" in blob or "בסיסי" in blob:
        return "Easy"
    topic = lesson.get("topic") or ""
    if topic_diff and topic in topic_diff:
        return topic_diff[topic]
    return "Easy"


def topic_difficulty_map(questions: list[dict] | None) -> dict[str, str]:
    scores = {"Easy": 1, "Medium": 2, "Hard": 3}
    buckets: dict[str, list[int]] = {}
    for question in questions or []:
        topic = question.get("topic") or ""
        if not topic:
            continue
        buckets.setdefault(topic, []).append(scores[normalize_difficulty(question.get("difficulty"))])
    result = {}
    for topic, values in buckets.items():
        avg = sum(values) / len(values)
        if avg >= 2.4:
            result[topic] = "Hard"
        elif avg >= 1.6:
            result[topic] = "Medium"
        else:
            result[topic] = "Easy"
    return result


def filter_lessons(
    lessons: list[dict],
    level: str,
    questions: list[dict] | None = None,
) -> list[dict]:
    """מתחילים רואים שיעורים בסיסיים; מתקדמים מקבלים גם מימ״ד/בגרות."""
    if not lessons:
        return []
    lvl = normalize_level(level)
    allowed = {
        "starter": {"Easy"},
        "easy": {"Easy", "Medium"},
        "intermediate": {"Easy", "Medium"},
        "advanced": {"Easy", "Medium", "Hard"},
        "elite": {"Easy", "Medium", "Hard"},
    }.get(lvl, {"Easy"})
    topic_diff = topic_difficulty_map(questions)
    ranked = []
    for lesson in lessons:
        diff = infer_lesson_difficulty(lesson, topic_diff)
        ranked.append((lesson, diff))
    filtered = [lesson for lesson, diff in ranked if diff in allowed]
    if not filtered:
        if lvl in {"starter", "easy"}:
            filtered = [lesson for lesson, diff in ranked if diff in {"Easy", "Medium"}]
        if not filtered:
            return sort_lessons(list(lessons))
    return sort_lessons(filtered)


def session_params(level: str, mode: str) -> dict[str, Any]:
    lvl = normalize_level(level)
    shape = SESSION_SHAPE.get(lvl) or SESSION_SHAPE["starter"]
    mode_key = mode if mode in shape else "practice"
    count = int(shape.get(mode_key, shape["practice"]))
    per_q = int(shape["seconds"])
    exam = mode in {"mock", "final", "timed"}
    timed = mode in {"final", "timed"} or (mode == "mock" and bool(shape.get("mock_timed")))
    return {
        "level": lvl,
        "count": count,
        "seconds": per_q if timed else None,
        "total_limit_sec": (per_q * count) if mode == "final" else None,
        "exam": exam,
        "mix": mix_for(lvl, exam=exam),
        "label": LEVEL_HE.get(lvl, "מתחיל"),
    }


class AdaptiveEngine:
    """אנליסט מקומי: רמה נפרדת לכל מקצוע, בלי API חיצוני."""

    def __init__(self, storage: Any):
        self.storage = storage

    # ---------- אחסון ----------
    def _all(self) -> dict:
        data = self.storage.get("subject_levels") if hasattr(self.storage, "get") else None
        return dict(data) if isinstance(data, dict) else {}

    def _save(self, subject: str, record: dict) -> None:
        data = self._all()
        data[subject] = record
        self.storage.set("subject_levels", data)

    def _bootstrap_level(self, subject: str) -> str:
        progress = {}
        if hasattr(self.storage, "get_progress"):
            progress = (self.storage.get_progress() or {}).get(subject) or {}
        total = int(progress.get("total", 0) or 0)
        correct = int(progress.get("correct", 0) or 0)
        acc = (correct / total) if total else 0.0
        if total >= 28 and acc >= 0.88:
            return "elite"
        if total >= 18 and acc >= 0.80:
            return "advanced"
        if total >= 12 and acc >= 0.75:
            return "intermediate"
        if total >= 6 and acc >= 0.70:
            return "easy"
        return "starter"

    def _fresh_record(self, subject: str) -> dict:
        return {
            "level": self._bootstrap_level(subject),
            "recent": [],
            "answers_at_level": 0,
            "changed_at": None,
            "history": [],
            "pending_event": None,
        }

    def record_for(self, subject: str) -> dict:
        key = subject_key(subject)
        data = self._all()
        rec = data.get(key)
        if not isinstance(rec, dict):
            rec = self._fresh_record(key)
            self._save(key, rec)
            return rec
        raw_level = rec.get("level")
        lvl = normalize_level(raw_level)
        if raw_level != lvl:
            rec = dict(rec)
            rec["level"] = lvl
            self._save(key, rec)
        return rec

    def level_of(self, subject: str) -> str:
        return normalize_level(self.record_for(subject).get("level"))

    def set_level(self, subject: str, level: str) -> None:
        key = subject_key(subject)
        rec = self.record_for(key)
        rec["level"] = normalize_level(level)
        rec["answers_at_level"] = 0
        rec["changed_at"] = time.strftime("%Y-%m-%d %H:%M")
        self._save(key, rec)

    def consume_event(self, subject: str) -> dict | None:
        rec = self.record_for(subject)
        event = rec.get("pending_event")
        if event:
            rec["pending_event"] = None
            self._save(subject_key(subject), rec)
        return event

    # ---------- עדכון אחרי תשובה ----------
    def observe(
        self,
        subject: str,
        is_correct: bool,
        difficulty: Any = "Easy",
        topic: str | None = None,
        time_sec: float | None = None,
    ) -> dict | None:
        key = subject_key(subject)
        rec = self.record_for(key)
        entry: dict[str, Any] = {
            "correct": bool(is_correct),
            "difficulty": normalize_difficulty(difficulty),
            "ts": time.strftime("%Y-%m-%d %H:%M"),
        }
        if topic:
            entry["topic"] = str(topic)
        if time_sec is not None:
            try:
                entry["time_sec"] = round(float(time_sec), 2)
            except (TypeError, ValueError):
                pass
        rec.setdefault("recent", []).append(entry)
        rec["recent"] = rec["recent"][-RECENT_KEEP:]
        rec["answers_at_level"] = int(rec.get("answers_at_level", 0) or 0) + 1
        event = self._maybe_adjust(key, rec)
        self._save(key, rec)
        return event

    def observe_session(self, subject: str, answers: list[dict]) -> dict | None:
        """מעבד סשן שלם ומחזיר את אירוע שינוי הרמה האחרון (אם היה)."""
        last = None
        for item in answers or []:
            event = self.observe(
                subject,
                bool(item.get("correct")),
                item.get("difficulty") or "Easy",
                topic=item.get("topic"),
                time_sec=item.get("time_sec"),
            )
            if event:
                last = event
        return last

    def _maybe_adjust(self, subject: str, rec: dict) -> dict | None:
        level = normalize_level(rec.get("level"))
        at_level = int(rec.get("answers_at_level", 0) or 0)
        recent = rec.get("recent") or []

        promo = PROMOTE.get(level)
        if promo and at_level >= promo["min_at_level"]:
            window = recent[-promo["window"] :]
            if self._should_promote(level, window, promo):
                nxt = next_level(level)
                if nxt:
                    return self._apply_change(subject, rec, nxt, "promote")

        demo = DEMOTE.get(level)
        if demo and at_level >= demo["min_at_level"]:
            window = recent[-demo["window"] :]
            if self._should_demote(window, demo):
                nxt = prev_level(level)
                if nxt:
                    return self._apply_change(subject, rec, nxt, "demote")
        return None

    def _should_promote(self, level: str, window: list[dict], promo: dict) -> bool:
        if len(window) < promo["window"]:
            return False
        if _accuracy(window) < promo["accuracy"]:
            return False
        if weighted_accuracy(window) < promo["accuracy"] - 0.04:
            return False
        if not _stable_tail(window):
            return False
        if _mostly_guessing(window):
            return False
        # מעבר למתקדם/רמה גבוהה דורש גם הצלחה בחומר שאינו קל.
        if level in {"intermediate", "advanced"} and not _showed_depth(window):
            return False
        return True

    def _should_demote(self, window: list[dict], demo: dict) -> bool:
        if len(window) < demo["window"]:
            return False
        if _accuracy(window) >= demo["accuracy"]:
            return False
        # ירידה רק בקושי מתמשך, לא אחרי שלוש נכונות שמראות התאוששות.
        if len(window) >= 3 and all(row.get("correct") for row in window[-3:]):
            return False
        return True

    def _apply_change(self, subject: str, rec: dict, new_level: str, kind: str) -> dict:
        old = normalize_level(rec.get("level"))
        new_level = normalize_level(new_level)
        rec["level"] = new_level
        rec["answers_at_level"] = 0
        rec["changed_at"] = time.strftime("%Y-%m-%d %H:%M")
        rec.setdefault("history", []).append(
            {"from": old, "to": new_level, "kind": kind, "date": rec["changed_at"]}
        )
        rec["history"] = rec["history"][-12:]
        name = subject_label(subject)
        if kind == "promote":
            title = f"עלית לרמה {LEVEL_HE[new_level]} ב{name}"
            blurbs = {
                "easy": f"הבסיס ב{name} יושב. מעכשיו קצת יותר מאתגר, עדיין בקצב נוח.",
                "intermediate": (
                    f"נראה ש{name} בבסיס כבר יושב. "
                    "מעכשיו התרגול, השיעורים והמבחנים יהיו ברמה בינונית, יותר רציניים."
                ),
                "advanced": (
                    f"מצוין. {name} עבר לרמת מתקדם. "
                    "השאלות קשות יותר, השיעורים כוללים מימ״ד/בגרות, והמבחן עם שעון צמוד."
                ),
                "elite": (
                    f"{name} ברמה גבוהה. חומר בגרות מלא, מבחנים ארוכים, וציפייה לדיוק גבוה."
                ),
            }
            message = blurbs.get(new_level, f"הרמה ב{name} עלתה ל{LEVEL_HE[new_level]}.")
        else:
            title = f"חזרה לרמה {LEVEL_HE[new_level]} ב{name}"
            message = (
                f"הדיוק ירד ב{name}, אז חוזרים קצת אחורה. "
                "נתרגל שוב מהרמה הזו עד שהחומר יתייצב."
            )
        event = {
            "kind": kind,
            "subject": subject,
            "from": old,
            "to": new_level,
            "from_he": LEVEL_HE.get(old, old),
            "to_he": LEVEL_HE.get(new_level, new_level),
            "title": title,
            "message": message,
        }
        rec["pending_event"] = event
        return event

    # ---------- בחירת תוכן ----------
    def select_questions(
        self,
        pool: list[dict],
        subject: str,
        count: int | None = None,
        mode: str = "practice",
        srs=None,
        prefer_topic: str | None = None,
        prefer_topics: list[str] | None = None,
        topic_only: bool = False,
    ) -> tuple[list[dict], dict[str, Any]]:
        level = self.level_of(subject)
        params = session_params(level, mode)
        want = int(count if count is not None else params["count"])
        want = min(max(1, want), len(pool) or 1)
        scorer = self._content_scorer(subject, srs)
        avoid = []
        if hasattr(self.storage, "recent_question_ids"):
            avoid = self.storage.recent_question_ids(subject)
        wanted: list[str] = []
        explicit_topics = bool(prefer_topic) or bool(prefer_topics)
        if prefer_topic:
            wanted.append(str(prefer_topic))
        for topic in prefer_topics or []:
            name = str(topic or "").strip()
            if name and name not in wanted:
                wanted.append(name)
        # תרגול רגיל בלי נושא ידני: האנליסט דוחף לנושאים החלשים
        if not wanted and mode in {"practice", "smart_practice", "compose"}:
            for topic in self.weak_topics(subject, limit=3):
                if topic not in wanted:
                    wanted.append(topic)
        if wanted:
            allowed = set(wanted)
            primary = [q for q in pool if q.get("topic") in allowed]
            secondary = [q for q in pool if q.get("topic") not in allowed]
            # נושא בלבד: לא לחרוג ממספר השאלות הזמינות בנושא
            if topic_only and primary:
                want = min(want, len(primary))
            # נושא שנבחר במפורש / topic_only: כל השאלות מהנושא.
            # דחיפה אוטומטית לנושא חלש: רוב השאלות משם, לא הכל.
            if explicit_topics or topic_only:
                first_n = min(want, len(primary)) if primary else 0
            else:
                struggle = self.struggling(subject)
                share = 0.90 if struggle else 0.72
                first_n = min(want, max(1, int(want * share)), len(primary)) if primary else 0
            picked = pick_by_mix(primary, params["mix"], first_n, scorer=scorer, avoid_ids=avoid) if primary else []
            need = want - len(picked)
            if need > 0 and secondary and not topic_only:
                picked = picked + pick_by_mix(secondary, params["mix"], need, scorer=scorer, avoid_ids=avoid)
        else:
            picked = pick_by_mix(pool, params["mix"], want, scorer=scorer, avoid_ids=avoid)
        if hasattr(self.storage, "remember_session_ids"):
            self.storage.remember_session_ids(subject, [q.get("id") for q in picked])
        params["count"] = len(picked)
        return picked, params

    def lessons_for(self, subject: str, lessons: list[dict], questions: list[dict] | None = None) -> list[dict]:
        return filter_lessons(lessons, self.level_of(subject), questions)

    def weak_topics(self, subject: str, limit: int = 3) -> list[str]:
        """נושאים עם דיוק נמוך אמיתי (Wilson + דעיכה) — לחיזוק ממוקד."""
        scored = self.topic_scores(subject)
        weak = [row for row in scored if row.get("weak")]
        return [row["topic"] for row in weak[:limit]]

    def topic_scores(self, subject: str) -> list[dict[str, Any]]:
        """דירוג נושאים עם ביטחון סטטיסטי, דעיכת זמן, וקושי."""
        rec = self.record_for(subject)
        buckets: dict[str, list[dict]] = {}
        now = time.time()
        for row in rec.get("recent") or []:
            topic = str(row.get("topic") or "").strip()
            if not topic:
                continue
            buckets.setdefault(topic, []).append(row)
        ranked: list[dict[str, Any]] = []
        for topic, rows in buckets.items():
            if len(rows) < 2:
                continue
            correct = sum(1 for row in rows if row.get("correct"))
            total = len(rows)
            raw_acc = correct / total
            conf = wilson_lower(correct, total)
            # דעיכה: טעויות אחרונות שוקלות יותר
            w_acc = weighted_accuracy(
                [
                    {
                        "correct": row.get("correct"),
                        "difficulty": row.get("difficulty") or "Easy",
                    }
                    for row in rows
                ],
                half_life=max(4.0, total / 2),
            )
            rush = 0
            timed = 0
            for row in rows:
                if row.get("time_sec") is None:
                    continue
                timed += 1
                try:
                    if float(row["time_sec"]) < RUSH_SEC and not row.get("correct"):
                        rush += 1
                except (TypeError, ValueError):
                    pass
            # שמירה: נושא שלא נגע בו הרבה זמן יורד בציון
            last_ts = None
            for row in reversed(rows):
                stamp = str(row.get("ts") or "")
                if stamp:
                    try:
                        last_ts = time.mktime(time.strptime(stamp, "%Y-%m-%d %H:%M"))
                        break
                    except ValueError:
                        continue
            retention = 1.0
            if last_ts:
                age_h = max(0.0, (now - last_ts) / 3600.0)
                retention = 0.5 ** (age_h / RETENTION_HALF_LIFE_H)
            strength = (0.45 * conf + 0.40 * w_acc + 0.15 * raw_acc) * (0.7 + 0.3 * retention)
            threshold = 0.58 if total >= 4 else 0.50
            weak = strength <= threshold or (raw_acc <= 0.45 and total >= 3)
            ranked.append(
                {
                    "topic": topic,
                    "total": total,
                    "correct": correct,
                    "accuracy": round(raw_acc * 100, 1),
                    "confidence": round(conf * 100, 1),
                    "strength": round(strength, 3),
                    "rush_misses": rush,
                    "weak": weak,
                }
            )
        ranked.sort(key=lambda item: (item["strength"], item["total"]))
        return ranked

    def mistake_patterns(self, subject: str) -> list[dict[str, Any]]:
        """דפוסי טעות: ניחוש מהיר, קושי גבוה, רצף טעויות."""
        recent = list(self.record_for(subject).get("recent") or [])
        if len(recent) < 4:
            return []
        patterns: list[dict[str, Any]] = []
        times = [
            float(row["time_sec"])
            for row in recent
            if row.get("time_sec") is not None and not row.get("correct")
        ]
        if len(times) >= 3 and sum(1 for t in times if t < RUSH_SEC) / len(times) >= 0.5:
            patterns.append(
                {
                    "kind": "rush",
                    "title": "ניחושים מהירים",
                    "message": "הרבה טעויות אחרי מענה קצר מ־3 שניות. לקרוא עד הסוף לפני בחירה.",
                }
            )
        hard_miss = [
            row
            for row in recent
            if not row.get("correct") and normalize_difficulty(row.get("difficulty")) == "Hard"
        ]
        if len(hard_miss) >= 3:
            patterns.append(
                {
                    "kind": "hard",
                    "title": "קושי בשאלות קשות",
                    "message": "נופלים בשאלות ברמה גבוהה. לחזק קודם בינוני יציב, ואז לחזור לקשות.",
                }
            )
        streak = 0
        best = 0
        for row in recent:
            if row.get("correct"):
                streak = 0
            else:
                streak += 1
                best = max(best, streak)
        if best >= 4:
            patterns.append(
                {
                    "kind": "streak",
                    "title": "רצף טעויות",
                    "message": f"היה רצף של {best} טעויות. עדיף סשן קצר עם הסבר אחרי כל תשובה.",
                }
            )
        return patterns

    def exam_readiness(self, subject: str) -> dict[str, Any]:
        """תחזית מוכנות למבחן (ציון 0..1 + ייעוץ). בלי לקרוא ל-snapshot."""
        rec = self.record_for(subject)
        level = normalize_level(rec.get("level"))
        promo = PROMOTE.get(level)
        recent = list(rec.get("recent") or [])
        window = promo["window"] if promo else 8
        slice_ = recent[-window:]
        total = len(slice_)
        acc = (sum(1 for row in slice_ if row.get("correct")) / total) if total else 0.0
        weak = self.weak_topics(subject)
        at_level = int(rec.get("answers_at_level") or 0)
        patterns = self.mistake_patterns(subject)
        struggle = self._struggle_from_parts(subject, total, acc * 100, weak, patterns)
        score = 0.0
        if total >= 4:
            score += 0.35 * acc
        level_bonus = {
            "easy": 0.08,
            "intermediate": 0.16,
            "advanced": 0.24,
            "elite": 0.30,
        }.get(level, 0.0)
        score += level_bonus
        score += min(0.18, at_level / 40.0)
        score -= 0.08 * min(3, len(weak))
        score -= 0.06 * len(patterns)
        if struggle:
            score -= 0.15
        score = max(0.0, min(1.0, score))
        if total < 6:
            label = "עדיין מוקדם"
            advice = "צריך עוד כמה סשנים לפני שמדברים על מבחן אמיתי."
        elif score >= 0.78:
            label = "מוכן למבחן דמה"
            advice = "אפשר מבחן דמה. אם הדיוק מחזיק, גם מבחן אמיתי."
        elif score >= 0.58:
            label = "כמעט מוכן"
            advice = (
                f"עוד חיזוק ב{' · '.join(weak[:2])}." if weak else "עוד סשן יציב ברמה הנוכחית."
            )
        else:
            label = "לא מוכן עדיין"
            advice = (
                f"להתמקד ב{' · '.join(weak[:2])} לפני מבחן."
                if weak
                else "לחזק דיוק בסשנים קצרים עם הסבר."
            )
        return {
            "subject": subject_key(subject),
            "score": round(score, 3),
            "label": label,
            "advice": advice,
            "weak_topics": weak,
            "patterns": [p.get("kind") for p in patterns],
        }

    def action_plan(self, subject: str) -> dict[str, Any]:
        """תוכנית פעולה קצרה למסך / חדר מפתח."""
        rec = self.record_for(subject)
        level = normalize_level(rec.get("level"))
        promo = PROMOTE.get(level)
        recent = list(rec.get("recent") or [])
        window = promo["window"] if promo else 8
        slice_ = recent[-window:]
        total = len(slice_)
        correct = sum(1 for row in slice_ if row.get("correct"))
        acc = (100.0 * correct / total) if total else 0.0
        at_level = int(rec.get("answers_at_level") or 0)
        weak = self.weak_topics(subject)
        patterns = self.mistake_patterns(subject)
        ready = self.exam_readiness(subject)
        nxt = next_level(level)
        progress = 0.0
        if promo and total:
            n_factor = min(1.0, at_level / max(1, promo["min_at_level"]))
            acc_factor = min(1.0, (acc / 100.0) / promo["accuracy"])
            progress = 0.4 * n_factor + 0.6 * acc_factor
        steps: list[str] = []
        if self._struggle_from_parts(subject, total, acc, weak, patterns):
            steps.append("סשן חירום: 6 עד 8 שאלות רק בנושא החלש, עם הסבר אחרי כל תשובה.")
        if weak:
            steps.append(f"עוד תרגול ב {' · '.join(weak[:2])} (כ־8 שאלות).")
        for pat in patterns[:2]:
            steps.append(pat.get("message") or pat.get("title") or "")
        if nxt and progress >= 0.75:
            steps.append(f"קרוב לעלייה ל{LEVEL_HE.get(nxt, nxt)}: לשמור דיוק גבוה בעוד סשן אחד.")
        if ready.get("score", 0) >= 0.78:
            steps.append("מבחן דמה לבדיקת יציבות בלי משוב אחרי כל שאלה.")
        if not steps:
            steps.append("תרגול קצר ברמה הנוכחית: 8 שאלות, בלי לקפוץ בין מקצועות.")
        plan = {
            "subject": subject_key(subject),
            "title": f"מה כדאי עכשיו ב{subject_label(subject)}",
            "steps": [s for s in steps if s][:4],
            "readiness": ready,
        }
        # שכבת AI מקומית (Ollama): זיהוי פערים שקטים מעל הסטטיסטיקה הקיימת.
        try:
            from core import ai_tutor

            plan = ai_tutor.enrichment_for_action_plan(
                subject, plan, engine=self, storage=self.storage, use_llm=False,
            )
        except Exception:
            pass
        return plan

    def _struggle_from_parts(
        self,
        subject: str,
        total: int,
        acc: float,
        weak: list[str],
        patterns: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        patterns = patterns if patterns is not None else self.mistake_patterns(subject)
        if total >= 6 and acc < 50:
            return {
                "severity": "subject",
                "subject": subject,
                "accuracy": acc,
                "total": total,
                "topics": weak,
            }
        if weak and total >= 4 and acc < 62:
            return {
                "severity": "topic",
                "subject": subject,
                "accuracy": acc,
                "total": total,
                "topics": weak,
            }
        if total >= 8 and len(patterns) >= 2 and acc < 70:
            return {
                "severity": "patterns",
                "subject": subject,
                "accuracy": acc,
                "total": total,
                "topics": weak,
            }
        return None

    def struggling(self, subject: str) -> dict[str, Any] | None:
        """כשהתלמיד ממש נכשל במקצוע/נושא. בלי לקרוא ל-snapshot."""
        rec = self.record_for(subject)
        level = normalize_level(rec.get("level"))
        promo = PROMOTE.get(level)
        recent = list(rec.get("recent") or [])
        window = promo["window"] if promo else 8
        slice_ = recent[-window:]
        total = len(slice_)
        acc = (100.0 * sum(1 for row in slice_ if row.get("correct")) / total) if total else 100.0
        weak = self.weak_topics(subject)
        return self._struggle_from_parts(subject, total, acc, weak)

    def _content_scorer(self, subject: str, srs):
        scored = self.topic_scores(subject)
        weak = {row["topic"] for row in scored if row.get("weak")}
        strength = {row["topic"]: float(row.get("strength") or 0.5) for row in scored}
        srs_fn = srs.score_question if srs is not None and hasattr(srs, "score_question") else None
        struggle = self.struggling(subject)
        patterns = self.mistake_patterns(subject)
        prefer_easy = any(p.get("kind") == "hard" for p in patterns)
        if not weak and srs_fn is None and not struggle:
            return None

        def score(question: dict) -> float:
            value = float(srs_fn(question)) if srs_fn else 0.0
            topic = str(question.get("topic") or "")
            if topic in weak:
                value += 60.0 if struggle else 40.0
                value += max(0.0, (0.55 - strength.get(topic, 0.4)) * 50.0)
            if struggle and topic in set(struggle.get("topics") or weak):
                value += 25.0
            diff = normalize_difficulty(question.get("difficulty"))
            if prefer_easy and diff == "Easy":
                value += 12.0
            if prefer_easy and diff == "Hard":
                value -= 8.0
            return value

        return score

    # ---------- תצוגה ----------
    def snapshot(self, subject: str) -> dict[str, Any]:
        rec = self.record_for(subject)
        level = normalize_level(rec.get("level"))
        nxt = next_level(level)
        promo = PROMOTE.get(level)
        recent = list(rec.get("recent") or [])
        window = promo["window"] if promo else 8
        slice_ = recent[-window:]
        correct = sum(1 for row in slice_ if row.get("correct"))
        total = len(slice_)
        acc = round(100 * correct / total, 1) if total else 0.0
        at_level = int(rec.get("answers_at_level", 0) or 0)
        if promo:
            n_factor = min(1.0, at_level / max(1, promo["min_at_level"]))
            acc_factor = min(1.0, (acc / 100.0) / promo["accuracy"]) if total else 0.0
            w_acc = weighted_accuracy(slice_) if slice_ else 0.0
            progress = (
                round(0.35 * n_factor + 0.45 * acc_factor + 0.20 * min(1.0, w_acc / max(promo["accuracy"], 0.01)), 3)
                if total
                else round(0.35 * n_factor, 3)
            )
        else:
            progress = 1.0
        weak = self.weak_topics(subject)
        ready = self.exam_readiness(subject)
        blurbs = {
            "starter": "מתחילים בקלות. כשיש רצף הצלחות, עולים שלב.",
            "easy": "רמה קלה. עוד קצת יציבות ועוברים לבינוני.",
            "intermediate": "כבר לא מתחילים. השאלות עמוקות יותר. עוד הצלחה תוביל למתקדם.",
            "advanced": "רמה גבוהה: שאלות קשות ומבחנים עם שעון.",
            "elite": "רמה גבוהה מאוד. שומרים על דיוק גם במבחן ארוך.",
        }
        shape = SESSION_SHAPE[level]
        need_pct = int(promo["accuracy"] * 100) if promo else 0
        return {
            "subject": subject_key(subject),
            "level": level,
            "level_he": LEVEL_HE[level],
            "emoji": LEVEL_EMOJI[level],
            "next_level": nxt,
            "next_level_he": LEVEL_HE.get(nxt or "", ""),
            "recent_correct": correct,
            "recent_total": total,
            "recent_accuracy": acc,
            "answers_at_level": at_level,
            "progress": progress,
            "weak_topics": weak,
            "exam_readiness": ready,
            "headline": f"רמה במקצוע: {LEVEL_HE[level]}",
            "blurb": blurbs[level],
            "progress_caption": (
                f"כדי לעלות ל{LEVEL_HE[nxt]}: {correct}/{window} נכונות אחרונות (צריך {need_pct}%)"
                if nxt and promo
                else "אתה ברמה הגבוהה במקצוע הזה."
            ),
            "exam_hint": (
                f"מבחן דמה: {shape['mock']} שאלות"
                + (" עם שעון" if shape.get("mock_timed") else " בלי שעון")
                + f"  ·  מבחן אמיתי: {shape['final']} שאלות"
            ),
            "pending_event": rec.get("pending_event"),
        }

    def all_snapshots(self, subjects: list[str]) -> dict[str, dict]:
        return {key: self.snapshot(key) for key in subjects}

    def _coach_for_snapshot(self, snap: dict[str, Any]) -> dict[str, str]:
        event = snap.get("pending_event")
        if event:
            return {
                "tone": event.get("kind") or "progressing",
                "title": event.get("title") or "עדכון רמה",
                "message": event.get("message") or snap["blurb"],
                "action": "level_changed",
            }
        name = subject_label(snap["subject"])
        plan = self.action_plan(snap["subject"])
        patterns = self.mistake_patterns(snap["subject"])
        nxt = snap.get("next_level")
        window = max(1, int(snap.get("recent_total") or 0))
        have = int(snap.get("recent_correct") or 0)
        promo = PROMOTE.get(snap["level"])
        if patterns and patterns[0].get("kind") == "rush" and window >= 5:
            return {
                "tone": "pace",
                "title": f"לאט יותר ב{name}",
                "message": patterns[0]["message"],
                "action": "slow_down",
            }
        if nxt and promo and window >= promo["window"] - 2:
            need = int(round(promo["accuracy"] * promo["window"]))
            if have >= need - 2:
                return {
                    "tone": "near_promote",
                    "title": f"קרוב לעלייה ב{name}",
                    "message": (
                        f"ב{name} יש {have} נכונות מתוך {promo['window']} האחרונות. "
                        f"עוד קצת יציבות והרמה תעלה ל{LEVEL_HE[nxt]}."
                    ),
                    "action": "push_for_level",
                }
        weak = snap.get("weak_topics") or []
        struggle = self.struggling(snap["subject"])
        if struggle and struggle.get("severity") in {"subject", "patterns"}:
            topics = " · ".join((struggle.get("topics") or weak)[:2]) or "החומר האחרון"
            gap = plan.get("silent_gap") or {}
            ai_msg = str(plan.get("ai_message") or gap.get("message") or "").strip()
            return {
                "tone": "struggle",
                "title": gap.get("coach_title") or f"עוצרים רגע ב{name}",
                "message": ai_msg or (
                    f"ב{name} יצא {int(struggle['accuracy'])}% ב{struggle['total']} האחרונות. "
                    f"נתרגל עכשיו שאלות בסגנון שקשה שם"
                    + (f" ({topics})" if topics else "")
                    + ", עם הסבר אחרי כל תשובה."
                ),
                "action": "drill_weak_topic",
            }
        if weak and snap.get("recent_accuracy", 100) < 72:
            topics = " · ".join(weak[:2])
            step = (plan.get("steps") or [""])[0]
            gap = plan.get("silent_gap") or {}
            ai_msg = str(plan.get("ai_message") or gap.get("message") or "").strip()
            return {
                "tone": "weak_topic",
                "title": gap.get("coach_title") or f"בואו נחזק את {name}",
                "message": ai_msg or (
                    f"יש קושי ב{topics}. "
                    + (step or "התרגול הבא ייטה לשם, כדי לסגור את הפער.")
                ),
                "action": "drill_weak_topic",
            }
        ready = snap.get("exam_readiness") or {}
        if snap["level"] == "advanced" and ready.get("score", 0) >= 0.78:
            return {
                "tone": "level_advanced",
                "title": snap["headline"],
                "message": f"{name} יציב למבחן. {ready.get('advice') or 'מבחן דמה יבדוק אם זה מחזיק תחת שעון.'}",
                "action": "exam_ready",
            }
        if snap["level"] == "advanced" and snap.get("recent_accuracy", 100) >= 80 and window >= 6:
            return {
                "tone": "level_advanced",
                "title": snap["headline"],
                "message": f"{name} ברמת מתקדם ויציב. מבחן דמה או מבחן אמיתי יבדקו אם זה מחזיק תחת שעון.",
                "action": "exam_ready",
            }
        return {
            "tone": "level_" + snap["level"],
            "title": snap["headline"],
            "message": snap["blurb"],
            "action": "practice_at_level",
        }

    def evaluate(self, subject: str | None = None) -> dict[str, str]:
        """הודעת מאמן לדשבורד, מבוססת רמות אמיתיות, לא משפט גנרי."""
        focus = (
            self.storage.get_focus_summary()
            if hasattr(self.storage, "get_focus_summary")
            else {"status": "stable"}
        )
        if focus.get("status") == "needs_break":
            return {
                "tone": "gentle_reset",
                "title": "הפסקה קצרה",
                "message": "נראה שצריך החלפת קצב. שלוש דקות מנוחה, ואז 5 שאלות ברמה הנוכחית שלך.",
                "action": "break_and_micro_practice",
            }

        if subject:
            return self._coach_for_snapshot(self.snapshot(subject))

        snapshots = []
        try:
            from core.config import ALL_SUBJECTS

            snapshots = [self.snapshot(key) for key in ALL_SUBJECTS]
        except Exception:
            snapshots = []

        promoted = [item for item in snapshots if (item.get("pending_event") or {}).get("kind") == "promote"]
        if promoted:
            event = promoted[0]["pending_event"]
            return {
                "tone": "promote",
                "title": event["title"],
                "message": event["message"],
                "action": "celebrate_level",
            }

        demoted = [item for item in snapshots if (item.get("pending_event") or {}).get("kind") == "demote"]
        if demoted:
            event = demoted[0]["pending_event"]
            return {
                "tone": "demote",
                "title": event["title"],
                "message": event["message"],
                "action": "recover_level",
            }

        measured = [item for item in snapshots if item.get("recent_total", 0) >= 5]
        if measured:
            weakest = min(measured, key=lambda item: (item["recent_accuracy"], -item["recent_total"]))
            struggle = self.struggling(weakest["subject"])
            name = subject_label(weakest["subject"])
            if struggle and struggle.get("severity") == "subject":
                topics = " · ".join((struggle.get("topics") or [])[:2])
                return {
                    "tone": "struggle",
                    "title": f"{name}: צריך עזרה עכשיו",
                    "message": (
                        f"ב{name} רק {int(struggle['accuracy'])}% ב{struggle['total']} האחרונות. "
                        + (f"הנושא שתוקעים בו: {topics}. " if topics else "")
                        + "כנסו לתרגול שם. נבחר שאלות באותו סגנון ונסביר אחרי כל תשובה."
                    ),
                    "action": "practice_weak_subject",
                }
            if weakest["recent_accuracy"] < 62:
                return {
                    "tone": "focus_weak",
                    "title": f"{name} צריך חיזוק",
                    "message": (
                        f"{name} הכי חלש עכשיו ({int(weakest['recent_accuracy'])}% "
                        f"ב{weakest['recent_total']} האחרונות). תרגול קצר שם יזיז יותר ממקצוע שכבר חזק."
                    ),
                    "action": "practice_weak_subject",
                }

        near = []
        for item in snapshots:
            promo = PROMOTE.get(item["level"])
            nxt = item.get("next_level")
            if not (nxt and promo and item.get("recent_total", 0) >= promo["window"] - 2):
                continue
            need = int(round(promo["accuracy"] * promo["window"]))
            if item["recent_correct"] >= need - 2:
                near.append(item)
        if near:
            return self._coach_for_snapshot(near[0])

        beginners = [
            item for item in snapshots
            if item["level"] in {"starter", "easy"} and item["answers_at_level"] < 8
        ]
        if beginners:
            name = subject_label(beginners[0]["subject"])
            return {
                "tone": "easy_start",
                "title": "מתחילים מקל",
                "message": (
                    f"ב{name} ובשאר המקצועות מתחילים משאלות קלות. "
                    "כשתצליחו ביציבות הרמה תעלה לבד, ואז גם השיעורים והמבחנים נהיים רציניים יותר."
                ),
                "action": "short_start",
            }

        advancing = [item for item in snapshots if item["level"] not in {"starter", "easy"}]
        if advancing:
            names = " · ".join(subject_label(item["subject"]) for item in advancing[:3])
            return {
                "tone": "progressing",
                "title": "הרמה עולה",
                "message": f"יש מקצועות שכבר לא במתחילים: {names}. ממשיכים משם, בלי לחזור על חומר קל סתם.",
                "action": "continue_momentum",
            }

        return {
            "tone": "easy_start",
            "title": "התחלה עדינה",
            "message": "בחרו מקצוע. מתחילים מקל, והרמה עולה כשתצליחו.",
            "action": "short_start",
        }

    def get_daily_nudge(self) -> str:
        return self.evaluate().get("message", "המשך בקצב קצר ונעים")
