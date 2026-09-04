import os
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import HOME_SUBJECTS, SUBJECTS, subject_key
from core.curriculum import build_all
from core.loader import load_subject


class ContentQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banks = build_all()

    def test_every_subject_has_lessons_and_questions(self):
        for key in HOME_SUBJECTS:
            bank = self.banks[key]
            self.assertGreaterEqual(len(bank["lessons"]), 3, key)
            self.assertGreaterEqual(len(bank["questions"]), 36, key)

    def test_options_are_real_distractors(self):
        for key, bank in self.banks.items():
            for q in bank["questions"]:
                self.assertEqual(len(q["options"]), 4, q["id"])
                joined = " ".join(q["options"])
                self.assertNotIn("גרסה שגויה", joined)
                self.assertNotIn("לא נכון (", joined)
                self.assertNotIn("only wrong", joined.lower())
                self.assertEqual(q["options"][q["answer"]], q["correct_answer"])
                self.assertTrue(q.get("explanation"))

    def test_english_and_civics_have_bagrut_aligned_lessons(self):
        eng = self.banks["english"]
        civ = self.banks["civics"]
        eng_titles = [l.get("title", "") for l in eng["lessons"]]
        civ_titles = [l.get("title", "") for l in civ["lessons"]]
        self.assertTrue(any("Meimad" in t for t in eng_titles), eng_titles[-8:])
        self.assertTrue(any("Bagrut" in t or "Module" in t or "units" in t for t in eng_titles), eng_titles[-8:])
        self.assertGreaterEqual(len(eng["lessons"]), 12)
        self.assertTrue(any("הכרזת" in t for t in civ_titles), civ_titles[-8:])
        self.assertTrue(any("שבות" in t or "חוק" in t for t in civ_titles), civ_titles[-8:])
        self.assertGreaterEqual(len(civ["lessons"]), 12)
        bagrut_eng = [l for l in eng["lessons"] if "בגרות" in (l.get("category") or "")]
        bagrut_civ = [l for l in civ["lessons"] if "בגרות" in (l.get("category") or "")]
        self.assertGreaterEqual(len(bagrut_eng), 8)
        self.assertGreaterEqual(len(bagrut_civ), 8)

    def test_stems_say_what_to_do(self):
        banned = {"מה נכון?", "מה נכון", "איך כותבים נכון?", "choose correct"}
        for key, bank in self.banks.items():
            for q in bank["questions"]:
                stem = " ".join(str(q.get("question") or "").split())
                low = stem.lower()
                self.assertNotIn(low, banned, f"{key} {q.get('id')}")
                self.assertFalse(
                    stem.startswith("מה מתאים כאן"),
                    f"{key} {q.get('id')}: {stem}",
                )
                self.assertFalse(
                    bool(re.search(r"^מה .{2,40} (הוא|היא|הם|הן)\s*\??$", stem)),
                    f"{key} {q.get('id')} inverted copula: {stem}",
                )

    def test_every_question_has_a_real_explanation(self):
        for key, bank in self.banks.items():
            for q in bank["questions"]:
                exp = (q.get("explanation") or "").strip()
                self.assertGreaterEqual(len(exp), 20, f"{key} {q.get('id')}")
                self.assertNotEqual(exp, q.get("correct_answer"))

    def test_english_has_advanced_grammar_lessons(self):
        eng = self.banks["english"]
        titles = " ".join(l.get("title", "") for l in eng["lessons"])
        self.assertTrue(
            any(
                marker in titles
                for marker in ("Relative clauses", "Reported speech", "Modals of deduction", "Advanced grammar")
            ),
            titles[-400:],
        )
        diffs = [q.get("difficulty") for q in eng["questions"]]
        self.assertGreaterEqual(diffs.count("Hard"), 40, f"english Hard={diffs.count('Hard')}")

    def test_every_subject_has_medium_and_hard_for_level_engine(self):
        from core.adaptive_engine import normalize_difficulty

        for key, bank in self.banks.items():
            diffs = [normalize_difficulty(q.get("difficulty")) for q in bank["questions"]]
            self.assertGreaterEqual(diffs.count("Medium"), 16, f"{key} Medium={diffs.count('Medium')}")
            self.assertGreaterEqual(diffs.count("Hard"), 16, f"{key} Hard={diffs.count('Hard')}")
            cats = [l.get("category") or "" for l in bank["lessons"]]
            self.assertTrue(
                any("בינוני" in c or "בגרות" in c or "מימ" in c for c in cats),
                f"{key} missing leveled lesson categories: {cats[-6:]}",
            )
        self.assertEqual(subject_key("english"), "english")
        self.assertEqual(subject_key("לשון"), "hebrew")

    def test_legacy_display_names_map_to_keys(self):
        self.assertEqual(subject_key("english"), "english")
        self.assertEqual(subject_key("לשון"), "hebrew")

    def test_serialized_banks_reach_release_size(self):
        import json

        total_lines = 0
        total_q = 0
        for bank in self.banks.values():
            total_q += len(bank.get("questions") or [])
            text = json.dumps(bank, ensure_ascii=False, indent=2)
            total_lines += text.count("\n") + 1
        self.assertGreaterEqual(total_q, 10000, f"questions={total_q}")
        self.assertGreaterEqual(total_lines, 220000, f"json_lines={total_lines} questions={total_q}")
        from core.curriculum import write_all
        from core.loader import clear_cache

        write_all()
        clear_cache()
        geo = load_subject("geography")
        self.assertTrue(geo)
        self.assertGreater(len(geo["questions"]), 40)

    def test_every_subject_has_three_unit_bagrut_pack(self):
        floors = {
            "hebrew": (7, 48),
            "english": (6, 40),
            "math": (7, 48),
            "history": (6, 40),
            "geography": (6, 40),
            "civics": (6, 40),
            "chemistry": (6, 40),
            "physics": (6, 40),
        }
        for key, (min_lessons, min_qs) in floors.items():
            bank = self.banks[key]
            lessons_3 = [
                lesson
                for lesson in bank["lessons"]
                if "3 יח" in (lesson.get("category") or "") or lesson.get("level") == "3units"
            ]
            qs_3 = [
                q
                for q in bank["questions"]
                if q.get("level") == "3units" or "3units" in (q.get("tags") or [])
            ]
            self.assertGreaterEqual(len(lessons_3), min_lessons, f"{key} 3-unit lessons={len(lessons_3)}")
            self.assertGreaterEqual(len(qs_3), min_qs, f"{key} 3-unit questions={len(qs_3)}")
            for q in qs_3:
                self.assertNotEqual(q.get("kind"), "trick", q.get("id"))
                self.assertEqual(len(q.get("options") or []), 4, q.get("id"))
                self.assertTrue(q.get("explanation"), q.get("id"))


if __name__ == "__main__":
    unittest.main()
