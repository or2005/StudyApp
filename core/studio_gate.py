"""כניסה לחדר מפתח. ההשוואה ב־hash, בלי לשמור סיסמה ביומן."""
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
LOCK_SECONDS = 15 * 60
GUARD_PATH = os.path.join(DATA_DIR, "studio_guard.json")
LOCK_MESSAGE = (
    "נשלח מייל ממחלקת הביטחון למתכנת.\n"
    "אסור לנסות לפרוץ לחדר הזה. הזהרו."
)


def _digest(user: str, password: str) -> str:
    raw = f"studyapp-studio-v1\0{(user or '').strip().lower()}\0{password or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check(user: str, password: str) -> bool:
    got = _digest(user, password)
    want = _digest("ordadshev", "Aa" + "327806" + "279@")
    return hmac.compare_digest(got, want)


def _load_guard() -> dict[str, Any]:
    try:
        with open(GUARD_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_guard(data: dict[str, Any]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GUARD_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False)


def _clear_guard() -> None:
    try:
        if os.path.isfile(GUARD_PATH):
            os.remove(GUARD_PATH)
    except OSError:
        pass


def locked_until() -> float:
    data = _load_guard()
    until = float(data.get("locked_until") or 0)
    if until and until <= time.time():
        _clear_guard()
        return 0
    return until


def send_security_alert() -> bool:
    url = (TELEMETRY_URL or "").strip()
    if not url:
        return False
    body = {
        "event": "studio_lockout",
        "version": VERSION,
        "attempts": MAX_FAILS,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "מחלקת ביטחון: הוקשה סיסמה שגויה 3 פעמים בחדר הבטוח. אין שם תלמיד ואין סיסמה.",
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
        return {"ok": False, "locked": True, "message": LOCK_MESSAGE, "alerted": True}
    if check(user, password):
        _clear_guard()
        return {"ok": True, "locked": False, "message": "", "alerted": False}
    data = _load_guard()
    fails = int(data.get("fails") or 0) + 1
    data["fails"] = fails
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
    return {"ok": False, "locked": True, "message": LOCK_MESSAGE, "alerted": alerted}
