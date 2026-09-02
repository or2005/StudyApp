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
    "Segoe UI Variable Text",
    "Segoe UI Variable",
    "Segoe UI",
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
    """בוחר גופן שקיים במחשב, Segoe ב־Windows, Noto/DejaVu בלינוקס."""
    family = default_ui_font()
    if root is not None or not is_windows():
        try:
            import tkinter.font as tkfont

            names = {item.lower(): item for item in tkfont.families(root)}
            candidates = WINDOWS_FONTS if is_windows() else LINUX_FONTS
            for candidate in candidates:
                hit = names.get(candidate.lower())
                if hit:
                    family = hit
                    break
        except Exception:
            pass
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
