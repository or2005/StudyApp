from __future__ import annotations

import random
import re
from typing import Any

_NUM_LEAD = re.compile(r"^([+-]?(?:\d+\.\d+|\d+))(.*)$")


def _leading_number(text: str):
    match = _NUM_LEAD.match(str(text).strip())
    if not match:
        return None
    raw, suffix = match.group(1), match.group(2)
    number = float(raw) if "." in raw else int(raw)
    return number, suffix


def _junk_option(correct: str, text: str, prompt: str = "") -> bool:
    """מסיח שבור: אות בודדת, או מילה + «ון» במקום תשובה אמיתית."""
    got = str(text or "").strip()
    want = str(correct or "").strip()
    blob = str(prompt or "")
    if not got:
        return True
    if got == want:
        return False
    if len(got) == 1 and not got.isdigit():
        return True
    if got.endswith("ון") and len(got) > 3:
        base = got[:-2]
        if base == want or (base and base in blob):
            return True
    if want and len(want) >= 2 and got == want + want[-1] and " " not in want:
        return True
    return False


def scrub_question(question: dict) -> dict:
    """מתקן אפשרויות שבורות ומנסח מחדש שאלה קצרה מדי."""
    item = dict(question)
    opts = [str(x) for x in (item.get("options") or [])]
    idx = item.get("answer")
    correct = str(item.get("correct_answer") or "").strip()
    if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
        correct = opts[idx]
    if opts:
        fresh = unique_options(
            correct,
            [x for x in opts if x != correct],
            prompt=str(item.get("question") or ""),
        )
        if correct in fresh:
            item["options"] = fresh
            item["answer"] = fresh.index(correct)
            item["correct_answer"] = correct
    from core.teach import clarify_stem

    item["question"] = clarify_stem(item)
    return item


def suggest_distractors(correct: str) -> list[str]:
    """מסיחים אמיתיים במקום «לא נכון (1)»: מספרים קרובים, או משפט ברור."""
    parsed = _leading_number(correct)
    out: list[str] = []
    if parsed is not None:
        number, suffix = parsed
        if isinstance(number, int):
            pool = [
                number + 1,
                number - 1,
                number + 2,
                number * 2,
                number // 2 if abs(number) > 1 else number + 3,
                number + 10,
                abs(number - 10),
                0,
                100,
                number + max(1, abs(number) // 10),
            ]
            for item in pool:
                text = f"{item}{suffix}"
                if text != str(correct):
                    out.append(text)
        else:
            for item in (number + 1, number - 1, number * 2, number / 2, 0.0):
                text = f"{item:g}{suffix}"
                if text != str(correct):
                    out.append(text)
    else:
        out.extend(["לא לפי הנתונים האלה", "אין מספיק מידע בשאלה", "תשובה שלא קשורה לנושא"])
    seen = {str(correct)}
    clean = []
    for item in out:
        text = str(item).strip()
        if text and text not in seen:
            clean.append(text)
            seen.add(text)
    return clean


def unique_options(correct: str, wrongs: list[str], prompt: str = "") -> list[str]:
    seen = {str(correct)}
    opts = [str(correct)]
    for item in list(wrongs) + suggest_distractors(correct):
        text = str(item).strip()
        if not text or text in seen:
            continue
        if text.startswith("לא נכון (") or "only wrong" in text.lower() or text == "גרסה שגויה":
            continue
        if _junk_option(str(correct), text, prompt):
            continue
        opts.append(text)
        seen.add(text)
        if len(opts) >= 4:
            break
    extra = 1
    while len(opts) < 4:
        text = f"אין מספיק מידע ({extra})"
        if text not in seen:
            opts.append(text)
            seen.add(text)
        extra += 1
    return opts[:4]


def polish_explanation(correct: str, explanation: str, topic: str = "", subject: str = "") -> str:
    """משלים הסבר קצר בהוראה מהנושא, לא במלל גנרי."""
    from core.teach import enrich_explanation

    return enrich_explanation(correct, explanation, topic, subject)


def _default_hint(subject: str, topic: str, question: str = "") -> str:
    from core.teach import live_hint

    return live_hint({"topic": topic, "hint": "", "question": question, "subject": subject}, subject)


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
    options = unique_options(correct, wrongs, prompt=question)
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
        "explanation": polish_explanation(correct, explanation, topic, subject),
        "difficulty": difficulty,
        "kind": "trick" if "trick" in qid else kind,
        "tags": [subject, topic, difficulty],
        "hint": hint or _default_hint(subject, topic, question),
    }
    if passage:
        item["kind"] = "passage"
        item["passage"] = passage
        item["passage_id"] = passage_id or qid
    from core.teach import clarify_stem

    item["question"] = clarify_stem(item)
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
            {"step": "guided", "title": "שיעור ותרגול", "summary": "אחרי הקריאה: תרגול קצר רק על אותו נושא."},
            {"step": "practice", "title": "תרגול", "summary": "שאלות עם הסבר אחרי כל תשובה."},
            {"step": "mock", "title": "מבחן דמה", "summary": "הציון בסוף, בלי משוב אחרי כל שאלה."},
            {"step": "timed", "title": "מבחן בזמן", "summary": "אותו מבחן, עם שעון לפי הרמה."},
        ],
        "topics": topics,
        "lessons": lessons,
        "questions": questions,
    }
