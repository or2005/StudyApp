import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import VERSION
from core.storage import UserStorage
from core import telemetry, updates


class VersionCompareTests(unittest.TestCase):
    def test_parse_and_compare(self):
        self.assertEqual(updates.parse_version("4.3.0"), (4, 3, 0))
        self.assertEqual(updates.parse_version("v4.10.2"), (4, 10, 2))
        self.assertTrue(updates.is_newer("4.3.1", "4.3.0"))
        self.assertTrue(updates.is_newer("5.0.0", "4.9.9"))
        self.assertFalse(updates.is_newer("4.3.0", "4.3.0"))
        self.assertFalse(updates.is_newer("4.2.9", "4.3.0"))

    def test_current_version_is_451(self):
        self.assertEqual(VERSION, "4.5.1")
        self.assertFalse(updates.is_newer(VERSION, VERSION))


class LocalUpdateTests(unittest.TestCase):
    def test_missing_file_is_rejected(self):
        result = updates.apply_local_file(os.path.join(tempfile.gettempdir(), "no-such-studyapp.exe"))
        self.assertFalse(result.get("ok"))
        self.assertIn("לא נמצא", result.get("message", ""))

    def test_random_file_is_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
            handle.write(b"not an update")
            path = handle.name
        try:
            result = updates.apply_local_file(path)
            self.assertFalse(result.get("ok"))
        finally:
            os.remove(path)


class TelemetryPrivacyTests(unittest.TestCase):
    def _storage(self, folder):
        storage = UserStorage(path=os.path.join(folder, "user_profile.json"))
        storage.save_student("אור דדשב", 17, "123456789")
        storage.set_pref("telemetry_opt_in", True)
        return storage

    def test_payload_has_only_allowed_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            storage = self._storage(folder)
            payload = telemetry.anonymous_payload(storage, "hello")
            self.assertEqual(set(payload.keys()), set(telemetry.ALLOWED_KEYS))
            self.assertEqual(payload["event"], "hello")
            self.assertEqual(payload["version"], VERSION)
            blob = json.dumps(payload, ensure_ascii=False)
            self.assertNotIn("אור דדשב", blob)
            self.assertNotIn("123456789", blob)
            for hint in ("name", "age", "idn", "student", "email", "question"):
                self.assertNotIn(hint, payload)

    def test_opt_out_sends_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            storage = UserStorage(path=os.path.join(folder, "user_profile.json"))
            storage.save_student("שם סודי", 16, "000000000")
            storage.set_pref("telemetry_opt_in", False)
            with patch("core.telemetry.urlopen") as mocked:
                result = telemetry.send_ping(storage, "hello")
                mocked.assert_not_called()
            self.assertFalse(result.get("ok"))
            self.assertIn("כבוי", result.get("message", ""))

    def test_validate_rejects_personal_fields(self):
        dirty = {
            "event": "hello",
            "version": VERSION,
            "os": "Windows",
            "os_ver": "10",
            "arch": "AMD64",
            "frozen": False,
            "install_id": "abc",
            "ts": "2026-09-02T00:00:00Z",
            "name": "אור",
            "age": 17,
        }
        clean = telemetry.validate_payload(dirty)
        self.assertNotIn("name", clean)
        self.assertNotIn("age", clean)
        self.assertEqual(set(clean.keys()) <= set(telemetry.ALLOWED_KEYS), True)

    def test_crash_ping_stays_anonymous(self):
        with tempfile.TemporaryDirectory() as folder:
            storage = self._storage(folder)
            captured = {}

            def fake_send(st, event, force=False):
                captured["event"] = event
                captured["payload"] = telemetry.anonymous_payload(st, event)
                return {"ok": True}

            with patch("core.telemetry.send_ping", fake_send):
                telemetry.send_crash(storage, ValueError("secret student name"))
            self.assertTrue(str(captured.get("event", "")).startswith("crash:"))
            blob = json.dumps(captured["payload"], ensure_ascii=False)
            self.assertNotIn("אור דדשב", blob)
            self.assertNotIn("secret student name", blob)


if __name__ == "__main__":
    unittest.main()
