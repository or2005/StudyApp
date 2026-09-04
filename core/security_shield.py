"""מגן שלמות לגרסת התקנה: זיהוי שינוי קבצים, הרצה חשודה, וחסימת חדר מפתח."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from typing import Any

from core.config import BASE_DIR, VERSION
from core.storage import DATA_DIR

MANIFEST_NAME = "integrity.manifest.json"
SEAL_NAME = "security_seal.json"
CRITICAL_REL = (
    "core/adaptive_engine.py",
    "core/analytics.py",
    "core/studio_gate.py",
    "core/security_shield.py",
    "core/config.py",
    "core/loader.py",
    "ui/app.py",
    "main.py",
)

_STATE: dict[str, Any] = {
    "checked": False,
    "ok": True,
    "frozen": False,
    "issues": [],
    "tampered": False,
    "debugger": False,
}


def _repo_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return BASE_DIR


def _file_digest(path: str) -> str | None:
    try:
        hasher = hashlib.sha256()
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 64)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError:
        return None


def build_manifest(root: str | None = None) -> dict[str, Any]:
    """בונה מניפסט hashes לקבצים קריטיים — נקרא בזמן בנייה."""
    root = os.path.abspath(root or BASE_DIR)
    files: dict[str, str] = {}
    for rel in CRITICAL_REL:
        full = os.path.join(root, rel.replace("/", os.sep))
        digest = _file_digest(full)
        if digest:
            files[rel.replace("\\", "/")] = digest
    # גם מאגרי שאלות — כדי שלא ישנו תוכן מאחורי הגב
    qdir = os.path.join(root, "data", "questions")
    if os.path.isdir(qdir):
        for name in sorted(os.listdir(qdir)):
            if not name.endswith(".json"):
                continue
            rel = f"data/questions/{name}"
            digest = _file_digest(os.path.join(qdir, name))
            if digest:
                files[rel] = digest
    return {
        "version": VERSION,
        "algo": "sha256",
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": files,
    }


def write_manifest(dest: str | None = None, root: str | None = None) -> str:
    root = os.path.abspath(root or BASE_DIR)
    dest = dest or os.path.join(root, MANIFEST_NAME)
    payload = build_manifest(root)
    with open(dest, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return dest


def _load_manifest(root: str) -> dict[str, Any] | None:
    for candidate in (
        os.path.join(root, MANIFEST_NAME),
        os.path.join(root, "_internal", MANIFEST_NAME),
        os.path.join(getattr(sys, "_MEIPASS", root), MANIFEST_NAME),
    ):
        if not os.path.isfile(candidate):
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _debugger_present() -> bool:
    if sys.gettrace() is not None:
        return True
    for name in ("pydevd", "debugpy", "_pydevd_bundle"):
        if name in sys.modules:
            return True
    # סימני סביבת פירוק נפוצים ב-Windows
    for key in ("PYTHONINSPECT", "PYTHONBREAKPOINT"):
        if os.environ.get(key):
            return True
    return False


def _source_tree_exposed(root: str) -> bool:
    """בגרסת exe לא אמור להיות עץ מקור ליד ההתקנה."""
    if not getattr(sys, "frozen", False):
        return False
    markers = (
        os.path.join(root, "core", "adaptive_engine.py"),
        os.path.join(root, "ui", "app.py"),
        os.path.join(root, "main.py"),
    )
    return any(os.path.isfile(path) for path in markers)


def verify(force: bool = False) -> dict[str, Any]:
    if _STATE["checked"] and not force:
        return dict(_STATE)
    frozen = bool(getattr(sys, "frozen", False))
    root = _repo_root()
    issues: list[str] = []
    tampered = False
    debugger = _debugger_present()

    if debugger and frozen:
        issues.append("זוהתה סביבת ניפוי באגים ליד גרסת התקנה.")

    if _source_tree_exposed(root):
        issues.append("נמצאו קבצי מקור ליד ההתקנה — חשד לחילוץ/העתקה.")
        tampered = True

    manifest = _load_manifest(root)
    if frozen and manifest is None:
        issues.append("חסר מניפסט שלמות — לא ניתן לאמת שהקבצים לא שונו.")
    elif manifest:
        files = manifest.get("files") or {}
        for rel, want in files.items():
            # ב-PyInstaller onedir הקבצים ב-_internal או ליד ה-exe
            candidates = [
                os.path.join(root, rel.replace("/", os.sep)),
                os.path.join(root, "_internal", rel.replace("/", os.sep)),
                os.path.join(getattr(sys, "_MEIPASS", root), rel.replace("/", os.sep)),
            ]
            got = None
            for path in candidates:
                if os.path.isfile(path):
                    got = _file_digest(path)
                    break
            if got is None:
                # במצב מקור בזמן פיתוח — דילוג רך
                if not frozen:
                    continue
                issues.append(f"חסר קובץ קריטי: {rel}")
                tampered = True
                continue
            if got != want:
                issues.append(f"קובץ שונה: {rel}")
                tampered = True

    ok = not tampered and not (frozen and debugger)
    _STATE.update(
        {
            "checked": True,
            "ok": ok,
            "frozen": frozen,
            "issues": issues,
            "tampered": tampered,
            "debugger": debugger,
            "root": root,
            "version": VERSION,
        }
    )
    _persist_seal(_STATE)
    return dict(_STATE)


def _persist_seal(state: dict[str, Any]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, SEAL_NAME)
    payload = {
        "ok": bool(state.get("ok")),
        "tampered": bool(state.get("tampered")),
        "debugger": bool(state.get("debugger")),
        "issues": list(state.get("issues") or [])[:12],
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": VERSION,
        "frozen": bool(state.get("frozen")),
    }
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except OSError:
        pass


def is_compromised() -> bool:
    state = verify()
    return bool(state.get("tampered") or (state.get("frozen") and state.get("debugger")))


def studio_allowed() -> bool:
    """חדר מפתח נחסם אם זוהה שינוי בגרסת התקנה."""
    state = verify()
    if state.get("frozen") and (state.get("tampered") or state.get("debugger")):
        return False
    return True


def status_report() -> str:
    state = verify(force=True)
    lines = [
        "מחלקת ביטחון · דוח שלמות",
        f"גרסה: {VERSION}",
        f"מצב: {'התקנה (frozen)' if state.get('frozen') else 'מקור (פיתוח)'}",
        f"תקין: {'כן' if state.get('ok') else 'לא'}",
        f"שינוי קבצים: {'כן' if state.get('tampered') else 'לא'}",
        f"ניפוי באגים: {'כן' if state.get('debugger') else 'לא'}",
        "",
    ]
    issues = list(state.get("issues") or [])
    if issues:
        lines.append("ממצאים:")
        for item in issues:
            lines.append(f"• {item}")
    else:
        lines.append("אין ממצאים חשודים.")
    lines.append("")
    lines.append(
        "הערה: הגנה מלאה מפני הנדסה לאחור אינה אפשרית בתוכנת שולחן עבודה, "
        "אבל המגן חוסם שינויים גסים, חוסם חדר מפתח אחרי חבלה, ומתריע."
    )
    return "\n".join(lines)


def student_warning() -> str | None:
    state = verify()
    if state.get("ok"):
        return None
    if state.get("tampered"):
        return (
            "זוהה שינוי בקבצי התוכנה. חלק מהכלים נחסמו.\n"
            "התקינו מחדש מעותק רשמי."
        )
    if state.get("debugger") and state.get("frozen"):
        return "זוהתה סביבת פירוק. מצב אבטחה מוגבר פעיל."
    return None
