# -*- coding: utf-8 -*-
"""סריקה ותיקון מלא של מאגרי שאלות + תוכן שיעורים."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.lesson_plain import organize_to_text
from core.stem_fix import clean_topic_label, polish_stem, scrub_explanation
from core.teach import clarify_stem
import re


def _fix_question(q: dict, subject: str) -> dict:
    row = dict(q)
    row["subject"] = row.get("subject") or subject
    stem = str(row.get("question") or "")
    new_stem = clarify_stem(row)
    if new_stem and new_stem != stem:
        row["question"] = new_stem
    else:
        row["question"] = polish_stem(stem, row)

    if row.get("topic"):
        row["topic"] = clean_topic_label(str(row.get("topic") or ""))

    tags = row.get("tags")
    if isinstance(tags, list):
        row["tags"] = [
            clean_topic_label(str(t)) if "סבב" in str(t) else t
            for t in tags
        ]

    exp = str(row.get("explanation") or "")
    cleaned = scrub_explanation(
        exp,
        keep_years_from=f"{row.get('question')} {row.get('correct_answer')} {row.get('topic')}",
        stem=str(row.get("question") or ""),
    )
    answer = str(row.get("correct_answer") or "").strip()
    # הסבר גנרי על «הציונות המודרנית» — גוזרים את הזנב הגנרי
    if cleaned and "הציונות המודרנית" in cleaned:
        cleaned = re.split(r"הציונות המודרנית", cleaned, maxsplit=1)[0].strip(" .;,")
        if answer and (not cleaned or cleaned == answer):
            cleaned = f"התשובה הנכונה היא «{answer}»."
        elif cleaned and answer and answer not in cleaned:
            cleaned = f"התשובה הנכונה היא «{answer}». {cleaned}"
    if cleaned:
        row["explanation"] = cleaned
    elif answer:
        row["explanation"] = f"התשובה הנכונה היא «{answer}»."

    hint = str(row.get("hint") or "").strip()
    if hint:
        if "הציונות המודרנית" in hint and answer in ("גולדה מאיר",):
            row["hint"] = f"חפשו את ראשת הממשלה הראשונה של ישראל."
        else:
            row["hint"] = scrub_explanation(hint, stem=str(row.get("question") or ""))
    return row


def _fix_lesson(lesson: dict, subject: str) -> dict:
    row = dict(lesson)
    if row.get("topic"):
        row["topic"] = clean_topic_label(str(row.get("topic") or ""))
    if row.get("title"):
        row["title"] = clean_topic_label(str(row.get("title") or ""))
    raw = str(row.get("content") or "")
    topic = str(row.get("topic") or row.get("title") or "")
    row["content"] = organize_to_text(raw, subject=subject, topic=topic)
    return row


def scrub_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    subject = str(data.get("subject") or path.stem)
    stats = {"questions": 0, "lessons": 0, "q_changed": 0, "l_changed": 0}

    questions = []
    for q in data.get("questions") or []:
        stats["questions"] += 1
        before = json.dumps(q, ensure_ascii=False, sort_keys=True)
        fixed = _fix_question(q, subject)
        after = json.dumps(fixed, ensure_ascii=False, sort_keys=True)
        if before != after:
            stats["q_changed"] += 1
        questions.append(fixed)
    data["questions"] = questions

    lessons = []
    for lesson in data.get("lessons") or []:
        stats["lessons"] += 1
        before = json.dumps(lesson, ensure_ascii=False, sort_keys=True)
        fixed = _fix_lesson(lesson, subject)
        after = json.dumps(fixed, ensure_ascii=False, sort_keys=True)
        if before != after:
            stats["l_changed"] += 1
        lessons.append(fixed)
    data["lessons"] = lessons

    # topics[] theory_content אם קיים
    topics = []
    for topic in data.get("topics") or []:
        t = dict(topic)
        if t.get("topic"):
            t["topic"] = clean_topic_label(str(t.get("topic") or ""))
        theory = str(t.get("theory_content") or t.get("theory") or "")
        if theory:
            t["theory_content"] = organize_to_text(
                theory, subject=subject, topic=str(t.get("topic") or ""),
            )
        nested = []
        for q in t.get("questions") or []:
            nested.append(_fix_question(q, subject))
        if "questions" in t:
            t["questions"] = nested
        topics.append(t)
    if topics:
        data["topics"] = topics

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats


def main() -> int:
    folder = ROOT / "data" / "questions"
    total = {"questions": 0, "lessons": 0, "q_changed": 0, "l_changed": 0}
    for path in sorted(folder.glob("*.json")):
        stats = scrub_file(path)
        print(f"{path.name}: Q {stats['q_changed']}/{stats['questions']}  L {stats['l_changed']}/{stats['lessons']}")
        for k in total:
            total[k] += stats[k]
    print(
        f"TOTAL: questions fixed {total['q_changed']}/{total['questions']}, "
        f"lessons fixed {total['l_changed']}/{total['lessons']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
