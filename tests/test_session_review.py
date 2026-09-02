import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.session_review import session_weak_topics, subject_topic_catalog


class SessionWeakTopicsTests(unittest.TestCase):
    def test_ranks_missed_topics_and_ignores_perfect_ones(self):
        answers = [
            {"topic": "שורשים", "correct": False},
            {"topic": "שורשים", "correct": False},
            {"topic": "שורשים", "correct": True},
            {"topic": "פיסוק", "correct": False},
            {"topic": "כתיב", "correct": True},
            {"topic": "כתיב", "correct": True},
        ]
        weak = session_weak_topics(answers)
        names = [row["topic"] for row in weak]
        self.assertEqual(names[0], "פיסוק")
        self.assertIn("שורשים", names)
        self.assertNotIn("כתיב", names)
        self.assertEqual(weak[0]["missed"], 1)
        self.assertEqual(weak[0]["accuracy"], 0)

    def test_limits_to_three(self):
        answers = []
        for topic in ("א", "ב", "ג", "ד"):
            answers.append({"topic": topic, "correct": False})
        weak = session_weak_topics(answers, limit=3)
        self.assertEqual(len(weak), 3)

    def test_empty_when_all_correct(self):
        self.assertEqual(session_weak_topics([{"topic": "כתיב", "correct": True}]), [])


class TopicCatalogTests(unittest.TestCase):
    def test_counts_practice_and_compose(self):
        data = {
            "topics": [{"topic": "שורשים"}, {"topic": "פיסוק"}],
            "questions": [
                {"topic": "שורשים"},
                {"topic": "שורשים"},
                {"topic": "פיסוק"},
            ],
        }
        compose = [{"topic": "שורשים"}, {"topic": "כתיב"}]
        rows = {item["name"]: item for item in subject_topic_catalog(data, compose)}
        self.assertEqual(rows["שורשים"]["practice"], 2)
        self.assertEqual(rows["שורשים"]["compose"], 1)
        self.assertEqual(rows["פיסוק"]["practice"], 1)
        self.assertEqual(rows["כתיב"]["compose"], 1)
        self.assertEqual(rows["כתיב"]["practice"], 0)


if __name__ == "__main__":
    unittest.main()
