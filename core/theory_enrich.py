"""מרחיב שיעורים עיוניים בלי לגעת בשאלות. רץ בטעינה ובבנייה."""
from __future__ import annotations

from core.config import subject_label
from core.theory_library import DEPTH, EXTRA_LESSONS, VOICE

MARKER = "למה זה חשוב"


def expand_lessons(subject: str, bank: dict) -> dict:
    key = str(subject or bank.get("subject") or "")
    lessons = list(bank.get("lessons") or [])
    for lesson in lessons:
        lesson["content"] = expand_one(key, lesson)
    seen = " ".join((item.get("title") or "") + " " + (item.get("topic") or "") for item in lessons)
    start = len(lessons) + 1
    for offset, (title, topic, body) in enumerate(EXTRA_LESSONS.get(key) or []):
        if title in seen:
            continue
        lessons.append(
            {
                "id": f"{key}_theory_{start + offset}",
                "title": f"{start + offset}. {title}",
                "category": "רמה בינונית",
                "content": expand_one(
                    key,
                    {"title": title, "topic": topic, "content": body},
                ),
                "topic": topic,
            }
        )
        seen += " " + title
    bank["lessons"] = lessons
    return bank


def expand_one(subject: str, lesson: dict) -> str:
    title = str(lesson.get("title") or lesson.get("topic") or "")
    topic = str(lesson.get("topic") or title)
    raw = str(lesson.get("content") or "").strip()
    if MARKER in raw:
        return raw
    parts = [raw] if raw else [title]
    depth = _match_depth(subject, f"{title} {topic} {raw[:180]}")
    if depth and depth not in raw:
        parts.extend(["", "הרחבה", depth])
    voice = VOICE.get(subject) or VOICE.get("_default") or {}
    name = subject_label(subject)
    topic_clean = topic.replace(f"{subject}_", "").strip() or name
    parts.extend(
        [
            "",
            MARKER,
            (voice.get("why") or "הנושא הזה חוזר במבחן וביום־יום. מי שמבין אותו חוסך ניחושים.").format(
                topic=topic_clean, subject=name
            ),
            "",
            "איך ללמוד את זה",
            (voice.get("how") or _default_how()).format(topic=topic_clean, subject=name),
            "",
            "טעויות נפוצות",
            (voice.get("mistakes") or "ממהרים לתשובה לפני שקראו את כל השאלה.").format(
                topic=topic_clean, subject=name
            ),
            "",
            "סיכום לפני תרגול",
            (voice.get("recap") or "חזרו על הדוגמה בקול, ואז ענו על שלוש שאלות לאט.").format(
                topic=topic_clean, subject=name
            ),
        ]
    )
    return "\n".join(parts).strip()


def _match_depth(subject: str, blob: str) -> str:
    text = blob.lower()
    best = ""
    best_hits = 0
    for keywords, essay in DEPTH.get(subject) or []:
        hits = sum(1 for word in keywords if word and word in blob)
        if hits > best_hits:
            best_hits = hits
            best = essay
        elif hits == 0:
            # also allow lowercase latin tokens
            hits = sum(1 for word in keywords if word.lower() in text)
            if hits > best_hits:
                best_hits = hits
                best = essay
    return best if best_hits else ""


def _default_how() -> str:
    return (
        "1. קראו פעם אחת בלי לענות.\n"
        "2. סמנו מילה אחת שלא ברורה.\n"
        "3. חזרו על הדוגמה בקול.\n"
        "4. רק אז עברו לתרגול."
    )
