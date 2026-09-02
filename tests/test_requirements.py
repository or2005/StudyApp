import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.analytics import AnalyticsEngine
from core.diagnostic import EXAM_LENGTH, build_diagnostic, compute_level
from core.storage import UserStorage


class StudyAppRequirementsTests(unittest.TestCase):
    def test_diagnostic_has_exactly_20_questions(self):
        questions = build_diagnostic()
        self.assertEqual(len(questions), EXAM_LENGTH)
        self.assertTrue(all("question" in q for q in questions))

    def test_diagnostic_bank_tags_match_real_subjects(self):
        from core.config import SUBJECTS
        from core.diagnostic import DIAGNOSTIC_BANK

        keys = {row[0] for row in DIAGNOSTIC_BANK}
        self.assertTrue(keys <= set(SUBJECTS), keys - set(SUBJECTS))
        self.assertIn("math", keys)
        self.assertIn("hebrew", keys)
        self.assertIn("geography", keys)
        for subject, topic, question, _opts, _answer, _diff in DIAGNOSTIC_BANK:
            blob = f"{topic} {question}"
            if any(token in blob for token in ("7 + 8", "6 × 7", "25%", "1/2 + 1/4", "3x + 6", "2, 4, 6, 8")):
                self.assertEqual(subject, "math", blob)

    def test_storage_persists_student_and_diagnostic_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = os.path.join(temp_dir, "user_profile.json")
            storage = UserStorage(path=profile_path)
            storage.save_student("אור דדשב", 17, "123456789")
            storage.save_diagnostic(
                15,
                EXAM_LENGTH,
                "intermediate",
                [{"subject": "math", "correct": True}],
                recommendations=["תרגל חזק יותר במתמטיקה"],
                weak_topics=["math"],
            )

            self.assertEqual(storage.get_student()["name"], "אור דדשב")
            diagnostic = storage.get_diagnostic()
            self.assertEqual(diagnostic["level"], "intermediate")
            self.assertEqual(diagnostic["weak_topics"], ["math"])
            self.assertIn("תרגל חזק יותר במתמטיקה", diagnostic["recommendations"])

    def test_level_computation_returns_valid_recommendations(self):
        result = compute_level(16)
        self.assertIn("level", result)
        self.assertIn("recommendations", result)
        self.assertTrue(len(result["recommendations"]) >= 3)

    def test_weak_topics_are_subject_keys(self):
        answers = [
            {"subject": "math", "correct": False},
            {"subject": "math", "correct": False},
            {"subject": "english", "correct": False},
            {"subject": "english", "correct": True},
        ]
        result = compute_level(10, answers=answers)
        self.assertTrue(all(topic in {"math", "english"} or topic.isascii() for topic in result["weak_topics"]))
        self.assertIn("math", result["weak_topics"])

    def test_analytics_detects_performance_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "analytics_stats.json")
            with open(db_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"history": ['
                    '{"topic": "math", "correct": true, "time_sec": 12},'
                    '{"topic": "math", "correct": false, "time_sec": 18},'
                    '{"topic": "english", "correct": true, "time_sec": 10}'
                    '], "topic_stats": {"math": {"total_questions": 2, "correct_answers": 1}, "english": {"total_questions": 1, "correct_answers": 1}}}'
                )
            analytics = AnalyticsEngine(db_path=db_path)
            overview = analytics.get_overview()
            summary = analytics.get_summary()
            self.assertTrue(overview["has_data"])
            self.assertGreater(overview["accuracy"], 0)
            self.assertIn("דוח ביצועים כולל", summary)
            self.assertTrue(len(analytics.get_recommendations()) >= 1)
            self.assertIn("trend", overview)
            math_row = next(item for item in overview["subject_breakdown"] if item["topic"] == "math")
            self.assertIn("confidence", math_row)
            self.assertLessEqual(math_row["confidence"], math_row["accuracy"])
            card = analytics.get_insight_card()
            self.assertTrue(card["has_data"])
            self.assertTrue(card["recommendation"])

    def test_weekly_parent_report_includes_analyst_note(self):
        from core.parent_report import build_report

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = UserStorage(path=os.path.join(temp_dir, "user_profile.json"))
            storage.save_student("נועה", 16, "")
            report = build_report(storage, insight="לחזק לשון השבוע.")
            self.assertIn("נועה", report["text"])
            self.assertIn("לחזק לשון השבוע.", report["text"])
            self.assertIn("המלצת האנליסט", report["html"])
            self.assertTrue(str(report["filename"]).endswith(".html"))

    def test_daily_practice_plan_is_created_and_marked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = UserStorage(path=os.path.join(temp_dir, "user_profile.json"))
            storage.set(
                "progress",
                {
                    "math": {"total": 5, "correct": 2, "time_sec": 120.0},
                    "english": {"total": 5, "correct": 5, "time_sec": 80.0},
                },
            )
            plan = storage.generate_daily_practice_plan(["math", "english"], ["math"])

            self.assertTrue(plan)
            self.assertTrue(any(task["subject"] == "math" for task in plan))
            self.assertEqual(plan[0]["mode"], "practice")

            task = plan[0]
            storage.mark_daily_task_complete(task["id"])
            updated = storage.get_daily_practice_plan()
            self.assertTrue(updated[0]["completed"])

    def test_rewards_and_focus_state_are_generated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = UserStorage(path=os.path.join(temp_dir, "user_profile.json"))
            storage.record_focus_event("rapid_navigation", {"count": 4})
            rewards = storage.award_points(12, "lesson_complete")
            focus = storage.get_focus_summary()

            self.assertGreater(rewards["points"], 0)
            self.assertGreaterEqual(rewards["gems"], 0)
            self.assertIn("status", focus)
            self.assertIn("suggestion", focus)


if __name__ == "__main__":
    unittest.main()
