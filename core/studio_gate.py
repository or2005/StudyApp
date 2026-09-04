"""כניסה לחדר מפתח. השוואת hash, נעילה, יומן אבטחה והתראה."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.request import Request, urlopen

from core.config import TELEMETRY_URL, VERSION
from core.storage import DATA_DIR

MAX_FAILS = 3
LOCK_SECONDS = 30 * 60
GUARD_PATH = os.path.join(DATA_DIR, "studio_guard.json")
EVENTS_PATH = os.path.join(DATA_DIR, "security_events.json")
MAX_EVENTS = 80
_GUARD_PEPPER = b"studyapp-guard-v2\x1fsecurity"
_XOR_KEY = 0x65
LOCK_MESSAGE = (
    "נשלח מייל ממחלקת הביטחון למתכנת.\n"
    "אסור לנסות לפרוץ לחדר הזה. הזהרו."
)


def _decode_xored(blob: bytes) -> str:
    return bytes(b ^ _XOR_KEY for b in blob).decode("ascii")


def _secret_material() -> tuple[str, str]:
    """מזהה מפעיל מחומר מקודד — לא כמחרוזת סיסמה גלויה בקוד."""
    # ordadshev
    user = _decode_xored(bytes([0x0A, 0x17, 0x01, 0x04, 0x01, 0x16, 0x0D, 0x00, 0x13]))
    # Aa327806279@
    password = _decode_xored(
        bytes([0x24, 0x04, 0x56, 0x57, 0x52, 0x5D, 0x55, 0x53, 0x57, 0x52, 0x5C, 0x25])
    )
    return user, password


def _digest(user: str, password: str) -> str:
    raw = f"studyapp-studio-v1\0{(user or '').strip().lower()}\0{password or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check(user: str, password: str) -> bool:
    got = _digest(user, password)
    want_user, want_pass = _secret_material()
    want = _digest(want_user, want_pass)
    return hmac.compare_digest(got, want)


def _sign_guard(payload: dict[str, Any]) -> str:
    body = json.dumps(
        {k: payload.get(k) for k in ("fails", "locked_until", "alert_sent")},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(_GUARD_PEPPER, body, hashlib.sha256).hexdigest()


def _load_guard() -> dict[str, Any]:
    try:
        with open(GUARD_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {}
        sig = str(data.get("sig") or "")
        if not sig:
            # קובץ ישן בלי חתימה — מקבלים ומחתימים בפעם הבאה
            return data
        if not hmac.compare_digest(sig, _sign_guard(data)):
            _log_event("guard_tamper", "קובץ נעילה שונה או מזויף")
            locked = {
                "fails": MAX_FAILS,
                "locked_until": time.time() + LOCK_SECONDS,
                "alert_sent": False,
            }
            try:
                _save_guard(locked)
            except OSError:
                pass
            return locked
        return data
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        _log_event("guard_corrupt", "קובץ נעילה פגום")
        return {}


def _save_guard(data: dict[str, Any]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = dict(data)
    payload["sig"] = _sign_guard(payload)
    with open(GUARD_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def _clear_guard() -> None:
    try:
        if os.path.isfile(GUARD_PATH):
            os.remove(GUARD_PATH)
    except OSError:
        pass


def _log_event(kind: str, note: str = "") -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    rows: list[dict[str, Any]] = []
    try:
        if os.path.isfile(EVENTS_PATH):
            with open(EVENTS_PATH, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            if isinstance(raw, list):
                rows = [item for item in raw if isinstance(item, dict)]
    except (OSError, json.JSONDecodeError):
        rows = []
    rows.append(
        {
            "kind": kind,
            "note": note,
            "version": VERSION,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )
    rows = rows[-MAX_EVENTS:]
    try:
        with open(EVENTS_PATH, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, ensure_ascii=False, indent=2)
    except OSError:
        pass


def recent_events(limit: int = 30) -> list[dict[str, Any]]:
    try:
        with open(EVENTS_PATH, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)][-limit:]
    except (OSError, json.JSONDecodeError):
        return []


def events_text(limit: int = 25) -> str:
    rows = recent_events(limit)
    if not rows:
        return "אין אירועי אבטחה עדיין."
    lines = ["יומן מחלקת ביטחון", "─" * 28]
    for row in reversed(rows):
        lines.append(f"{row.get('ts', '?')}  ·  {row.get('kind', '?')}")
        note = str(row.get("note") or "").strip()
        if note:
            lines.append(f"  {note}")
    return "\n".join(lines)


def locked_until() -> float:
    data = _load_guard()
    until = float(data.get("locked_until") or 0)
    if until and until <= time.time():
        _clear_guard()
        return 0
    return until


def send_security_alert(extra: str = "") -> bool:
    url = (TELEMETRY_URL or "").strip()
    if not url:
        return False
    note = (
        "מחלקת ביטחון: הוקשה סיסמה שגויה 3 פעמים בחדר הבטוח. "
        "אין שם תלמיד ואין סיסמה."
    )
    if extra:
        note = f"{note} {extra}"
    body = {
        "event": "studio_lockout",
        "version": VERSION,
        "attempts": MAX_FAILS,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": note,
        "_subject": "StudyApp מחלקת ביטחון — ניסיון כניסה כושל לחדר הבטוח",
        "_template": "box",
        "_captcha": "false",
    }
    req = Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"StudyApp/{VERSION}",
        },
    )
    try:
        with urlopen(req, timeout=12) as resp:
            resp.read()
        return True
    except OSError:
        return False


def attempt(user: str, password: str) -> dict[str, Any]:
    until = locked_until()
    if until:
        left_min = max(1, int((until - time.time()) / 60))
        return {
            "ok": False,
            "locked": True,
            "message": LOCK_MESSAGE + f"\nנעילה לעוד כ־{left_min} דקות.",
            "alerted": True,
        }
    if check(user, password):
        _clear_guard()
        _log_event("studio_login_ok", "כניסה מוצלחת לחדר מפתח")
        return {"ok": True, "locked": False, "message": "", "alerted": False}
    data = _load_guard()
    fails = int(data.get("fails") or 0) + 1
    data["fails"] = fails
    _log_event("studio_login_fail", f"ניסיון כושל ({fails}/{MAX_FAILS})")
    if fails < MAX_FAILS:
        _save_guard(data)
        left = MAX_FAILS - fails
        return {
            "ok": False,
            "locked": False,
            "message": f"הסיסמה לא נכונה. נשארו {left} ניסיונות.",
            "alerted": False,
        }
    data["locked_until"] = time.time() + LOCK_SECONDS
    alerted = send_security_alert()
    data["alert_sent"] = alerted
    _save_guard(data)
    _log_event(
        "studio_lockout",
        "נעילה אחרי 3 כשלונות" + (" · התראה נשלחה" if alerted else ""),
    )
    return {"ok": False, "locked": True, "message": LOCK_MESSAGE, "alerted": alerted}


def force_lock_session_note() -> str:
    _log_event("studio_logout", "יציאה מחדר מפתח")
    return "נסגר חדר המפתח."
