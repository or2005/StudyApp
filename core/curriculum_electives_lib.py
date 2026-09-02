"""עזרים משותפים למקצועות בחירה."""
from __future__ import annotations

import random

from core.quiz import make_question, wrap_subject


def theory(title: str, steps: list[str], example: str, extra: str = "") -> str:
    lines = [title, "", "קריאה בקצב איטי. שורה־שורה:", ""]
    for i, step in enumerate(steps, start=1):
        lines.append(f"{i}. {step}")
    lines.extend(["", "דוגמה:", example])
    if extra:
        lines.extend(["", extra])
    lines.append("")
    lines.append("אחרי הדוגמה אפשר לעבור לתרגול.")
    return "\n".join(lines)


def pack(subject: str, title: str, blocks: list[tuple[str, str, list]]) -> dict:
    rng = random.Random(subject)
    topics = []
    for topic, text, items in blocks:
        qs = []
        for i, row in enumerate(items):
            q, ans, wrong, why = row[:4]
            diff = row[4] if len(row) > 4 else "Easy"
            hint = row[5] if len(row) > 5 else ""
            qs.append(
                make_question(
                    subject,
                    topic,
                    f"{subject}_{topic[:10]}_{i+1}",
                    q,
                    ans,
                    wrong,
                    why,
                    diff,
                    hint=hint,
                    rng=rng,
                )
            )
        topics.append({"topic": topic, "theory_content": text, "questions": qs})
    return wrap_subject(subject, title, topics)


def level_lessons(bank: dict) -> dict:
    """חלק מהשיעורים מקבלים רמה בינונית / מתקדמת למנוע הרמות."""
    lessons = bank.get("lessons") or []
    n = len(lessons)
    for i, lesson in enumerate(lessons):
        if n <= 1:
            lesson["category"] = "רמה בינונית"
            continue
        if i >= int(n * 0.55):
            lesson["category"] = "רמה מתקדמת"
        elif i >= int(n * 0.28):
            lesson["category"] = "רמה בינונית"
        else:
            lesson["category"] = "שיעור עיוני"
    return bank
