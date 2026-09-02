import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import (
    ALL_SUBJECTS,
    COMING_SOON_SUBJECTS,
    ELECTIVE_SUBJECTS,
    HOME_SUBJECTS,
    SUBJECTS,
    is_coming_soon,
    subject_key,
)
from core.curriculum_arabic import build_arabic
from core.curriculum_first_aid import build_first_aid
from core.general_exam import SUBJECT_COUNTS
from core.loader import load_subject


class ElectiveSubjectsTests(unittest.TestCase):
    def test_electives_are_not_core_exam_subjects(self):
        self.assertEqual(ELECTIVE_SUBJECTS, ["arabic", "first_aid"])
        for key in ELECTIVE_SUBJECTS:
            self.assertIn(key, SUBJECTS)
            self.assertIn(key, ALL_SUBJECTS)
            self.assertNotIn(key, HOME_SUBJECTS)
            self.assertNotIn(key, SUBJECT_COUNTS)
        self.assertEqual(subject_key("ערבית"), "arabic")
        self.assertEqual(subject_key("עזרה ראשונה"), "first_aid")
        self.assertEqual(COMING_SOON_SUBJECTS, frozenset({"arabic", "first_aid"}))
        for key in ELECTIVE_SUBJECTS:
            self.assertTrue(is_coming_soon(key), key)
        self.assertFalse(is_coming_soon("hebrew"))

    def test_arabic_bank_is_everyday_and_leveled(self):
        bank = build_arabic()
        self.assertGreaterEqual(len(bank["lessons"]), 10)
        self.assertGreaterEqual(len(bank["questions"]), 90)
        diffs = [q.get("difficulty") for q in bank["questions"]]
        self.assertGreaterEqual(diffs.count("Medium"), 16)
        self.assertGreaterEqual(diffs.count("Hard"), 16)
        cats = " ".join(l.get("category") or "" for l in bank["lessons"])
        self.assertIn("בינוני", cats)
        blob = " ".join(l.get("content") or "" for l in bank["lessons"])
        self.assertIn("السلام", blob)
        self.assertIn("شكرا", blob)

    def test_first_aid_bank_is_wide_and_has_disclaimer(self):
        bank = build_first_aid()
        self.assertGreaterEqual(len(bank["lessons"]), 36)
        self.assertGreaterEqual(len(bank["questions"]), 220)
        diffs = [q.get("difficulty") for q in bank["questions"]]
        self.assertGreaterEqual(diffs.count("Medium"), 16)
        self.assertGreaterEqual(diffs.count("Hard"), 16)
        titles = " ".join(l.get("title") or "" for l in bank["lessons"])
        for marker in ("החייאה", "AED", "חנק", "דימום", "שבץ", "אנפילקסיס", "נלוקסון"):
            self.assertIn(marker, titles, marker)
        first = bank["lessons"][0]["content"]
        self.assertIn("לימוד", first)
        self.assertIn("101", first)
        self.assertTrue(any("בינוני" in (l.get("category") or "") for l in bank["lessons"]))

    def test_serialized_elective_files_load(self):
        for key in ELECTIVE_SUBJECTS:
            data = load_subject(key) or {}
            self.assertGreaterEqual(len(data.get("lessons") or []), 3, key)
            self.assertGreaterEqual(len(data.get("questions") or []), 36, key)


if __name__ == "__main__":
    unittest.main()
