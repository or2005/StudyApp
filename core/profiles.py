"""כמה פרופילים במחשב אחד, בלי לדרוס התקדמות בין אחים."""
from __future__ import annotations

import json
import os
import shutil
import time
from typing import Any

from core.storage import get_persistent_app_dir

DEFAULT_ID = "default"
REGISTRY_NAME = "profiles.json"
_migrated = False


def _root(root: str | None = None) -> str:
    return root or get_persistent_app_dir()


def registry_path(root: str | None = None) -> str:
    return os.path.join(_root(root), REGISTRY_NAME)


def profile_dir(profile_id: str, root: str | None = None) -> str:
    return os.path.join(_root(root), "profiles", profile_id)


def profile_files(profile_id: str, root: str | None = None) -> dict[str, str]:
    folder = profile_dir(profile_id, root)
    return {
        "dir": folder,
        "user_profile": os.path.join(folder, "user_profile.json"),
        "user_stats": os.path.join(folder, "user_stats.json"),
        "session_state": os.path.join(folder, "session_state.json"),
    }


def _atomic_write(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _blank_registry() -> dict[str, Any]:
    return {
        "current": DEFAULT_ID,
        "profiles": [{"id": DEFAULT_ID, "name": "תלמיד", "created": time.strftime("%Y-%m-%d")}],
        "os": {
            "autostart": False,
            "daily_reminder": False,
            "reminder_hour": 17,
            "reminder_minute": 0,
        },
    }


def load_registry(root: str | None = None) -> dict[str, Any]:
    path = registry_path(root)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("bad registry")
        data.setdefault("current", DEFAULT_ID)
        data.setdefault("profiles", [])
        data.setdefault("os", _blank_registry()["os"])
        if not data["profiles"]:
            data["profiles"] = _blank_registry()["profiles"]
        ids = {item.get("id") for item in data["profiles"] if isinstance(item, dict)}
        if data["current"] not in ids:
            data["current"] = data["profiles"][0]["id"]
        return data
    except Exception:
        return _blank_registry()


def save_registry(data: dict[str, Any], root: str | None = None) -> None:
    _atomic_write(registry_path(root), data)


def get_os_pref(key: str, default: Any = None, root: str | None = None) -> Any:
    os_prefs = load_registry(root).get("os") or {}
    return os_prefs.get(key, default)


def set_os_pref(key: str, value: Any, root: str | None = None) -> None:
    data = load_registry(root)
    os_prefs = data.setdefault("os", _blank_registry()["os"])
    os_prefs[key] = value
    save_registry(data, root)


def ensure_migrated(root: str | None = None) -> dict[str, Any]:
    """מעביר user_profile.json הישן לפרופיל ברירת מחדל, פעם אחת."""
    global _migrated
    base = _root(root)
    data = load_registry(root)
    current = str(data.get("current") or DEFAULT_ID)
    files = profile_files(current, root)
    os.makedirs(files["dir"], exist_ok=True)
    for name in ("user_profile.json", "user_stats.json", "session_state.json"):
        src = os.path.join(base, name)
        dst = os.path.join(files["dir"], name)
        if os.path.isfile(src) and not os.path.isfile(dst):
            try:
                shutil.move(src, dst)
            except Exception:
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass
    if not os.path.isfile(registry_path(root)):
        save_registry(data, root)
    _migrated = True
    return data


def current_id(root: str | None = None) -> str:
    ensure_migrated(root)
    return str(load_registry(root).get("current") or DEFAULT_ID)


def current_files(root: str | None = None) -> dict[str, str]:
    ensure_migrated(root)
    return profile_files(current_id(root), root)


def list_profiles(root: str | None = None) -> list[dict[str, Any]]:
    ensure_migrated(root)
    rows = []
    current = current_id(root)
    for item in load_registry(root).get("profiles") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        row = dict(item)
        row["current"] = row["id"] == current
        rows.append(row)
    return rows


def current_name(root: str | None = None) -> str:
    cid = current_id(root)
    for item in list_profiles(root):
        if item.get("id") == cid:
            return str(item.get("name") or "תלמיד")
    return "תלמיד"


def _unique_name(name: str, profiles: list[dict], skip_id: str | None = None) -> str:
    clean = (name or "").strip() or "תלמיד"
    taken = {
        str(item.get("name") or "")
        for item in profiles
        if item.get("id") != skip_id
    }
    if clean not in taken:
        return clean
    idx = 2
    while f"{clean} ({idx})" in taken:
        idx += 1
    return f"{clean} ({idx})"


def create_profile(name: str, root: str | None = None) -> str:
    ensure_migrated(root)
    data = load_registry(root)
    profiles = data.setdefault("profiles", [])
    pid = f"p{int(time.time() * 1000)}"
    display = _unique_name(name, profiles)
    profiles.append({"id": pid, "name": display, "created": time.strftime("%Y-%m-%d")})
    os.makedirs(profile_files(pid, root)["dir"], exist_ok=True)
    save_registry(data, root)
    return pid


def rename_profile(profile_id: str, name: str, root: str | None = None) -> bool:
    ensure_migrated(root)
    data = load_registry(root)
    profiles = data.get("profiles") or []
    display = _unique_name(name, profiles, skip_id=profile_id)
    for item in profiles:
        if item.get("id") == profile_id:
            item["name"] = display
            save_registry(data, root)
            return True
    return False


def switch_profile(profile_id: str, root: str | None = None) -> bool:
    ensure_migrated(root)
    data = load_registry(root)
    ids = {item.get("id") for item in data.get("profiles") or []}
    if profile_id not in ids:
        return False
    os.makedirs(profile_files(profile_id, root)["dir"], exist_ok=True)
    data["current"] = profile_id
    save_registry(data, root)
    return True


def delete_profile(profile_id: str, root: str | None = None) -> str | None:
    """מוחק פרופיל. מחזיר את מזהה הפרופיל הפעיל אחרי המחיקה, או None אם נכשל."""
    ensure_migrated(root)
    data = load_registry(root)
    profiles = [item for item in (data.get("profiles") or []) if isinstance(item, dict)]
    if len(profiles) <= 1:
        return None
    if not any(item.get("id") == profile_id for item in profiles):
        return None
    remaining = [item for item in profiles if item.get("id") != profile_id]
    data["profiles"] = remaining
    if data.get("current") == profile_id:
        data["current"] = remaining[0]["id"]
    folder = profile_files(profile_id, root)["dir"]
    save_registry(data, root)
    try:
        shutil.rmtree(folder, ignore_errors=True)
    except Exception:
        pass
    return str(data["current"])
