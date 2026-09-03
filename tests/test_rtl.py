import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import rtltext
from core.config import rtl


class RtlTextTests(unittest.TestCase):
    def tearDown(self):
        rtltext.set_mode("auto")

    def test_visual_line_fixes_english_windows_word_order(self):
        src = "שלום, sara! ברוך הבא חזרה"
        visual = rtltext.visual_line(src)
        self.assertTrue(visual.startswith("חזרה"))
        self.assertTrue(visual.endswith("שלום,"))
        self.assertIn("sara!", visual)
        self.assertEqual(rtltext.visual_line(visual), src)

    def test_hebrew_period_moves_with_the_word(self):
        self.assertEqual(rtltext.visual_line("אתמול."), ".אתמול")
        self.assertEqual(rtltext.visual_line(".אתמול"), "אתמול.")

    def test_apply_visual_has_no_bidi_isolates(self):
        src = "יש עדכון 4.5.2"
        with patch("core.rtltext.resolved_mode", return_value="words"):
            once = rtltext.apply(src)
            twice = rtltext.apply(once)
        self.assertEqual(once, twice)
        self.assertNotIn("\u2067", once)
        self.assertNotIn("\u202b", once)
        self.assertTrue(rtltext.strip_marks(once).startswith("4.5.2"))

    def test_hebrew_windows_uses_embedding_not_visual(self):
        src = "עדכן עכשיו"
        with patch("core.rtltext.resolved_mode", return_value="off"), patch(
            "core.rtltext.windows_has_rtl_ui", return_value=True
        ):
            wrapped = rtltext.apply(src)
        self.assertTrue(wrapped.startswith("\u202b"))
        self.assertTrue(wrapped.endswith("\u202c"))
        self.assertIn("עדכן עכשיו", wrapped)

    def test_config_rtl_strips_old_marks(self):
        with patch("core.rtltext.resolved_mode", return_value="off"), patch(
            "core.rtltext.windows_has_rtl_ui", return_value=True
        ):
            text = rtl("\u200fהגדרות\u200f")
        self.assertEqual(text.count("הגדרות"), 1)
        self.assertNotIn("\u200f", text)

    def test_force_words_mode(self):
        rtltext.set_mode("words")
        text = rtltext.apply("עדכן עכשיו")
        self.assertIn("עכשיו", rtltext.strip_marks(text).split()[0])

    def test_english_keeps_question_mark(self):
        src = "Could you help me, please?"
        with patch("core.rtltext.resolved_mode", return_value="words"):
            shown = rtltext.strip_marks(rtltext.apply(src))
        self.assertTrue(shown.endswith("?"))
        self.assertTrue(shown.startswith("Could"))
        self.assertIn("\u202a", rtltext.apply(src))

    def test_hebrew_windows_keeps_english_punctuation(self):
        src = "Look! He is ___ help."
        with patch("core.rtltext.resolved_mode", return_value="off"), patch(
            "core.rtltext.windows_has_rtl_ui", return_value=True
        ):
            wrapped = rtltext.apply(src)
        self.assertIn("\u202a", wrapped)
        self.assertNotIn("\u202b", wrapped)
        self.assertTrue(rtltext.strip_marks(wrapped).endswith("."))

    def test_english_sentence_is_not_reversed(self):
        src = "I have seen that film."
        self.assertEqual(rtltext.visual_line(src), src)

    def test_math_formula_is_not_reversed(self):
        src = "x² − 5x + 6 = 0"
        self.assertEqual(rtltext.visual_line(src), src)

    def test_formula_then_hebrew_keeps_equation_readable(self):
        src = "5x − 2x + 7 = 16. מהו x?"
        visual = rtltext.visual_line(src)
        self.assertIn("5x − 2x + 7 = 16", visual)
        self.assertTrue(visual.startswith("5x"))
        self.assertIn("מהו", visual)

    def test_many_latin_islands_do_not_scramble_formula(self):
        src = "מהו ב־2H2 + O2 → 2H2O, יחס H2 ל־O2?"
        visual = rtltext.visual_line(src)
        self.assertIn("2H2 + O2", visual)
        self.assertNotIn("O2 → 2H2O, +", visual)

    def test_mixed_hebrew_keeps_english_chunk(self):
        src = "השלימו: She ___ her homework."
        visual = rtltext.visual_line(src)
        self.assertIn("She ___ her homework.", visual)
        self.assertNotIn("homework. her ___ She", visual)
        self.assertEqual(rtltext.visual_line(visual), src)

    def test_percent_line_keeps_number_readable(self):
        src = "20% מ־150 הם"
        visual = rtltext.visual_line(src)
        self.assertIn("20%", visual)
        self.assertEqual(rtltext.visual_line(visual), src)


if __name__ == "__main__":
    unittest.main()
