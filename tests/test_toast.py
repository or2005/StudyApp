import os
import sys
import tkinter as tk
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.theme import apply_mode
from ui.toast import ToastHost


class ToastHostTests(unittest.TestCase):
    def setUp(self):
        apply_mode("Light")
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_show_creates_and_dismisses_frame(self):
        host = ToastHost(self.root)
        host.show("יעד היום הושלם", "15 שאלות", kind="success", ms=50)
        self.root.update_idletasks()
        self.assertIsNotNone(host._frame)
        texts = []

        def walk(widget):
            try:
                texts.append(str(widget.cget("text") or ""))
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                walk(child)

        walk(host._frame)
        blob = " ".join(texts)
        self.assertIn("יעד היום הושלם", blob)
        host.dismiss()
        self.assertIsNone(host._frame)

    def test_second_show_replaces_first(self):
        host = ToastHost(self.root)
        host.show("אחת", ms=5000)
        first = host._frame
        host.show("שתיים", ms=5000)
        self.assertIsNot(host._frame, first)
        host.dismiss()


if __name__ == "__main__":
    unittest.main()
