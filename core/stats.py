from __future__ import annotations

import json
import os
from datetime import datetime

HISTORY_LIMIT = 500
SAVE_EVERY = 10


class DatabaseManager:
    """Stores answer history and per-topic stats in a local JSON file."""

    def __init__(self, db_path=None):
        if db_path is None:
            from core.profiles import current_files, ensure_migrated

            ensure_migrated()
            db_path = current_files()["user_stats"]
        self.db_path = db_path
        self._cache = {"history": [], "topic_stats": {}}
        self._dirty = False
        self._pending = 0
        self._ensure_db_exists()
        self._load_data()

    def _ensure_db_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            initial_data = {"history": [], "topic_stats": {}}
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(initial_data, handle, ensure_ascii=False, indent=2)

    def _load_data(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as handle:
                self._cache = json.load(handle)
        except Exception:
            self._cache = {"history": [], "topic_stats": {}}
        self._dirty = False

    def _save_data(self):
        folder = os.path.dirname(self.db_path)
        os.makedirs(folder, exist_ok=True)
        tmp = self.db_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self._cache, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, self.db_path)
        self._dirty = False

    def log_answer(self, topic, difficulty, is_correct, time_taken_sec, subject=None):
        data = self._cache
        if not data.get("history") and not data.get("topic_stats"):
            self._load_data()
            data = self._cache

        entry = {
            "topic": topic,
            "difficulty": difficulty,
            "correct": is_correct,
            "time_sec": round(time_taken_sec, 2),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if subject:
            entry["subject"] = str(subject)
        history = data.setdefault("history", [])
        history.append(entry)
        if len(history) > HISTORY_LIMIT:
            data["history"] = history[-HISTORY_LIMIT:]

        topic_stats = data.setdefault("topic_stats", {})
        if topic not in topic_stats:
            topic_stats[topic] = {"total_questions": 0, "correct_answers": 0}

        topic_stats[topic]["total_questions"] += 1
        if is_correct:
            topic_stats[topic]["correct_answers"] += 1

        self._dirty = True
        # כתיבה של כל הקובץ אחרי כל שאלה הופכת את התרגול לאיטי יותר ויותר.
        self._pending += 1
        if self._pending >= SAVE_EVERY:
            self._pending = 0
            self._save_data()

    def close(self):
        if self._dirty:
            self._save_data()
        self._pending = 0
