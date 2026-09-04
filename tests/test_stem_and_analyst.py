# -*- coding: utf-8 -*-
"""Focused regression for stem polish + analyst + short teach blocks."""
from __future__ import annotations

import unittest

from core.adaptive_engine import AdaptiveEngine
from core.stem_fix import polish_stem, scrub_explanation
from core.teach import clarify_stem, needs_task_prompt, teach_after_answer


class StemPolishTests(unittest.TestCase):
    def test_vague_physics_unit_becomes_specific(self):
        got = clarify_stem({
            "question": "איזו אפשרות נכונה בנושא פיזיקה?",
            "correct_answer": "ניוטון",
            "options": ["ג׳אול", "ניוטון", "ואט", "פסקל"],
            "explanation": "התשובה הנכונה היא «ניוטון». N",
            "subject": "physics",
        })
        self.assertNotIn("איזו אפשרות נכונה", got)
        self.assertIn("כוח", got)

    def test_vague_chemistry_ph(self):
        got = clarify_stem({
            "question": "איזו אפשרות נכונה בנושא כימיה?",
            "correct_answer": "חומצי",
            "options": ["חומצי", "בסיסי", "ניטרלי", "מוצק"],
            "explanation": "התשובה הנכונה היא «חומצי». <7",
        })
        self.assertIn("pH", got)
        self.assertNotIn("איזו אפשרות נכונה", got)
        q = {
            "question": "מי היה בידוד טוב?",
            "correct_answer": "מאט מעבר חום",
            "options": ["מוחק טמפרטורה", "מגדיל מסה תמיד", "מאט מעבר חום", "יוצר אור"],
            "subject": "physics",
        }
        got = clarify_stem(q)
        self.assertNotIn("מי היה", got)
        self.assertIn("בידוד", got)

    def test_meter_measures(self):
        got = clarify_stem({
            "question": "מי היה מטר מודד?",
            "correct_answer": "אורך",
            "options": ["מסה", "חום", "אורך", "זמן"],
        })
        self.assertTrue(got.startswith("מה מודד"))
        self.assertIn("מטר", got)

    def test_strip_leading_dash(self):
        got = polish_stem("- מהו חום?")
        self.assertNotIn("-", got.lstrip())
        self.assertIn("חום", got)
        self.assertEqual(polish_stem("— שאלה"), "שאלה")

    def test_prime_minister_feminine(self):
        got = polish_stem("מהו ראשת הממשלה הראשונה?")
        self.assertTrue(got.startswith("מי הייתה"), got)
        self.assertIn("ראשת", got)

    def test_bare_who_golda(self):
        got = polish_stem("מי גולדה מאיר?")
        self.assertTrue(got.startswith("מי הייתה"), got)

    def test_topic_round_stripped(self):
        from core.stem_fix import clean_topic_label
        from core.teach import topic_label

        self.assertEqual(
            clean_topic_label("היסטוריה — סבב C: ציונות ומדינה (2)"),
            "היסטוריה ציונות ומדינה",
        )
        # מקף עברי מהמאגר
        self.assertEqual(
            clean_topic_label("היסטוריה ־ סבב C: ציונות ומדינה (2)"),
            "היסטוריה ציונות ומדינה",
        )
        self.assertNotIn("סבב", topic_label("סבב C: ציונות ומדינה", "history"))
        self.assertNotIn("סבב", topic_label("היסטוריה ־ סבב C: ציונות ומדינה (2)", "history"))

    def test_tense_phrase_not_person(self):
        self.assertEqual(
            clarify_stem({"question": "מהו אתמול רצתי?"}),
            "באיזה זמן כתוב «אתמול רצתי»?",
        )

    def test_strip_round_anywhere(self):
        self.assertNotIn("סבב", polish_stem("מה הם 2+2? (סבב B)"))
        self.assertNotIn("סבב", polish_stem("סבב C: מה הניגוד של «ארוך»?"))

    def test_percent_shave(self):
        self.assertEqual(polish_stem("מהי 50% מ־90 שווה?"), "כמה הם 50% מ־90?")

    def test_remainder(self):
        self.assertEqual(polish_stem("מהו השארית ב־73 ÷ 7?"), "מה השארית ב־73 ÷ 7?")

    def test_series_next(self):
        self.assertEqual(
            polish_stem("2, 4, 6, 8, ... הבא?"),
            "מה האיבר הבא בסדרה: 2, 4, 6, 8, ...?",
        )

    def test_speed_trail(self):
        got = polish_stem("גוף עבר 48 מ׳ ב־6 ש׳ במהירות קבועה. המהירות")
        self.assertTrue(got.startswith("גוף עבר"), got)
        self.assertIn("מה המהירות", got)

    def test_helium_location(self):
        got = polish_stem("מהו הליום נמצא בטבלה ליד?")
        self.assertIn("ליד מה", got)
        self.assertIn("הליום", got)

    def test_flashlight_why(self):
        self.assertEqual(polish_stem("מהו פנס בלילה עוזר כי?"), "למה פנס בלילה עוזר?")

    def test_voting_age_gender(self):
        self.assertEqual(polish_stem("מהי גיל הבחירה לכנסת?"), "מהו גיל הבחירה לכנסת?")

    def test_scrub_filler_and_orphan_year(self):
        text = scrub_explanation(
            "הנקודה העדינה: 1957 לאומיות במאה התשע-עשרה היא הרעיון שעם ראוי למדינה. "
            "קראו שוב את השאלה, בדקו יחידות, ופסלו מה שלא מתאים.",
            keep_years_from="מהי לאומיות",
            stem="מהי לאומיות במאה התשע-עשרה?",
        )
        self.assertNotIn("1957", text)
        self.assertNotIn("קראו שוב", text)
        self.assertNotIn("-", text.replace("־", ""))

    def test_teach_blocks_are_short(self):
        blocks = teach_after_answer(
            {
                "question": "השלימו: מלחמת העולם השנייה הסתיימה ב ____",
                "correct_answer": "1945",
                "explanation": (
                    "התשובה הנכונה היא «1945». קראו שוב את השאלה, בדקו יחידות, ופסלו מה שלא מתאים. "
                    "מלחמת העולם השנייה באירופה מ-1939 עד 1945. הראשונה נמשכה מ-1914 עד 1918."
                ),
                "topic": "ציר זמן",
                "subject": "history",
            },
            is_correct=True,
            subject="history",
        )
        self.assertIn("1945", blocks["why"])
        self.assertNotIn("קראו שוב", blocks["why"])
        self.assertEqual(blocks.get("watch") or "", "")
        self.assertLessEqual(len(blocks["why"]), 220)

    def test_wrong_adjective_gets_relevant_tip(self):
        blocks = teach_after_answer(
            {
                "question": "מהו במשפט 'בית גדול' שם התואר?",
                "correct_answer": "גדול",
                "explanation": "התשובה הנכונה היא «גדול». מתאר את הבית. שם עצם הוא דבר, אדם או רעיון.",
                "topic": "חלקי דיבר",
                "subject": "hebrew",
            },
            is_correct=False,
            subject="hebrew",
        )
        self.assertIn("גדול", blocks["why"])
        self.assertNotIn("שם עצם הוא", blocks["why"])
        self.assertIn("תואר", blocks["how"])
        self.assertTrue(blocks.get("watch"))
        self.assertNotIn("צליל דומה", blocks.get("watch", ""))

    def test_clear_stem_skips_task_prompt(self):
        self.assertFalse(needs_task_prompt({"question": "מה הניגוד של «ארוך»?", "subject": "hebrew"}))
        self.assertTrue(needs_task_prompt({"question": "___", "passage": "קטע", "subject": "hebrew"}))


class FakeStorage:
    def __init__(self):
        self._data = {"adaptive": {}}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


class AnalystTests(unittest.TestCase):
    def test_struggle_detected(self):
        store = FakeStorage()
        engine = AdaptiveEngine(store)
        subj = "physics"
        for i in range(8):
            engine.observe(subj, is_correct=(i % 5 == 0), topic="חום ויחידות", difficulty="Easy")
        flag = engine.struggling(subj)
        self.assertIsNotNone(flag)

    def test_snapshot_does_not_recurse(self):
        store = FakeStorage()
        engine = AdaptiveEngine(store)
        for i in range(6):
            engine.observe("math", is_correct=i % 2 == 0, topic="שברים", difficulty="Medium", time_sec=4)
        snap = engine.snapshot("math")
        ready = engine.exam_readiness("math")
        plan = engine.action_plan("math")
        self.assertIn("level", snap)
        self.assertIn("score", ready)
        self.assertTrue(plan.get("steps"))
        self.assertEqual(snap.get("exam_readiness", {}).get("score"), ready.get("score"))

    def test_topic_scores_and_deep_analytics(self):
        from core.analytics import AnalyticsEngine
        import tempfile, json, os

        store = FakeStorage()
        engine = AdaptiveEngine(store)
        for i in range(10):
            engine.observe("hebrew", False, topic="פיסוק", difficulty="Easy", time_sec=1.0)
        scores = engine.topic_scores("hebrew")
        self.assertTrue(scores)
        self.assertTrue(scores[0].get("weak"))
        tmp = tempfile.mkdtemp()
        stats = os.path.join(tmp, "user_stats.json")
        with open(stats, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "history": [
                        {
                            "topic": "פיסוק",
                            "subject": "hebrew",
                            "difficulty": "Easy",
                            "correct": i % 3 == 0,
                            "time_sec": 2.0,
                            "timestamp": f"2026-01-0{(i % 9) + 1}T10:00:00",
                        }
                        for i in range(12)
                    ],
                    "topic_stats": {},
                },
                handle,
            )
        report = AnalyticsEngine(db_path=stats).get_deep_report("hebrew")
        self.assertIn("אנליסט", report)


if __name__ == "__main__":
    unittest.main()
