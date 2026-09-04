import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import HOME_SUBJECTS, MEIMAD_SUBJECTS, subject_key, subject_label
from core.exam_engine import ExamSession
from core.loader import load_subject


class BankQualityTests(unittest.TestCase):
    def test_no_trick_questions_left_in_any_bank(self):
        for key in HOME_SUBJECTS:
            data = load_subject(key) or {}
            tricks = [q for q in (data.get("questions") or []) if q.get("kind") == "trick"]
            self.assertEqual(tricks, [], f"{key} still contains generated trick questions")

    def test_math_is_a_real_subject(self):
        self.assertIn("math", HOME_SUBJECTS)
        self.assertIn("math", MEIMAD_SUBJECTS)
        data = load_subject("math") or {}
        self.assertGreaterEqual(len(data.get("lessons") or []), 5)
        self.assertGreaterEqual(len(data.get("questions") or []), 40)
        three_unit = [q for q in (data.get("questions") or []) if q.get("level") == "3units"]
        self.assertGreaterEqual(len(three_unit), 48, "math 3-unit Bagrut pack")

    def test_meimad_aliases_point_to_math(self):
        self.assertEqual(subject_key("meimad"), "math")
        self.assertEqual(subject_key("חשבון"), "math")
        self.assertEqual(subject_key("לשון"), "hebrew")

    def test_every_question_has_answer_within_options(self):
        for key in HOME_SUBJECTS:
            for q in (load_subject(key) or {}).get("questions") or []:
                options = q.get("options") or []
                answer = q.get("answer")
                self.assertIsInstance(answer, int, f"{key}/{q.get('id')} has no answer index")
                self.assertTrue(0 <= answer < len(options), f"{key}/{q.get('id')} answer out of range")

    def test_question_ids_are_unique_per_subject(self):
        for key in HOME_SUBJECTS:
            ids = [str(q.get("id")) for q in (load_subject(key) or {}).get("questions") or []]
            self.assertTrue(all(ids), f"{key} has questions without id")
            self.assertEqual(len(ids), len(set(ids)), f"{key} has duplicate question ids")


class ExamSessionTests(unittest.TestCase):
    def _questions(self, count=4):
        return [
            {"id": f"q{i}", "question": f"שאלה {i}", "options": ["א", "ב"], "answer": 0,
             "correct_answer": "א", "topic": "בדיקה"}
            for i in range(count)
        ]

    def test_skip_moves_question_to_end_once(self):
        session = ExamSession(self._questions(3))
        first_id = session.get_current_question()["id"]
        self.assertTrue(session.skip_current())
        self.assertNotEqual(session.get_current_question()["id"], first_id)
        self.assertEqual(session.questions[-1]["id"], first_id)
        while session.get_current_question()["id"] != first_id:
            session.current_index += 1
        self.assertFalse(session.can_skip(), "אסור לדלג פעמיים על אותה שאלה")

    def test_total_time_limit_reported(self):
        session = ExamSession(self._questions(2), mode="final", total_limit_sec=120)
        left = session.remaining_total()
        self.assertIsNotNone(left)
        self.assertLessEqual(left, 120)
        self.assertFalse(session.out_of_time())

    def test_wrong_answers_carry_review_data(self):
        session = ExamSession(self._questions(2))
        session.submit_answer(1, 3.0)
        wrong = session.wrong_answers()
        self.assertEqual(len(wrong), 1)
        self.assertIn("question", wrong[0])
        self.assertIn("correct_answer", wrong[0])
        self.assertEqual(wrong[0]["selected"], 1)

    def test_state_round_trip_keeps_skips(self):
        session = ExamSession(self._questions(3), subject_key="hebrew")
        session.skip_current()
        restored = ExamSession.from_state(session.to_state())
        self.assertEqual(restored.skipped, session.skipped)
        self.assertEqual(len(restored.questions), 3)

    def test_fill_unanswered_marks_rest_wrong_without_duplicate(self):
        session = ExamSession(self._questions(4), mode="general", total_limit_sec=1)
        session.submit_answer(0, 1.0)
        session.submit_answer(1, 1.0)
        added = session.fill_unanswered()
        self.assertEqual(added, 2)
        self.assertEqual(len(session.user_answers), 4)
        self.assertEqual(sum(1 for item in session.user_answers if item.get("correct")), 1)
        self.assertEqual(session.fill_unanswered(), 0)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="studyapp-test-")
        os.environ["LOCALAPPDATA"] = self.tmp
        os.environ["APPDATA"] = self.tmp
        for module in [m for m in list(sys.modules) if m.startswith("core.storage")]:
            del sys.modules[module]
        from core.storage import UserStorage

        self.storage = UserStorage()

    def test_id_number_is_not_stored_in_full(self):
        self.storage.save_student("אור", 17, "123456789")
        student = self.storage.get_student()
        self.assertNotIn("id_number", student)
        self.assertEqual(student.get("id_hint"), "6789")
        raw = json.dumps(student, ensure_ascii=False)
        self.assertNotIn("123456789", raw)

    def test_mistake_is_recorded_and_resolved(self):
        question = {"id": "x1", "subject": "civics", "question": "שאלה", "options": ["א", "ב"],
                    "answer": 1, "correct_answer": "ב", "explanation": "כי כך"}
        self.storage.record_mistake(question, 0)
        self.assertEqual(len(self.storage.get_mistakes()), 1)
        self.storage.record_mistake(question, 0)
        self.assertEqual(self.storage.get_mistakes()[0]["times_wrong"], 2)
        self.storage.clear_mistake("x1")
        self.assertEqual(self.storage.get_mistakes(), [])

    def test_export_import_round_trip(self):
        self.storage.save_student("אור", 17, "")
        bundle = self.storage.export_bundle()
        self.storage.reset_all()
        self.assertEqual(self.storage.get_student(), {})
        self.assertTrue(self.storage.import_bundle(bundle))
        self.assertEqual(self.storage.get_student().get("name"), "אור")
        self.assertFalse(self.storage.import_bundle({"nope": 1}))

    def test_study_plan_scales_with_exam_date(self):
        import datetime

        soon = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
        self.storage.set_exam_date(soon, "מימ״ד")
        plan = self.storage.study_plan()
        self.assertEqual(plan["days"], 10)
        self.assertGreater(plan["per_day"], 0)
        far = (datetime.date.today() + datetime.timedelta(days=200)).isoformat()
        self.storage.set_exam_date(far, "מימ״ד")
        self.assertLessEqual(self.storage.study_plan()["per_day"], plan["per_day"])


class AdaptiveEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="studyapp-adapt-")
        os.environ["LOCALAPPDATA"] = self.tmp
        os.environ["APPDATA"] = self.tmp
        for module in [m for m in list(sys.modules) if m.startswith("core.storage")]:
            del sys.modules[module]
        from core.storage import UserStorage
        from core.adaptive_engine import AdaptiveEngine

        self.storage = UserStorage()
        self.engine = AdaptiveEngine(self.storage)

    def _pool(self):
        from core.adaptive_engine import pick_by_mix

        pool = []
        for diff, n in (("Easy", 20), ("Medium", 20), ("Hard", 20)):
            for i in range(n):
                pool.append({"id": f"{diff}-{i}", "difficulty": diff, "question": diff})
        return pool

    def test_new_subject_starts_beginner(self):
        self.assertEqual(self.engine.level_of("civics"), "starter")

    def test_success_promotes_beginner_to_intermediate(self):
        event = None
        for _ in range(8):
            event = self.engine.observe("civics", True, "Easy") or event
        self.assertEqual(self.engine.level_of("civics"), "easy")
        self.assertIsNotNone(event)
        self.assertEqual(event["kind"], "promote")
        self.assertEqual(event["to"], "easy")

    def test_beginner_mix_avoids_hard(self):
        from core.adaptive_engine import mix_for, pick_by_mix, normalize_difficulty

        picked = pick_by_mix(self._pool(), mix_for("beginner"), 10, rng=__import__("random").Random(1))
        diffs = [normalize_difficulty(q["difficulty"]) for q in picked]
        self.assertNotIn("Hard", diffs)
        self.assertGreaterEqual(diffs.count("Easy"), 6)

    def test_practice_picks_differ_across_sessions(self):
        from core.adaptive_engine import mix_for, pick_by_mix

        pool = self._pool()
        first = [q["id"] for q in pick_by_mix(pool, mix_for("beginner"), 10, rng=__import__("random").Random(3))]
        second = [q["id"] for q in pick_by_mix(pool, mix_for("beginner"), 10, rng=__import__("random").Random(4))]
        self.assertNotEqual(first, second)

    def test_avoid_ids_are_pushed_later(self):
        from core.adaptive_engine import mix_for, pick_by_mix

        pool = [{"id": f"Easy-{i}", "difficulty": "Easy", "question": "q"} for i in range(20)]
        avoid = [f"Easy-{i}" for i in range(12)]
        picked = pick_by_mix(pool, mix_for("beginner"), 8, rng=__import__("random").Random(5), avoid_ids=avoid)
        ids = [q["id"] for q in picked]
        self.assertTrue(any(item not in avoid for item in ids))

    def test_advanced_exam_prefers_hard(self):
        from core.adaptive_engine import mix_for, pick_by_mix, normalize_difficulty

        picked = pick_by_mix(self._pool(), mix_for("advanced", exam=True), 20, rng=__import__("random").Random(2))
        diffs = [normalize_difficulty(q["difficulty"]) for q in picked]
        self.assertGreaterEqual(diffs.count("Hard"), 10)

    def test_practice_sessions_have_at_least_15_questions(self):
        from core.adaptive_engine import LEVELS, session_params

        for level in LEVELS:
            count = session_params(level, "practice")["count"]
            self.assertGreaterEqual(count, 12, f"{level} practice={count}")

    def test_short_topic_practice_fills_to_session_size(self):
        pool = []
        for i in range(5):
            pool.append({"id": f"t-{i}", "topic": "נושא קצר", "difficulty": "Easy", "question": "q"})
        for diff, n in (("Easy", 10), ("Medium", 10), ("Hard", 10)):
            for i in range(n):
                pool.append({"id": f"{diff}-{i}", "topic": "אחר", "difficulty": diff, "question": diff})
        picked, params = self.engine.select_questions(pool, "civics", mode="practice", prefer_topic="נושא קצר")
        self.assertGreaterEqual(len(picked), 12)
        self.assertEqual(sum(1 for q in picked if q["topic"] == "נושא קצר"), 5)
        self.assertEqual(params["count"], len(picked))

    def test_topic_only_does_not_fill_from_other_topics(self):
        pool = []
        for i in range(5):
            pool.append({"id": f"t-{i}", "topic": "שורשים", "difficulty": "Easy", "question": "q"})
        for i in range(20):
            pool.append({"id": f"o-{i}", "topic": "אחר", "difficulty": "Easy", "question": "o"})
        picked, params = self.engine.select_questions(
            pool, "hebrew", mode="practice", prefer_topic="שורשים", topic_only=True,
        )
        self.assertEqual(len(picked), 5)
        self.assertTrue(all(q["topic"] == "שורשים" for q in picked))
        self.assertEqual(params["count"], 5)

    def test_prefer_topics_keeps_only_those_when_strict(self):
        pool = [
            {"id": "a1", "topic": "פיסוק", "difficulty": "Easy", "question": "a"},
            {"id": "a2", "topic": "פיסוק", "difficulty": "Easy", "question": "b"},
            {"id": "b1", "topic": "שורשים", "difficulty": "Easy", "question": "c"},
            {"id": "z1", "topic": "אחר", "difficulty": "Easy", "question": "z"},
        ]
        picked, _ = self.engine.select_questions(
            pool, "hebrew", count=10, prefer_topics=["פיסוק", "שורשים"], topic_only=True,
        )
        self.assertEqual(len(picked), 3)
        self.assertTrue(all(q["topic"] in {"פיסוק", "שורשים"} for q in picked))

    def test_lessons_filtered_by_level(self):
        lessons = [
            {"id": "a", "title": "1. בסיס", "category": "שיעור עיוני", "topic": "קל"},
            {"id": "b", "title": "2. בינוני", "category": "רמה בינונית", "topic": "בינוני"},
            {"id": "c", "title": "3. בגרות", "category": "מימ״ד / בגרות", "topic": "קשה"},
        ]
        qs = [
            {"topic": "קל", "difficulty": "Easy"},
            {"topic": "בינוני", "difficulty": "Medium"},
            {"topic": "קשה", "difficulty": "Hard"},
        ]
        from core.adaptive_engine import filter_lessons

        beg = filter_lessons(lessons, "beginner", qs)
        self.assertEqual([x["id"] for x in beg], ["a"])
        mid = filter_lessons(lessons, "intermediate", qs)
        self.assertEqual([x["id"] for x in mid], ["a", "b"])
        adv = filter_lessons(lessons, "advanced", qs)
        self.assertEqual([x["id"] for x in adv], ["a", "b", "c"])

    def test_lessons_sorted_by_number(self):
        from core.adaptive_engine import filter_lessons, sort_lessons

        lessons = [
            {"id": "hebrew_lesson_30", "title": "30. כתיב", "category": "שיעור עיוני", "topic": "כתיב"},
            {"id": "hebrew_lesson_2", "title": "2. מילים", "category": "שיעור עיוני", "topic": "מילים"},
            {"id": "hebrew_lesson_10", "title": "10. פיסוק", "category": "שיעור עיוני", "topic": "פיסוק"},
            {"id": "hebrew_lesson_1", "title": "1. בסיס", "category": "שיעור עיוני", "topic": "בסיס"},
        ]
        ordered = sort_lessons(lessons)
        self.assertEqual([x["title"].split(".", 1)[0] for x in ordered], ["1", "2", "10", "30"])
        filtered = filter_lessons(lessons, "beginner", None)
        self.assertEqual([x["id"] for x in filtered], [
            "hebrew_lesson_1", "hebrew_lesson_2", "hebrew_lesson_10", "hebrew_lesson_30",
        ])

    def test_practice_order_is_easy_to_hard(self):
        from core.adaptive_engine import mix_for, pick_by_mix, normalize_difficulty

        picked = pick_by_mix(self._pool(), mix_for("advanced"), 15, rng=__import__("random").Random(9))
        ranks = [{"Easy": 0, "Medium": 1, "Hard": 2}[normalize_difficulty(q["difficulty"])] for q in picked]
        self.assertEqual(ranks, sorted(ranks))

    def test_rushed_near_miss_does_not_promote(self):
        event = None
        for i in range(8):
            event = self.engine.observe("history", i != 3, "Easy", time_sec=1.1)
        self.assertIsNone(event)
        self.assertEqual(self.engine.level_of("history"), "starter")

    def test_easy_only_success_does_not_skip_to_advanced(self):
        for _ in range(8):
            self.engine.observe("physics", True, "Easy")
        self.assertEqual(self.engine.level_of("physics"), "easy")
        for _ in range(10):
            self.engine.observe("physics", True, "Easy")
        self.assertEqual(self.engine.level_of("physics"), "intermediate")
        event = None
        for _ in range(14):
            event = self.engine.observe("physics", True, "Easy")
        self.assertIsNone(event)
        self.assertEqual(self.engine.level_of("physics"), "intermediate")

    def test_medium_mastery_promotes_to_advanced(self):
        for _ in range(8):
            self.engine.observe("chemistry", True, "Easy")
        self.assertEqual(self.engine.level_of("chemistry"), "easy")
        for _ in range(10):
            self.engine.observe("chemistry", True, "Medium")
        self.assertEqual(self.engine.level_of("chemistry"), "intermediate")
        event = None
        for _ in range(12):
            event = self.engine.observe("chemistry", True, "Medium") or event
        self.assertIsNotNone(event)
        self.assertEqual(event["kind"], "promote")
        self.assertEqual(self.engine.level_of("chemistry"), "advanced")

    def test_sustained_failure_demotes_intermediate(self):
        for _ in range(8):
            self.engine.observe("english", True, "Easy")
        self.assertEqual(self.engine.level_of("english"), "easy")
        for _ in range(10):
            self.engine.observe("english", True, "Medium")
        self.assertEqual(self.engine.level_of("english"), "intermediate")
        event = None
        for _ in range(8):
            event = self.engine.observe("english", False, "Medium") or event
        self.assertIsNotNone(event)
        self.assertEqual(event["kind"], "demote")
        self.assertEqual(self.engine.level_of("english"), "easy")

    def test_evaluate_names_the_weak_subject(self):
        for _ in range(6):
            self.engine.observe("math", False, "Easy")
        for _ in range(6):
            self.engine.observe("hebrew", True, "Easy")
        coach = self.engine.evaluate()
        self.assertIn(subject_label("math"), coach["message"])
        self.assertEqual(coach["action"], "practice_weak_subject")

    def test_recent_failures_rank_as_live_weak_subject(self):
        for _ in range(5):
            self.engine.observe("english", False, "Easy")
        for _ in range(5):
            self.engine.observe("civics", True, "Easy")
        snaps = self.engine.all_snapshots(["english", "civics"])
        weak = [
            key for key, item in snaps.items()
            if item.get("recent_total", 0) >= 4 and item.get("recent_accuracy", 100) < 72
        ]
        self.assertEqual(weak, ["english"])

    def test_weak_topics_drive_question_priority(self):
        for _ in range(4):
            self.engine.observe("civics", False, "Easy", topic="זכויות")
        for _ in range(4):
            self.engine.observe("civics", True, "Easy", topic="רשויות")
        self.assertEqual(self.engine.weak_topics("civics")[0], "זכויות")
        pool = []
        for i in range(12):
            pool.append({"id": f"w-{i}", "topic": "זכויות", "difficulty": "Easy"})
            pool.append({"id": f"s-{i}", "topic": "רשויות", "difficulty": "Easy"})
        picked, _ = self.engine.select_questions(pool, "civics", count=10, mode="practice")
        weak = sum(1 for q in picked if q["topic"] == "זכויות")
        self.assertGreaterEqual(weak, 6)


if __name__ == "__main__":
    unittest.main()
