"""Open the real StudyApp window, click through screens, and capture what a student sees."""
from __future__ import annotations

import os
import re
import sys
import tempfile
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

TMP = tempfile.mkdtemp(prefix="studyapp-play-")
os.environ["LOCALAPPDATA"] = TMP
os.environ["APPDATA"] = TMP

from core import dialogs, rtltext

rtltext.set_mode("words")  # English/Russian Windows, where words used to flip

DIALOGS: list[str] = []
BUGS: list[str] = []
NOTES: list[str] = []
FLAGS: list[str] = []
SHOT_DIR = os.path.join(ROOT, "_qa_play")
os.makedirs(SHOT_DIR, exist_ok=True)

_EN = re.compile(r"[A-Za-z]{2,}")
_HEB = re.compile(r"[\u0590-\u05FF]")


def note(msg: str) -> None:
    print(msg, flush=True)
    NOTES.append(msg)


def bug(msg: str) -> None:
    print("BUG:", msg, flush=True)
    BUGS.append(msg)


def flag(msg: str) -> None:
    print("FLAG:", msg, flush=True)
    FLAGS.append(msg)


def _log_dialog(kind, title, text):
    DIALOGS.append(f"{kind}: {title} | {text}")
    print(f"  [dialog] {kind}: {title}", flush=True)


dialogs.info = lambda t, x: _log_dialog("info", t, x)
dialogs.error = lambda t, x: _log_dialog("error", t, x)
dialogs.confirm = lambda t, x: True
dialogs.choose = lambda *a, **k: 0

from core.config import ALL_SUBJECTS, HOME_SUBJECTS, SUBJECTS, is_coming_soon
from core.rtltext import strip_marks
from ui.app import StudyApp
from ui.fast import FastRow
from ui.screens.lesson import LessonScreen
from ui.screens.onboarding import OnboardingFrame
from ui.screens.practice import PracticeScreen
from ui.screens.results import ResultsScreen
from ui.widgets import OptionTile


def walk(widget):
    yield widget
    try:
        kids = widget.winfo_children()
    except Exception:
        return
    for child in kids:
        yield from walk(child)


def pump(app, ms: int = 80) -> None:
    deadline = time.time() + ms / 1000
    while time.time() < deadline:
        try:
            app.update()
        except Exception:
            break
        time.sleep(0.008)


def shot(app, name: str) -> None:
    pump(app, 80)
    path = os.path.join(SHOT_DIR, f"{name}.png")
    try:
        from PIL import ImageGrab

        app.deiconify()
        app.lift()
        app.focus_force()
        pump(app, 60)
        x, y = app.winfo_rootx(), app.winfo_rooty()
        w, h = app.winfo_width(), app.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)
        note(f"shot {name} ({w}x{h})")
    except Exception as exc:
        note(f"shot skipped {name}: {exc}")


def visible_labels(root) -> list[str]:
    out = []
    for w in walk(root):
        try:
            txt = strip_marks(str(w.cget("text") or "")).strip()
        except Exception:
            continue
        if txt:
            out.append(txt)
    return out


def inspect_labels(root, where: str) -> None:
    for txt in visible_labels(root):
        if "Traceback" in txt or "Exception" in txt:
            bug(f"{where}: traceback on screen: {txt[:80]}")
        if txt in {"None", "null", "undefined", "nan"}:
            bug(f"{where}: empty/placeholder label {txt!r}")
        en = _EN.findall(txt)
        if len(en) >= 4:
            # flipped English often starts with a trailing word + period
            if re.search(r"^[A-Za-z]+\.\s+[a-z]+", txt):
                flag(f"{where}: English may be reversed: {txt[:90]}")
            joined = " ".join(en)
            if joined != " ".join(reversed(en)) and " ".join(reversed(en[:4])) == " ".join(en[:4][::-1]):
                pass
        if len(txt) <= 2 and _HEB.search(txt) and txt not in {"א", "ב", "ג", "ד", "‹"}:
            flag(f"{where}: tiny Hebrew fragment {txt!r}")


def buttons(root):
    found = []
    for w in walk(root):
        name = w.__class__.__name__
        if name in {"CTkButton", "ModernButton", "GhostButton", "TkButton", "FastButton", "Button"}:
            found.append(w)
    return found


def click_named(root, *needles: str) -> bool:
    for btn in buttons(root):
        try:
            txt = strip_marks(str(btn.cget("text") or ""))
        except Exception:
            continue
        if any(n in txt for n in needles):
            cmd = btn.cget("command")
            if cmd:
                cmd()
                return True
    return False


def practice_screen(app):
    for w in walk(app.content):
        if isinstance(w, PracticeScreen):
            return w
    return None


def dump_question(app, where: str) -> dict | None:
    screen = practice_screen(app)
    if screen is None:
        flag(f"{where}: practice screen missing")
        return None
    q = screen.session.get_current_question() if screen.session else None
    if not q:
        flag(f"{where}: no current question")
        return None
    orig = str(q.get("question") or "")
    visual = rtltext.visual_line(orig)
    labels = visible_labels(screen)
    blob = "\n".join(labels)
    note(f"{where} Q: {orig[:110]}")
    en_orig = _EN.findall(orig)
    en_vis = _EN.findall(visual)
    if len(en_orig) >= 3 and en_vis == list(reversed(en_orig)):
        bug(f"{where}: English words fully reversed in visual_line: {orig[:80]}")
    if "She" in orig and "homework" in orig.lower() and "homework. her" in visual.lower():
        bug(f"{where}: mixed English chunk reversed")
    if not screen.exam_mode:
        if "מה השאלה מבקשת" not in blob:
            flag(f"{where}: practice question has no task prompt. stem={orig[:70]}")
        if len(orig) < 14 and "נרדפת" in orig and "קרובה במשמעות" not in blob:
            flag(f"{where}: short synonym stem not expanded: {orig}")
    inspect_labels(screen, where)
    opts = q.get("options") or []
    for opt in opts:
        vis = rtltext.visual_line(str(opt))
        words = _EN.findall(str(opt))
        if len(words) >= 4 and _EN.findall(vis) == list(reversed(words)):
            bug(f"{where}: option English reversed: {opt}")
    return q


def answer_one(app, prefer_wrong: bool = False) -> bool:
    screen = practice_screen(app)
    if screen is None:
        return False
    q = screen.session.get_current_question()
    if not q:
        return False
    if screen._is_compose(q):
        try:
            expected = str(q.get("correct_answer") or "x")
            if getattr(screen, "_typed", None) is not None:
                screen._typed.set(expected)
            elif getattr(screen, "_answer_box", None) is not None:
                screen._answer_box.insert("1.0", expected)
            screen._submit_text()
            pump(app, 50)
            click_named(app, "לשאלה הבאה")
            return True
        except Exception as exc:
            bug(f"compose submit failed: {exc}")
            return False
    idx = 0
    if prefer_wrong and isinstance(q.get("answer"), int):
        idx = 0 if q.get("answer") != 0 else 1
    try:
        screen._choose(idx)
    except Exception as exc:
        bug(f"choose failed: {exc}")
        return False
    pump(app, 50)
    if not screen.exam_mode:
        click_named(app, "לשאלה הבאה")
        pump(app, 40)
    else:
        pump(app, 280)
    return True


def finish_diagnostic(app) -> None:
    for _ in range(30):
        pump(app, 30)
        frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
        if frame is None:
            return
        if getattr(frame, "questions", None) and frame.q_index < len(frame.questions):
            try:
                frame._pick(0)
                frame._next_question()
            except Exception as exc:
                bug(f"diagnostic failed: {exc}")
                return
            continue
        try:
            frame.on_done()
            pump(app, 160)
            return
        except Exception:
            if click_named(app, "המשך לדשבורד"):
                pump(app, 120)
            return


def unlock_exams(app) -> None:
    for key in HOME_SUBJECTS:
        for i in range(22):
            app.storage.record_answer(key, "כללי", True, 0.8, question_id=f"{key}-play-{i}")


def click_all_sidebar(app) -> None:
    names = [strip_marks(str(b.cget("text") or "")) for b in buttons(app)]
    note("sidebar-ish buttons: " + " | ".join(n for n in names if n)[:400])
    for tab, label in (
        ("subjects", "nav_subjects"),
        ("meimad", "nav_meimad"),
        ("general_exam", "nav_general"),
        ("mistakes", "nav_mistakes"),
        ("settings", "nav_settings"),
        ("about", "nav_about"),
        ("dashboard", "nav_dashboard"),
    ):
        try:
            app._nav(tab)
            pump(app, 70)
            inspect_labels(app.content, tab)
            shot(app, label)
        except Exception as exc:
            bug(f"nav {tab} crashed: {exc}\n{traceback.format_exc()}")


def play_subject(app, key: str) -> None:
    name = SUBJECTS[key]["name"]
    note(f"===== {name} =====")
    if is_coming_soon(key):
        try:
            app._show_subject_hub(key)
            pump(app, 50)
            shot(app, f"hub_{key}_soon")
        except Exception as exc:
            bug(f"{name} coming-soon hub crashed: {exc}")
        return
    try:
        app._show_subject_hub(key)
        pump(app, 70)
        inspect_labels(app.content, f"hub {name}")
        shot(app, f"hub_{key}")
    except Exception as exc:
        bug(f"{name} hub crashed: {exc}\n{traceback.format_exc()}")
        return

    try:
        app._start_mode(key, "read")
        pump(app, 80)
        inspect_labels(app.content, f"lessons {name}")
        shot(app, f"lessons_{key}")
        clicked = False
        for row in walk(app.content):
            if isinstance(row, FastRow):
                row._click()
                clicked = True
                break
        pump(app, 90)
        if not any(isinstance(w, LessonScreen) for w in walk(app.content)):
            flag(f"{name}: lesson did not open (clicked={clicked})")
        else:
            inspect_labels(app.content, f"lesson {name}")
            shot(app, f"lesson_{key}")
            if click_named(app, "תרגול קצר על השיעור"):
                pump(app, 90)
                dump_question(app, f"{name} guided")
                shot(app, f"guided_{key}")
                answer_one(app)
                pump(app, 40)
                click_named(app, "חזרה", "חזרה למסך הראשי")
    except Exception as exc:
        bug(f"{name} lesson crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode(key, "practice")
        pump(app, 80)
        dump_question(app, f"{name} practice1")
        shot(app, f"practice_{key}_q1")
        answer_one(app)
        pump(app, 50)
        dump_question(app, f"{name} practice2")
        shot(app, f"practice_{key}_q2")
        answer_one(app, prefer_wrong=True)
        pump(app, 50)
        if practice_screen(app) and not practice_screen(app).exam_mode:
            shot(app, f"feedback_{key}")
        click_named(app, "לשאלה הבאה")
        pump(app, 40)
        click_named(app, "חזרה למסך הראשי", "חזרה")
    except Exception as exc:
        bug(f"{name} practice crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode(key, "compose")
        pump(app, 80)
        if practice_screen(app):
            dump_question(app, f"{name} compose")
            shot(app, f"compose_{key}")
            answer_one(app)
        app._show_subject_hub(key)
    except Exception as exc:
        bug(f"{name} compose crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode(key, "mock")
        pump(app, 80)
        dump_question(app, f"{name} mock")
        shot(app, f"mock_{key}")
        answer_one(app)
        app._show_subject_hub(key)
    except Exception as exc:
        bug(f"{name} mock crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode(key, "final")
        pump(app, 80)
        if practice_screen(app) and app.current_mode == "final":
            dump_question(app, f"{name} final")
            shot(app, f"final_{key}")
            answer_one(app)
        else:
            note(f"{name} final still locked or missing")
        app._show_subjects()
    except Exception as exc:
        bug(f"{name} final crashed: {exc}\n{traceback.format_exc()}")


def main() -> int:
    note(f"temp profile: {TMP}")
    note(f"rtl mode: {rtltext.get_mode()} resolved={rtltext.resolved_mode()}")
    t0 = time.perf_counter()
    app = StudyApp()
    app.geometry("1280x820")
    app.deiconify()
    app.lift()
    pump(app, 200)
    shot(app, "01_register")
    inspect_labels(app.content, "register")

    frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
    if frame is None:
        bug("registration screen missing")
    else:
        try:
            frame.name_var.set("נועה בדיקה")
            frame.age_var.set("16")
            frame.id_var.set("")
            frame._submit_details()
        except Exception as exc:
            bug(f"register submit: {exc}")
    pump(app, 120)
    shot(app, "02_diagnostic")
    finish_diagnostic(app)
    pump(app, 220)
    shot(app, "03_dashboard")
    inspect_labels(app.content, "dashboard")

    click_all_sidebar(app)

    app._nav("settings")
    pump(app, 80)
    click_named(app, "כהה")
    pump(app, 120)
    shot(app, "settings_dark")
    click_named(app, "בהיר")
    pump(app, 80)
    inspect_labels(app.content, "settings")

    unlock_exams(app)

    for key in ALL_SUBJECTS:
        play_subject(app, key)

    try:
        app._show_meimad_hub()
        pump(app, 80)
        inspect_labels(app.content, "meimad hub")
        shot(app, "meimad_hub")
        app._start_meimad_exam()
        pump(app, 100)
        dump_question(app, "meimad q1")
        shot(app, "meimad_q1")
        answer_one(app)
        pump(app, 80)
        dump_question(app, "meimad q2")
        shot(app, "meimad_q2")
        app._show_results()
        pump(app, 150)
        shot(app, "meimad_results")
    except Exception as exc:
        bug(f"meimad crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._show_general_exam_hub()
        pump(app, 80)
        inspect_labels(app.content, "general hub")
        shot(app, "general_hub")
        app._start_general_exam()
        pump(app, 100)
        dump_question(app, "general q1")
        shot(app, "general_q1")
        answer_one(app)
        app._show_results()
        pump(app, 150)
        shot(app, "general_results")
        if any(isinstance(w, ResultsScreen) for w in walk(app.content)):
            note("general used ResultsScreen")
    except Exception as exc:
        bug(f"general exam crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._show_dashboard()
        pump(app, 80)
        app._start_smart_practice()
        pump(app, 100)
        dump_question(app, "smart")
        shot(app, "smart_practice")
        answer_one(app)
    except Exception as exc:
        bug(f"smart practice crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode("hebrew", "practice")
        pump(app, 80)
        for _ in range(12):
            if not answer_one(app):
                break
        pump(app, 150)
        shot(app, "results_hebrew")
        inspect_labels(app.content, "results")
        if not any(isinstance(w, ResultsScreen) for w in walk(app.content)):
            flag("hebrew full practice did not reach results")
    except Exception as exc:
        bug(f"results crashed: {exc}\n{traceback.format_exc()}")

    app._nav("mistakes")
    pump(app, 120)
    inspect_labels(app.content, "mistakes")
    shot(app, "mistakes_filled")

    note("--- DIALOGS ---")
    for d in DIALOGS:
        note(d)
    note(f"--- FLAGS ({len(FLAGS)}) ---")
    for item in FLAGS:
        note(item)
    note(f"--- BUGS ({len(BUGS)}) ---")
    for item in BUGS:
        note(item)
    note(f"done in {time.perf_counter() - t0:.1f}s")

    report = os.path.join(ROOT, "_qa_play_report.txt")
    with open(report, "w", encoding="utf-8") as handle:
        handle.write("\n".join(NOTES + ["", "FLAGS:", *FLAGS, "", "BUGS:", *BUGS, "", "DIALOGS:", *DIALOGS]))
    print("wrote", report, flush=True)

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
