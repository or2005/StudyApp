"""המחשות היסטוריה — כיסוי ≥50% וציור תקין."""
from __future__ import annotations

import unittest

from core.illustrations.history import attach_history_visuals, coverage_stats
from core.illustrations.render import render_visual_png
from core.illustrations.schema import get_visual
from core.loader import clear_cache, load_subject


class HistoryVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clear_cache()
        cls.bank = load_subject("history")

    def test_history_loads(self):
        self.assertIsNotNone(self.bank)
        self.assertGreaterEqual(len(self.bank.get("lessons") or []), 20)
        self.assertGreaterEqual(len(self.bank.get("questions") or []), 100)

    def test_coverage_lessons_half_questions_matched(self):
        stats = coverage_stats(self.bank)
        self.assertGreaterEqual(stats["lessons_ratio"], 0.50, stats)
        # שאלות: רק התאמה אמיתית, בלי איור אקראי
        self.assertGreaterEqual(stats["questions_ratio"], 0.15, stats)

    def test_golda_question_gets_state_not_congress(self):
        from core.illustrations.history import build_visual_for

        visual = build_visual_for(
            {
                "question": "מי הייתה ראשת הממשלה הראשונה?",
                "correct_answer": "גולדה מאיר",
                "topic": "ציונות ומדינה",
                "explanation": "גולדה מאיר. הציונות המודרנית ביקשה בית לאומי",
            }
        )
        self.assertIsNotNone(visual)
        self.assertEqual(visual.get("title"), "מוסדות וחוקים")
        self.assertNotEqual(visual.get("title"), "ציונות מוסדית")

    def test_other_subjects_untouched(self):
        clear_cache()
        math = load_subject("math")
        hit = sum(1 for q in (math.get("questions") or [])[:80] if get_visual(q))
        self.assertEqual(hit, 0)

    def test_render_all_kinds(self):
        kinds = {
            str(get_visual(q).get("kind"))
            for q in (self.bank.get("questions") or [])
            if get_visual(q)
        }
        self.assertGreaterEqual(len(kinds), 5, kinds)
        sample = next(q for q in self.bank["questions"] if get_visual(q))
        for mode in ("lesson", "question", "explain"):
            png = render_visual_png(get_visual(sample), width=640, height=180, mode=mode)
            self.assertTrue(png.startswith(b"\x89PNG"))

    def test_attach_is_idempotent_enough(self):
        again = attach_history_visuals(dict(self.bank))
        stats = coverage_stats(again)
        self.assertGreaterEqual(stats["lessons_ratio"], 0.50)
        self.assertGreaterEqual(stats["questions_ratio"], 0.15)


if __name__ == "__main__":
    unittest.main()
