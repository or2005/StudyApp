# -*- coding: utf-8 -*-
"""ניקוי מקפי AI (— –) וניסוחים שבורים בכל מאגרי השאלות."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QDIR = ROOT / "data" / "questions"

# מקף אמריקאי/AI → ניסוח עברי טבעי
_EM = "\u2014"  # —
_EN = "\u2013"  # –

_AIISH = [
    (re.compile(r"\bחשוב לציין ש"), ""),
    (re.compile(r"\bראוי לציין ש"), ""),
    (re.compile(r"\bבסך הכול\b"), "בסך הכל"),
    (re.compile(r"\bניתן לומר ש"), ""),
    (re.compile(r"\bבעצם\s*,\s*"), ""),
    (re.compile(r"חשבו לפי הכלל:\s*"), ""),
    (re.compile(r"הנקודה העדינה\s*[:：]\s*"), ""),
    (re.compile(r"ניסוח עדין\s*[:：]\s*"), ""),
]


def _humanize(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    raw = text
    # מקף ארוך בין מילים עבריות → נקודתיים או פסיק לפי הקשר
    raw = raw.replace(f" {_EM} ", ": ")
    raw = raw.replace(f" {_EN} ", ", ")
    raw = raw.replace(_EM, ": ")
    raw = raw.replace(_EN, "-")
    # טווחים מספריים: 6: 8 → 6 עד 8 אם נראה כמו טווח שאלות
    raw = re.sub(r"(\d+)\s*:\s*(\d+)\s+שאלות", r"\1 עד \2 שאלות", raw)
    for pat, repl in _AIISH:
        raw = pat.sub(repl, raw)
    raw = re.sub(r" {2,}", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip() if text.strip() == text.strip() else raw


def _walk(obj):
    if isinstance(obj, dict):
        out = {}
        for key, val in obj.items():
            if key in {
                "question",
                "explanation",
                "hint",
                "topic",
                "title",
                "content",
                "theory_content",
                "theory",
                "correct_answer",
                "selected_text",
            } or key.endswith("_he"):
                if isinstance(val, str):
                    out[key] = _humanize(val)
                else:
                    out[key] = _walk(val)
            elif key in {"options", "tags", "examples"} and isinstance(val, list):
                out[key] = [
                    _humanize(item) if isinstance(item, str) else _walk(item) for item in val
                ]
            else:
                out[key] = _walk(val)
        return out
    if isinstance(obj, list):
        return [_walk(item) for item in obj]
    return obj


def main() -> None:
    changed_files = 0
    dash_before = 0
    dash_after = 0
    for path in sorted(QDIR.glob("*.json")):
        blob = path.read_text(encoding="utf-8")
        before = blob.count(_EM) + blob.count(_EN)
        dash_before += before
        data = json.loads(blob)
        fixed = _walk(data)
        out = json.dumps(fixed, ensure_ascii=False, indent=2) + "\n"
        after = out.count(_EM) + out.count(_EN)
        dash_after += after
        if out != blob:
            path.write_text(out, encoding="utf-8")
            changed_files += 1
            print(f"fixed {path.name}: dashes {before} -> {after}")
    print(f"files_changed={changed_files} dashes {dash_before} -> {dash_after}")


if __name__ == "__main__":
    main()
