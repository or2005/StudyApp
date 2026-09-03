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

    def test_visual_keeps_hebrew_letters_inside_a_word(self):
        self.assertEqual(rtltext.visual_line("אנגלית"), "אנגלית")

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


if __name__ == "__main__":
    unittest.main()
