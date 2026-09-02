import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.compose import (
    answers_match,
    compose_pool,
    infer_write_guide,
    is_writable,
    normalize_answer,
)
from core.compose_bank import COMPOSE_BANK
from core.config import ALL_SUBJECTS, HOME_SUBJECTS, SUBJECT_MODES
from core.exam_engine import ExamSession


class ComposeModeTests(unittest.TestCase):
    def test_mode_is_listed(self):
        self.assertIn("compose", SUBJECT_MODES)
        self.assertIn("יצור", SUBJECT_MODES["compose"]["name"])

    def test_normalize_ignores_nikud_and_finals(self):
        self.assertEqual(normalize_answer("חברה"), normalize_answer("חברָה"))
        self.assertEqual(normalize_answer("ספרים"), normalize_answer("ספרים."))
        self.assertEqual(normalize_answer("ירושלים"), normalize_answer("ירושלים"))

    def test_accepts_close_variants(self):
        q = {"correct_answer": "H2O", "accepted": ["H₂O"]}
        self.assertTrue(answers_match("h2o", q))
        self.assertTrue(answers_match("H₂O", q))
        self.assertFalse(answers_match("CO2", q))

    def test_accepts_number_and_hebrew_article(self):
        self.assertTrue(answers_match("30.0", {"correct_answer": "30"}))
        self.assertTrue(answers_match("הכנסת", {"correct_answer": "כנסת"}))
        self.assertTrue(answers_match("כנסת", {"correct_answer": "הכנסת"}))

    def test_session_scores_typed_answers(self):
        session = ExamSession(
            [
                {
                    "id": "c1",
                    "question": "כתבו את הבירה",
                    "correct_answer": "ירושלים",
                    "kind": "compose",
                    "compose": True,
                }
            ],
            mode="compose",
        )
        self.assertTrue(session.submit_answer(-1, 2.0, typed="ירושלים"))
        self.assertEqual(session.score, 1)
        self.assertEqual(session.user_answers[0]["selected_text"], "ירושלים")

    def test_wrong_typed_answer_is_wrong(self):
        session = ExamSession(
            [{"id": "c2", "correct_answer": "30", "kind": "compose", "compose": True}],
            mode="compose",
        )
        self.assertFalse(session.submit_answer(-1, 1.0, typed="12"))
        self.assertEqual(session.score, 0)

    def test_every_subject_has_a_compose_pool(self):
        for key in ALL_SUBJECTS:
            pool = compose_pool(key, [])
            self.assertGreaterEqual(len(pool), 40, key)
            self.assertTrue(all(item.get("kind") == "compose" for item in pool))

    def test_home_subjects_still_covered(self):
        for key in HOME_SUBJECTS:
            self.assertGreaterEqual(len(COMPOSE_BANK[key]), 40, key)


class ComposeBankQualityTests(unittest.TestCase):
    def test_questions_are_self_contained(self):
        bad = ("איזה משפט נכון", "מה נכון?", "איך כותבים נכון?", "בחרו את")
        for key, items in COMPOSE_BANK.items():
            for item in items:
                prompt = item.get("question") or ""
                for token in bad:
                    self.assertNotIn(token, prompt, f"{key} {item.get('id')}")

    def test_every_item_has_guide_answer_and_explanation(self):
        for key, items in COMPOSE_BANK.items():
            diffs = {item.get("difficulty") for item in items}
            self.assertTrue({"Easy", "Medium"} <= diffs, key)
            for item in items:
                self.assertTrue(item.get("correct_answer"), item.get("id"))
                self.assertGreaterEqual(len(item.get("explanation") or ""), 40, item.get("id"))
                guide = infer_write_guide(item)
                self.assertTrue(guide, item.get("id"))
                self.assertTrue(
                    any(tok in (item.get("question") or "") for tok in (
                        "כתבו", "השלימו", "חשבו", "Write", "Complete", "פתרו",
                    )),
                    item.get("id"),
                )

    def test_vague_multiple_choice_is_not_writable(self):
        self.assertFalse(is_writable({
            "question": "איזה משפט נכון?",
            "correct_answer": "הילד קרא ספר.",
            "options": ["א", "ב", "ג", "ד"],
        }))
        self.assertFalse(is_writable({
            "question": "מה נכון?",
            "correct_answer": "בית ספר",
            "options": ["ביתספר", "בית ספר"],
        }))

    def test_explicit_write_prompt_is_writable(self):
        self.assertTrue(is_writable({
            "question": "כתבו את הבירה של ישראל.",
            "correct_answer": "ירושלים",
        }))
        self.assertTrue(is_writable({
            "question": "השלימו: I ____ a student.",
            "correct_answer": "am",
        }))

    def test_converted_mc_does_not_pollute_the_pool(self):
        junk = [
            {"id": "mc1", "question": "איזה משפט נכון?", "correct_answer": "משפט א",
             "options": ["משפט א", "משפט ב", "משפט ג", "משפט ד"]},
        ]
        pool = compose_pool("hebrew", junk)
        ids = {item.get("id") for item in pool}
        self.assertNotIn("mc1", ids)
        self.assertTrue(any(item["id"].startswith("compose_he_") for item in pool))

    def test_beginner_session_can_fill_ten(self):
        for key in ALL_SUBJECTS:
            easy = [q for q in COMPOSE_BANK[key] if q.get("difficulty") == "Easy"]
            self.assertGreaterEqual(len(easy), 8, key)
            self.assertGreaterEqual(len(COMPOSE_BANK[key]), 40, key)


if __name__ == "__main__":
    unittest.main()
