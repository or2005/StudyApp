"""Spaced repetition, prioritizes weak / due questions for adaptive practice."""
from __future__ import annotations

import time
from typing import Any


def _now() -> float:
    return time.time()


class SpacedRepetition:
    """Light SM-2 style scheduler stored in user profile."""

    def __init__(self, storage: Any):
        self.storage = storage

    def _data(self) -> dict:
        return self.storage.get("srs") or {}

    def _save(self, data: dict) -> None:
        self.storage.set("srs", data)

    def record(self, question_id: str, correct: bool, quality: int | None = None) -> dict:
        qid = str(question_id or "")
        if not qid:
            return {}
        data = dict(self._data())
        item = dict(data.get(qid) or {"interval": 0, "ease": 2.3, "due": 0})
        ease = float(item.get("ease", 2.3) or 2.3)
        if quality is None:
            quality = 2 if correct else 0
        quality = max(0, min(3, int(quality)))
        if quality <= 0:
            interval = 1
            ease = max(1.5, ease - 0.2)
        elif quality == 1:
            interval = 1
            ease = max(1.5, ease - 0.05)
        elif quality == 2:
            interval = item.get("interval") or 0
            if interval == 0:
                interval = 1
            elif interval == 1:
                interval = 3
            else:
                interval = max(1, int(interval * ease))
            ease = min(2.8, ease + 0.05)
        else:
            interval = item.get("interval") or 1
            if interval <= 1:
                interval = 4
            else:
                interval = max(4, int(interval * ease * 1.3))
            ease = min(2.8, ease + 0.08)
        due = _now() + interval * 86400
        data[qid] = {
            "interval": interval,
            "ease": round(ease, 2),
            "due": due,
            "last": _now(),
            "quality": quality,
        }
        self._save(data)
        return data[qid]

    def score_question(self, q: dict) -> float:
        qid = str(q.get("id") or "")
        data = self._data()
        item = data.get(qid)
        if not item:
            return 100.0
        due = float(item.get("due") or 0)
        if due <= _now():
            return 80.0 + min(20.0, (_now() - due) / 3600)
        return max(0.0, 40.0 - (due - _now()) / 86400)

    def due_ids(self) -> set[str]:
        """מזהי שאלות שהגיע מועד החזרה עליהן. נקרא מהפרופיל בלבד, בלי לטעון מאגרים."""
        now = _now()
        return {
            qid for qid, item in self._data().items()
            if float((item or {}).get("due") or 0) <= now
        }

    def due_count(self) -> int:
        return len(self.due_ids())

    def due_questions(self, questions: list[dict], limit: int = 20) -> list[dict]:
        """השאלות שמחכות לחזרה, הכי מאוחרות קודם."""
        due = self.due_ids()
        if not due:
            return []
        pending = [q for q in questions if str(q.get("id") or "") in due]
        pending.sort(key=self.score_question, reverse=True)
        return pending[:limit]

    def next_due_in_days(self) -> int | None:
        """כמה ימים עד החזרה הבאה, כשאין שום דבר לחזרה עכשיו."""
        data = self._data()
        if not data:
            return None
        now = _now()
        future = [float(item.get("due") or 0) for item in data.values() if float(item.get("due") or 0) > now]
        if not future:
            return None
        return max(0, int((min(future) - now) // 86400))

    def prioritize(self, questions: list[dict], count: int) -> list[dict]:
        if not questions:
            return []
        ranked = sorted(questions, key=lambda q: self.score_question(q), reverse=True)
        head = ranked[: max(count, 1)]
        rest = ranked[len(head) :]
        import random

        random.shuffle(rest)
        picked = head + rest
        return picked[:count]
