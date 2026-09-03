import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.adaptive_engine import session_params
from core.quiz import polish_explanation
from core.teach import (
    clarify_stem,
    display_explanation,
    enrich_explanation,
    feedback_note,
    live_hint,
    match_depth,
    task_prompt,
    teaching,
)


class TeachTests(unittest.TestCase):
    def test_match_depth_finds_percent_rule(self):
        essay = match_depth("math", "אחוזים הנחה")
        self.assertIn("חלק ממאה", essay)

    def test_empty_explanation_teaches_the_topic(self):
        text = enrich_explanation("30", "", "אחוזים", "math")
        self.assertIn("30", text)
        self.assertIn("חלק ממאה", text)
        self.assertNotIn("אם טעיתם", text)

    def test_short_explanation_keeps_author_text(self):
        text = enrich_explanation("60", "מורידים רבע מהמחיר.", "אחוזים", "math")
        self.assertIn("מורידים רבע", text)
        self.assertIn("60", text)

    def test_short_unmatched_topic_still_gets_teaching(self):
        text = enrich_explanation("yes", "Because.", "unknown-topic", "english")
        self.assertGreaterEqual(len(text), 40)
        self.assertIn("Because", text)

    def test_polish_accepts_subject(self):
        text = polish_explanation("בית ספר", "", "סמיכות", "hebrew")
        self.assertIn("בית ספר", text)
        self.assertTrue(len(text) > 20)

    def test_generic_hint_becomes_topic_rule(self):
        hint = live_hint(
            {
                "hint": "קראו שוב את השאלה. מה בדיוק מבקשים למצוא?",
                "topic": "אחוזים",
                "question": "כמה הם 15 אחוז מ־200?",
                "subject": "math",
            },
            "math",
        )
        self.assertIn("חלק ממאה", hint)

    def test_custom_hint_is_kept(self):
        hint = live_hint({"hint": "מוצאים אחד אחוז ואז כופלים.", "topic": "אחוזים"}, "math")
        self.assertEqual(hint, "מוצאים אחד אחוז ואז כופלים.")

    def test_wrong_feedback_names_the_common_mistake(self):
        note = feedback_note(
            {"topic": "אחוזים", "question": "הנחה של 25 אחוז", "subject": "math"},
            correct=False,
            subject="math",
        )
        self.assertTrue(note)
        self.assertTrue("אחוז" in note or "חלק" in note)

    def test_display_explanation_reads_question_fields(self):
        text = display_explanation(
            {
                "correct_answer": "סמיכות",
                "explanation": "",
                "topic": "סמיכות",
                "subject": "hebrew",
            }
        )
        self.assertIn("סמיכות", text)

    def test_teaching_fills_subject_voice(self):
        guide = teaching("civics", "כנסת")
        self.assertIn("כנסת", guide["mistakes"])
        self.assertTrue(guide["how"])

    def test_unique_options_never_use_dummy_labels(self):
        from core.quiz import unique_options

        opts = unique_options("10", ["10", "10"])
        self.assertEqual(len(opts), 4)
        self.assertEqual(len(set(opts)), 4)
        blob = " ".join(opts)
        self.assertNotIn("לא נכון (", blob)
        self.assertIn("10", opts)

    def test_scrub_drops_fake_suffix_and_lone_letter(self):
        from core.quiz import scrub_question

        item = scrub_question(
            {
                "question": "הניגוד של «כהה»",
                "correct_answer": "בהיר",
                "options": ["בהיר", "כההון", "ב", "צבע"],
                "answer": 0,
            }
        )
        self.assertNotIn("כההון", item["options"])
        self.assertNotIn("ב", item["options"])
        self.assertIn("בהיר", item["options"])
        self.assertEqual(len(item["options"]), 4)

    def test_clarify_stem_expands_short_synonym(self):
        self.assertEqual(
            clarify_stem({"question": "נרדפת למהיר"}),
            "איזו מילה קרובה במשמעות ל«מהיר»?",
        )
        self.assertIn("לסייע", clarify_stem({"question": "נרדפת ל«לסייע» בהקשר עזרה"}))
        self.assertEqual(
            clarify_stem({"question": "הניגוד של «כהה»"}),
            "איזו מילה הפוכה במשמעות ל«כהה»?",
        )
        self.assertTrue(clarify_stem({"question": "השלימו: She ___ a cat."}).startswith("השלימו"))
        self.assertIn("החסר", clarify_stem({"question": "She ___ a cat."}))
        self.assertEqual(
            clarify_stem({"question": "APPLE זה"}),
            "מה המשמעות של «APPLE»?",
        )
        self.assertEqual(
            clarify_stem({"question": "מה מתאים כאן: APPLE זה?"}),
            "מה המשמעות של «APPLE»?",
        )
        self.assertEqual(
            clarify_stem({"question": "מים שפירים הם"}),
            "מהם מים שפירים?",
        )
        self.assertEqual(
            clarify_stem({"question": "25% מ־80 הם"}),
            "כמה הם 25% מ־80?",
        )
        self.assertEqual(
            clarify_stem({"question": "מה 25% מ־80 הם?"}),
            "כמה הם 25% מ־80?",
        )
        self.assertNotEqual(
            clarify_stem({"question": "מילת קישור של סיבה"}),
            "מילת קישור של סיבה",
        )
        self.assertIn("משמעות", clarify_stem({"question": "بيت בערבית זה"}))
        self.assertTrue(clarify_stem({"question": "also משמש ל"}).startswith("למה"))
        self.assertEqual(
            clarify_stem({"question": "מה המשמעות של «APPLE»?"}),
            "מה המשמעות של «APPLE»?",
        )

    def test_task_prompt_explains_without_leaking_answer(self):
        item = {
            "question": "נרדפת למהיר",
            "correct_answer": "זריז",
            "options": ["זריז", "איטי", "כבד", "רדום"],
            "explanation": "מהיר ≈ זריז.",
            "subject": "hebrew",
        }
        prompt = task_prompt(item)
        self.assertIn("משמעות", prompt)
        self.assertNotIn("זריז", prompt)
        self.assertNotIn("איטי", prompt)

    def test_task_prompt_for_english_gap(self):
        prompt = task_prompt(
            {
                "question": "השלימו: She ___ her homework.",
                "correct_answer": "has finished",
                "subject": "english",
            }
        )
        self.assertIn("השלימו", prompt)
        self.assertNotIn("has finished", prompt)

    def test_task_prompt_for_passage(self):
        prompt = task_prompt(
            {
                "question": "מה המסקנה מהקטע?",
                "passage": "רק מעט תלמידים רכבו על אופניים.",
                "correct_answer": "רובם הלכו ברגל",
                "subject": "hebrew",
            }
        )
        self.assertIn("קטע", prompt)
        self.assertNotIn("אופניים", prompt)
        self.assertNotIn("ברגל", prompt)

    def test_guided_session_is_short(self):
        beginner = session_params("beginner", "guided")
        advanced = session_params("advanced", "guided")
        self.assertEqual(beginner["count"], 6)
        self.assertEqual(advanced["count"], 8)
        self.assertFalse(beginner["exam"])


if __name__ == "__main__":
    unittest.main()
