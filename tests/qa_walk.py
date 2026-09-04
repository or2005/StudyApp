"""QA walkthrough of the live CustomTkinter StudyApp window."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import tkinter as tk
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.chdir(ROOT)

# Isolate user data so real profile is not touched.
TMP = tempfile.mkdtemp(prefix="studyapp-qa-")
os.environ["LOCALAPPDATA"] = TMP
os.environ["APPDATA"] = TMP

from core import dialogs

DIALOGS: list[str] = []


def _log_dialog(kind, title, text):
    DIALOGS.append(f"{kind}: {title}, {text}")
    print(f"  [dialog] {kind}: {title}")


dialogs.info = lambda t, x: _log_dialog("info", t, x)
dialogs.error = lambda t, x: _log_dialog("error", t, x)
dialogs.confirm = lambda t, x: True

from ui.app import StudyApp
from ui.screens.onboarding import OnboardingFrame
from ui.screens.practice import PracticeScreen
from ui.screens.lesson import LessonScreen

REPORT: list[str] = []
SLOW: list[str] = []
BUGS: list[str] = []
SHOT_DIR = os.path.join(ROOT, "_qa_shots")
os.makedirs(SHOT_DIR, exist_ok=True)


def note(msg: str) -> None:
    print(msg)
    REPORT.append(msg)


def bug(msg: str) -> None:
    print("BUG:", msg)
    BUGS.append(msg)


def strip_rtl(text: str) -> str:
    from core.rtltext import strip_marks

    return strip_marks(text or "").strip()


def walk(widget):
    yield widget
    try:
        kids = widget.winfo_children()
    except Exception:
        return
    for child in kids:
        yield from walk(child)


def buttons(root):
    import customtkinter as ctk

    from ui.fast import FastButton, TkButton
    from ui.widgets import ModernButton

    found = []
    for w in walk(root):
        try:
            if isinstance(w, (ctk.CTkButton, tk.Button, TkButton, FastButton, ModernButton)):
                found.append(w)
        except Exception:
            continue
    return found


def click_named(root, *needles: str) -> bool:
    for btn in buttons(root):
        try:
            txt = strip_rtl(str(btn.cget("text") or ""))
        except Exception:
            continue
        for needle in needles:
            if needle in txt:
                cmd = btn.cget("command")
                if cmd:
                    cmd()
                    return True
    return False


def fill_entries(root, values: list[str]) -> int:
    filled = 0
    for w in walk(root):
        name = w.__class__.__name__
        if name in {"CTkEntry", "Entry"}:
            if filled >= len(values):
                break
            try:
                w.delete(0, "end")
                w.insert(0, values[filled])
                filled += 1
            except Exception:
                continue
    return filled


def pump(app, ms: int = 80) -> None:
    app.update()
    app.update_idletasks()
    deadline = time.time() + ms / 1000
    while time.time() < deadline:
        app.update()
        time.sleep(0.01)


def timed(label: str, fn, limit_ms: int = 400):
    t0 = time.perf_counter()
    try:
        result = fn()
        elapsed = (time.perf_counter() - t0) * 1000
        msg = f"{label}: {elapsed:.0f} ms"
        note(msg)
        if elapsed > limit_ms:
            SLOW.append(msg)
        return result, elapsed
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        bug(f"{label} crashed after {elapsed:.0f} ms: {exc}\n{traceback.format_exc()}")
        return None, elapsed


def shot(app, name: str) -> None:
    pump(app, 50)
    path = os.path.join(SHOT_DIR, f"{name}.png")
    try:
        from PIL import ImageGrab

        x = app.winfo_rootx()
        y = app.winfo_rooty()
        w = app.winfo_width()
        h = app.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(path)
        note(f"screenshot {name} ({w}x{h})")
    except Exception as exc:
        note(f"screenshot skipped ({name}): {exc}")


def answer_practice(app, max_q: int = 40) -> int:
    answered = 0
    for _ in range(max_q):
        pump(app, 40)
        screen = None
        for w in walk(app.content):
            if isinstance(w, PracticeScreen):
                screen = w
                break
        if screen is None:
            break
        opts = []
        if getattr(screen, "opts", None):
            try:
                opts = list(screen.opts.winfo_children())
            except Exception:
                opts = []
        if not opts:
            if not click_named(screen, "לשאלה הבאה"):
                break
            continue
        try:
            opts[0].invoke()
        except Exception:
            try:
                cmd = opts[0].cget("command")
                if cmd:
                    cmd()
            except Exception as exc:
                bug(f"option click failed: {exc}")
                break
        answered += 1
        pump(app, 80)
        click_named(app, "לשאלה הבאה")
        pump(app, 80)
        # exam auto-advance
        if getattr(screen, "exam_mode", False):
            pump(app, 750)
    return answered


def finish_diagnostic(app) -> None:
    for i in range(25):
        pump(app, 40)
        frame = None
        for w in walk(app.content):
            if isinstance(w, OnboardingFrame):
                frame = w
                break
        if frame is None:
            return
        if getattr(frame, "selected", None) is not None:
            try:
                frame.selected.set(0)
            except Exception:
                pass
        if not click_named(frame, "הבא", "סיום אבחון", "המשך לדשבורד"):
            # maybe summary already
            if click_named(app, "המשך לדשבורד"):
                pump(app, 200)
                return
            break
        pump(app, 60)
    # wait for thread + summary
    for _ in range(40):
        pump(app, 50)
        if click_named(app, "המשך לדשבורד"):
            pump(app, 150)
            return


def main() -> int:
    note(f"QA temp dir: {TMP}")
    t0 = time.perf_counter()
    app = StudyApp()
    app.geometry("1280x820")
    app.deiconify()
    app.lift()
    app.focus_force()
    pump(app, 200)
    note(f"startup: {(time.perf_counter() - t0) * 1000:.0f} ms")
    shot(app, "01_register")

    filled = fill_entries(app, ["נועה דמה", "16", ""])
    note(f"filled entries: {filled}")
    if filled < 2:
        bug("could not fill registration fields")
    frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
    if frame is not None:
        try:
            frame._terms_ok.set(True)
        except Exception:
            pass
    if not click_named(app, "המשך"):
        bug("registration next button not found")
    pump(app, 120)
    frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
    if frame is not None:
        frame.advance_setup_for_tests()
        frame._stage("diagnostic")
    pump(app, 150)
    shot(app, "02_diagnostic")

    timed("diagnostic 20 questions", lambda: finish_diagnostic(app), 8000)
    pump(app, 250)
    shot(app, "03_dashboard")

    # Sidebar navigation
    for tab, label in (("subjects", "04_subjects"), ("mistakes", "04b_mistakes"), ("settings", "05_settings"), ("about", "06_about"), ("dashboard", "07_dashboard2")):
        _, ms = timed(f"nav {tab}", lambda t=tab: app._nav(t), 250)
        shot(app, label)

    # Settings clicks
    app._nav("settings")
    pump(app, 80)
    click_named(app, "כהה")
    pump(app, 120)
    shot(app, "08_dark")
    click_named(app, "בהיר")
    pump(app, 80)
    click_named(app, "מיקוד")
    pump(app, 80)

    # Subjects: open every subject hub + lesson + practice sample
    from core.adaptive_engine import session_params
    from core.config import HOME_SUBJECTS, SUBJECTS

    app._nav("subjects")
    pump(app, 80)
    for key in HOME_SUBJECTS:
        name = SUBJECTS[key]["name"]
        timed(f"hub {name}", lambda k=key: app._show_subject_hub(k), 500)
        pump(app, 60)
        shot(app, f"hub_{key}")

        timed(f"lessons {name}", lambda k=key: app._start_mode(k, "read"), 500)
        pump(app, 80)
        # open first lesson (רשימת השיעורים היא FastRow, לא CTkButton)
        clicked = False
        from ui.fast import FastRow

        for row in walk(app.content):
            if isinstance(row, FastRow):
                try:
                    row._click()
                    clicked = True
                    break
                except Exception as exc:
                    bug(f"{name}: lesson row click failed: {exc}")
                    break
        if not clicked:
            for btn in buttons(app.content):
                txt = strip_rtl(str(btn.cget("text") or ""))
                if txt.startswith("1."):
                    try:
                        btn.cget("command")()
                        clicked = True
                        break
                    except Exception:
                        continue
        pump(app, 100)
        if not any(isinstance(w, LessonScreen) for w in walk(app.content)):
            bug(f"{name}: lesson screen did not open (clicked={clicked})")
        else:
            shot(app, f"lesson_{key}")
            click_named(app, "תרגול קצר על השיעור")
            pump(app, 100)
            n = answer_practice(app, max_q=4)
            note(f"{name} lesson-practice answered {n}")
            pump(app, 100)
            click_named(app, "חזרה למסך הראשי", "חזרה לבית", "חזרה למקצועות", "חזרה")

        timed(f"practice {name}", lambda k=key: app._start_mode(k, "practice"), 600)
        pump(app, 80)
        n = answer_practice(app, max_q=3)
        note(f"{name} practice answered {n}")
        pump(app, 80)
        # leave results if present
        click_named(app, "חזרה למסך הראשי")
        pump(app, 60)

        # mock: only 3 answers then abandon via finishing remaining would be long.
        # Start mock, answer 2, then force-finish by navigating away.
        timed(f"mock start {name}", lambda k=key: app._start_mode(k, "mock"), 700)
        pump(app, 80)
        n = answer_practice(app, max_q=2)
        level = app.adaptive_engine.level_of(key)
        mock_params = session_params(level, "mock")
        note(f"{name} mock answered {n} (size should be {mock_params['count']})")
        if app.current_session:
            note(f"  mock session total={app.current_session.get_total()} timed={app.current_session.time_limit_sec}")
            if app.current_session.get_total() != mock_params["count"]:
                bug(f"{name} mock size is {app.current_session.get_total()} expected {mock_params['count']}")
            if bool(app.current_session.time_limit_sec) != bool(mock_params["seconds"]):
                bug(f"{name} mock timer mismatch for level {level}")
        app._show_subject_hub(key)
        pump(app, 40)

        timed(f"final start {name}", lambda k=key: app._start_mode(k, "final"), 700)
        pump(app, 80)
        if app.current_mode == "final" and app.current_session:
            final_params = session_params(level, "final")
            note(f"  final total={app.current_session.get_total()} timed={app.current_session.time_limit_sec}")
            if app.current_session.get_total() != final_params["count"]:
                bug(f"{name} final size is {app.current_session.get_total()} expected {final_params['count']}")
            if not app.current_session.time_limit_sec:
                bug(f"{name} final is not timed")
            answer_practice(app, max_q=1)
        else:
            note(f"{name} final locked (dialogs={DIALOGS[-1:]})")
        app._show_subjects()
        pump(app, 40)

    # Smart practice from dashboard
    app._show_dashboard()
    pump(app, 80)
    app._start_smart_practice()
    pump(app, 150)
    n = answer_practice(app, max_q=3)
    note(f"smart practice answered {n}")
    shot(app, "09_smart_or_dialog")

    # Complete a full short practice to hit results screen
    app._start_mode("hebrew", "practice")
    pump(app, 80)
    n = answer_practice(app, max_q=20)
    note(f"full hebrew practice answered {n}")
    pump(app, 200)
    shot(app, "10_results")
    if not click_named(app, "חזרה למסך הראשי"):
        # results might have crashed
        bug("results home button missing, likely crash on results screen")

    pump(app, 80)
    shot(app, "11_after_results")

    note("--- DIALOGS ---")
    for d in DIALOGS:
        note(d)
    note("--- SLOW (>400ms) ---")
    for s in SLOW:
        note(s)
    note("--- BUGS ---")
    for b in BUGS:
        note(b)
    note(f"done in {(time.perf_counter() - t0):.1f}s  bugs={len(BUGS)} slow={len(SLOW)}")

    report_path = os.path.join(ROOT, "_qa_report.txt")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(REPORT + ["", "BUGS:"] + BUGS))
    print("wrote", report_path)

    try:
        app.storage.close()
        app.destroy()
    except Exception:
        pass
    return 1 if BUGS else 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
