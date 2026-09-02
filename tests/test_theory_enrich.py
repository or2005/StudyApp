import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import ALL_SUBJECTS
from core.loader import clear_cache, load_subject
from core.theory_enrich import MARKER, expand_lessons
from core.theory_library import DEPTH, EXTRA_LESSONS, VOICE


class TheoryEnrichTests(unittest.TestCase):
    def test_library_covers_every_subject(self):
        for key in ALL_SUBJECTS:
            self.assertIn(key, VOICE, key)
            self.assertGreaterEqual(len(DEPTH.get(key) or []), 8, key)
            self.assertGreaterEqual(len(EXTRA_LESSONS.get(key) or []), 4, key)

    def test_expand_adds_teaching_sections(self):
        bank = {
            "subject": "math",
            "lessons": [
                {
                    "id": "t1",
                    "title": "1. אחוזים",
                    "topic": "אחוזים",
                    "category": "שיעור עיוני",
                    "content": "אחוז הוא חלק ממאה.",
                }
            ],
        }
        out = expand_lessons("math", bank)
        text = out["lessons"][0]["content"]
        self.assertIn(MARKER, text)
        self.assertIn("הרחבה", text)
        self.assertGreater(len(text), 200)
        self.assertGreaterEqual(len(out["lessons"]), 2)

    def test_loaded_lessons_are_longer(self):
        clear_cache()
        bank = load_subject("hebrew") or {}
        lessons = bank.get("lessons") or []
        self.assertGreaterEqual(len(lessons), 35)
        blob = lessons[0].get("content") or ""
        self.assertIn(MARKER, blob)
        self.assertGreaterEqual(len(blob), 400)


if __name__ == "__main__":
    unittest.main()
