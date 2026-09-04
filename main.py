"""StudyApp, נקודת כניסה לחלון שולחן העבודה."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _windows_dpi() -> None:
    from core.display import enable_dpi_awareness

    enable_dpi_awareness()


def _show_message(title: str, text: str, error: bool = True) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if error:
            messagebox.showerror(title, text)
        else:
            messagebox.showinfo(title, text)
        root.destroy()
    except Exception:
        print(f"{title}: {text}", file=sys.stderr)


def _single_instance() -> bool:
    """מונע שני חלונות שדורסים את אותו פרופיל, Windows ולינוקס."""
    from core.platformutil import acquire_single_instance

    if acquire_single_instance():
        return True
    _show_message("StudyApp", "StudyApp כבר פתוחה במחשב הזה.", error=False)
    return False


def main() -> int:
    try:
        from multiprocessing import freeze_support

        freeze_support()
    except Exception:
        pass

    try:
        from core.textfix import force_utf8

        force_utf8()
    except Exception:
        pass

    _windows_dpi()
    try:
        from core.nativeos import bind_app_identity

        bind_app_identity()
    except Exception:
        pass

    if "--remind" in sys.argv:
        from core.reminders import fire_reminder

        return fire_reminder()

    if not _single_instance():
        return 0

    from core.applog import LOG_PATH, get_logger, install_crash_handlers, setup_logging

    setup_logging()
    install_crash_handlers()
    log = get_logger("main")

    try:
        from core import security_shield

        seal = security_shield.verify()
        if not seal.get("ok"):
            log.warning("security seal issues: %s", seal.get("issues"))
            warn = security_shield.student_warning()
            if warn and seal.get("frozen"):
                _show_message("StudyApp · אבטחה", warn, error=False)
    except Exception:
        log.exception("security check failed")

    try:
        from ui.app import run

        run()
    except ModuleNotFoundError as exc:
        log.exception("missing dependency")
        extra = ""
        if sys.platform.startswith("linux"):
            extra = (
                "\nבלינוקס חסרה לעיתים חבילת Tk:\n"
                "Debian/Ubuntu:  sudo apt install python3-tk python3-venv\n"
                "Fedora:         sudo dnf install python3-tkinter\n"
                "Arch:           sudo pacman -S tk\n"
                "openSUSE:       sudo zypper install python3-tk\n"
                "Alpine:         sudo apk add py3-tkinter\n\n"
            )
        _show_message(
            "StudyApp",
            "חסרה חבילה להפעלת התוכנה.\n"
            f"{extra}"
            "או: pip install -r requirements.txt\n\n"
            f"פרטים: {exc}",
        )
        return 1
    except Exception:
        log.exception("app crashed")
        _show_message(
            "StudyApp",
            "התוכנה נעצרה בגלל תקלה.\n"
            "הפרטים נשמרו ביומן במחשב שלך:\n\n"
            f"{LOG_PATH}",
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
