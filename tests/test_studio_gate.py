import os
import sys
import tkinter as tk
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tempfile
import zipfile

from core.studio_brief import briefing, census_text, count_code_lines, info_text
from core.studio_gate import check
from core.studio_pack import write_source_zip, write_usb_zip
from ui.screens.studio import StudioScreen


class StudioGateTests(unittest.TestCase):
    def test_known_operator_is_accepted(self):
        self.assertTrue(check("ordadshev", "Aa" + "327806" + "279@"))
        self.assertTrue(check("OrDadShev", "Aa" + "327806" + "279@"))

    def test_wrong_password_is_rejected(self):
        self.assertFalse(check("ordadshev", "wrong"))
        self.assertFalse(check("", ""))
        self.assertFalse(check("admin", "Aa" + "327806" + "279@"))

    def test_briefing_names_version_and_paths(self):
        text = briefing()
        self.assertIn("StudyApp", text)
        self.assertIn("DATA_DIR=", text)
        self.assertIn("BANK", text)
        self.assertIn("hebrew", census_text())

    def test_info_text_counts_code_and_questions(self):
        text = info_text()
        self.assertIn("שורות קוד", text)
        self.assertIn("שאלות בכל המקצועות", text)
        self.assertIn("StudyApp Files", text)
        counted = count_code_lines()
        self.assertGreater(counted["files"], 10)
        self.assertGreater(counted["lines"], 100)

    def test_source_zip_skips_venv_and_uses_studio_name(self):
        tmp = tempfile.mkdtemp(prefix="studio-pack-")
        os.makedirs(os.path.join(tmp, "core"))
        os.makedirs(os.path.join(tmp, ".venv", "Lib"))
        with open(os.path.join(tmp, "main.py"), "w", encoding="utf-8") as handle:
            handle.write("print('ok')\n")
        with open(os.path.join(tmp, ".venv", "Lib", "skip.py"), "w", encoding="utf-8") as handle:
            handle.write("nope\n")
        dest = os.path.join(tmp, "StudyAppFiles.zip")
        write_source_zip(dest, root=tmp)
        names = zipfile.ZipFile(dest).namelist()
        self.assertTrue(any(name.startswith("StudyAppFiles/") for name in names))
        self.assertTrue(any(name.endswith("main.py") for name in names))
        self.assertFalse(any(".venv" in name for name in names))
        self.assertTrue(any("איך-לפתוח-ב-VS-Code.txt" in name for name in names))
        self.assertTrue(any(name.endswith("פתח-ב-VS-Code.bat") for name in names))
        self.assertTrue(any(".vscode/settings.json" in name.replace("\\", "/") for name in names))

    def test_usb_zip_has_launcher(self):
        tmp = tempfile.mkdtemp(prefix="studio-usb-")
        with open(os.path.join(tmp, "main.py"), "w", encoding="utf-8") as handle:
            handle.write("print('ok')\n")
        dest = os.path.join(tmp, "StudyApp-USB.zip")
        write_usb_zip(dest, root=tmp)
        names = zipfile.ZipFile(dest).namelist()
        blob = " ".join(names)
        self.assertIn("StudyApp-USB/", blob)
        self.assertTrue(any("הפעל-מהדיסק.bat" in name or name.endswith(".bat") for name in names))

    def test_studio_desk_is_hebrew(self):
        root = tk.Tk()
        root.withdraw()
        try:
            screen = StudioScreen(root, unlocked=True, actions={"info": lambda: "שורות קוד: 1"})
            texts = []

            def collect(widget):
                try:
                    value = widget.cget("text")
                    if value:
                        texts.append(str(value))
                except tk.TclError:
                    pass
                for child in widget.winfo_children():
                    collect(child)

            collect(screen)
            blob = " ".join(texts)
            self.assertIn("חדר מפתח", blob)
            self.assertIn("שמירת קבצי תוכנה", blob)
            self.assertIn("עמודת מידע", blob)
            self.assertIn("חבילת דיסק און קי", blob)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
