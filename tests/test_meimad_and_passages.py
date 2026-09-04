import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.exam_engine import ExamSession
from core.loader import load_subject
from core.meimad_exam import SECTIONS, build_meimad_exam, can_take_meimad, section_count
from core.quiz import make_question


class MeimadExamTests(unittest.TestCase):
    def test_three_timed_chapters(self):
        built = build_meimad_exam(load_subject, seed=1)
        self.assertEqual(len(built["chapters"]), 3)
        self.assertEqual([c["key"] for c in built["chapters"]], ["hebrew", "english", "math"])
        self.assertGreaterEqual(len(built["questions"]), section_count('hebrew') * 2)
        for chapter in built["chapters"]:
            self.assertEqual(chapter["end"] - chapter["start"], section_count(chapter["key"]))
            secs = next(row[3] for row in SECTIONS if row[0] == chapter["key"])
            self.assertEqual(chapter["seconds"], secs)

    def test_skip_stays_inside_chapter(self):
        questions = [
            {"id": f"{sec}{i}", "question": "q", "options": ["א", "ב"], "answer": 0,
             "correct_answer": "א", "subject": sec, "topic": "x"}
            for sec in ("hebrew", "english")
            for i in range(4)
        ]
        chapters = [
            {"key": "hebrew", "name": "עברית", "start": 0, "end": 4, "seconds": 60},
            {"key": "english", "name": "אנגלית", "start": 4, "end": 8, "seconds": 60},
        ]
        session = ExamSession(questions, mode="meimad", chapters=chapters)
        first = session.get_current_question()["id"]
        self.assertTrue(session.skip_current())
        ids = [q["id"] for q in session.questions[:4]]
        self.assertEqual(ids[-1], first)
        self.assertTrue(all(qid.startswith("hebrew") for qid in ids))

    def test_close_chapter_moves_forward(self):
        questions = [{"id": str(i), "options": ["א", "ב"], "answer": 0, "correct_answer": "א"} for i in range(4)]
        chapters = [
            {"key": "a", "name": "א", "start": 0, "end": 2, "seconds": 1},
            {"key": "b", "name": "ב", "start": 2, "end": 4, "seconds": 1},
        ]
        session = ExamSession(questions, mode="meimad", chapters=chapters)
        self.assertTrue(session.close_chapter())
        self.assertEqual(session.current_index, 2)
        self.assertEqual(session.current_chapter()["key"], "b")
        self.assertEqual(len(session.wrong_answers()), 2)

    def test_locked_without_diagnostic(self):
        class Empty:
            def get_diagnostic(self):
                return None

            def get_pref(self, key, default=None):
                return default

        self.assertFalse(can_take_meimad(Empty()))

    def test_unlocked_after_onboarding_intermediate(self):
        class Ready:
            def get_diagnostic(self):
                return None

            def get_pref(self, key, default=None):
                return {
                    "onboarding_complete": True,
                    "preferred_level": "intermediate",
                }.get(key, default)

            def has_profile(self):
                return True

        self.assertTrue(can_take_meimad(Ready()))


class PassageTests(unittest.TestCase):
    def test_make_question_keeps_passage(self):
        q = make_question(
            "english", "unseen", "p1", "What?", "yes", ["no", "maybe", "never"],
            "because the text says so clearly enough.", "Easy",
            passage="A short original passage about school.", passage_id="en_p",
        )
        self.assertEqual(q["kind"], "passage")
        self.assertIn("school", q["passage"])

    def test_banks_contain_passage_questions(self):
        from core.curriculum import build_all

        banks = build_all()
        for key in ("hebrew", "english", "math"):
            passages = [q for q in banks[key]["questions"] if q.get("kind") == "passage"]
            self.assertGreaterEqual(len(passages), 4, key)
            self.assertTrue(all(q.get("passage") for q in passages), key)

    def test_math_has_method_lessons(self):
        from core.curriculum import build_all

        titles = " ".join(l.get("title", "") for l in build_all()["math"]["lessons"])
        self.assertIn("אחוזים", titles)
        self.assertIn("יחס", titles)
        self.assertGreaterEqual(len(build_all()["math"]["questions"]), 100)


if __name__ == "__main__":
    unittest.main()
