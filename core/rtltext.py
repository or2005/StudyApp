"""עברית על Windows באנגלית: Tk מצייר מילים נכון אבל את הפסקה משמאל לימין."""
from __future__ import annotations

import os
import re
from typing import Final

_BIDI_MARKS: Final[str] = (
    "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)
_SEG = re.compile(r"\S+|\s+")
_RTL_LANG: Final[frozenset[int]] = frozenset({0x01, 0x0D})  # Arabic, Hebrew
_FORCE_VISUAL: bool | None = None


def strip_marks(text: str) -> str:
    if not text:
        return text
    return "".join(ch for ch in text if ch not in _BIDI_MARKS)


def windows_has_rtl_ui() -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes

        k32 = ctypes.windll.kernel32
        for name in (
            "GetUserDefaultUILanguage",
            "GetSystemDefaultUILanguage",
            "GetUserDefaultLangID",
        ):
            langid = int(getattr(k32, name)())
            if (langid & 0x3FF) in _RTL_LANG:
                return True
    except Exception:
        return False
    return False


def configure_for_os() -> bool:
    """קובע פעם אחת: מחשב לא־עברי/ערבי צריך סידור מילים ויזואלי."""
    global _FORCE_VISUAL
    _FORCE_VISUAL = _detect_visual()
    return _FORCE_VISUAL


def _detect_visual() -> bool:
    if os.name == "nt":
        return not windows_has_rtl_ui()
    loc = (os.environ.get("LANG") or os.environ.get("LC_ALL") or os.environ.get("LC_CTYPE") or "").lower()
    return not (loc.startswith("he") or loc.startswith("ar") or ".he" in loc)


def needs_visual() -> bool:
    if _FORCE_VISUAL is not None:
        return _FORCE_VISUAL
    return _detect_visual()


def visual_line(text: str) -> str:
    """הופך סדר מילים בלי להפוך אותיות. Uniscribe כבר מצייר כל מילה עברית נכון."""
    if not text or text.isspace():
        return text
    return "".join(reversed(_SEG.findall(text)))


def _already(text: str) -> bool:
    return len(text) >= 2 and text[0] in "\u202b\u2067" and text[-1] in "\u202c\u2069"


def apply(text: str) -> str:
    if not text:
        return text
    if _already(text):
        return text
    if "\n" in text:
        return "\n".join(apply(line) for line in text.split("\n"))
    cleaned = strip_marks(text)
    if needs_visual():
        return "\u2067" + visual_line(cleaned) + "\u2069"
    return "\u202b" + cleaned + "\u202c"
