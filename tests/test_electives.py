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
from core.general_exam import SUBJECT_COUNTS
from core.loader import load_subject


class ElectiveSubjectsTests(unittest.TestCase):
    def test_electives_are_not_core_exam_subjects(self):
        self.assertEqual(ELECTIVE_SUBJECTS, ["electricity", "electronics"])
        for key in ELECTIVE_SUBJECTS:
            self.assertIn(key, SUBJECTS)
            self.assertIn(key, ALL_SUBJECTS)
            self.assertNotIn(key, HOME_SUBJECTS)
            self.assertNotIn(key, SUBJECT_COUNTS)
            self.assertFalse(is_coming_soon(key), key)
        self.assertEqual(subject_key("חשמל"), "electricity")
        self.assertEqual(subject_key("אלקטרוניקה"), "electronics")
        self.assertEqual(COMING_SOON_SUBJECTS, frozenset())
        self.assertNotIn("arabic", SUBJECTS)
        self.assertNotIn("first_aid", SUBJECTS)
        self.assertNotIn("driving_theory", SUBJECTS)
        self.assertNotIn("driving_theory", ALL_SUBJECTS)
        self.assertFalse(is_coming_soon("hebrew"))

    def test_serialized_elective_files_load(self):
        for key in ELECTIVE_SUBJECTS:
            data = load_subject(key) or {}
            self.assertGreaterEqual(len(data.get("lessons") or []), 3, key)
            self.assertGreaterEqual(len(data.get("questions") or []), 36, key)
        self.assertIsNone(load_subject("driving_theory"))

    def test_removed_banks_are_gone(self):
        self.assertIsNone(load_subject("arabic"))
        self.assertIsNone(load_subject("first_aid"))


if __name__ == "__main__":
    unittest.main()
