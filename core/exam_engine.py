from __future__ import annotations

import time


class ExamSession:
    def __init__(
        self,
        questions,
        mode="practice",
        current_index=0,
        score=0,
        user_answers=None,
        start_time=None,
        time_limit_sec=None,
        subject_key=None,
        topic=None,
        total_limit_sec=None,
        skipped=None,
        flagged=None,
        chapters=None,
        chapter_started_at=None,
    ):
        self.questions = list(questions or [])
        self.mode = mode
        self.current_index = int(current_index or 0)
        self.score = int(score or 0)
        self.start_time = start_time if start_time is not None else time.time()
        self.user_answers = list(user_answers or [])
        self.time_limit_sec = time_limit_sec
        self.total_limit_sec = total_limit_sec
        self.subject_key = subject_key
        self.topic = topic
        self.skipped = set(skipped or [])
        self.flagged = set(flagged or [])
        self.question_started_at = time.time()
        # פרקים: כל אחד עם טווח שאלות ושעון משלו, כמו במבחן מימ״ד האמיתי.
        self.chapters = list(chapters or [])
        self.chapter_started_at = chapter_started_at if chapter_started_at is not None else time.time()

    @classmethod
    def from_state(cls, state):
        if not state:
            return None
        return cls(
            questions=state.get("questions", []),
            mode=state.get("mode", "practice"),
            current_index=int(state.get("current_index", 0) or 0),
            score=int(state.get("score", 0) or 0),
            user_answers=list(state.get("user_answers") or []),
            start_time=state.get("start_time", time.time()),
            time_limit_sec=state.get("time_limit_sec"),
            subject_key=state.get("subject_key"),
            topic=state.get("topic"),
            total_limit_sec=state.get("total_limit_sec"),
            skipped=state.get("skipped") or [],
            flagged=state.get("flagged") or [],
            chapters=state.get("chapters") or [],
            chapter_started_at=state.get("chapter_started_at"),
        )

    def to_state(self, subject_key=None):
        return {
            "subject_key": subject_key or self.subject_key,
            "mode": self.mode,
            "questions": self.questions,
            "current_index": self.current_index,
            "score": self.score,
            "user_answers": self.user_answers,
            "start_time": self.start_time,
            "time_limit_sec": self.time_limit_sec,
            "total_limit_sec": self.total_limit_sec,
            "topic": self.topic,
            "skipped": sorted(self.skipped),
            "flagged": sorted(self.flagged),
            "chapters": self.chapters,
            "chapter_started_at": self.chapter_started_at,
        }

    # ---------- פרקים ----------
    def current_chapter(self) -> dict | None:
        for chapter in self.chapters:
            if chapter["start"] <= self.current_index < chapter["end"]:
                return chapter
        return None

    def chapter_index(self) -> int:
        chapter = self.current_chapter()
        return self.chapters.index(chapter) + 1 if chapter else 0

    def chapter_remaining(self) -> int | None:
        chapter = self.current_chapter()
        if not chapter or not chapter.get("seconds"):
            return None
        return max(0, int(chapter["seconds"] - (time.time() - self.chapter_started_at)))

    def close_chapter(self) -> bool:
        """נגמר הזמן לפרק: מה שלא נענה נספר כשגוי, ועוברים לפרק הבא."""
        chapter = self.current_chapter()
        if not chapter:
            return False
        while self.current_index < chapter["end"] and self.current_index < len(self.questions):
            self.submit_answer(-1, 0.0)
        self.chapter_started_at = time.time()
        self.mark_question_start()
        return not self.is_finished()

    def chapter_breakdown(self) -> list[dict]:
        rows = []
        for chapter in self.chapters:
            answers = self.user_answers[chapter["start"]:chapter["end"]]
            total = chapter["end"] - chapter["start"]
            correct = sum(1 for item in answers if item.get("correct"))
            answered = len(answers)
            rows.append(
                {
                    "key": chapter.get("key"),
                    "name": chapter.get("name"),
                    "correct": correct,
                    "answered": answered,
                    "total": total,
                    "percent": round(100 * correct / total) if total else 0,
                }
            )
        return rows

    # ---------- זמן ----------
    def mark_question_start(self):
        self.question_started_at = time.time()

    def remaining_for_question(self):
        if not self.time_limit_sec:
            return None
        return max(0, int(self.time_limit_sec - (time.time() - self.question_started_at)))

    def remaining_total(self):
        if not self.total_limit_sec:
            return None
        return max(0, int(self.total_limit_sec - (time.time() - self.start_time)))

    def out_of_time(self) -> bool:
        left = self.remaining_total()
        return left is not None and left <= 0

    # ---------- ניווט ----------
    def get_current_question(self):
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def can_skip(self) -> bool:
        q = self.get_current_question()
        if not q:
            return False
        if str(q.get("id")) in self.skipped:
            return False
        chapter = self.current_chapter()
        if chapter:
            return self.current_index < chapter["end"] - 1
        return self.current_index < len(self.questions) - 1

    def skip_current(self) -> bool:
        """מעביר את השאלה לסוף הפרק (או לסוף המבחן). פעם אחת לכל שאלה."""
        if not self.can_skip():
            return False
        chapter = self.current_chapter()
        q = self.questions.pop(self.current_index)
        self.skipped.add(str(q.get("id")))
        if chapter:
            self.questions.insert(chapter["end"] - 1, q)
        else:
            self.questions.append(q)
        self.mark_question_start()
        return True

    def toggle_flag(self) -> bool:
        q = self.get_current_question()
        if not q:
            return False
        qid = str(q.get("id"))
        if qid in self.flagged:
            self.flagged.discard(qid)
            return False
        self.flagged.add(qid)
        return True

    def is_flagged(self) -> bool:
        q = self.get_current_question()
        return bool(q) and str(q.get("id")) in self.flagged

    # ---------- תשובות ----------
    def submit_answer(self, selected_index, time_taken_sec, typed: str | None = None):
        q = self.get_current_question()
        if not q:
            return False
        compose = bool(q.get("compose") or q.get("kind") == "compose" or self.mode == "compose")
        if compose:
            from core.compose import answers_match

            text = "" if typed is None else str(typed)
            is_correct = answers_match(text, q)
            selected = text
        else:
            is_correct = selected_index == q.get("answer")
            selected = selected_index
        if is_correct:
            self.score += 1
        self.user_answers.append(
            {
                "question_id": q.get("id"),
                "topic": q.get("topic"),
                "subject": q.get("subject"),
                "question": q.get("question"),
                "options": q.get("options"),
                "answer": q.get("answer"),
                "correct_answer": q.get("correct_answer"),
                "explanation": q.get("explanation"),
                "selected": selected,
                "selected_text": typed if compose else "",
                "correct": is_correct,
                "time_sec": round(time_taken_sec, 2),
            }
        )
        self.current_index += 1
        return is_correct

    def wrong_answers(self) -> list:
        return [a for a in self.user_answers if not a.get("correct")]

    def fill_unanswered(self) -> int:
        """שאלות שלא נענו (נגמר הזמן) נספרות כשגויות בדוח."""

        def _key(item, id_field="question_id"):
            qid = item.get(id_field)
            if qid not in (None, ""):
                return f"id:{qid}"
            return f"q:{(item.get('question') or '')}|{(item.get('topic') or '')}"

        answered = {_key(item) for item in self.user_answers}
        added = 0
        for q in self.questions:
            key = _key(q, id_field="id")
            if key in answered:
                continue
            self.user_answers.append(
                {
                    "question_id": q.get("id"),
                    "topic": q.get("topic"),
                    "subject": q.get("subject"),
                    "question": q.get("question"),
                    "options": q.get("options"),
                    "answer": q.get("answer"),
                    "correct_answer": q.get("correct_answer"),
                    "explanation": q.get("explanation"),
                    "selected": None,
                    "correct": False,
                    "time_sec": 0,
                }
            )
            answered.add(key)
            added += 1
        return added

    def get_total(self):
        return len(self.questions)

    def is_finished(self):
        return self.current_index >= len(self.questions)

    def get_total_time(self):
        return round(time.time() - self.start_time, 2)
