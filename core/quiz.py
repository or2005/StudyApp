from __future__ import annotations

import random
from typing import Any


def unique_options(correct: str, wrongs: list[str]) -> list[str]:
    seen = {str(correct)}
    opts = [str(correct)]
    for item in wrongs:
        text = str(item)
        if text not in seen:
            opts.append(text)
            seen.add(text)
        if len(opts) >= 4:
            break
    filler = 1
    while len(opts) < 4:
        extra = f"לא נכון ({filler})"
        if extra not in seen and extra != str(correct):
            opts.append(extra)
            seen.add(extra)
        filler += 1
    return opts[:4]


def polish_explanation(correct: str, explanation: str, topic: str = "") -> str:
    """מוודא שלכל שאלה יש הסבר אמיתי, לא משפט קצר מדי."""
    exp = (explanation or "").strip()
    answer = str(correct or "").strip()
    topic = str(topic or "").strip()
    if not exp:
        base = f"התשובה הנכונה היא «{answer}»."
        if topic:
            base += f" זה שייך לנושא «{topic}»."
        return base + " קראו שוב את השאלה, פסלו מה שלא מתאים, וחזרו לשיעור הקצר."
    if len(exp) < 55:
        lead = f"התשובה הנכונה היא «{answer}». " if answer and answer not in exp else ""
        return (
            f"{lead}{exp} "
            "אם טעיתם, קראו את השאלה לאט, בדקו מה בדיוק נשאל, וחזרו לשיעור בנושא."
        )
    if answer and answer not in exp[:120]:
        return f"התשובה הנכונה היא «{answer}». {exp}"
    return exp


def make_question(
    subject: str,
    topic: str,
    qid: str,
    question: str,
    correct: str,
    wrongs: list[str],
    explanation: str,
    difficulty: str = "Easy",
    hint: str = "",
    rng: random.Random | None = None,
    kind: str = "normal",
    passage: str = "",
    passage_id: str = "",
) -> dict[str, Any]:
    roller = rng or random.Random(qid)
    options = unique_options(correct, wrongs)
    roller.shuffle(options)
    answer = options.index(str(correct))
    item = {
        "id": qid,
        "subject": subject,
        "topic": topic,
        "question": question,
        "options": options,
        "answer": answer,
        "correct_answer": str(correct),
        "explanation": polish_explanation(correct, explanation, topic),
        "difficulty": difficulty,
        "kind": "trick" if "trick" in qid else kind,
        "tags": [subject, topic, difficulty],
        "hint": hint or "קראו שוב את השאלה. מה בדיוק מבקשים למצוא?",
    }
    if passage:
        item["kind"] = "passage"
        item["passage"] = passage
        item["passage_id"] = passage_id or qid
    return item


def wrap_subject(key: str, title: str, topics: list[dict[str, Any]]) -> dict[str, Any]:
    questions: list[dict[str, Any]] = []
    lessons: list[dict[str, Any]] = []
    for idx, topic in enumerate(topics, start=1):
        topic_name = topic["topic"]
        theory = topic.get("theory_content") or topic.get("theory") or ""
        block = []
        for q in topic.get("questions") or []:
            q = dict(q)
            q.setdefault("subject", key)
            q.setdefault("topic", topic_name)
            block.append(q)
            questions.append(q)
        topic["questions"] = block
        topic["theory_content"] = theory
        lessons.append(
            {
                "id": f"{key}_lesson_{idx}",
                "title": f"{idx}. {topic_name}",
                "category": "שיעור עיוני",
                "content": theory,
                "topic": topic_name,
            }
        )
    return {
        "subject": key,
        "title": title,
        "study_path": [
            {"step": "read", "title": "שיעור עיוני", "summary": "קוראים בקצב שלכם. משפטים קצרים ודוגמה אחת."},
            {"step": "guided", "title": "שיעור ותרגול", "summary": "אחרי הקריאה: 5 שאלות רק על אותו נושא."},
            {"step": "practice", "title": "תרגול", "summary": "8 שאלות עם הסבר אחרי כל תשובה."},
            {"step": "mock", "title": "מבחן דמה", "summary": "10 שאלות. הציון בסוף."},
            {"step": "timed", "title": "מבחן בזמן", "summary": "10 שאלות ושעון רגוע לכל שאלה."},
        ],
        "topics": topics,
        "lessons": lessons,
        "questions": questions,
    }
