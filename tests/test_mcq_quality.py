import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.mcq_quality import harden_options, looks_too_easy, numeric_near_misses


class McqQualityTests(unittest.TestCase):
    def test_numeric_near_misses_are_close(self):
        misses = numeric_near_misses("3A", v=24, r=8, need=4)
        self.assertGreaterEqual(len(misses), 3)
        self.assertNotIn("192A", misses)
        for item in misses:
            self.assertFalse(looks_too_easy("3A", item), item)

    def test_harden_replaces_wild_numeric(self):
        opts, answer = harden_options(
            ["3A", "192A", "2A", "4A"],
            0,
            topic="אוהם",
            prompt="מעגל 24V ו־8Ω",
        )
        self.assertEqual(opts[answer], "3A")
        self.assertNotIn("192A", opts)
        for i, text in enumerate(opts):
            if i == answer:
                continue
            self.assertFalse(looks_too_easy("3A", text), text)

    def test_harden_replaces_absurd_text(self):
        opts, answer = harden_options(
            ["לנתק ולוודא שאין מתח", "לגעת קודם", "תמרור עצור", "בנזין"],
            0,
            topic="בטיחות",
            prompt="לפני נגיעה במוליך",
        )
        self.assertEqual(opts[answer], "לנתק ולוודא שאין מתח")
        joined = " ".join(opts)
        self.assertNotIn("תמרור", joined)
        self.assertNotIn("בנזין", joined)


if __name__ == "__main__":
    unittest.main()
