"""לקוח Ollama מקומי — בלי מפתח API, רק http://localhost:11434."""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any

from core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED_DEFAULT,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SEC,
)

_lock = threading.Lock()
_cache: dict[str, Any] = {
    "ok": None,
    "checked_at": 0.0,
    "models": (),
    "error": "",
}
_HEALTH_TTL = 20.0


def _base_url(override: str | None = None) -> str:
    raw = (override or os.environ.get("STUDYAPP_OLLAMA_URL") or OLLAMA_BASE_URL or "").strip()
    return raw.rstrip("/") or "http://localhost:11434"


def _model_name(override: str | None = None) -> str:
    return (override or os.environ.get("STUDYAPP_OLLAMA_MODEL") or OLLAMA_MODEL or "qwen2.5:3b").strip()


def _timeout(override: float | None = None) -> float:
    if override is not None:
        return float(override)
    try:
        return float(os.environ.get("STUDYAPP_OLLAMA_TIMEOUT") or OLLAMA_TIMEOUT_SEC)
    except (TypeError, ValueError):
        return float(OLLAMA_TIMEOUT_SEC)


def enabled(storage=None) -> bool:
    """העדפת משתמש גוברת על ברירת המחדל בקוד."""
    if storage is not None:
        pref = storage.get_pref("ollama_enabled", None)
        if pref is not None:
            return bool(pref)
    env = os.environ.get("STUDYAPP_OLLAMA_ENABLED")
    if env is not None:
        return env.strip().lower() not in {"0", "false", "off", "no"}
    return bool(OLLAMA_ENABLED_DEFAULT)


def configured_model(storage=None) -> str:
    if storage is not None:
        pref = str(storage.get_pref("ollama_model") or "").strip()
        if pref:
            return pref
    return _model_name()


def configured_url(storage=None) -> str:
    if storage is not None:
        pref = str(storage.get_pref("ollama_url") or "").strip()
        if pref:
            return pref.rstrip("/")
    return _base_url()


def _request(
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    timeout: float | None = None,
    base: str | None = None,
) -> dict[str, Any]:
    url = f"{_base_url(base)}{path}"
    data = None
    headers = {"Accept": "application/json", "User-Agent": "StudyApp-Ollama/1.0"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=_timeout(timeout)) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return {}
    return json.loads(raw)


def health(
    *,
    force: bool = False,
    storage=None,
    timeout: float | None = 3.0,
) -> dict[str, Any]:
    """בדיקת חיבור קצרה עם מטמון."""
    now = time.time()
    with _lock:
        if (
            not force
            and _cache["ok"] is not None
            and (now - float(_cache["checked_at"] or 0)) < _HEALTH_TTL
        ):
            return {
                "ok": bool(_cache["ok"]),
                "models": list(_cache["models"] or ()),
                "error": str(_cache["error"] or ""),
                "url": configured_url(storage),
                "model": configured_model(storage),
                "cached": True,
            }
    url = configured_url(storage)
    model = configured_model(storage)
    try:
        data = _request("GET", "/api/tags", timeout=timeout, base=url)
        names = tuple(
            str(item.get("name") or "").strip()
            for item in (data.get("models") or [])
            if isinstance(item, dict) and item.get("name")
        )
        with _lock:
            _cache.update(ok=True, checked_at=now, models=names, error="")
        return {
            "ok": True,
            "models": list(names),
            "error": "",
            "url": url,
            "model": model,
            "cached": False,
            "has_model": any(
                name == model or name.startswith(f"{model}:") or model.startswith(name.split(":")[0])
                for name in names
            ),
        }
    except Exception as exc:
        msg = str(exc).strip() or type(exc).__name__
        with _lock:
            _cache.update(ok=False, checked_at=now, models=(), error=msg)
        return {
            "ok": False,
            "models": [],
            "error": msg,
            "url": url,
            "model": model,
            "cached": False,
            "has_model": False,
        }


def invalidate_health() -> None:
    with _lock:
        _cache["ok"] = None
        _cache["checked_at"] = 0.0


def chat(
    messages: list[dict[str, str]],
    *,
    system: str = "",
    model: str | None = None,
    storage=None,
    temperature: float = 0.3,
    timeout: float | None = None,
    format_json: bool = False,
) -> str:
    """שיחה עם המודל המקומי. מחזיר טקסט ריק אם נכשל."""
    if not enabled(storage):
        return ""
    status = health(storage=storage)
    if not status.get("ok"):
        return ""
    chosen = (model or configured_model(storage)).strip()
    payload_msgs: list[dict[str, str]] = []
    if system.strip():
        payload_msgs.append({"role": "system", "content": system.strip()})
    for row in messages:
        role = str(row.get("role") or "user").strip() or "user"
        content = str(row.get("content") or "").strip()
        if content:
            payload_msgs.append({"role": role, "content": content})
    if not payload_msgs:
        return ""
    body: dict[str, Any] = {
        "model": chosen,
        "messages": payload_msgs,
        "stream": False,
        "options": {
            "temperature": float(temperature),
            "num_predict": 512,
        },
    }
    if format_json:
        body["format"] = "json"
    try:
        data = _request(
            "POST",
            "/api/chat",
            payload=body,
            timeout=timeout,
            base=configured_url(storage),
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        invalidate_health()
        return ""
    msg = data.get("message") if isinstance(data, dict) else None
    if isinstance(msg, dict):
        return str(msg.get("content") or "").strip()
    return str(data.get("response") or "").strip()


def generate(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    storage=None,
    temperature: float = 0.3,
    timeout: float | None = None,
) -> str:
    """קריאה פשוטה ל-/api/generate."""
    if not enabled(storage):
        return ""
    status = health(storage=storage)
    if not status.get("ok"):
        return ""
    chosen = (model or configured_model(storage)).strip()
    body: dict[str, Any] = {
        "model": chosen,
        "prompt": str(prompt or "").strip(),
        "stream": False,
        "options": {"temperature": float(temperature), "num_predict": 512},
    }
    if system.strip():
        body["system"] = system.strip()
    try:
        data = _request(
            "POST",
            "/api/generate",
            payload=body,
            timeout=timeout,
            base=configured_url(storage),
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        invalidate_health()
        return ""
    return str((data or {}).get("response") or "").strip()


def status_line(storage=None) -> str:
    st = health(storage=storage, force=True)
    if not enabled(storage):
        return "העוזר המקומי כבוי בהגדרות."
    if not st.get("ok"):
        return (
            f"אין חיבור לכתובת {st.get('url')}. "
            "התקינו והריצו Ollama, ואז בחרו מודל כמו qwen2.5:3b."
        )
    models = st.get("models") or []
    model = st.get("model") or configured_model(storage)
    if models and not st.get("has_model"):
        shown = " · ".join(models[:3])
        return f"יש חיבור, אבל המודל «{model}» חסר. זמינים: {shown or 'אין'}."
    return f"מחובר · {model}"
