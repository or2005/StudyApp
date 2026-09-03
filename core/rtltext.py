"""עברית על Windows לא־עברי: בלי סימני bidi שמהפכים את התיקון בחזרה."""
from __future__ import annotations

import os
import re
from typing import Final

# סימני כיוון. לא שמים אותם על טקסט שכבר סודר ויזואלית.
_BIDI_MARKS: Final[str] = (
    "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u2060"
)
_SEG = re.compile(r"\S+|\s+")
_RUNS = re.compile(r"[\u0590-\u05FF]+|[^\u0590-\u05FF]+")
_RTL_LANG: Final[frozenset[int]] = frozenset({0x01, 0x0D})  # Arabic, Hebrew
_DONE = "\u2060"  # word joiner: לא משנה כיוון, מסמן שכבר עובד
_MODE = "auto"  # auto | words | letters | off


def strip_marks(text: str) -> str:
    if not text:
        return text
    return "".join(ch for ch in text if ch not in _BIDI_MARKS)


def windows_ui_langid() -> int:
    """רק שפת ממשק Windows, לא מקלדת ולא locale."""
    if os.name != "nt":
        return 0
    try:
        import ctypes

        return int(ctypes.windll.kernel32.GetUserDefaultUILanguage()) & 0x3FF
    except Exception:
        return 0


def windows_has_rtl_ui() -> bool:
    return windows_ui_langid() in _RTL_LANG


def set_mode(mode: str) -> str:
    global _MODE
    clean = (mode or "auto").strip().lower()
    if clean not in {"auto", "words", "letters", "off"}:
        clean = "auto"
    _MODE = clean
    return _MODE


def get_mode() -> str:
    return _MODE


def resolved_mode() -> str:
    if _MODE in {"words", "letters", "off"}:
        return _MODE
    if os.name == "nt":
        return "off" if windows_has_rtl_ui() else "words"
    loc = (os.environ.get("LANG") or os.environ.get("LC_ALL") or os.environ.get("LC_CTYPE") or "").lower()
    if loc.startswith("he") or loc.startswith("ar") or ".he" in loc:
        return "off"
    return "words"


def configure_for_os() -> str:
    return resolved_mode()


def needs_visual() -> bool:
    return resolved_mode() in {"words", "letters"}


def visual_line(text: str) -> str:
    """הופך סדר מילים בלי להפוך אותיות."""
    if not text or text.isspace():
        return text
    return "".join(reversed(_SEG.findall(text)))


def visual_letters(text: str) -> str:
    """הופך גם אותיות עבריות, למחשב שמצייר משמאל בלי Uniscribe."""
    if not text:
        return text
    runs = _RUNS.findall(text)
    out: list[str] = []
    for run in reversed(runs):
        if run and "\u0590" <= run[0] <= "\u05FF":
            out.append(run[::-1])
        else:
            out.append(run)
    return "".join(out)


def _already(text: str) -> bool:
    return bool(text) and text[0] == _DONE


def apply(text: str) -> str:
    if not text:
        return text
    if _already(text):
        return text
    if "\n" in text:
        return "\n".join(apply(line) for line in text.split("\n"))
    cleaned = strip_marks(text)
    mode = resolved_mode()
    if mode == "words":
        return _DONE + visual_line(cleaned)
    if mode == "letters":
        return _DONE + visual_letters(cleaned)
    if windows_has_rtl_ui():
        return "\u202b" + cleaned + "\u202c"
    return cleaned
