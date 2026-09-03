"""Focused live QA after bugfixes: results crash, nav, final exam, screenshots."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
TMP = tempfile.mkdtemp(prefix="studyapp-qa2-")
os.environ["LOCALAPPDATA"] = TMP
os.environ["APPDATA"] = TMP

from core import dialogs

dialogs.info = lambda t, x: print("dialog-info", t)
dialogs.error = lambda t, x: print("dialog-error", t)
dialogs.confirm = lambda t, x: True

from ui.app import StudyApp
from ui.screens.onboarding import OnboardingFrame
from ui.screens.practice import PracticeScreen
from ui.screens.results import ResultsScreen

SHOT = os.path.join(ROOT, "_qa_shots")
os.makedirs(SHOT, exist_ok=True)
BUGS = []


def rtl_strip(t):
    from core.rtltext import strip_marks

    return strip_marks(t or "")


def walk(w):
    yield w
    try:
        for c in w.winfo_children():
            yield from walk(c)
    except Exception:
        return


def pump(app, ms=60):
    end = time.time() + ms / 1000
    while time.time() < end:
        app.update()
        time.sleep(0.01)


def shot(app, name):
    pump(app, 40)
    try:
        from PIL import ImageGrab
        x, y = app.winfo_rootx(), app.winfo_rooty()
        img = ImageGrab.grab(bbox=(x, y, x + app.winfo_width(), y + app.winfo_height()))
        img.save(os.path.join(SHOT, f"{name}.png"))
        print("shot", name, img.size)
    except Exception as e:
        print("shot-fail", name, e)


def buttons(root):
    out = []
    for w in walk(root):
        if w.__class__.__name__ in {"CTkButton", "ModernButton"}:
            out.append(w)
    return out


def click(root, *needles):
    for b in buttons(root):
        try:
            txt = rtl_strip(str(b.cget("text") or ""))
        except Exception:
            continue
        if any(n in txt for n in needles):
            cmd = b.cget("command")
            if cmd:
                cmd()
                return True
    return False


def fill(root, values):
    n = 0
    for w in walk(root):
        if w.__class__.__name__ in {"CTkEntry", "Entry"} and n < len(values):
            w.delete(0, "end")
            w.insert(0, values[n])
            n += 1
    return n


def answer(app, max_q):
    n = 0
    for _ in range(max_q):
        pump(app, 30)
        screen = next((w for w in walk(app.content) if isinstance(w, PracticeScreen)), None)
        if not screen:
            break
        opts = list(screen.opts.winfo_children()) if getattr(screen, "opts", None) else []
        if not opts:
            click(app, "לשאלה הבאה")
            continue
        try:
            opts[0].invoke()
        except Exception:
            cmd = opts[0].cget("command")
            if cmd:
                cmd()
        n += 1
        pump(app, 50)
        click(app, "לשאלה הבאה")
        if getattr(screen, "exam_mode", False):
            pump(app, 750)
    return n


def diagnostic(app):
    for _ in range(25):
        pump(app, 30)
        frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
        if not frame:
            return
        if getattr(frame, "selected", None) is not None:
            frame.selected.set(0)
        if not click(frame, "הבא", "סיום אבחון", "המשך לדשבורד"):
            if click(app, "המשך לדשבורד"):
                pump(app, 120)
                return
            break
        pump(app, 40)
    for _ in range(40):
        pump(app, 40)
        if click(app, "המשך לדשבורד"):
            pump(app, 120)
            return


def main():
    t0 = time.perf_counter()
    app = StudyApp()
    app.geometry("1280x820")
    app.lift()
    pump(app, 200)
    print("startup_ms", round((time.perf_counter() - t0) * 1000))
    shot(app, "01_register")

    fill(app, ["נועה דמה", "16", ""])
    click(app, "המשך למבחן אבחון")
    pump(app, 120)
    shot(app, "02_diagnostic")
    diagnostic(app)
    pump(app, 200)
    shot(app, "03_dashboard")

    for tab, name in (("subjects", "04_subjects"), ("settings", "05_settings"), ("about", "06_about")):
        t1 = time.perf_counter()
        app._nav(tab)
        pump(app, 80)
        print(f"nav_{tab}_ms", round((time.perf_counter() - t1) * 1000))
        shot(app, name)

    t1 = time.perf_counter()
    app._show_subject_hub("hebrew")
    pump(app, 80)
    print("hub_hebrew_ms", round((time.perf_counter() - t1) * 1000))
    shot(app, "07_hub")

    app._start_mode("hebrew", "read")
    pump(app, 80)
    shot(app, "08_lessons")
    click(app, "1.")
    pump(app, 100)
    shot(app, "09_lesson")

    app._start_mode("hebrew", "practice")
    pump(app, 80)
    n = answer(app, 20)
    print("practice_answered", n)
    pump(app, 200)
    has_results = any(isinstance(w, ResultsScreen) for w in walk(app.content))
    print("results_shown", has_results)
    if not has_results:
        BUGS.append("results screen did not appear after practice")
    shot(app, "10_results")
    click(app, "חזרה למסך הראשי")
    pump(app, 80)

    # Unlock final: record enough answers
    for i in range(25):
        app.storage.record_answer("hebrew", "כתיב", True, 1.0)
    print("can_final", app.storage.can_take_final("hebrew"))
    app._start_mode("hebrew", "final")
    pump(app, 100)
    print("final_mode", app.current_mode, "total", app.current_session.get_total() if app.current_session else None,
          "timed", app.current_session.time_limit_sec if app.current_session else None)
    shot(app, "11_final")
    n = answer(app, 3)
    print("final_answered", n)

    app._nav("subjects")
    pump(app, 80)
    shot(app, "12_subjects_end")

    print("BUGS", BUGS)
    print("elapsed", round(time.perf_counter() - t0, 1))
    try:
        app.destroy()
    except Exception:
        pass
    return 1 if BUGS else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
