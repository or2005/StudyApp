"""
StudyApp, מנגנון שמירה מקומית (Local Persistence)
שומר את כל נתוני המשתמש בקובץ JSON קבוע:
פרטי תלמיד, תוצאות אבחון, תשובות והתקדמות, שורדים סגירה והפעלה מחדש.
"""

import json
import os
import threading
import time
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_persistent_app_dir() -> str:
    """Returns a machine-local application directory that survives app restarts."""
    if os.name == "nt":
        base_dir = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or os.path.expanduser("~")
        )
    else:
        base_dir = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share"
        )
    app_dir = os.path.join(base_dir, "StudyApp")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


DATA_DIR = get_persistent_app_dir()
PROFILE_PATH = os.path.join(DATA_DIR, "user_profile.json")

_lock = threading.Lock()


def default_user_profile_path() -> str:
    from core.profiles import current_files, ensure_migrated

    ensure_migrated()
    return current_files()["user_profile"]


class UserStorage:
    """שמירה וטעינה של פרופיל המשתמש עם cache בזיכרון (מהיר, בלי קריאות דיסק מיותרות)."""

    def __init__(self, path: str | None = None):
        self.path = path or default_user_profile_path()
        self._cache: dict = {}
        self._dirty = False
        self._flush_timer: threading.Timer | None = None
        self._load()

    # ---------- טעינה / שמירה ----------
    def _load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _flush(self) -> None:
        """כתיבה אטומית (קובץ זמני + החלפה) כדי שהנתונים לא ייפגעו."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
            self._dirty = False
        except Exception as e:
            print("storage flush error:", e)

    def _schedule_flush(self, delay: float = 0.25) -> None:
        if self._flush_timer is not None:
            self._flush_timer.cancel()

        def _flush_later() -> None:
            try:
                self.flush()
            finally:
                self._flush_timer = None

        self._flush_timer = threading.Timer(delay, _flush_later)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def flush(self) -> None:
        with _lock:
            if self._dirty:
                self._flush()

    def close(self) -> None:
        """שמירה אחרונה וביטול הטיימר, אחרת נשארים תהליכי רקע אחרי סגירת החלון."""
        timer = self._flush_timer
        self._flush_timer = None
        if timer is not None:
            try:
                timer.cancel()
            except Exception:
                pass
        self.flush()

    # ---------- API גנרי ----------
    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        with _lock:
            self._cache[key] = value
            self._dirty = True
            if save:
                self._schedule_flush()

    # ---------- פרופיל תלמיד ----------
    def has_profile(self) -> bool:
        return bool(self._cache.get("student"))

    def save_student(self, name: str, age: int, id_number: str = "") -> None:
        """ת\"ז לא נשמרת במלואה, רק 4 ספרות אחרונות לזיהוי, וגם זה רק אם הוזנה."""
        digits = "".join(ch for ch in str(id_number or "") if ch.isdigit())
        self.set(
            "student",
            {
                "name": name,
                "age": age,
                "id_hint": digits[-4:] if digits else "",
                "created_at": time.strftime("%Y-%m-%d %H:%M"),
            },
        )

    def get_student(self) -> dict:
        return self._cache.get("student") or {}

    # ---------- אבחון ----------
    def save_diagnostic(
        self,
        score: int,
        total: int,
        level: str,
        answers: list,
        recommendations: list[str] | None = None,
        weak_topics: list[str] | None = None,
    ) -> None:
        self.set(
            "diagnostic",
            {
                "score": score,
                "total": total,
                "level": level,
                "answers": answers,
                "recommendations": recommendations or [],
                "weak_topics": weak_topics or [],
                "date": time.strftime("%Y-%m-%d %H:%M"),
            },
        )

    def get_diagnostic(self) -> dict | None:
        return self._cache.get("diagnostic")

    def get_level(self) -> str:
        d = self.get_diagnostic()
        return (d or {}).get("level", "לא אובחן")

    # ---------- התקדמות ----------
    def record_answer(
        self, subject: str, topic: str, is_correct: bool, time_sec: float,
        question_id: str | None = None,
    ) -> None:
        with _lock:
            progress: dict = self._cache.setdefault("progress", {})
            sub: dict = progress.setdefault(
                subject, {"total": 0, "correct": 0, "time_sec": 0.0, "topics": {}, "seen_ids": []}
            )
            sub["total"] += 1
            if is_correct:
                sub["correct"] += 1
            sub["time_sec"] += round(time_sec, 2)
            t = sub["topics"].setdefault(topic or "כללי", {"total": 0, "correct": 0})
            t["total"] += 1
            if is_correct:
                t["correct"] += 1
            qid = str(question_id or "").strip()
            if qid:
                seen = sub.setdefault("seen_ids", [])
                if qid not in seen:
                    seen.append(qid)
                    if len(seen) > 500:
                        del seen[:-400]
            self._cache["last_activity"] = time.strftime("%Y-%m-%d %H:%M")
            self._dirty = True
            self._schedule_flush()

    def get_progress(self) -> dict:
        return self._cache.get("progress") or {}

    def recent_question_ids(self, subject: str) -> list[str]:
        rows = (self._cache.get("recent_session_ids") or {}).get(subject) or []
        return [str(item) for item in rows if item]

    def remember_session_ids(self, subject: str, ids: list) -> None:
        with _lock:
            recents = self._cache.setdefault("recent_session_ids", {})
            row = list(recents.get(subject) or [])
            for qid in ids or []:
                text = str(qid or "").strip()
                if text:
                    row.append(text)
            recents[subject] = row[-90:]
            self._dirty = True
            self._schedule_flush()

    def get_overall_stats(self) -> dict:
        progress = self.get_progress()
        total = sum(s.get("total", 0) for s in progress.values())
        correct = sum(s.get("correct", 0) for s in progress.values())
        time_sec = sum(s.get("time_sec", 0.0) for s in progress.values())
        acc = round(100 * correct / total, 1) if total else 0.0
        return {
            "total": total,
            "correct": correct,
            "accuracy": acc,
            "time_sec": round(time_sec, 1),
            "subjects_started": len(progress),
        }

    def get_mastery_by_subject(self) -> dict:
        """Returns subject mastery percentages for the dashboard."""
        mastery = {}
        for subject, stats in (self.get_progress() or {}).items():
            total = int(stats.get("total", 0) or 0)
            correct = int(stats.get("correct", 0) or 0)
            mastery[subject] = {
                "total": total,
                "correct": correct,
                "accuracy": round((100 * correct / total), 1) if total else 0.0,
            }
        return mastery

    def study_plan(self) -> dict:
        """תוכנית לאחור מתאריך המבחן: כמה שאלות ביום צריך כדי לכסות את החומר."""
        from core.config import DAILY_GOAL_TARGET, MEIMAD_SUBJECTS
        from core.loader import load_subject

        days = self.days_to_exam()
        progress = self.get_progress()
        total = done = 0
        for key in MEIMAD_SUBJECTS:
            bank = (load_subject(key) or {}).get("questions") or []
            total += len(bank)
            done += int((progress.get(key) or {}).get("total", 0) or 0)
        left = max(0, total - done)
        if not days or days <= 0 or left == 0:
            per_day = DAILY_GOAL_TARGET
        else:
            per_day = max(5, min(60, -(-left // days)))
        return {
            "days": days,
            "total": total,
            "done": min(done, total),
            "left": left,
            "per_day": per_day,
            "coverage": round(100 * min(done, total) / total) if total else 0,
        }

    def get_daily_goal(self) -> dict:
        """Daily learning objective based on sessions completed today."""
        from core.config import DAILY_GOAL_TARGET

        today = time.strftime("%Y-%m-%d")
        target = DAILY_GOAL_TARGET
        if self.get_exam_date().get("date"):
            try:
                target = self.study_plan()["per_day"]
            except Exception:
                target = DAILY_GOAL_TARGET
        completed = 0
        sessions = self.get_sessions() or []
        for item in sessions:
            session_date = (item.get("date") or "").split(" ")[0]
            if session_date == today:
                completed += int(item.get("total", 0) or 0)
        completion = min(100, int((completed / target) * 100)) if target else 0
        return {
            "target": target,
            "completed": completed,
            "completion": completion,
            "is_done": completed >= target,
        }

    def get_learning_snapshot(self) -> dict:
        mastery = self.get_mastery_by_subject()
        overall = self.get_overall_stats()
        weak_subjects = [
            subject
            for subject, info in sorted(
                mastery.items(),
                key=lambda x: (x[1].get("accuracy", 0), x[1].get("total", 0)),
            )
            if info.get("total", 0) > 0 and info.get("accuracy", 0) < 70
        ][:3]
        return {
            "overall": overall,
            "mastery": mastery,
            "weak_subjects": weak_subjects,
            "daily_goal": self.get_daily_goal(),
        }

    def award_points(self, points: int, activity: str) -> dict:
        """Give immediate feedback for even tiny actions: answers, streaks, lesson completion."""
        with _lock:
            rewards = self._cache.setdefault(
                "rewards",
                {
                    "points": 0,
                    "gems": 0,
                    "history": [],
                    "badges": [],
                },
            )
            points = max(int(points), 0)
            rewards["points"] += points
            rewards["gems"] = rewards["points"] // 100
            rewards["history"].append(
                {
                    "activity": activity,
                    "points": points,
                    "time": time.strftime("%Y-%m-%d %H:%M"),
                }
            )
            rewards["history"] = rewards["history"][-25:]

            if rewards["points"] >= 50 and "starter" not in rewards["badges"]:
                rewards["badges"].append("starter")
            if rewards["points"] >= 250 and "focus" not in rewards["badges"]:
                rewards["badges"].append("focus")

            self._dirty = True
            self._schedule_flush()
            return {
                "points": points,
                "total_points": rewards["points"],
                "gems": rewards["gems"],
                "badge": rewards["badges"][-1] if rewards["badges"] else "new",
            }

    def mark_lesson_complete(self, lesson_id: str) -> None:
        with _lock:
            done = self._cache.setdefault("completed_lessons", [])
            if lesson_id not in done:
                done.append(lesson_id)
                self._cache["completed_lessons"] = done[-400:]
                self._dirty = True
                self._schedule_flush()

    def is_lesson_complete(self, lesson_id: str) -> bool:
        return lesson_id in (self._cache.get("completed_lessons") or [])

    def add_xp(self, amount: int) -> dict:
        with _lock:
            xp = int(self._cache.get("xp", 0) or 0) + max(0, int(amount))
            self._cache["xp"] = xp
            level = 1 + xp // 100
            badges = self._cache.setdefault("achievements", [])
            if xp >= 100 and "xp100" not in badges:
                badges.append("xp100")
            self._dirty = True
            self._schedule_flush()
            return {"xp": xp, "level": level, "badges": badges}

    def can_take_final(self, subject: str) -> bool:
        from core.config import FINAL_EXAM_MIN_ACCURACY, FINAL_EXAM_MIN_QUESTIONS

        if self.get_pref("studio_unlock_gates"):
            return True
        stats = (self.get_progress() or {}).get(subject) or {}
        total = int(stats.get("total", 0) or 0)
        correct = int(stats.get("correct", 0) or 0)
        acc = round(100 * correct / total, 1) if total else 0
        return total >= FINAL_EXAM_MIN_QUESTIONS and acc >= FINAL_EXAM_MIN_ACCURACY

    def record_exam_official(self, subject: str, score: int, total: int) -> None:
        with _lock:
            exams = self._cache.setdefault("official_exams", [])
            exams.append(
                {
                    "subject": subject,
                    "score": score,
                    "total": total,
                    "percent": round(100 * score / total, 1) if total else 0,
                    "date": time.strftime("%Y-%m-%d %H:%M"),
                }
            )
            self._cache["official_exams"] = exams[-50:]
            self._dirty = True
            self._flush()

    def save_general_exam_report(self, report: dict) -> None:
        payload = dict(report or {})
        payload["date"] = payload.get("date") or time.strftime("%Y-%m-%d %H:%M")
        with _lock:
            self._cache["general_exam"] = payload
            history = self._cache.setdefault("general_exam_history", [])
            history.append(
                {
                    "date": payload["date"],
                    "score": payload.get("score"),
                    "total": payload.get("total"),
                    "percent": payload.get("percent"),
                    "scaled": payload.get("scaled"),
                    "grade": payload.get("grade"),
                    "level_he": payload.get("level_he"),
                }
            )
            self._cache["general_exam_history"] = history[-20:]
            self._dirty = True
            self._flush()

    def get_general_exam_report(self) -> dict | None:
        data = self._cache.get("general_exam")
        return dict(data) if isinstance(data, dict) else None

    def award_lesson_once(self, lesson_id: str) -> dict:
        with _lock:
            opened = self._cache.setdefault("opened_lessons", [])
            if lesson_id in opened:
                return {"points": 0, "total_points": (self._cache.get("rewards") or {}).get("points", 0)}
            opened.append(lesson_id)
            self._cache["opened_lessons"] = opened[-80:]
            self._dirty = True
        return self.award_points(10, "lesson_open")

    def get_reward_summary(self) -> dict:
        rewards = self._cache.get("rewards") or {
            "points": 0,
            "gems": 0,
            "history": [],
            "badges": [],
        }
        return {
            "points": int(rewards.get("points", 0) or 0),
            "gems": int(rewards.get("gems", 0) or 0),
            "badges": rewards.get("badges", []),
            "recent": rewards.get("history", [])[-3:],
        }

    def record_focus_event(self, event_type: str, payload: dict | None = None) -> dict:
        """Tracks attention dips and converts them into a suggestion for rest or lighter activity."""
        with _lock:
            focus = self._cache.setdefault(
                "focus",
                {
                    "history": [],
                    "status": "stable",
                    "suggestion": "המשך עם תרגול קצר ורגוע",
                },
            )
            event_count = int((payload or {}).get("count", 1) or 1)
            event_data = {
                "event_type": event_type,
                "count": event_count,
                "time": time.strftime("%Y-%m-%d %H:%M"),
                "payload": payload or {},
            }
            focus.setdefault("history", []).append(event_data)
            focus["history"] = focus["history"][-20:]

            if event_type == "rapid_navigation" and event_count >= 3:
                focus["status"] = "needs_break"
                focus["suggestion"] = (
                    "הפסקה של 3 דקות + מעבר לתרגול קצר יותר, כדי לשמור על ריכוז"
                )
            elif event_type == "focus_mode_on":
                focus["status"] = "focus_mode"
                focus["suggestion"] = "מצב מיקוד פעיל, חשוף רק את התוכן המרכזי"
            elif event_type == "answer_correct":
                focus["status"] = "stable"
                focus["suggestion"] = "התקדמת יפה, כדאי להמשיך עם עוד 3 דקות"
            else:
                focus["status"] = "stable"
                focus["suggestion"] = "המשך עם תרגול קצר ורגוע"

            self._dirty = True
            self._schedule_flush()
            return {
                "status": focus["status"],
                "suggestion": focus["suggestion"],
                "count": event_count,
            }

    def get_focus_summary(self) -> dict:
        focus = self._cache.get("focus") or {
            "status": "stable",
            "suggestion": "המשך עם תרגול קצר ורגוע",
        }
        return {
            "status": focus.get("status", "stable"),
            "suggestion": focus.get("suggestion", "המשך עם תרגול קצר ורגוע"),
            "history": (focus.get("history") or [])[-5:],
        }

    def generate_daily_practice_plan(
        self, subjects: list[str] | None = None, weak_subjects: list[str] | None = None
    ) -> list[dict]:
        """Build a short, adaptive plan for the day.
        Each task is: {id, subject, title, mode, difficulty, accuracy, completed}
        """
        if subjects is None:
            progress = self.get_progress()
            subjects = list(progress.keys()) or []

        if not subjects:
            return []

        from core.config import subject_key as normalize_subject

        weak = {normalize_subject(item) for item in ((weak_subjects or []) or []) if item}
        progress = self.get_progress()
        from core.adaptive_engine import LEVEL_HE, AdaptiveEngine

        engine = AdaptiveEngine(self)
        tasks = []
        for subject in subjects:
            stats = progress.get(subject, {})
            total = int(stats.get("total", 0) or 0)
            correct = int(stats.get("correct", 0) or 0)
            accuracy = round((100 * correct / total), 1) if total else 0.0
            level = engine.level_of(subject)
            tasks.append(
                {
                    "id": f"daily_{subject}_{int(time.time())}",
                    "subject": subject,
                    "title": f"תרגול {subject}",
                    "mode": "practice" if subject in weak else "lessons",
                    "difficulty": level,
                    "level_he": LEVEL_HE.get(level, "מתחיל"),
                    "accuracy": accuracy,
                    "completed": False,
                }
            )

        tasks = sorted(
            tasks, key=lambda t: (0 if t["subject"] in weak else 1, t["accuracy"])
        )
        plan = tasks[:3]
        for index, task in enumerate(plan):
            if index == 0 and task["mode"] == "lessons":
                task["mode"] = "practice"
            task["title"] = {
                "practice": "תרגול ממוקד, חיזוק בעיות",
                "lessons": "שיעור קצר + חזרה",
            }.get(task["mode"], "תרגול יומי")
            task["id"] = f"daily_{task['subject']}_{index + 1}"

        self.set("daily_practice", {"date": time.strftime("%Y-%m-%d"), "tasks": plan})
        return plan

    def get_daily_practice_plan(self) -> list[dict]:
        today = time.strftime("%Y-%m-%d")
        plan_data = self._cache.get("daily_practice") or {}
        if plan_data.get("date") == today and plan_data.get("tasks"):
            return plan_data["tasks"]

        from core.config import subject_key as normalize_subject

        diagnostic = self.get_diagnostic() or {}
        weak_subjects = [normalize_subject(item) for item in (diagnostic.get("weak_topics", []) or [])]
        subjects = list(self.get_progress().keys()) or []
        if not subjects:
            from core.config import HOME_SUBJECTS

            subjects = list(HOME_SUBJECTS)
        plan = self.generate_daily_practice_plan(subjects, weak_subjects)
        self.set("daily_practice", {"date": today, "tasks": plan})
        return plan

    def mark_daily_task_complete(self, task_id: str) -> bool:
        plan_data = self._cache.get("daily_practice") or {}
        tasks = plan_data.get("tasks") or []
        for task in tasks:
            if task.get("id") == task_id:
                task["completed"] = True
                self._dirty = True
                self._flush()
                return True
        return False

    # ---------- מבחנים/תרגולים שהושלמו ----------
    def record_session(self, subject: str, mode: str, score: int, total: int) -> None:
        with _lock:
            sessions: list = self._cache.setdefault("sessions", [])

            # חשב streak: סשן מוצלח = דיוק >= 70%
            is_success = (score / total >= 0.7) if total > 0 else False

            sessions.append(
                {
                    "subject": subject,
                    "mode": mode,
                    "score": score,
                    "total": total,
                    "accuracy": round(100 * score / total, 1) if total else 0,
                    "success": is_success,
                    "date": time.strftime("%Y-%m-%d %H:%M"),
                }
            )

            # Update streak
            streak_info = self._cache.setdefault(
                "streak", {"current": 0, "best": 0, "last_date": None}
            )
            today = time.strftime("%Y-%m-%d")
            if streak_info.get("last_date") == today:
                # אותו היום - בדוק אם הוסיפו סשן מוצלח
                if is_success:
                    if not streak_info.get("updated_today"):
                        streak_info["current"] += 1
                        streak_info["updated_today"] = True
            else:
                # יום חדש
                if is_success:
                    streak_info["current"] += 1
                    streak_info["last_date"] = today
                    streak_info["updated_today"] = True
                else:
                    streak_info["current"] = 0
                    streak_info["last_date"] = today
                    streak_info["updated_today"] = False

            streak_info["best"] = max(streak_info["best"], streak_info["current"])

            self._cache["sessions"] = sessions[-100:]  # מגביל גודל
            self._dirty = True
            self._flush()

    def get_sessions(self) -> list:
        return self._cache.get("sessions") or []

    def get_streak(self) -> dict:
        """Get current and best streak info"""
        streak_info = self._cache.get("streak") or {"current": 0, "best": 0}
        return {
            "current": streak_info.get("current", 0),
            "best": streak_info.get("best", 0),
        }

    def reset_all(self) -> None:
        with _lock:
            self._cache = {}
            self._flush()

    # ---------- מחברת טעויות ----------
    def record_mistake(self, question: dict, selected_index: int) -> None:
        """שומר שאלה שנענתה לא נכון, כדי שאפשר יהיה לחזור עליה."""
        qid = str((question or {}).get("id") or "")
        if not qid:
            return
        with _lock:
            book: dict = self._cache.setdefault("mistakes", {})
            entry = book.get(qid) or {}
            book[qid] = {
                "id": qid,
                "subject": question.get("subject", ""),
                "topic": question.get("topic", ""),
                "question": question.get("question", ""),
                "options": question.get("options") or [],
                "answer": question.get("answer"),
                "correct_answer": question.get("correct_answer", ""),
                "explanation": question.get("explanation", ""),
                "selected": selected_index,
                "times_wrong": int(entry.get("times_wrong", 0)) + 1,
                "last": time.strftime("%Y-%m-%d %H:%M"),
                "resolved": False,
            }
            if len(book) > 400:
                oldest = sorted(book.values(), key=lambda x: x.get("last", ""))[: len(book) - 400]
                for item in oldest:
                    book.pop(item.get("id", ""), None)
            self._dirty = True
            self._schedule_flush()

    def clear_mistake(self, question_id: str) -> None:
        """נענתה נכון, מסמן שנפתרה."""
        qid = str(question_id or "")
        with _lock:
            book: dict = self._cache.get("mistakes") or {}
            if qid in book:
                book[qid]["resolved"] = True
                book[qid]["last"] = time.strftime("%Y-%m-%d %H:%M")
                self._dirty = True
                self._schedule_flush()

    def get_mistakes(self, subject: str | None = None, include_resolved: bool = False) -> list:
        book: dict = self._cache.get("mistakes") or {}
        items = list(book.values())
        if not include_resolved:
            items = [item for item in items if not item.get("resolved")]
        if subject:
            items = [item for item in items if item.get("subject") == subject]
        return sorted(items, key=lambda x: (-int(x.get("times_wrong", 0)), x.get("last", "")))

    def forget_mistakes(self) -> None:
        self.set("mistakes", {})

    # ---------- דיווח על שאלות ----------
    def report_question(self, question: dict, reason: str) -> None:
        """שאלה שנראית שגויה. נשמרת עם ההקשר המלא כדי שאפשר יהיה לתקן אותה."""
        qid = str((question or {}).get("id") or "")
        if not qid:
            return
        with _lock:
            reports: dict = self._cache.setdefault("reports", {})
            reports[qid] = {
                "id": qid,
                "subject": question.get("subject", ""),
                "topic": question.get("topic", ""),
                "question": question.get("question", ""),
                "options": question.get("options") or [],
                "correct_answer": question.get("correct_answer", ""),
                "reason": reason,
                "when": time.strftime("%Y-%m-%d %H:%M"),
            }
            self._dirty = True
            self._schedule_flush()

    def get_reports(self) -> list:
        return sorted((self._cache.get("reports") or {}).values(), key=lambda x: x.get("when", ""), reverse=True)

    def reported_ids(self) -> set:
        return set((self._cache.get("reports") or {}).keys())

    def unreport_question(self, question_id: str) -> None:
        with _lock:
            reports: dict = self._cache.get("reports") or {}
            if str(question_id) in reports:
                reports.pop(str(question_id), None)
                self._dirty = True
                self._schedule_flush()

    def clear_reports(self) -> None:
        self.set("reports", {})

    # ---------- תאריך מבחן ----------
    def set_exam_date(self, iso_date: str, label: str = "") -> None:
        self.set("exam_target", {"date": iso_date, "label": label})

    def get_exam_date(self) -> dict:
        return self._cache.get("exam_target") or {}

    def days_to_exam(self) -> int | None:
        target = self.get_exam_date().get("date")
        if not target:
            return None
        try:
            import datetime

            day = datetime.date.fromisoformat(str(target))
            return (day - datetime.date.today()).days
        except Exception:
            return None

    # ---------- העדפות ----------
    def get_pref(self, key: str, default: Any = None) -> Any:
        return (self._cache.get("prefs") or {}).get(key, default)

    def set_pref(self, key: str, value: Any) -> None:
        with _lock:
            prefs = self._cache.setdefault("prefs", {})
            prefs[key] = value
            self._dirty = True
            self._schedule_flush()

    # ---------- גיבוי ----------
    def export_bundle(self) -> dict:
        return {
            "app": "StudyApp",
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "profile": self._cache,
        }

    def import_bundle(self, bundle: dict) -> bool:
        payload = (bundle or {}).get("profile")
        if not isinstance(payload, dict) or not payload:
            return False
        with _lock:
            self._cache = payload
            self._dirty = True
            self._flush()
        return True
