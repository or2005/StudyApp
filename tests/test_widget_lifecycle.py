import os
import sys
import tkinter as tk
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.applog import is_stale_widget_error
from ui.fast import FastButton, FastScroll, ThinScrollbar, TkButton, widget_alive


class StaleErrorTests(unittest.TestCase):
    def test_bad_window_path_is_stale(self):
        err = tk.TclError('bad window path name ".!fastscroll.!canvas.!frame.!aboutscreen"')
        self.assertTrue(is_stale_widget_error(err))

    def test_invalid_command_on_widget_is_stale(self):
        err = tk.TclError('invalid command name ".!fastscroll.!thinscrollbar"')
        self.assertTrue(is_stale_widget_error(err))

    def test_real_tcl_error_is_not_stale(self):
        self.assertFalse(is_stale_widget_error(tk.TclError('unknown option "-foo"')))
        self.assertFalse(is_stale_widget_error(ValueError("nope")))
        self.assertFalse(is_stale_widget_error(None))

    def test_dead_after_callback_is_stale(self):
        err = tk.TclError('invalid command name "2698806414464update"')
        self.assertTrue(is_stale_widget_error(err))


class WidgetLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_scrollbar_focus_after_destroy(self):
        bar = ThinScrollbar(self.root, command=lambda *a: None)
        bar.destroy()
        self.assertFalse(widget_alive(bar))
        bar.focus()
        bar.focus_set()
        bar.set(0.0, 0.4)
        bar.set_colors("#111111", "#222222")

    def test_fastbutton_hover_after_destroy(self):
        btn = FastButton(self.root, "כהה", command=lambda: None)
        btn.destroy()
        btn._enter()
        btn._leave()
        btn.focus()
        btn.focus_set()

    def test_tkbutton_hover_after_destroy(self):
        btn = TkButton(self.root, text="הגדרות", command=lambda: None)
        btn.destroy()
        btn._enter()
        btn._leave()
        btn.focus()

    def test_fastscroll_set_bg_after_child_gone(self):
        scroll = FastScroll(self.root)
        child = tk.Frame(scroll.body, bg="#abcdef")
        child.pack()
        self.root.update_idletasks()
        child.destroy()
        scroll.set_bg("#f4f1ea")
        scroll.to_top()
        scroll.destroy()
        scroll.set_bg("#111111")
        scroll.to_top()
        self.assertFalse(widget_alive(scroll))


if __name__ == "__main__":
    unittest.main()
