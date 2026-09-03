"""הבדלי מערכת, Windows ולינוקס (וגם macOS אם יגיע)."""
from __future__ import annotations

import os
import sys
from typing import TextIO

from core.config import ADHD_CONFIG

LINUX_FONTS = (
    "Noto Sans Hebrew",
    "Noto Sans",
    "DejaVu Sans",
    "FreeSans",
    "Liberation Sans",
    "Ubuntu",
    "Cantarell",
    "Sans",
)

WINDOWS_FONTS = (
    "Segoe UI",
    "Arial",
    "Tahoma",
    "David",
    "Noto Sans Hebrew",
    "Times New Roman",
    "Microsoft Sans Serif",
    "Segoe UI Variable Text",
    "Segoe UI Variable",
)

_LOCK_HANDLE: TextIO | None = None


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def default_ui_font() -> str:
    if is_windows():
        return "Segoe UI"
    if sys.platform == "darwin":
        return "Helvetica Neue"
    return "DejaVu Sans"


def apply_ui_font(root=None) -> str:
    """בוחר גופן עם עברית, גם במחשב רוסי או אנגלי."""
    from core import textfix

    family = textfix.pick_hebrew_font(root) if root is not None else default_ui_font()
    if root is None and is_linux():
        try:
            import tkinter.font as tkfont

            names = {item.lower(): item for item in tkfont.families(root)}
            for candidate in LINUX_FONTS:
                hit = names.get(candidate.lower())
                if hit:
                    family = hit
                    break
        except Exception:
            family = default_ui_font()
    ADHD_CONFIG["font_family"] = family
    return family


def acquire_single_instance() -> bool:
    """True = אפשר להמשיך. False = כבר רצה עותק אחר."""
    global _LOCK_HANDLE
    if is_windows():
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateMutexW(None, True, "Local\\StudyAppDesktopMutex")
            globals()["_WIN_MUTEX"] = handle
            if kernel32.GetLastError() == 183:
                return False
        except Exception:
            return True
        return True

    try:
        import fcntl

        from core.storage import get_persistent_app_dir

        path = os.path.join(get_persistent_app_dir(), "studyapp.lock")
        handle = open(path, "w", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        handle.write(str(os.getpid()))
        handle.flush()
        _LOCK_HANDLE = handle
    except OSError:
        return False
    except Exception:
        return True
    return True
