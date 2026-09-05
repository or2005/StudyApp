"""לקוח Ollama מקומי — בלי מפתח API, רק http://localhost:11434."""
from __future__ import annotations

import json
import os
import socket
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
_chat_gate = threading.Lock()
_cache: dict[str, Any] = {
    "ok": None,
    "checked_at": 0.0,
    "models": (),
    "error": "",
    "has_model": None,
}
_last_error = ""
_HEALTH_TTL = 25.0
# בקשות כבדות במקביל מפילות מחשבים חלשים וגורמות ל־Ollama להיתקע.
_MAX_CHAT_SECONDS = 45.0
_DEFAULT_PREDICT = 256


def _base_url(override: str | None = None) -> str:
    raw = (override or os.environ.get("STUDYAPP_OLLAMA_URL") or OLLAMA_BASE_URL or "").strip()
    return raw.rstrip("/") or "http://localhost:11434"


def _model_name(override: str | None = None) -> str:
    return (override or os.environ.get("STUDYAPP_OLLAMA_MODEL") or OLLAMA_MODEL or "qwen2.5:3b").strip()


def _timeout(override: float | None = None) -> float:
    if override is not None:
        return float(min(float(override), 90.0))
    try:
        base = float(os.environ.get("STUDYAPP_OLLAMA_TIMEOUT") or OLLAMA_TIMEOUT_SEC)
    except (TypeError, ValueError):
        base = float(OLLAMA_TIMEOUT_SEC)
    return float(min(max(8.0, base), _MAX_CHAT_SECONDS))


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


def last_error() -> str:
    with _lock:
        return str(_last_error or "")


def _set_error(msg: str) -> None:
    global _last_error
    with _lock:
        _last_error = str(msg or "").strip()


def _model_present(names: tuple[str, ...] | list[str], model: str) -> bool:
    model = (model or "").strip()
    if not model or not names:
        return False
    base = model.split(":")[0]
    for name in names:
        name = str(name or "").strip()
        if not name:
            continue
        if name == model or name.startswith(f"{model}:") or name.split(":")[0] == base:
            return True
    return False


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
    wait = _timeout(timeout)
    with urllib.request.urlopen(req, timeout=wait) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return {}
    return json.loads(raw)


def health(
    *,
    force: bool = False,
    storage=None,
    timeout: float | None = 2.5,
) -> dict[str, Any]:
    """בדיקת חיבור קצרה עם מטמון."""
    now = time.time()
    model = configured_model(storage)
    url = configured_url(storage)
    with _lock:
        if (
            not force
            and _cache["ok"] is not None
            and (now - float(_cache["checked_at"] or 0)) < _HEALTH_TTL
        ):
            names = list(_cache["models"] or ())
            has = _cache.get("has_model")
            if has is None:
                has = _model_present(names, model)
            return {
                "ok": bool(_cache["ok"]),
                "models": names,
                "error": str(_cache["error"] or ""),
                "url": url,
                "model": model,
                "cached": True,
                "has_model": bool(has),
            }
    try:
        data = _request("GET", "/api/tags", timeout=timeout, base=url)
        names = tuple(
            str(item.get("name") or "").strip()
            for item in (data.get("models") or [])
            if isinstance(item, dict) and item.get("name")
        )
        has = _model_present(names, model)
        with _lock:
            _cache.update(
                ok=True, checked_at=now, models=names, error="", has_model=has,
            )
        _set_error("" if has else f"המודל «{model}» חסר ב־Ollama")
        return {
            "ok": True,
            "models": list(names),
            "error": "" if has else f"המודל «{model}» חסר",
            "url": url,
            "model": model,
            "cached": False,
            "has_model": has,
        }
    except Exception as exc:
        msg = str(exc).strip() or type(exc).__name__
        with _lock:
            _cache.update(ok=False, checked_at=now, models=(), error=msg, has_model=False)
        _set_error(msg)
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
        _cache["has_model"] = None


def busy() -> bool:
    return _chat_gate.locked()


def chat(
    messages: list[dict[str, str]],
    *,
    system: str = "",
    model: str | None = None,
    storage=None,
    temperature: float = 0.3,
    timeout: float | None = None,
    format_json: bool = False,
    num_predict: int | None = None,
) -> str:
    """שיחה עם המודל המקומי. מחזיר טקסט ריק אם נכשל / עסוק / אין מודל."""
    if not enabled(storage):
        _set_error("העוזר המקומי כבוי")
        return ""
    # בלי נעילה כפולה: בקשה שנייה נופלת מיד ל־fallback במקום לחכות דקות.
    if not _chat_gate.acquire(blocking=False):
        _set_error("העוזר עדיין עונה על בקשה קודמת. נסו שוב בעוד רגע.")
        return ""
    try:
        status = health(storage=storage, timeout=2.0)
        if not status.get("ok"):
            _set_error(status.get("error") or "אין חיבור ל־Ollama")
            return ""
        # חשוב: אם המודל חסר, Ollama עלול להתחיל הורדה ארוכה ולתקוע את הממשק.
        if status.get("models") and not status.get("has_model"):
            _set_error(
                f"המודל «{status.get('model')}» לא מותקן. "
                f"ב־Ollama הריצו: ollama pull {status.get('model')}"
            )
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
        predict = int(num_predict if num_predict is not None else _DEFAULT_PREDICT)
        predict = max(64, min(400, predict))
        body: dict[str, Any] = {
            "model": chosen,
            "messages": payload_msgs,
            "stream": False,
            "keep_alive": "2m",
            "options": {
                "temperature": float(temperature),
                "num_predict": predict,
            },
        }
        if format_json:
            body["format"] = "json"
        wait = _timeout(timeout if timeout is not None else _MAX_CHAT_SECONDS)
        data = _request(
            "POST",
            "/api/chat",
            payload=body,
            timeout=wait,
            base=configured_url(storage),
        )
        msg = data.get("message") if isinstance(data, dict) else None
        if isinstance(msg, dict):
            text = str(msg.get("content") or "").strip()
        else:
            text = str((data or {}).get("response") or "").strip()
        if not text:
            _set_error("המודל החזיר תשובה ריקה")
        else:
            _set_error("")
        return text
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout, OSError, ValueError, json.JSONDecodeError) as exc:
        invalidate_health()
        err = str(exc).strip() or type(exc).__name__
        if "timed out" in err.lower() or isinstance(exc, (TimeoutError, socket.timeout)):
            _set_error("התשובה לקחה יותר מדי זמן. נסו שוב, או כבו את העוזר בהגדרות.")
        else:
            _set_error(err)
        return ""
    except Exception as exc:
        invalidate_health()
        _set_error(str(exc).strip() or type(exc).__name__)
        return ""
    finally:
        try:
            _chat_gate.release()
        except RuntimeError:
            pass


def generate(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    storage=None,
    temperature: float = 0.3,
    timeout: float | None = None,
    num_predict: int | None = None,
) -> str:
    """קריאה פשוטה ל-/api/generate."""
    if not enabled(storage):
        return ""
    # ממומש מעל chat כדי ליהנות מאותן הגנות (נעילה / מודל חסר / timeout).
    messages = [{"role": "user", "content": str(prompt or "").strip()}]
    return chat(
        messages,
        system=system,
        model=model,
        storage=storage,
        temperature=temperature,
        timeout=timeout,
        num_predict=num_predict,
    )


def status_line(storage=None) -> str:
    st = health(storage=storage, force=True, timeout=2.5)
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
        return (
            f"יש חיבור, אבל המודל «{model}» חסר. "
            f"הריצו בטרמינל: ollama pull {model}. "
            f"זמינים: {shown or 'אין'}."
        )
    if busy():
        return f"מחובר · {model} · עסוק עכשיו"
    return f"מחובר · {model}"
