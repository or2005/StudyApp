import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import CONTACT_EMAIL, DEVELOPER_NAME, DEVELOPER_NAME_EN, copyright_he
from ui.screens.about import TERMS


class AboutIdentityTests(unittest.TestCase):
    def test_developer_and_contact_are_published(self):
        self.assertEqual(DEVELOPER_NAME, "אור דדשב")
        self.assertEqual(DEVELOPER_NAME_EN, "Or Dadshaev")
        self.assertEqual(CONTACT_EMAIL, "dadshaev@gmail.com")
        notice = copyright_he()
        self.assertIn("אור דדשב", notice)
        self.assertIn("כל הזכויות שמורות", notice)
        self.assertIn("2026", notice)

    def test_terms_include_contact_and_limits(self):
        blob = " ".join(title + " " + body for title, body in TERMS)
        self.assertIn(DEVELOPER_NAME, blob)
        self.assertIn(CONTACT_EMAIL, blob)
        self.assertIn("כפי שהיא", blob)
        self.assertGreaterEqual(len(TERMS), 6)

    def test_about_screen_renders_identity(self):
        import customtkinter as ctk

        from ui.screens.about import AboutScreen

        root = ctk.CTk()
        root.withdraw()
        try:
            screen = AboutScreen(root)
            texts: list[str] = []

            def walk(widget):
                try:
                    text = widget.cget("text")
                except Exception:
                    text = ""
                if text:
                    texts.append(str(text))
                for child in widget.winfo_children():
                    walk(child)

            walk(screen)
            blob = " ".join(texts)
            self.assertIn("אור דדשב", blob)
            self.assertIn("dadshaev@gmail.com", blob)
            self.assertIn("כל הזכויות שמורות", blob)
            self.assertIn("תקנון שימוש", blob)
            self.assertIn("פרטיות", blob)
        finally:
            root.destroy()
