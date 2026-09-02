"""פינג אנונימי בהסכמה, בלי שם, גיל, ת״ז או נתוני למידה."""
from __future__ import annotations

import json
import os
import platform
import time
import uuid
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.config import TELEMETRY_URL, VERSION
from core.storage import DATA_DIR

ALLOWED_KEYS = frozenset({
    "event",
    "version",
    "os",
    "os_ver",
    "arch",
    "frozen",
    "install_id",
    "ts",
})
FORBIDDEN_HINTS = ("name", "age", "id", "idn", "student", "email", "path", "question")
QUEUE_PATH = os.path.join(DATA_DIR, "anon_ping_queue.json")


def ensure_install_id(storage) -> str:
    current = str(storage.get_pref("install_id") or "").strip()
    if current:
        return current
    fresh = str(uuid.uuid4())
    storage.set_pref("install_id", fresh)
    return fresh


def anonymous_payload(storage, event: str) -> dict[str, Any]:
    payload = {
        "event": str(event or "hello")[:40],
        "version": VERSION,
        "os": platform.system(),
        "os_ver": platform.release(),
        "arch": platform.machine(),
        "frozen": bool(getattr(__import__("sys"), "frozen", False)),
        "install_id": ensure_install_id(storage),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return {key: payload[key] for key in ALLOWED_KEYS}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    clean = {key: payload[key] for key in ALLOWED_KEYS if key in payload}
    blob = json.dumps(clean, ensure_ascii=False).lower()
    for hint in ("תעודת", "ת\"ז", "student_name"):
        if hint in blob:
            raise ValueError("payload contains personal data")
    return clean


def opted_in(storage) -> bool:
    return bool(storage.get_pref("telemetry_opt_in", False))


def send_ping(storage, event: str, force: bool = False) -> dict[str, Any]:
    if not force and not opted_in(storage):
        return {"ok": False, "message": "כבוי. לא נשלח כלום."}
    payload = validate_payload(anonymous_payload(storage, event))
    url = (TELEMETRY_URL or "").strip()
    if not url:
        _queue(payload)
        return {"ok": True, "queued": True, "message": "נשמר במחשב. אין יעד רשת מוגדר."}
    body = dict(payload)
    body["_subject"] = f"StudyApp {payload['event']} {payload['version']}"
    body["_template"] = "box"
    body["_captcha"] = "false"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=data,
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
        storage.set_pref("telemetry_last", payload["ts"])
        storage.set_pref("telemetry_last_event", payload["event"])
        return {"ok": True, "message": "נשלח פינג אנונימי (גרסה ומערכת בלבד)."}
    except (URLError, TimeoutError, OSError) as exc:
        _queue(payload)
        return {"ok": False, "queued": True, "message": f"לא הגיע לרשת, נשמר במחשב: {exc}"}


def maybe_hello(storage) -> None:
    if not opted_in(storage):
        return
    if storage.get_pref("telemetry_hello_sent"):
        return
    result = send_ping(storage, "hello")
    if result.get("ok") and not result.get("queued"):
        storage.set_pref("telemetry_hello_sent", True)


def maybe_weekly(storage) -> None:
    if not opted_in(storage):
        return
    last = str(storage.get_pref("telemetry_last") or "")
    if last[:10] == time.strftime("%Y-%m-%d"):
        return
    try:
        last_day = last[:10]
        if last_day:
            then = time.strptime(last_day, "%Y-%m-%d")
            if time.time() - time.mktime(then) < 6 * 24 * 3600:
                return
    except Exception:
        pass
    send_ping(storage, "alive")


def send_crash(storage, exc: BaseException | None) -> None:
    if not opted_in(storage):
        return
    kind = type(exc).__name__ if exc else "unknown"
    payload = anonymous_payload(storage, f"crash:{kind}"[:40])
    send_ping(storage, payload["event"])


def _queue(payload: dict[str, Any]) -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        items = []
        if os.path.isfile(QUEUE_PATH):
            with open(QUEUE_PATH, "r", encoding="utf-8") as handle:
                items = json.load(handle) or []
        if not isinstance(items, list):
            items = []
        items.append(payload)
        items = items[-30:]
        with open(QUEUE_PATH, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass
