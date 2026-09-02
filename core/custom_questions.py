"""שאלות שהמשתמש מוסיף בעצמו, בלי לגעת בקוד."""
from __future__ import annotations

import json
import os
import time
from typing import Any

from core.config import ALL_SUBJECTS, subject_key
from core.quiz import make_question
from core.storage import get_persistent_app_dir

BANNED = ("גרסה שגויה",)


def custom_dir(root: str | None = None) -> str:
    folder = os.path.join(root or get_persistent_app_dir(), "custom_questions")
    os.makedirs(folder, exist_ok=True)
    return folder


def subject_path(subject: str, root: str | None = None) -> str:
    key = subject_key(subject)
    return os.path.join(custom_dir(root), f"{key}.json")


def load_for_subject(subject: str, root: str | None = None) -> list[dict[str, Any]]:
    path = subject_path(subject, root)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        rows = data.get("questions") if isinstance(data, dict) else data
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []


def _save_for_subject(subject: str, rows: list[dict[str, Any]], root: str | None = None) -> None:
    path = subject_path(subject, root)
    tmp = path + ".tmp"
    payload = {"subject": subject_key(subject), "questions": rows}
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def list_all(root: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ALL_SUBJECTS:
        for row in load_for_subject(key, root):
            items.append(row)
    return items


def _has_banned(text: str) -> bool:
    blob = str(text or "")
    return any(token in blob for token in BANNED)


def validate_draft(
    subject: str,
    question: str,
    options: list[str],
    correct_index: int,
    explanation: str,
    topic: str = "",
) -> str | None:
    key = subject_key(subject)
    if key not in ALL_SUBJECTS:
        return "בחרו מקצוע מהרשימה."
    q = (question or "").strip()
    if len(q) < 8:
        return "השאלה קצרה מדי."
    cleaned = [str(item or "").strip() for item in options]
    if len(cleaned) < 4 or any(len(item) < 1 for item in cleaned[:4]):
        return "צריך ארבע תשובות מלאות."
    if len(set(cleaned[:4])) < 4:
        return "כל ארבע התשובות חייבות להיות שונות."
    if not (0 <= int(correct_index) < 4):
        return "סמנו איזו תשובה נכונה."
    exp = (explanation or "").strip()
    if len(exp) < 20:
        return "ההסבר חייב להיות לפחות 20 תווים."
    blob = " ".join([q, topic, exp, *cleaned[:4]])
    if _has_banned(blob):
        return "אי אפשר לשמור טקסט שמכיל «גרסה שגויה»."
    return None


def add_question(
    subject: str,
    question: str,
    options: list[str],
    correct_index: int,
    explanation: str,
    topic: str = "",
    difficulty: str = "Easy",
    root: str | None = None,
) -> dict[str, Any]:
    error = validate_draft(subject, question, options, correct_index, explanation, topic)
    if error:
        raise ValueError(error)
    key = subject_key(subject)
    cleaned = [str(item).strip() for item in options[:4]]
    answer = cleaned[int(correct_index)]
    wrongs = [item for idx, item in enumerate(cleaned) if idx != int(correct_index)]
    qid = f"custom_{key}_{int(time.time() * 1000)}"
    item = make_question(
        subject=key,
        topic=(topic or "").strip() or "שאלות שהוספתי",
        qid=qid,
        question=question.strip(),
        correct=answer,
        wrongs=wrongs,
        explanation=explanation.strip(),
        difficulty=difficulty if difficulty in {"Easy", "Medium", "Hard"} else "Easy",
    )
    item["custom"] = True
    rows = load_for_subject(key, root)
    rows.append(item)
    _save_for_subject(key, rows, root)
    try:
        from core.loader import clear_cache

        clear_cache()
    except Exception:
        pass
    return item


def delete_question(question_id: str, root: str | None = None) -> bool:
    qid = str(question_id or "")
    if not qid:
        return False
    changed = False
    for key in ALL_SUBJECTS:
        rows = load_for_subject(key, root)
        kept = [row for row in rows if str(row.get("id")) != qid]
        if len(kept) != len(rows):
            _save_for_subject(key, kept, root)
            changed = True
    if changed:
        try:
            from core.loader import clear_cache

            clear_cache()
        except Exception:
            pass
    return changed


def merge_into(subject: str, data: dict[str, Any] | None, root: str | None = None) -> dict[str, Any] | None:
    if not data:
        return data
    extras = load_for_subject(subject, root)
    if not extras:
        return data
    questions = list(data.get("questions") or [])
    seen = {str(row.get("id")) for row in questions}
    for row in extras:
        qid = str(row.get("id") or "")
        if qid and qid not in seen:
            questions.append(row)
            seen.add(qid)
    data["questions"] = questions
    return data
