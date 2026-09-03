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
    def test_visual_line_fixes_english_windows_word_order(self):
        src = "שלום, sara! ברוך הבא חזרה"
        visual = rtltext.visual_line(src)
        self.assertTrue(visual.startswith("חזרה"))
        self.assertTrue(visual.endswith("שלום,"))
        self.assertIn("sara!", visual)
        self.assertEqual(rtltext.visual_line(visual), src)

    def test_visual_keeps_hebrew_letters_inside_a_word(self):
        self.assertEqual(rtltext.visual_line("אנגלית"), "אנגלית")

    def test_apply_is_idempotent_in_visual_mode(self):
        src = "יש עדכון 4.5.2"
        with patch("core.rtltext.needs_visual", return_value=True):
            once = rtltext.apply(src)
            twice = rtltext.apply(once)
        self.assertEqual(once, twice)
        self.assertTrue(rtltext.strip_marks(once).startswith("4.5.2"))

    def test_hebrew_windows_uses_embedding_not_visual(self):
        src = "עדכן עכשיו"
        with patch("core.rtltext.needs_visual", return_value=False):
            wrapped = rtltext.apply(src)
        self.assertTrue(wrapped.startswith("\u202b"))
        self.assertTrue(wrapped.endswith("\u202c"))
        self.assertIn("עדכן עכשיו", wrapped)

    def test_config_rtl_strips_old_marks(self):
        with patch("core.rtltext.needs_visual", return_value=False):
            text = rtl("\u200fהגדרות\u200f")
        self.assertEqual(text.count("הגדרות"), 1)
        self.assertNotIn("\u200f", text)


if __name__ == "__main__":
    unittest.main()
