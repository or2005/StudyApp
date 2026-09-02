import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.platformutil import LINUX_FONTS, apply_ui_font, default_ui_font, is_linux, is_windows
from core.storage import get_persistent_app_dir


class PlatformSupportTests(unittest.TestCase):
    def test_windows_or_linux_font_defaults(self):
        family = default_ui_font()
        self.assertTrue(family)
        if is_windows():
            self.assertEqual(family, "Segoe UI")
        if is_linux():
            self.assertIn(family, LINUX_FONTS + ("DejaVu Sans",))

    def test_apply_ui_font_sets_config(self):
        from core.config import ADHD_CONFIG

        name = apply_ui_font()
        self.assertEqual(ADHD_CONFIG["font_family"], name)
        self.assertTrue(name)

    def test_data_dir_is_writable(self):
        path = get_persistent_app_dir()
        self.assertTrue(os.path.isdir(path))
        probe = os.path.join(path, ".write_probe")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("ok")
        os.remove(probe)

    def test_linux_launcher_is_posix(self):
        script = os.path.join(ROOT, "packaging", "linux", "StudyApp.sh")
        with open(script, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.startswith(b"#!/bin/sh"))
        self.assertNotIn(b"\r\n", raw)
        self.assertIn(b"python3-tk", raw)
        self.assertIn(b"dnf", raw)
        self.assertIn(b"pacman", raw)
        self.assertIn(b"zypper", raw)
        self.assertIn(b"apk add", raw)

    def test_linux_installers_exist(self):
        for rel in (
            "packaging/linux/install.sh",
            "packaging/linux/studyapp.desktop",
            "scripts/install-linux.sh",
        ):
            path = os.path.join(ROOT, rel)
            self.assertTrue(os.path.isfile(path), rel)


if __name__ == "__main__":
    unittest.main()
