"""Extra live stress beyond qa_walk: every subject/mode, skip, timer, restore, settings.

Isolates LOCALAPPDATA. Records native crashes first, then patches just enough
in-process (missing import / dashboard card) to keep exercising other screens.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

TMP = tempfile.mkdtemp(prefix="studyapp-stress-")
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
dialogs.choose = lambda *a, **k: None

from core.config import HOME_SUBJECTS, SUBJECTS
from core.diagnostic import EXAM_LENGTH
from core.loader import load_subject
from ui.app import StudyApp
from ui.screens.practice import PracticeScreen
from ui.screens.results import ResultsScreen
from ui.fast import FastRow

BUGS: list[str] = []
SLOW: list[str] = []
NOTES: list[str] = []


def note(msg: str) -> None:
    print(msg)
    NOTES.append(msg)


def bug(msg: str) -> None:
    print("BUG:", msg)
    BUGS.append(msg)


def pump(app, ms: int = 60) -> None:
    deadline = time.time() + ms / 1000
    while time.time() < deadline:
        try:
            app.update()
        except Exception:
            break
        time.sleep(0.008)


def timed(label: str, fn, limit_ms: int = 400):
    t0 = time.perf_counter()
    try:
        result = fn()
        elapsed = (time.perf_counter() - t0) * 1000
        note(f"{label}: {elapsed:.0f} ms")
        if elapsed > limit_ms:
            SLOW.append(f"{label}: {elapsed:.0f} ms")
        return result, elapsed
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        bug(f"{label} crashed after {elapsed:.0f} ms: {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        return None, elapsed


def walk(widget):
    yield widget
    try:
        kids = widget.winfo_children()
    except Exception:
        return
    for child in kids:
        yield from walk(child)


def practice_screen(app):
    for w in walk(app.content):
        if isinstance(w, PracticeScreen):
            return w
    return None


def answer_n(app, n: int, wrong: bool = False) -> int:
    answered = 0
    for _ in range(n):
        pump(app, 30)
        screen = practice_screen(app)
        if screen is None:
            break
        q = app.current_session.get_current_question() if app.current_session else None
        if q is None:
            break
        idx = 0
        if wrong:
            idx = 0 if q.get("answer") != 0 else 1
        try:
            screen._choose(idx)
        except Exception as exc:
            bug(f"choose failed: {exc}")
            break
        answered += 1
        pump(app, 50)
        if getattr(screen, "exam_mode", False):
            pump(app, 650)
        else:
            try:
                screen._render()
            except Exception:
                pass
            pump(app, 40)
    return answered


def skip_once(app) -> bool:
    screen = practice_screen(app)
    if not screen:
        return False
    try:
        screen._skip()
        pump(app, 40)
        return True
    except Exception as exc:
        bug(f"skip crashed: {exc}")
        return False


def expire_timer(app) -> None:
    session = app.current_session
    if not session:
        return
    session.total_limit_sec = 1
    session.start_time = time.time() - 5
    screen = practice_screen(app)
    if screen and screen.timer_lbl:
        try:
            screen._tick()
        except Exception as exc:
            bug(f"timer tick crashed: {exc}")
    else:
        try:
            app._show_results()
        except Exception as exc:
            bug(f"forced results after timer crashed: {exc}")


def patch_for_deeper_qa(app) -> None:
    """Keep exercising after known native crashes so more paths get hit."""
    import ui.app as appmod

    if not hasattr(appmod, "load_subject"):
        appmod.load_subject = load_subject
        note("patched ui.app.load_subject (was missing)")
    if not hasattr(app, "_pack_general_exam_card"):
        def _stub(parent):
            note("stub _pack_general_exam_card called")
        app._pack_general_exam_card = _stub
        note("stubbed StudyApp._pack_general_exam_card")


def main() -> int:
    note(f"stress temp dir: {TMP}")
    t0 = time.perf_counter()

    # --- native crash hunt (no patches yet) ---
    app = StudyApp()
    app.geometry("1100x720")
    app.deiconify()
    pump(app, 150)
    note(f"startup: {(time.perf_counter() - t0) * 1000:.0f} ms")

    native_has = hasattr(app, "_pack_general_exam_card")
    note(f"native _pack_general_exam_card: {native_has}")
    import ui.app as appmod
    note(f"native ui.app.load_subject: {hasattr(appmod, 'load_subject')}")

    app.storage.save_student("נועה סטרס", 16, "")
    app.storage.save_diagnostic(11, EXAM_LENGTH, "intermediate", [{"subject": "hebrew", "correct": False}])
    _, ms = timed("NATIVE dashboard", app._show_dashboard, 800)
    if ms and any("NATIVE dashboard crashed" in b for b in BUGS):
        note("dashboard is broken natively, continuing with in-process patches")

    _, hub_ms = timed("NATIVE hub hebrew", lambda: app._show_subject_hub("hebrew"), 800)

    patch_for_deeper_qa(app)

    timed("patched dashboard", app._show_dashboard, 800)
    pump(app, 80)

    # onboarding empty-state is skipped because we already have a profile.
    # settings / about / mistakes / meimad / general hubs
    for tab in ("subjects", "mistakes", "settings", "about", "meimad", "general_exam"):
        timed(f"nav {tab}", lambda t=tab: app._nav(t), 350)
        pump(app, 40)

    # theme + font (rebuild shell)
    timed("theme dark", lambda: app._set_theme("Dark"), 900)
    pump(app, 80)
    timed("font huge", lambda: app._set_font_size("ענק"), 900)
    pump(app, 80)
    timed("font normal", lambda: app._set_font_size("רגיל"), 900)
    pump(app, 60)
    timed("theme light", lambda: app._set_theme("Light"), 900)
    pump(app, 60)
    app.focus_mode = False
    timed("toggle focus", app._toggle_focus_mode, 500)
    pump(app, 40)
    timed("toggle focus off", app._toggle_focus_mode, 500)
    pump(app, 40)

    app._save_exam_date("2026-06-15", "מימ״ד")
    pump(app, 40)
    timed("dashboard with exam date", app._show_dashboard, 800)
    pump(app, 50)

    # empty mistakes
    timed("empty mistakes", app._show_mistakes, 300)
    app._start_mistake_drill(None)
    if DIALOGS and "אין כרגע טעויות" not in DIALOGS[-1]:
        note(f"mistake drill dialog: {DIALOGS[-1:]}")

    # every subject: hub, read, practice, mock, timed, skip, restore
    for key in HOME_SUBJECTS:
        name = SUBJECTS[key]["name"]
        timed(f"hub {name}", lambda k=key: app._show_subject_hub(k), 500)
        pump(app, 40)

        timed(f"lessons {name}", lambda k=key: app._start_mode(k, "read"), 500)
        pump(app, 50)
        clicked = False
        for row in walk(app.content):
            if isinstance(row, FastRow):
                try:
                    row._click()
                    clicked = True
                    break
                except Exception as exc:
                    bug(f"{name} lesson click: {exc}")
                    break
        pump(app, 60)
        if not clicked:
            bug(f"{name}: no lesson row to open")
        else:
            # lesson -> practice on this topic
            pass

        timed(f"practice {name}", lambda k=key: app._start_mode(k, "practice"), 600)
        pump(app, 40)
        n = answer_n(app, 2)
        skip_once(app)
        n2 = answer_n(app, 1)
        note(f"{name} practice answered {n}+{n2}")

        # session restore
        if app.current_session:
            state = app.current_session.to_state(key)
            app.session_store.save(state)
            app._show_subjects()
            pump(app, 30)
            timed(f"restore {name}", app._restore_last_session, 400)
            pump(app, 40)
            if not practice_screen(app):
                bug(f"{name}: restore did not reopen practice")

        timed(f"mock {name}", lambda k=key: app._start_mode(k, "mock"), 700)
        pump(app, 40)
        skip_once(app)
        answer_n(app, 1)
        if app.current_session:
            note(f"  mock total={app.current_session.get_total()} timed={app.current_session.time_limit_sec}")

        timed(f"timed-mode {name}", lambda k=key: app._start_mode(k, "timed"), 700)
        pump(app, 40)
        if app.current_session:
            note(f"  timed total={app.current_session.get_total()} q-limit={app.current_session.time_limit_sec}")
            expire_timer(app)
            pump(app, 80)
            if practice_screen(app) and app.current_session and not app.current_session.out_of_time():
                note(f"{name} timer expiry did not finish session")

        # unlock + start final (don't finish 20+ questions, seed storage)
        for _ in range(22):
            app.storage.record_answer(key, "כללי", True, 1.0)
        timed(f"final {name}", lambda k=key: app._start_mode(k, "final"), 700)
        pump(app, 40)
        if app.current_mode == "final" and app.current_session:
            note(f"  final total={app.current_session.get_total()} timed={app.current_session.time_limit_sec}")
            skip_ok = skip_once(app)
            if skip_ok and app.current_session and app.current_session.current_index == 0:
                # skip is allowed in mock but not final, if skip changed question that's a bug
                q0 = app.current_session.get_current_question()
                note(f"  final skip attempted, still on q={bool(q0)}")
            answer_n(app, 1)
        else:
            note(f"{name} final not opened (dialogs={DIALOGS[-1:]})")

        app._show_subjects()
        pump(app, 20)

    # smart practice + daily review + mistakes after wrong answers
    app._start_mode("civics", "practice")
    pump(app, 40)
    answer_n(app, 6, wrong=True)
    pump(app, 40)
    timed("results after wrongs", app._show_results, 800)
    pump(app, 80)
    has_results = any(isinstance(w, ResultsScreen) for w in walk(app.content))
    note(f"results shown: {has_results}")
    if not has_results:
        bug("results screen missing after forced finish")

    timed("mistakes after wrongs", app._show_mistakes, 400)
    pump(app, 40)
    n_mist = len(app.storage.get_mistakes())
    note(f"mistakes stored: {n_mist}")
    timed("mistake drill", lambda: app._start_mistake_drill(None), 500)
    pump(app, 50)
    answer_n(app, 2)

    timed("smart practice", app._start_smart_practice, 700)
    pump(app, 40)
    answer_n(app, 2)

    timed("daily review", app._start_daily_review, 700)
    pump(app, 40)
    if practice_screen(app):
        answer_n(app, 1)
        skip_once(app)

    # meimad + general exam start (will likely crash on leftover parent / load_subject)
    timed("meimad hub", app._show_meimad_hub, 400)
    pump(app, 40)
    timed("start meimad", app._start_meimad_exam, 1500)
    pump(app, 80)
    if practice_screen(app):
        note(f"meimad running mode={app.current_mode} total={app.current_session.get_total() if app.current_session else None}")
        skip_once(app)
        answer_n(app, 1)
        expire_timer(app)
        pump(app, 80)

    timed("general hub", app._show_general_exam_hub, 400)
    pump(app, 40)
    # seed coverage so unlock can succeed
    for key in HOME_SUBJECTS:
        for i in range(25):
            app.storage.record_answer(key, "כללי", True, 0.8, question_id=f"{key}-q{i}")
    timed("start general exam", app._start_general_exam, 2000)
    pump(app, 80)
    if practice_screen(app):
        note(f"general running total={app.current_session.get_total() if app.current_session else None}")
        skip_once(app)
        answer_n(app, 2)
        expire_timer(app)
        pump(app, 80)

    # about + settings again after lots of data
    timed("about late", app._show_about, 300)
    timed("settings late", app._show_settings, 400)
    timed("subjects late", app._show_subjects, 600)
    timed("dashboard late", app._show_dashboard, 900)

    note("--- DIALOGS ---")
    for d in DIALOGS:
        note(d)
    note("--- SLOW ---")
    for s in SLOW:
        note(s)
    note("--- BUGS ---")
    for b in BUGS:
        note(b)
    note(f"done in {(time.perf_counter() - t0):.1f}s bugs={len(BUGS)} slow={len(SLOW)}")

    report_path = os.path.join(ROOT, "_qa_stress_report.txt")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(NOTES + ["", "BUGS:"] + BUGS))
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
