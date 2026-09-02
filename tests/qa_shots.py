"""צילום ממוקד של המסכים שקשה להגיע אליהם בהליכה מלאה:
תוצאות עם סקירה, מחברת טעויות, ותרגול טעויות."""
from __future__ import annotations

import os
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

TMP = tempfile.mkdtemp(prefix="studyapp-shots-")
os.environ["LOCALAPPDATA"] = TMP
os.environ["APPDATA"] = TMP

from core import dialogs

dialogs.info = lambda t, x: print(f"  [info] {t}: {x}")
dialogs.error = lambda t, x: print(f"  [ERROR] {t}: {x}")
dialogs.confirm = lambda t, x: True

from core.diagnostic import EXAM_LENGTH
from ui.app import StudyApp

SHOT_DIR = os.path.join(ROOT, "_qa_shots")
os.makedirs(SHOT_DIR, exist_ok=True)


def pump(app, ms=120):
    app.update_idletasks()
    app.update()
    end = time.time() + ms / 1000
    while time.time() < end:
        app.update()
        time.sleep(0.005)


def shot(app, name):
    pump(app, 150)
    try:
        from PIL import ImageGrab

        app.lift()
        app.focus_force()
        pump(app, 150)
        box = (app.winfo_rootx(), app.winfo_rooty(),
               app.winfo_rootx() + app.winfo_width(), app.winfo_rooty() + app.winfo_height())
        ImageGrab.grab(bbox=box).save(os.path.join(SHOT_DIR, f"{name}.png"))
        print("shot", name)
    except Exception as exc:
        print("shot failed", name, exc)


def main():
    app = StudyApp()
    app.storage.save_student("נועה בדיקה", 17, "")
    app.storage.save_diagnostic(11, EXAM_LENGTH, "intermediate",
                                [{"subject": "hebrew", "correct": False}],
                                recommendations=["לחזק לשון"], weak_topics=["hebrew"])
    app.storage.set_exam_date("2026-06-15", "מימ״ד")
    app._choose_start_screen()
    pump(app, 200)
    shot(app, "n1_dashboard")

    # תרגול קצר שבו עונים תמיד לא נכון, כדי למלא מחברת טעויות
    app._start_mode("civics", "practice")
    pump(app, 150)
    for _ in range(12):
        screen = None
        for widget in app.content.winfo_children():
            if widget.__class__.__name__ == "PracticeScreen":
                screen = widget
                break
        if screen is None:
            break
        q = app.current_session.get_current_question()
        if q is None:
            break
        wrong_index = 0 if q.get("answer") != 0 else 1
        screen._choose(wrong_index)
        pump(app, 60)
        if not app.current_session.is_finished():
            screen._render()
            pump(app, 40)
        else:
            break
    shot(app, "n2_practice_feedback")

    app._show_results()
    pump(app, 250)
    shot(app, "n3_results_review")

    app._nav("mistakes")
    pump(app, 200)
    shot(app, "n4_mistakes")

    app._start_mistake_drill(None)
    pump(app, 200)
    shot(app, "n5_mistake_drill")

    app._show_subject_hub("english")
    pump(app, 150)
    shot(app, "n6_hub_english")

    app._show_lessons("english")
    pump(app, 150)
    shot(app, "n7_lessons")

    app._nav("settings")
    pump(app, 150)
    shot(app, "n8_settings")

    print("mistakes stored:", len(app.storage.get_mistakes()))
    app.storage.close()
    app.destroy()
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
