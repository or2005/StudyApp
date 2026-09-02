import os
import random
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import HOME_SUBJECTS
from core.general_exam import (
    GENERAL_EXAM_SIZE,
    SUBJECT_COUNTS,
    build_general_exam,
    build_report,
    can_take_general_exam,
    coverage_for_subject,
    letter_grade,
    scaled_score,
    unlock_progress,
)
from core.loader import load_subject


class GeneralExamTests(unittest.TestCase):
    def test_counts_sum_to_fifty(self):
        self.assertEqual(sum(SUBJECT_COUNTS.values()), GENERAL_EXAM_SIZE)
        self.assertEqual(set(SUBJECT_COUNTS), set(HOME_SUBJECTS))

    def test_build_exam_covers_all_subjects(self):
        questions = build_general_exam(load_subject, rng=random.Random(7))
        self.assertEqual(len(questions), GENERAL_EXAM_SIZE)
        subjects = {q.get("subject") for q in questions}
        for key in HOME_SUBJECTS:
            self.assertIn(key, subjects, f"missing {key}")
        ids = [q.get("id") for q in questions]
        self.assertEqual(len(ids), len(set(ids)))
        for q in questions:
            self.assertEqual(len(q.get("options") or []), 4, q.get("id"))
            self.assertTrue(q.get("letter_options"))

    def test_scaled_score_and_grades(self):
        self.assertEqual(scaled_score(0, 50), 200)
        self.assertEqual(scaled_score(50, 50), 800)
        self.assertEqual(letter_grade(92), "A")
        self.assertEqual(letter_grade(50), "F")

    def test_report_lists_weak_subjects_and_plan(self):
        answers = []
        for i, key in enumerate(HOME_SUBJECTS):
            answers.append(
                {
                    "subject": key,
                    "topic": f"נושא-{key}",
                    "correct": key in {"hebrew", "english", "math"},
                    "time_sec": 20,
                }
            )
        # inflate civics failures
        for _ in range(5):
            answers.append({"subject": "civics", "topic": "זכויות", "correct": False, "time_sec": 12})
            answers.append({"subject": "history", "topic": "השואה", "correct": False, "time_sec": 10})
        report = build_report(answers, total=len(answers))
        self.assertIn("percent", report)
        self.assertTrue(report["plan"])
        self.assertTrue(report["recommendations"])
        self.assertTrue(report["narrative"])
        names = [row["key"] for row in report["subjects"]]
        self.assertEqual(names, list(HOME_SUBJECTS))
        self.assertTrue({"civics", "history"} & set(report["weak_subjects"]))

    def test_unlock_requires_half_coverage_in_every_subject(self):
        tmp = tempfile.mkdtemp(prefix="studyapp-gen-")
        os.environ["LOCALAPPDATA"] = tmp
        os.environ["APPDATA"] = tmp
        for module in [m for m in list(sys.modules) if m.startswith("core.storage")]:
            del sys.modules[module]
        from core.storage import UserStorage

        storage = UserStorage()
        self.assertFalse(can_take_general_exam(storage))
        for key in HOME_SUBJECTS[:-1]:
            for i in range(20):
                storage.record_answer(key, "t", True, 1.0, question_id=f"{key}-{i}")
        self.assertFalse(can_take_general_exam(storage))
        last = HOME_SUBJECTS[-1]
        for i in range(20):
            storage.record_answer(last, "t", True, 1.0, question_id=f"{last}-{i}")
        self.assertTrue(can_take_general_exam(storage))
        status = unlock_progress(storage)
        self.assertTrue(status["unlocked"])
        self.assertEqual(status["ready_subjects"], 8)

    def test_legacy_attempt_counts_count_toward_coverage(self):
        row = coverage_for_subject({"total": 25, "seen_ids": []})
        self.assertTrue(row["ready"])
        low = coverage_for_subject({"total": 5, "seen_ids": []})
        self.assertFalse(low["ready"])


if __name__ == "__main__":
    unittest.main()
