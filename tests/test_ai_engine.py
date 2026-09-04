"""בדיקות מנוע AI מערכתי — זיכרון, שומר בחינה, קצב, כוונות צ'אט."""
from __future__ import annotations

import unittest
from unittest import mock


class FakeStorage:
    def __init__(self):
        self.prefs = {}

    def get_pref(self, key, default=None):
        return self.prefs.get(key, default)

    def set_pref(self, key, value):
        self.prefs[key] = value


class FakeAdaptive:
    def weak_topics(self, subject, limit=3):
        return ["שברים", "טריגונומטריה"][:limit]

    def mistake_patterns(self, subject):
        return [{"kind": "rush", "title": "rush", "message": "מהר מדי"}]

    def struggling(self, subject):
        return {"severity": "topic", "accuracy": 40, "total": 8, "topics": ["שברים"]}

    def action_plan(self, subject):
        return {"steps": ["חיזוק שברים"], "readiness": {"weak_topics": ["שברים"]}}

    def snapshot(self, subject):
        return {"recent_total": 10, "recent_accuracy": 40, "weak_topics": ["שברים"]}

    def topic_scores(self, subject):
        return []

    def record_for(self, subject):
        return {"recent": []}


class AIEngineTests(unittest.TestCase):
    def setUp(self):
        from core.ai_engine import AIEngine

        self.storage = FakeStorage()
        self.engine = AIEngine(self.storage, FakeAdaptive())

    def test_exam_guard_locks_helpers(self):
        feat = self.engine.features_for_mode("final")
        self.assertTrue(feat["exam_locked"])
        self.assertFalse(feat["paraphrase"])
        self.assertFalse(feat["tutor"])
        practice = self.engine.features_for_mode("practice")
        self.assertTrue(practice["paraphrase"])

    def test_memory_roundtrip(self):
        self.engine.remember(subject="math", topic="שברים", text="הסברנו העברת אגפים")
        rows = self.engine.recall("math", "שברים")
        self.assertTrue(rows)
        self.assertIn("אגפים", rows[0]["text"])

    def test_pacing_shortens_on_rush(self):
        pace = self.engine.pacing("math")
        self.assertTrue(pace["shorten"])
        self.assertIsNotNone(pace["count_cap"])
        self.assertEqual(self.engine.adjust_count("math", "practice", 16), pace["count_cap"])

    def test_classify_rush(self):
        self.assertEqual(
            self.engine.classify_error({"question": "2+2"}, time_sec=1.0, is_correct=False),
            "rush",
        )

    def test_hint_ladder_levels(self):
        q = {"question": "מהו 2+2?", "topic": "חשבון", "subject": "math"}
        h1 = self.engine.hint_ladder(q, 1, "math")
        h3 = self.engine.hint_ladder(q, 3, "math")
        self.assertIn("כיוון", h1)
        self.assertIn("מלכודת", h3)

    def test_chat_practice_intent(self):
        out = self.engine.assistant_chat("התאם לי תרגול לרמה שלי", use_llm=False)
        self.assertEqual(out.get("action"), "start_practice")
        self.assertTrue(out.get("subject"))
        self.assertTrue(out.get("reply"))

    def test_chat_weak_intent(self):
        out = self.engine.assistant_chat("איפה אני חלש?", use_llm=False)
        self.assertIn("reply", out)
        self.assertTrue(out["reply"])

    def test_sidebar_nav_includes_ai(self):
        from ui.widgets import Sidebar

        keys = [k for k, _ in Sidebar.NAV_KEYS]
        self.assertIn("ai_assistant", keys)
        self.assertLess(keys.index("ai_assistant"), keys.index("settings"))

    def test_on_answer_stores_error_memory(self):
        self.engine.on_answer(
            {"subject": "math", "topic": "שברים", "question": "1/2"},
            is_correct=False,
            time_sec=1.2,
            subject="math",
            mode="practice",
        )
        self.assertTrue(self.engine.memory_list())


if __name__ == "__main__":
    unittest.main()
