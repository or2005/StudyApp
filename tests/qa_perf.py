"""מדידת זמני מסך, להריץ לפני ואחרי אופטימיזציה."""
from __future__ import annotations

import os
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

TMP = tempfile.mkdtemp(prefix="studyapp-perf-")
os.environ["LOCALAPPDATA"] = TMP
os.environ["APPDATA"] = TMP

from core import dialogs

dialogs.info = lambda t, x: None
dialogs.error = lambda t, x: None
dialogs.confirm = lambda t, x: True

from core.config import HOME_SUBJECTS
from ui.app import StudyApp

RESULTS: list[tuple[str, float]] = []


def pump(app, ms=60):
    app.update_idletasks()
    app.update()
    end = time.time() + ms / 1000
    while time.time() < end:
        app.update()
        time.sleep(0.005)


def measure(app, label, fn, repeat=3):
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        app.update_idletasks()
        app.update()
        times.append((time.perf_counter() - t0) * 1000)
    best = min(times)
    avg = sum(times) / len(times)
    RESULTS.append((label, avg))
    flag = "  <== SLOW" if avg > 300 else ""
    print(f"{label:34s} avg {avg:7.0f} ms   best {best:7.0f} ms{flag}")
    return avg


def main():
    t0 = time.perf_counter()
    app = StudyApp()
    startup = (time.perf_counter() - t0) * 1000
    print(f"{'startup (window build)':34s} avg {startup:7.0f} ms")
    RESULTS.append(("startup", startup))

    app.storage.save_student("בדיקה", 17, "")
    app.storage.save_diagnostic(12, 20, "intermediate", [{"subject": "hebrew", "correct": True}])
    pump(app, 100)

    measure(app, "nav dashboard", lambda: app._nav("dashboard"))
    measure(app, "nav subjects", lambda: app._nav("subjects"))
    measure(app, "nav settings", lambda: app._nav("settings"))
    measure(app, "nav about", lambda: app._nav("about"))

    for key in ("civics", "english", "hebrew"):
        measure(app, f"hub {key}", lambda k=key: app._show_subject_hub(k))
        measure(app, f"lessons list {key}", lambda k=key: app._show_lessons(k))

    data_key = "civics"
    app._show_lessons(data_key)
    pump(app, 40)
    from core.loader import load_subject

    lessons = (load_subject(data_key) or {}).get("lessons") or []
    if lessons:
        measure(app, "open lesson", lambda: app._open_lesson(data_key, lessons[0]["id"]))

    measure(app, "start practice", lambda: app._start_mode("hebrew", "practice"))
    measure(app, "next question render", lambda: app._render_practice())

    print("\nTOTAL nav cost:", f"{sum(v for k, v in RESULTS if k.startswith('nav')):.0f} ms")
    slow = [f"{k} ({v:.0f}ms)" for k, v in RESULTS if v > 300]
    print("SLOW:", ", ".join(slow) if slow else "none")

    try:
        app.storage.close()
        app.destroy()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
