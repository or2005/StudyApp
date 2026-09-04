# -*- coding: utf-8 -*-
"""Focused regression for stem polish + analyst struggle."""
from __future__ import annotations

import unittest

from core.adaptive_engine import AdaptiveEngine
from core.stem_fix import polish_stem
from core.teach import clarify_stem


class StemPolishTests(unittest.TestCase):
    def test_false_who_insulation(self):
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
        self.assertEqual(polish_stem("- מהו חום?"), "מהו חום?")
        self.assertEqual(polish_stem("— שאלה"), "שאלה")

    def test_person_kept(self):
        got = clarify_stem({"question": "מי היה הרצל?", "subject": "history"})
        self.assertTrue(got.startswith("מי היה"), got)
        got2 = clarify_stem({"question": "מי היה דוד בן גוריון?", "subject": "history"})
        self.assertTrue(got2.startswith("מי היה"), got2)

    def test_teach_after_answer_has_how(self):
        from core.teach import teach_after_answer

        blocks = teach_after_answer(
            {
                "question": "מה הייתה הצהרת בלפור?",
                "correct_answer": "תמיכה בבית לאומי",
                "explanation": "הנקודה העדינה: 1917 תמיכה בריטית.",
                "topic": "הצהרת בלפור",
                "subject": "history",
                "visual": {
                    "kind": "document",
                    "title": "הצהרת בלפור",
                    "caption": "1917: תמיכה בריטית בבית לאומי.",
                    "reveal_note": "1917: תמיכה בריטית בבית לאומי.",
                },
            },
            is_correct=False,
            subject="history",
        )
        self.assertTrue(
            ("התשובה" in blocks["why"]) or ("1917" in blocks["why"]) or ("בלפור" in blocks.get("why", "")),
            blocks,
        )
        self.assertTrue(blocks.get("how"))
        self.assertIn("שרשרת", blocks["how"])
        self.assertTrue(blocks.get("watch"))
        self.assertTrue(blocks.get("picture"))
        self.assertIn("איור", blocks["picture"])
        self.assertNotIn("הנקודה העדינה", blocks.get("why", ""))
        self.assertNotIn("-", blocks.get("why", "").replace("־", ""))

    def test_orphan_year_stripped_when_not_in_stem(self):
        from core.teach import teach_after_answer

        blocks = teach_after_answer(
            {
                "question": "מהי לאומיות במאה התשע-עשרה?",
                "correct_answer": "עם עם שפה וזיכרון משותפים ראוי למדינה",
                "explanation": "הנקודה העדינה: 1957 לאומיות במאה התשע-עשרה היא הרעיון שעם עם שפה וזיכרון משותפים ראוי למדינה.",
                "topic": "זיכרון וגבורה",
                "subject": "history",
            },
            is_correct=True,
            subject="history",
        )
        self.assertNotIn("1957", blocks["why"])
        self.assertNotIn("-", blocks["why"].replace("־", ""))
        self.assertTrue(blocks.get("how"))
        self.assertTrue(blocks.get("watch"))  # takeaway even when correct
        self.assertIn("לאומיות", blocks["why"])
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
        coach = engine.evaluate(subj)
        self.assertIn(coach.get("tone"), {"struggle", "weak_topic"})


if __name__ == "__main__":
    unittest.main()
