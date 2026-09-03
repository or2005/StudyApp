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
_MIXED_PIECE = re.compile(
    r"[\u0590-\u05FF]+[־\-]*|[A-Za-z0-9]+|[^A-Za-z0-9\u0590-\u05FF\s]+|\s+"
)
_HEB = re.compile(r"[\u0590-\u05FF]")
_LTR = re.compile(r"[A-Za-z0-9]")
_RTL_LANG: Final[frozenset[int]] = frozenset({0x01, 0x0D})  # Arabic, Hebrew
_LRE = "\u202a"
_RLE = "\u202b"
_PDF = "\u202c"
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


def _expand_parts(text: str) -> list[str]:
    """מפריד «ב־2H2» ל־עברית ולנוסחה, כדי שהנוסחה לא תתהפך."""
    out: list[str] = []
    for tok in _SEG.findall(text):
        if tok.isspace() or not (_HEB.search(tok) and _LTR.search(tok)):
            out.append(tok)
            continue
        out.extend(_MIXED_PIECE.findall(tok) or [tok])
    return out


def _token_kind(tok: str) -> str:
    if not tok or tok.isspace():
        return "space"
    if _HEB.search(tok):
        return "rtl"
    if _LTR.search(tok):
        return "ltr"
    return "neutral"


def _run_dir(parts: list[str], start: int) -> str:
    """כיוון ריצה: ניקוד וסימנים נצמדים לעברית או לאנגלית שלידם."""
    idx = start
    while idx < len(parts):
        kind = _token_kind(parts[idx])
        if kind in {"rtl", "ltr"}:
            return kind
        idx += 1
    return "ltr"


def _directional_runs(parts: list[str]) -> list[tuple[str, list[str]]]:
    """מקבץ מילים לאותו כיוון. רווח בין עברית לאנגלית נשאר מפריד."""
    runs: list[tuple[str, list[str]]] = []
    idx = 0
    n = len(parts)
    while idx < n:
        kind = _token_kind(parts[idx])
        if kind == "space":
            buf = [parts[idx]]
            idx += 1
            while idx < n and _token_kind(parts[idx]) == "space":
                buf.append(parts[idx])
                idx += 1
            runs.append(("space", buf))
            continue
        direction = _run_dir(parts, idx)
        buf = [parts[idx]]
        idx += 1
        while idx < n:
            nxt = _token_kind(parts[idx])
            if nxt in {direction, "neutral"}:
                if nxt == "neutral" and direction == "rtl":
                    look_n = idx
                    while look_n < n and _token_kind(parts[look_n]) in {"neutral", "space"}:
                        look_n += 1
                    if look_n < n and _token_kind(parts[look_n]) == "ltr":
                        break
                buf.append(parts[idx])
                idx += 1
                continue
            if nxt != "space":
                break
            look = idx
            while look < n and _token_kind(parts[look]) == "space":
                look += 1
            if look < n and _token_kind(parts[look]) in {direction, "neutral"}:
                buf.extend(parts[idx:look])
                idx = look
                continue
            break
        runs.append((direction, buf))
    return runs


def _split_he_punct(tok: str) -> list[str]:
    """מפריד נקודה/סימן שאלה ממילה עברית כדי שהפיסוק יישב בסוף הקריאה מימין."""
    if _token_kind(tok) != "rtl":
        return [tok]
    lead = re.match(r"^([.!?]+)([\u0590-\u05FF].*)$", tok)
    if lead:
        return [lead.group(1), lead.group(2)]
    trail = re.match(r"^([\u0590-\u05FF].*?)([.!?]+)$", tok)
    if trail:
        return [trail.group(1), trail.group(2)]
    return [tok]


def _is_short_ltr(tokens: list[str]) -> bool:
    chunk = "".join(tokens).strip()
    return bool(re.fullmatch(r"[A-Za-z][.?]?", chunk))


def _glue_short_ltr(runs: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """מצמיד x / a / v? למילה העברית שלידם, כדי לא לקרוע «מהו x?»."""
    out: list[tuple[str, list[str]]] = []
    idx = 0
    n = len(runs)
    while idx < n:
        direction, tokens = runs[idx]
        if direction == "rtl":
            look = idx + 1
            spaces: list[str] = []
            if look < n and runs[look][0] == "space":
                spaces = runs[look][1]
                look += 1
            if look < n and runs[look][0] == "ltr" and _is_short_ltr(runs[look][1]):
                out.append(("rtl", tokens + spaces + runs[look][1]))
                idx = look + 1
                continue
        out.append((direction, tokens))
        idx += 1
    return out


def visual_line(text: str) -> str:
    """סדר מילים לקריאה מימין ב-Windows לועזי, בלי להפוך אנגלית או נוסחה."""
    if not text or text.isspace():
        return text
    parts = _expand_parts(text)
    kinds = {_token_kind(part) for part in parts}
    if "rtl" not in kinds:
        return text
    if "ltr" not in kinds:
        expanded = []
        for part in parts:
            expanded.extend(_split_he_punct(part))
        return "".join(reversed(expanded))
    runs = _glue_short_ltr(_directional_runs(parts))
    equation = any(ch in text for ch in "=\u2192\u21d2") and any(ch.isdigit() for ch in text)
    ordered = runs if equation else list(reversed(runs))
    out: list[str] = []
    for direction, tokens in ordered:
        if direction == "rtl":
            inner: list[str] = []
            for tok in tokens:
                inner.extend(_split_he_punct(tok))
            out.append("".join(reversed(inner)))
        else:
            out.append("".join(tokens))
    return "".join(out)


def visual_letters(text: str) -> str:
    """הופך גם אותיות עבריות, למחשב שמצייר משמאל בלי Uniscribe."""
    if not text:
        return text
    if not _HEB.search(text):
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


def _wrap_latin_runs(text: str) -> str:
    """שומר פיסוק וסדר באנגלית/מספרים גם כשהתווית עברית מימין לשמאל."""
    if not text or not _LTR.search(text):
        return text
    if not _HEB.search(text):
        return _LRE + text + _PDF
    out: list[str] = []
    for direction, tokens in _directional_runs(_SEG.findall(text)):
        chunk = "".join(tokens)
        if direction == "ltr":
            out.append(_LRE + chunk + _PDF)
        else:
            out.append(chunk)
    return "".join(out)


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
        if not _HEB.search(cleaned):
            return _DONE + _wrap_latin_runs(cleaned)
        return _DONE + _wrap_latin_runs(visual_line(cleaned))
    if mode == "letters":
        if not _HEB.search(cleaned):
            return _DONE + _wrap_latin_runs(cleaned)
        return _DONE + visual_letters(cleaned)
    if windows_has_rtl_ui():
        if not _HEB.search(cleaned):
            return _wrap_latin_runs(cleaned)
        if _LTR.search(cleaned):
            return _RLE + _wrap_latin_runs(cleaned) + _PDF
        return _RLE + cleaned + _PDF
    return cleaned


def apply_paragraph(text: str) -> str:
    """לקטע שמתלפף: בלי היפוך ויזואלי של כל הפסקה, ששובר נקודות באמצע שורה."""
    if not text:
        return text
    if _already(text):
        return text
    cleaned = strip_marks(text)
    if resolved_mode() not in {"words", "letters"}:
        return apply(text)
    if not _HEB.search(cleaned):
        return _DONE + _wrap_latin_runs(cleaned)
    body = _wrap_latin_runs(cleaned) if _LTR.search(cleaned) else cleaned
    return _DONE + _RLE + body + _PDF
