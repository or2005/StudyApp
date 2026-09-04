"""QA חי לשחרור: הרשמה, דשבורד, תרגול, מבחנים, מבחן כללי, מימ״ד, הגדרות."""
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

TMP = tempfile.mkdtemp(prefix="studyapp-release-qa-")
os.environ["LOCALAPPDATA"] = TMP
os.environ["APPDATA"] = TMP

from core import dialogs
from core.config import COLORS, HOME_SUBJECTS
from core.theme import current_mode

DIALOGS: list[str] = []


def _log_dialog(kind, title, text):
    DIALOGS.append(f"{kind}: {title}, {text}")
    print(f"  [dialog] {kind}: {title}")


dialogs.info = lambda t, x: _log_dialog("info", t, x)
dialogs.error = lambda t, x: _log_dialog("error", t, x)
dialogs.confirm = lambda t, x: True
dialogs.choose = lambda *a, **k: None

from ui.app import StudyApp
from ui.screens.general_report import GeneralExamReportScreen
from ui.screens.onboarding import OnboardingFrame
from ui.screens.practice import PracticeScreen
from ui.screens.results import ResultsScreen
from ui.fast import FastRow

BUGS: list[str] = []
NOTES: list[str] = []


def note(msg: str) -> None:
    print(msg)
    NOTES.append(msg)


def bug(msg: str) -> None:
    print("BUG:", msg)
    BUGS.append(msg)


def walk(widget):
    yield widget
    try:
        kids = widget.winfo_children()
    except Exception:
        return
    for child in kids:
        yield from walk(child)


def pump(app, ms: int = 60) -> None:
    deadline = time.time() + ms / 1000
    while time.time() < deadline:
        try:
            app.update()
        except Exception:
            break
        time.sleep(0.008)


def practice_screen(app):
    for w in walk(app.content):
        if isinstance(w, PracticeScreen):
            return w
    return None


def click_named(root, *needles: str) -> bool:
    for w in walk(root):
        try:
            from core.rtltext import strip_marks

            txt = strip_marks(str(w.cget("text") or ""))
        except Exception:
            continue
        if w.__class__.__name__ not in {"CTkButton", "ModernButton", "GhostButton", "TkButton", "FastButton"}:
            continue
        if any(n in txt for n in needles):
            cmd = w.cget("command")
            if cmd:
                cmd()
                return True
    return False


def fill_entries(root, values: list[str]) -> int:
    filled = 0
    for w in walk(root):
        if w.__class__.__name__ in {"CTkEntry", "Entry"} and filled < len(values):
            try:
                w.delete(0, "end")
                w.insert(0, values[filled])
                filled += 1
            except Exception:
                continue
    return filled


def finish_diagnostic(app) -> None:
    for _ in range(25):
        pump(app, 30)
        frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
        if frame is None:
            return
        if getattr(frame, "questions", None) and frame.q_index < len(frame.questions):
            try:
                frame._pick(0)
                frame._next_question()
            except Exception as exc:
                bug(f"diagnostic next failed: {exc}")
                break
            continue
        if not getattr(frame, "questions", None):
            bug("diagnostic questions missing, still on welcome?")
            break
        try:
            frame.on_done()
            pump(app, 150)
            return
        except Exception:
            if click_named(app, "המשך לדשבורד"):
                pump(app, 150)
                return
            break


def answer_n(app, n: int) -> int:
    answered = 0
    for _ in range(n):
        pump(app, 30)
        screen = practice_screen(app)
        if screen is None:
            break
        try:
            screen._choose(0)
        except Exception as exc:
            bug(f"choose failed: {exc}")
            break
        answered += 1
        pump(app, 50)
        if getattr(screen, "exam_mode", False):
            pump(app, 280)
        else:
            click_named(app, "לשאלה הבאה")
            pump(app, 40)
    return answered


def colors_of_options(screen) -> list[str]:
    out = []
    for btn in getattr(screen, "_buttons", []) or []:
        try:
            out.append(str(btn.cget("fg_color") or "").upper())
        except Exception:
            continue
    return out


def assert_no_exam_leak(app, label: str) -> None:
    screen = practice_screen(app)
    if not screen or not screen.exam_mode:
        bug(f"{label}: practice screen missing for leak check")
        return
    success = str(COLORS["success"]).upper()
    danger = str(COLORS["danger"]).upper()
    q = screen.session.get_current_question()
    if not q:
        bug(f"{label}: no current question")
        return
    wrong = 0 if q.get("answer") != 0 else 1
    try:
        screen._choose(wrong)
    except Exception as exc:
        bug(f"{label}: choose crashed: {exc}\n{traceback.format_exc()}")
        return
    pump(app, 40)
    found = colors_of_options(screen)
    if any(success in c or c == success for c in found):
        bug(f"{label}: exam leaked SUCCESS color {found}")
    if any(danger in c or c == danger for c in found):
        bug(f"{label}: exam leaked DANGER color {found}")
    else:
        note(f"{label}: no green/red leak ({found[:4]})")
    pump(app, 280)


def main() -> int:
    note(f"release QA temp dir: {TMP}")
    t0 = time.perf_counter()
    app = StudyApp()
    app.geometry("1200x780")
    app.deiconify()
    pump(app, 180)
    note(f"startup: {(time.perf_counter() - t0) * 1000:.0f} ms")

    frame = next((w for w in walk(app.content) if isinstance(w, OnboardingFrame)), None)
    if frame is None:
        bug("onboarding frame missing at startup")
    else:
        try:
            frame.name_var.set("נועה שחרור")
            frame.age_var.set("16")
            frame.id_var.set("")
            frame._terms_ok.set(True)
            frame._submit_details()
            frame.advance_setup_for_tests()
            frame._stage("diagnostic")
        except Exception as exc:
            bug(f"registration submit failed: {exc}")
            filled = fill_entries(app, ["נועה שחרור", "16", ""])
            if filled < 2:
                bug("could not fill registration fields")
            if not click_named(app, "המשך למבחן אבחון"):
                bug("registration next button missing")
    pump(app, 120)
    finish_diagnostic(app)
    pump(app, 200)
    if not app.storage.get_diagnostic():
        bug("diagnostic was not saved")
    if any(isinstance(w, OnboardingFrame) for w in walk(app.content)):
        bug("still on onboarding after diagnostic")
    else:
        note("onboarding -> dashboard ok")

    for tab in ("subjects", "mistakes", "settings", "about", "meimad", "general_exam", "dashboard"):
        try:
            app._nav(tab)
            pump(app, 50)
            note(f"nav {tab} ok")
        except Exception as exc:
            bug(f"nav {tab} crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._show_subject_hub("hebrew")
        pump(app, 50)
        app._start_mode("hebrew", "read")
        pump(app, 60)
        clicked = False
        for row in walk(app.content):
            if isinstance(row, FastRow):
                row._click()
                clicked = True
                break
        pump(app, 80)
        if not clicked:
            bug("hebrew: no lesson row")
        else:
            note("hebrew lesson opened")
    except Exception as exc:
        bug(f"hebrew lesson crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode("hebrew", "practice")
        pump(app, 50)
        n = answer_n(app, 3)
        note(f"hebrew practice sample {n}")
        app._show_results()
        pump(app, 120)
        if not any(isinstance(w, ResultsScreen) for w in walk(app.content)):
            bug("results screen missing after practice")
        else:
            note("results screen ok")
            if not click_named(app, "חזרה למסך הראשי"):
                bug("results home button missing")
    except Exception as exc:
        bug(f"practice/results crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._start_mode("english", "mock")
        pump(app, 60)
        if app.current_session:
            note(f"mock total={app.current_session.get_total()} mode={app.current_mode}")
            assert_no_exam_leak(app, "mock")
        else:
            bug("mock session did not start")
    except Exception as exc:
        bug(f"mock leak check crashed: {exc}\n{traceback.format_exc()}")

    before_level = app.adaptive_engine.level_of("hebrew")
    before_total = int((app.storage.get_progress().get("hebrew") or {}).get("total", 0) or 0)

    for key in HOME_SUBJECTS:
        for i in range(22):
            app.storage.record_answer(key, "כללי", True, 0.8, question_id=f"{key}-unlock-{i}")

    try:
        app._show_general_exam_hub()
        pump(app, 50)
        app._start_general_exam()
        pump(app, 80)
        if not practice_screen(app) or app.current_mode != "general":
            bug(f"general exam did not start (mode={app.current_mode} dialogs={DIALOGS[-2:]})")
        else:
            note(f"general exam total={app.current_session.get_total()}")
            if app.current_session.get_total() != 50:
                bug(f"general exam size {app.current_session.get_total()} != 50")
            assert_no_exam_leak(app, "general")
            answer_n(app, 2)
            screen = practice_screen(app)
            app.current_session.total_limit_sec = 1
            app.current_session.start_time = time.time() - 5
            if screen and screen.timer_lbl:
                screen._tick()
            else:
                app._show_results()
            pump(app, 150)
            if not any(isinstance(w, GeneralExamReportScreen) for w in walk(app.content)):
                bug("general exam report screen missing after timeout")
            else:
                note("general exam report ok")
            report = app.storage.get_general_exam_report() or {}
            if int(report.get("total") or 0) != 50:
                bug(f"general report total={report.get('total')} expected 50")
            if "grade" not in report or "scaled" not in report:
                bug(f"general report incomplete keys={list(report)}")
            after_level = app.adaptive_engine.level_of("hebrew")
            after_total = int((app.storage.get_progress().get("hebrew") or {}).get("total", 0) or 0)
            if after_level != before_level:
                bug(f"general exam changed hebrew level {before_level} -> {after_level}")
            if after_total != before_total + 22:
                bug(f"general exam polluted hebrew totals {before_total} -> {after_total}")
            app._show_dashboard()
            pump(app, 80)
            note("dashboard after general report ok")
    except Exception as exc:
        bug(f"general exam crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._show_meimad_hub()
        pump(app, 40)
        app._start_meimad_exam()
        pump(app, 80)
        if practice_screen(app) and app.current_mode == "meimad":
            note(f"meimad total={app.current_session.get_total()} chapters={len(app.current_session.chapters)}")
            assert_no_exam_leak(app, "meimad")
            app._show_results()
            pump(app, 120)
            note("meimad results ok")
        else:
            bug(f"meimad did not start (mode={app.current_mode})")
    except Exception as exc:
        bug(f"meimad crashed: {exc}\n{traceback.format_exc()}")

    try:
        app._set_theme("Dark")
        pump(app, 80)
        if current_mode() != "Dark":
            bug(f"theme did not switch to Dark ({current_mode()})")
        app._set_theme("Light")
        pump(app, 80)
        app._nav("about")
        pump(app, 50)
        app._nav("settings")
        pump(app, 50)
        app._nav("mistakes")
        pump(app, 50)
        note("theme/about/settings/mistakes ok")
    except Exception as exc:
        bug(f"settings/about crashed: {exc}\n{traceback.format_exc()}")

    note("--- DIALOGS ---")
    for d in DIALOGS:
        note(d)
    note("--- BUGS ---")
    for b in BUGS:
        note(b)
    note(f"done in {(time.perf_counter() - t0):.1f}s bugs={len(BUGS)}")

    report_path = os.path.join(ROOT, "_qa_release_report.txt")
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
