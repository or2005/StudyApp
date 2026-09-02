import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import custom_questions, nativeos, profiles
from core.loader import clear_cache, load_subject
from core.parent_report import build_report, write_report
from core.storage import UserStorage


class ProfileIsolationTests(unittest.TestCase):
    def test_legacy_files_move_into_default_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = os.path.join(tmp, "user_profile.json")
            with open(legacy, "w", encoding="utf-8") as handle:
                json.dump({"student": {"name": "נועה"}}, handle, ensure_ascii=False)
            profiles.ensure_migrated(tmp)
            dest = profiles.profile_files("default", tmp)["user_profile"]
            self.assertTrue(os.path.isfile(dest))
            self.assertFalse(os.path.isfile(legacy))
            with open(dest, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["student"]["name"], "נועה")

    def test_switch_keeps_progress_apart(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles.ensure_migrated(tmp)
            first = profiles.current_files(tmp)
            store_a = UserStorage(path=first["user_profile"])
            store_a.save_student("נועה", 16, "")
            store_a.close()
            pid = profiles.create_profile("יואב", tmp)
            self.assertTrue(profiles.switch_profile(pid, tmp))
            store_b = UserStorage(path=profiles.current_files(tmp)["user_profile"])
            store_b.save_student("יואב", 14, "")
            store_b.close()
            names = {item["id"]: item["name"] for item in profiles.list_profiles(tmp)}
            self.assertEqual(names["default"], "תלמיד")
            self.assertIn("יואב", names.values())
            profiles.switch_profile("default", tmp)
            again = UserStorage(path=profiles.current_files(tmp)["user_profile"])
            self.assertEqual(again.get_student().get("name"), "נועה")
            again.close()

    def test_cannot_delete_last_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles.ensure_migrated(tmp)
            self.assertIsNone(profiles.delete_profile("default", tmp))
            self.assertEqual(len(profiles.list_profiles(tmp)), 1)

    def test_os_reminder_pref_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles.ensure_migrated(tmp)
            profiles.set_os_pref("daily_reminder", True, tmp)
            profiles.set_os_pref("reminder_hour", 19, tmp)
            self.assertTrue(profiles.get_os_pref("daily_reminder", False, tmp))
            self.assertEqual(profiles.get_os_pref("reminder_hour", 17, tmp), 19)


class CustomQuestionTests(unittest.TestCase):
    def test_merge_into_subject_bank(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = custom_questions.add_question(
                "civics",
                "מהי זכות יסוד במדינה דמוקרטית?",
                ["חופש הביטוי", "חובת שירות בלבד", "רק זכות הצבעה", "אין זכויות"],
                0,
                "חופש הביטוי היא זכות יסוד שמגינה על האזרח מפני השתקה.",
                "זכויות",
                "Easy",
                root=tmp,
            )
            merged = custom_questions.merge_into("civics", {"questions": []}, root=tmp)
            ids = [row.get("id") for row in merged["questions"]]
            self.assertIn(item["id"], ids)
            self.assertTrue(item.get("custom"))

    def test_loader_includes_custom_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = custom_questions.add_question(
                "history",
                "באיזו שנה הוקמה מדינת ישראל?",
                ["1948", "1967", "1973", "1917"],
                0,
                "מדינת ישראל הוקמה בשנת 1948, אחרי החלטת האומות המאוחדות.",
                "הקמת המדינה",
                root=tmp,
            )
            with patch("core.custom_questions.get_persistent_app_dir", return_value=tmp):
                clear_cache()
                data = load_subject("history") or {}
            ids = [str(row.get("id")) for row in data.get("questions") or []]
            self.assertIn(item["id"], ids)

    def test_rejects_banned_placeholder(self):
        error = custom_questions.validate_draft(
            "hebrew",
            "שאלה עם גרסה שגויה בפנים",
            ["א", "ב", "ג", "ד"],
            0,
            "הסבר ארוך מספיק כדי לעבור את הרף המינימלי.",
        )
        self.assertIsNotNone(error)


class ParentReportTests(unittest.TestCase):
    def test_report_contains_student_and_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "user_profile.json")
            storage = UserStorage(path=path)
            storage.save_student("נועה כהן", 16, "")
            storage.set("progress", {"hebrew": {"total": 20, "correct": 16, "time_sec": 90}})
            storage.set("last_activity", "2026-09-02 18:00")
            storage.flush()
            report = build_report(storage, insight="חזקו לשון.")
            self.assertIn("נועה כהן", report["text"])
            self.assertIn("נועה כהן", report["html"])
            self.assertIn("80", report["text"])
            self.assertIn("חזקו לשון", report["text"])
            out = os.path.join(tmp, "weekly.html")
            write_report(out, report)
            with open(out, "r", encoding="utf-8") as handle:
                body = handle.read()
            self.assertIn("dir=\"rtl\"", body)
            storage.close()


class NativeOsTests(unittest.TestCase):
    def test_parse_reminder_time(self):
        self.assertEqual(nativeos.parse_hhmm("19:05"), (19, 5))
        self.assertEqual(nativeos.parse_hhmm("7"), (7, 0))
        self.assertEqual(nativeos.parse_hhmm("bad"), (17, 0))

    def test_launch_argv_includes_remind_flag(self):
        argv = nativeos.launch_argv("--remind")
        self.assertIn("--remind", argv)
        self.assertGreaterEqual(len(argv), 2)

    def test_autostart_file_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            startup = os.path.join(tmp, "Startup")
            os.makedirs(startup)
            desktop = os.path.join(tmp, "studyapp.desktop")
            with patch.object(nativeos, "_startup_dir_windows", return_value=startup):
                with patch.object(nativeos, "_linux_autostart_path", return_value=desktop):
                    self.assertTrue(nativeos.set_autostart(True))
                    self.assertTrue(nativeos.autostart_enabled())
                    self.assertTrue(nativeos.set_autostart(False))
                    self.assertFalse(nativeos.autostart_enabled())


class ReminderPrefTests(unittest.TestCase):
    def test_nudge_once_per_day(self):
        from core.reminders import maybe_nudge

        class FakeStorage:
            def __init__(self):
                self.prefs = {}

            def get_daily_goal(self):
                return {"is_done": False, "target": 15, "completed": 3}

            def get_student(self):
                return {"name": "נועה"}

            def get_pref(self, key, default=None):
                return self.prefs.get(key, default)

            def set_pref(self, key, value):
                self.prefs[key] = value

        fake = FakeStorage()
        with patch("core.profiles.get_os_pref", return_value=True):
            with patch("core.nativeos.notify", return_value=True) as notify:
                self.assertTrue(maybe_nudge(fake))
                self.assertFalse(maybe_nudge(fake))
                self.assertEqual(notify.call_count, 1)


if __name__ == "__main__":
    unittest.main()
