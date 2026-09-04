import os
import sys
import tempfile
import tkinter as tk
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import COLORS
from core.theme import apply_mode
from ui.fast import FastScroll
from ui.widgets import PAGE_WIDTH, ContextRail, Sidebar


class StudioLayoutTests(unittest.TestCase):
    def setUp(self):
        apply_mode("Light")
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_nav_items_are_plain_labels(self):
        for item in Sidebar.NAV_KEYS:
            self.assertEqual(len(item), 2)
            _key, msg = item
            self.assertFalse(any(ord(ch) > 9000 for ch in msg), msg)

    def test_sidebar_active_uses_bar_not_green_fill(self):
        side = Sidebar(self.root, on_nav=lambda _k: None)
        texts = []
        self._collect_text(side, texts)
        blob = " ".join(texts)
        self.assertIn("StudyApp", blob)
        self.assertIn("הבית", blob)
        self.assertNotIn("ס", blob)
        self.assertTrue(getattr(side, "_logo_photo", None))
        self.assertNotIn("מקצועות", blob)
        self.assertNotIn("למידה בקצב שלך", blob)
        self.assertNotIn("למידה למבחן", blob)
        self.assertNotIn("🎓", blob)
        side.set_active("settings")
        gold = COLORS.get("sidebar_active") or COLORS.get("gold") or COLORS["accent"]
        idle = COLORS.get("sidebar_bg") or COLORS["banner"]
        hover = COLORS.get("sidebar_hover") or COLORS["card_hover"]
        self.assertEqual(side._bars["settings"].cget("bg"), gold)
        self.assertEqual(side.buttons["settings"].cget("fg_color"), hover)
        self.assertEqual(side.buttons["dashboard"].cget("fg_color"), idle)
        self.assertNotEqual(side.buttons["settings"].cget("fg_color"), COLORS["primary"])

    def test_context_rail_lists_status_metrics(self):
        rail = ContextRail(self.root)
        rail.set_data(
            {
                "daily": {"completed": 4, "target": 15, "completion": 26},
                "streak": 3,
                "accuracy": 81,
                "exam_when": "בעוד 12 ימים",
                "exam_label": "מימ״ד",
                "weak_label": "לשון",
                "weak_key": "hebrew",
                "mistakes": 2,
            }
        )
        texts = []
        self._collect_text(rail, texts)
        blob = " ".join(texts)
        self.assertIn("יעד היום", blob)
        self.assertIn("4 / 15", blob)
        self.assertIn("רצף", blob)
        self.assertIn("דיוק", blob)
        self.assertIn("81%", blob)
        self.assertIn("לחיזוק", blob)
        self.assertIn("לשון", blob)
        self.assertIn("הטעויות שלי", blob)
        self.assertIn("דוח ביצועים שבועי", blob)
        self.assertLess(blob.find("הטעויות שלי"), blob.find("דוח ביצועים שבועי"))

    def test_dashboard_grid_starts_on_the_right(self):
        from ui.app import StudyApp

        grid = tk.Frame(self.root)
        first = tk.Label(grid, text="first")
        second = tk.Label(grid, text="second")
        StudyApp._grid_rtl(grid, first, 0)
        StudyApp._grid_rtl(grid, second, 1)
        self.assertEqual(int(first.grid_info()["column"]), 1)
        self.assertEqual(int(second.grid_info()["column"]), 0)

    def test_compact_subject_tile_is_clickable(self):
        from ui.widgets import CompactSubjectTile

        hits = []
        tile = CompactSubjectTile(self.root, "hebrew", "מתחיל", 80, 12, on_open=lambda: hits.append("ok"))
        texts = []
        self._collect_text(tile, texts)
        blob = " ".join(texts)
        self.assertIn("לשון", blob)
        self.assertIn("80", blob)
        self.assertNotIn("הכנס למקצוע", blob)
        self.assertNotIn("המשך לתרגל", blob)
        tile._click()
        self.assertEqual(hits, ["ok"])

    def test_coming_soon_tile_is_dimmed_and_blocked(self):
        from ui.widgets import CompactSubjectTile

        hits = []
        tile = CompactSubjectTile(
            self.root, "arabic", "מתחיל", 80, 12,
            on_open=lambda: hits.append("opened"),
            coming_soon=True,
        )
        texts = []
        self._collect_text(tile, texts)
        blob = " ".join(texts)
        self.assertIn("ערבית", blob)
        self.assertIn("בהכנה", blob)
        self.assertNotIn("הכנס למקצוע", blob)
        tile._click()
        self.assertEqual(hits, [])

    def test_fastscroll_centers_fixed_page_width(self):
        scroll = FastScroll(self.root, max_width=PAGE_WIDTH)
        scroll._on_canvas_configure(type("E", (), {"width": 1100})())
        x, _y = scroll.canvas.coords(scroll._window)
        self.assertEqual(x, (1100 - PAGE_WIDTH) // 2)
        width = int(scroll.canvas.itemcget(scroll._window, "width"))
        self.assertEqual(width, PAGE_WIDTH)

    def _collect_text(self, widget, out):
        try:
            out.append(str(widget.cget("text") or ""))
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._collect_text(child, out)


class AppChromeTests(unittest.TestCase):
    def test_app_shell_has_rail_and_hides_it_in_exam(self):
        from core.diagnostic import EXAM_LENGTH
        from ui.app import StudyApp
        from ui.widgets import DailyBanner, StatChip

        tmp = tempfile.mkdtemp(prefix="studyapp-layout-")
        os.environ["LOCALAPPDATA"] = tmp
        os.environ["APPDATA"] = tmp
        app = StudyApp()
        self.addCleanup(app.destroy)
        app.storage.save_student("נועה", 16, "")
        app.storage.save_diagnostic(
            11, EXAM_LENGTH, "intermediate",
            [{"subject": "hebrew", "correct": False}],
            recommendations=["לחזק לשון"],
            weak_topics=["hebrew"],
        )
        app.storage.set_exam_date("2026-06-15", "מימ״ד")
        app.geometry("1360x800")
        app.update_idletasks()
        app._choose_start_screen()
        app.update_idletasks()
        app.update()
        self.assertTrue(app.sidebar.winfo_ismapped())
        self.assertFalse(app.rail.winfo_ismapped())
        self.assertTrue(app.scroll.winfo_ismapped())
        kinds = [w.__class__.__name__ for w in app.content.winfo_children()]
        self.assertIn("StudioHero", kinds)
        self.assertIn("StartLessonCard", kinds)
        self.assertNotIn("DailyBanner", kinds)
        self.assertNotIn("StatChip", kinds)
        texts = []
        self._collect_text(app.content, texts)
        blob = " ".join(texts)
        self.assertIn("מה עכשיו", blob)
        self.assertIn("נועה", blob)
        self.assertIn("המקצועות שלך", blob)
        self.assertIn("לשון", blob)
        self.assertIn("מתמטיקה", blob)
        self.assertIn("בקרוב", blob)
        self.assertIn("ערבית", blob)
        self.assertNotIn("חשבון וכמותי", blob)
        self.assertNotIn("המשך מאיפה שעצרת", blob)
        self.assertNotIn("דוח להורה", blob)
        self.assertNotIn("דיוק לפי מקצוע", blob)
        self.assertNotIn("חיזוק נקודות חולשה", blob)
        self.assertNotIn("מבחן כללי", blob)
        try:
            from PIL import ImageGrab

            shot_dir = os.path.join(ROOT, "_qa_shots")
            os.makedirs(shot_dir, exist_ok=True)
            app.lift()
            app.update()
            box = (
                app.winfo_rootx(),
                app.winfo_rooty(),
                app.winfo_rootx() + app.winfo_width(),
                app.winfo_rooty() + app.winfo_height(),
            )
            ImageGrab.grab(bbox=box).save(os.path.join(shot_dir, "studio_dashboard.png"))
        except Exception:
            pass
        app._start_mode("hebrew", "mock")
        app.update_idletasks()
        app.update()
        self.assertFalse(app.rail.winfo_ismapped())
        self.assertFalse(app.sidebar.winfo_ismapped())

    def test_theme_and_focus_toggle_do_not_crash(self):
        from core.diagnostic import EXAM_LENGTH
        from ui.app import StudyApp

        tmp = tempfile.mkdtemp(prefix="studyapp-theme-")
        os.environ["LOCALAPPDATA"] = tmp
        os.environ["APPDATA"] = tmp
        app = StudyApp()
        self.addCleanup(app.destroy)
        app.storage.save_student("נועה", 16, "")
        app.storage.save_diagnostic(
            11, EXAM_LENGTH, "intermediate",
            [{"subject": "hebrew", "correct": False}],
            recommendations=["לחזק לשון"],
            weak_topics=["hebrew"],
        )
        app._choose_start_screen()
        app.update()
        app._show_settings()
        app.update()
        texts = []
        self._collect_text(app.content, texts)
        blob = " ".join(texts)
        self.assertIn("תצוגה", blob)
        self.assertIn("גיבוי", blob)
        self.assertNotIn("פינג אנונימי", blob)
        self.assertNotIn("יומן תקלות", blob)
        self.assertNotIn("עורך שאלות", blob)
        self.assertNotIn("בדיקת התראה", blob)
        self.assertIn("עדכוני תוכנה", blob)
        self.assertIn("שפת עזר", blob)
        app._set_theme("Dark")
        app.update()
        self.assertEqual(app.active_tab, "settings")
        app._toggle_focus_mode()
        app.update()
        self.assertTrue(app.focus_mode)
        app._toggle_focus_mode()
        app.update()
        self.assertFalse(app.focus_mode)
        app._set_font_size("קטן")
        app.update()
        app._set_theme("Light")
        app.update()
        self.assertTrue(app.sidebar.winfo_exists())
        self.assertTrue(app.scroll.winfo_exists())

    def _collect_text(self, widget, out):
        try:
            out.append(str(widget.cget("text") or ""))
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._collect_text(child, out)


if __name__ == "__main__":
    unittest.main()
