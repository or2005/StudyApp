"""מסדר שיעורים עיוניים לקריאה ברורה. רץ בטעינה ובבנייה."""
from __future__ import annotations

from core.config import subject_key
from core.lesson_plain import organize_to_text
from core.theory_library import EXTRA_LESSONS

# כותרת סעיף שמסמנת שהשיעור כבר מסודר
MARKER = "הסבר"


def expand_lessons(subject: str, bank: dict) -> dict:
    key = subject_key(str(subject or bank.get("subject") or ""))
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
    raw = str(lesson.get("content") or "").strip() or title
    return organize_to_text(raw, subject=subject_key(subject), topic=topic)
