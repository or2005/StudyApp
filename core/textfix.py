"""תצוגת עברית על כל Windows: רוסית, אנגלית, ערבית ושאר השפות."""
from __future__ import annotations

import os
import sys

from core import rtltext

# שפות Windows נפוצות אצל תלמידים כאן.
_LANG_NAMES = {
    0x09: "en",
    0x0D: "he",
    0x01: "ar",
    0x19: "ru",
    0x0B: "fi",
    0x0C: "fr",
    0x07: "de",
    0x0A: "es",
    0x10: "it",
    0x16: "pt",
    0x11: "ja",
    0x04: "zh",
    0x22: "uk",
    0x27: "uz",
    0x1F: "tr",
    0x2D: "eu",
}

HEBREW_FONTS = (
    "Segoe UI",
    "Arial",
    "Tahoma",
    "David",
    "Noto Sans Hebrew",
    "Times New Roman",
    "Microsoft Sans Serif",
    "DejaVu Sans",
    "Noto Sans",
)


def force_utf8() -> bool:
    changed = False
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
            changed = True
        except Exception:
            pass
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        changed = True
    except Exception:
        pass
    return changed


def tcl_utf8(root) -> bool:
    try:
        root.tk.call("encoding", "system", "utf-8")
        return True
    except Exception:
        return False


def os_lang() -> str:
    if sys.platform.startswith("win"):
        try:
            import ctypes

            langid = int(ctypes.windll.kernel32.GetUserDefaultUILanguage())
            return _LANG_NAMES.get(langid & 0x3FF, f"lang-{langid & 0x3FF:02x}")
        except Exception:
            pass
    loc = (os.environ.get("LANG") or os.environ.get("LC_ALL") or "en").lower()
    return loc.split(".")[0].split("_")[0] or "en"


def guess_helper() -> str:
    code = os_lang()
    if code in {"he", "en", "ru", "ar"}:
        return code
    if code in {"uk", "be", "kk"}:
        return "ru"
    return "en" if code != "he" else "he"


def _families(root) -> dict[str, str]:
    try:
        import tkinter.font as tkfont

        return {name.lower(): name for name in tkfont.families(root)}
    except Exception:
        return {}


def font_has_hebrew(root, family: str) -> bool:
    try:
        import tkinter.font as tkfont

        font = tkfont.Font(root=root, family=family, size=16)
        hebrew = font.measure("שלום")
        boxes = font.measure("□□□□")
        latin = font.measure("abcd")
        if hebrew <= 2:
            return False
        if hebrew == boxes and hebrew < latin * 1.2:
            return False
        return True
    except Exception:
        return family.lower() in {item.lower() for item in HEBREW_FONTS}


def pick_hebrew_font(root=None) -> str:
    names = _families(root) if root is not None else {}
    for candidate in HEBREW_FONTS:
        real = names.get(candidate.lower(), candidate if not names else "")
        if not real:
            continue
        if root is None or font_has_hebrew(root, real):
            return real
    return "Arial"


def apply_text_engine(root=None) -> dict:
    """פונט, UTF-8, וכיוון עברית לפי שפת Windows."""
    force_utf8()
    tcl_ok = tcl_utf8(root) if root is not None else False
    from core.config import ADHD_CONFIG

    family = pick_hebrew_font(root)
    ADHD_CONFIG["font_family"] = family
    rtltext.configure_for_os()
    if root is not None:
        try:
            import tkinter.font as tkfont

            for name in (
                "TkDefaultFont",
                "TkTextFont",
                "TkMenuFont",
                "TkHeadingFont",
                "TkCaptionFont",
                "TkSmallCaptionFont",
                "TkIconFont",
                "TkTooltipFont",
            ):
                try:
                    tkfont.nametofont(name).configure(family=family)
                except Exception:
                    pass
        except Exception:
            pass
    return {
        "os_lang": os_lang(),
        "font": family,
        "utf8": True,
        "tcl_utf8": tcl_ok,
        "visual_rtl": rtltext.needs_visual(),
    }
