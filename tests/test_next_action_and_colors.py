import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import HOME_SUBJECTS, SUBJECTS
from core.next_action import pick_next_action
from core.theme import apply_mode, subject_accent


class NextActionTests(unittest.TestCase):
    def test_resume_does_not_block_home(self):
        nxt = pick_next_action(has_saved=True, due_now=9, mistakes=4, weak_keys=["math"])
        self.assertEqual(nxt["id"], "review")
        self.assertNotEqual(nxt.get("title"), "המשך מאיפה שעצרת")

    def test_review_before_mistakes(self):
        nxt = pick_next_action(has_saved=False, due_now=7, mistakes=4, review_batch=20)
        self.assertEqual(nxt["id"], "review")
        self.assertIn("7", nxt["title"])

    def test_weak_subject_label(self):
        nxt = pick_next_action(has_saved=False, due_now=0, mistakes=0, weak_keys=["hebrew"])
        self.assertEqual(nxt["id"], "weak")
        self.assertIn("לשון", nxt["title"])
        self.assertEqual(nxt["subject"], "hebrew")

    def test_fallback_subjects(self):
        nxt = pick_next_action(has_saved=False, due_now=0, mistakes=0)
        self.assertEqual(nxt["id"], "subjects")


class SubjectColorTests(unittest.TestCase):
    def test_every_home_subject_has_its_own_color(self):
        apply_mode("Light")
        colors = [subject_accent(key) for key in HOME_SUBJECTS]
        self.assertEqual(len(colors), len(set(colors)), colors)
        stored = [SUBJECTS[key]["color"] for key in HOME_SUBJECTS]
        self.assertEqual(len(stored), len(set(stored)), stored)

    def test_dark_accents_stay_distinct(self):
        apply_mode("Dark")
        colors = [subject_accent(key) for key in HOME_SUBJECTS]
        self.assertEqual(len(colors), len(set(colors)), colors)
        apply_mode("Light")


if __name__ == "__main__":
    unittest.main()
