import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.session_state import SessionStateManager


class SessionRecoveryTests(unittest.TestCase):
    def test_session_state_manager_keeps_backup_and_restores_latest_valid_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "session_state.json")
            manager = SessionStateManager(path=path)
            first = {
                "questions": [{"question": "Q1", "options": ["A", "B"], "answer": 0, "topic": "math"}],
                "current_index": 0,
                "mode": "practice",
                "subject_key": "math",
                "score": 0,
                "user_answers": [],
            }
            second = {
                "questions": [{"question": "Q1", "options": ["A", "B"], "answer": 0, "topic": "math"}, {"question": "Q2", "options": ["A", "B"], "answer": 1, "topic": "math"}],
                "current_index": 1,
                "mode": "exam",
                "subject_key": "math",
                "score": 1,
                "user_answers": [{"question_id": "q1", "selected": 0, "correct": True}],
            }

            manager.save(first)
            manager.save(second)
            self.assertTrue(os.path.exists(manager.backup_path))

            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{not valid json")

            restored = manager.load()
            self.assertEqual(restored["mode"], "exam")
            self.assertEqual(restored["current_index"], 1)
            self.assertEqual(len(restored["questions"]), 2)

    def test_session_state_manager_rejects_invalid_payloads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "session_state.json")
            manager = SessionStateManager(path=path)
            self.assertFalse(manager.save({"questions": "not-a-list"}))
            self.assertEqual(manager.load(), {})


if __name__ == "__main__":
    unittest.main()
