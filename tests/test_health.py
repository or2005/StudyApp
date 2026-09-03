import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import health


class HealthScanTests(unittest.TestCase):
    def test_healthy_install_says_ok(self):
        report = health.scan_and_repair()
        self.assertIn("message", report)
        self.assertTrue(report["message"])

    def test_repairs_missing_data_dir(self):
        tmp = tempfile.mkdtemp(prefix="health-")
        missing = os.path.join(tmp, "no-such-data")
        with patch.object(health, "DATA_DIR", missing), patch.object(
            health, "PROFILE_PATH", os.path.join(missing, "user_profile.json")
        ):
            report = health.scan_and_repair()
        self.assertTrue(os.path.isdir(missing))
        self.assertTrue(any("תיקיית הנתונים" in item for item in report["fixed"]))

    def test_quarantines_broken_profile(self):
        tmp = tempfile.mkdtemp(prefix="health-prof-")
        profile = os.path.join(tmp, "user_profile.json")
        with open(profile, "w", encoding="utf-8") as handle:
            handle.write("{not-json")
        with patch.object(health, "DATA_DIR", tmp), patch.object(health, "PROFILE_PATH", profile):
            report = health.scan_and_repair()
        self.assertTrue(os.path.isfile(profile + ".broken"))
        self.assertFalse(os.path.isfile(profile))
        self.assertTrue(any("פרופיל" in item for item in report["fixed"]))
