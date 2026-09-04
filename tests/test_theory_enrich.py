import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import ALL_SUBJECTS
from core.loader import clear_cache, load_subject
from core.lesson_plain import organize_lesson
from core.theory_enrich import MARKER, expand_lessons
from core.theory_library import DEPTH, EXTRA_LESSONS, VOICE


class TheoryEnrichTests(unittest.TestCase):
    def test_library_covers_every_subject(self):
        for key in ALL_SUBJECTS:
            self.assertIn(key, VOICE, key)
            self.assertGreaterEqual(len(DEPTH.get(key) or []), 8, key)
            self.assertGreaterEqual(len(EXTRA_LESSONS.get(key) or []), 4, key)

    def test_expand_organizes_without_meta_junk(self):
        bank = {
            "subject": "hebrew",
            "lessons": [
                {
                    "id": "t1",
                    "title": "1. כתיב בסיסי",
                    "topic": "כתיב",
                    "category": "שיעור עיוני",
                    "content": (
                        "כתיב\n\n"
                        "קריאה בקצב איטי. שורה-שורה:\n"
                        "1. קוראים את המילה בשקט.\n"
                        "2. בודקים אם יש יוד מיותרת.\n"
                        "דוגמה:\n"
                        "חברה שלי, בלי יוד מיותרת.\n"
                        "הרחבה\n"
                        "האקדמיה ממליצה על כתיב מלא עם וו ויו״ד לפי כללים.\n"
                        "למה זה חשוב\n"
                        "כי כתיב משפיע על הבנה.\n"
                        "איך ללמוד את זה\n"
                        "1. קראו בקול.\n"
                        "טעויות נפוצות\n"
                        "מוסיפים יוד סתם.\n"
                    ),
                }
            ],
        }
        out = expand_lessons("hebrew", bank)
        text = out["lessons"][0]["content"]
        self.assertIn("1.", text)
        self.assertIn("דוגמה", text)
        self.assertNotIn("למה זה חשוב", text)
        self.assertNotIn("איך ללמוד", text)
        self.assertIn("קריאה בקצב איטי", text)
        parts = organize_lesson(text, subject="hebrew", topic="כתיב")
        self.assertTrue(parts["reading"])
        self.assertIn("חברה", parts["example"])

    def test_loaded_lessons_are_readable(self):
        clear_cache()
        bank = load_subject("hebrew") or {}
        lessons = bank.get("lessons") or []
        self.assertGreaterEqual(len(lessons), 20)
        blob = lessons[0].get("content") or ""
        self.assertGreaterEqual(len(blob), 40)
        self.assertNotIn("איך ללמוד את זה", blob)


if __name__ == "__main__":
    unittest.main()
