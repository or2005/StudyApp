import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

AI_DASHES = ("\u2014", "\u2013")  # em dash, en dash. Hebrew maqaf (־) is allowed.


def _walk(folder, suffixes):
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [name for name in dirnames if name not in {"__pycache__"}]
        for name in filenames:
            if name.endswith(suffixes):
                yield os.path.join(dirpath, name)


class NoAiDashTests(unittest.TestCase):
    def test_ui_and_question_banks_have_no_em_dash(self):
        hits = []
        for folder, suffixes in (
            (os.path.join(ROOT, "ui"), (".py",)),
            (os.path.join(ROOT, "data", "questions"), (".json",)),
        ):
            for path in _walk(folder, suffixes):
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
                for dash in AI_DASHES:
                    if dash in text:
                        rel = os.path.relpath(path, ROOT)
                        hits.append(f"{rel} contains U+{ord(dash):04X}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
