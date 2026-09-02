"""עדכוני תוכנה, בדיקה ברשת, הורדה, והתקנה מקובץ מקומי."""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.config import (
    GITHUB_REPO,
    UPDATE_MANIFEST_URLS,
    VERSION,
    BASE_DIR,
)

log = None

USER_AGENT = f"StudyApp/{VERSION} (+https://github.com/dadshaev/StudyApp)"
TIMEOUT = 18
MAX_DOWNLOAD = 450 * 1024 * 1024


def _log():
    global log
    if log is None:
        from core.applog import get_logger

        log = get_logger("updates")
    return log


def parse_version(value: str) -> tuple[int, int, int]:
    nums = [int(part) for part in re.findall(r"\d+", str(value or "0"))]
    while len(nums) < 3:
        nums.append(0)
    return nums[0], nums[1], nums[2]


def is_newer(remote: str, current: str = VERSION) -> bool:
    return parse_version(remote) > parse_version(current)


def install_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(BASE_DIR)


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _get_json(url: str) -> dict | list | None:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        if isinstance(exc, HTTPError) and getattr(exc, "code", None) == 404:
            _log().debug("fetch 404 %s", url)
        else:
            _log().info("fetch failed %s: %s", url, exc)
        return None


def _pick_asset(assets: list[dict], names: tuple[str, ...]) -> str:
    lowered = [(str(item.get("name") or ""), str(item.get("browser_download_url") or "")) for item in assets]
    for needle in names:
        for name, url in lowered:
            if needle in name.lower() and url:
                return url
    return ""


def _from_github() -> dict[str, Any] | None:
    repo = (GITHUB_REPO or "").strip()
    if not repo:
        return None
    data = _get_json(f"https://api.github.com/repos/{repo}/releases/latest")
    if not isinstance(data, dict):
        return None
    tag = str(data.get("tag_name") or data.get("name") or "").lstrip("vV")
    if not tag:
        return None
    assets = data.get("assets") or []
    if not isinstance(assets, list):
        assets = []
    win_setup = _pick_asset(assets, ("-setup.exe", "setup.exe"))
    win_zip = _pick_asset(assets, ("-windows.zip", "windows.zip", ".zip"))
    linux = _pick_asset(assets, ("linux-portable", ".tar.gz"))
    return {
        "version": tag,
        "notes": (data.get("body") or "")[:800],
        "windows_setup": win_setup,
        "windows_zip": win_zip,
        "linux_portable": linux,
        "page": data.get("html_url") or "",
        "source": "github",
    }


def _from_manifest() -> dict[str, Any] | None:
    bundled = os.path.join(BASE_DIR, "docs", "latest.json")
    urls = list(UPDATE_MANIFEST_URLS)
    if os.path.isfile(bundled):
        try:
            with open(bundled, "r", encoding="utf-8") as handle:
                local = json.load(handle)
            if isinstance(local, dict) and local.get("version"):
                # הקובץ המצורף מתאר את הגרסה הנוכחית; ברשת מחפשים חדשה יותר.
                pass
        except Exception:
            local = None
    else:
        local = None
    for url in urls:
        data = _get_json(url)
        if isinstance(data, dict) and data.get("version"):
            data = dict(data)
            data["source"] = "manifest"
            return data
    if isinstance(local, dict) and local.get("version"):
        local = dict(local)
        local["source"] = "bundled"
        return local
    return None


def check_latest(current: str = VERSION) -> dict[str, Any]:
    """בודק אם יש גרסה חדשה. לא מוריד."""
    remote = _from_github() or _from_manifest()
    if not remote:
        return {
            "ok": False,
            "newer": False,
            "current": current,
            "latest": current,
            "error": "offline",
            "message": "אין חיבור, או שערוץ העדכונים עוד לא פורסם. אפשר להתקין מקובץ ידנית.",
        }
    latest = str(remote.get("version") or current).lstrip("vV")
    newer = is_newer(latest, current)
    download = preferred_download(remote)
    notes = str(remote.get("notes") or "").strip()
    if newer and not notes:
        notes = "גלילה ומעבר בין מסכים חלקים יותר. ההתקדמות בלימוד לא נמחקת."
    if newer:
        message = f"יש גרסה חדשה: {latest} (אצלך {current})."
    else:
        message = f"התוכנה מעודכנת. גרסה {current}."
    return {
        "ok": True,
        "newer": newer,
        "current": current,
        "latest": latest,
        "notes": notes,
        "download": download,
        "windows_setup": remote.get("windows_setup") or "",
        "windows_zip": remote.get("windows_zip") or "",
        "linux_portable": remote.get("linux_portable") or "",
        "page": remote.get("page") or "",
        "source": remote.get("source") or "",
        "message": message,
    }


def preferred_download(info: dict[str, Any]) -> str:
    if os.name == "nt":
        return str(info.get("windows_setup") or info.get("windows_zip") or "")
    return str(info.get("linux_portable") or "")


def download_file(url: str, dest: str, on_progress: Callable[[int, int], None] | None = None) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        if total > MAX_DOWNLOAD:
            raise OSError("קובץ העדכון גדול מדי.")
        got = 0
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "wb") as handle:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                got += len(chunk)
                if got > MAX_DOWNLOAD:
                    raise OSError("קובץ העדכון גדול מדי.")
                handle.write(chunk)
                if on_progress:
                    on_progress(got, total)
    return dest


def _looks_like_update(path: str) -> str:
    """מחזיר 'setup' / 'zip' / 'tar' או מחרוזת ריקה."""
    name = os.path.basename(path).lower()
    if name.endswith(".exe") and "studyapp" in name:
        return "setup"
    if name.endswith(".zip"):
        return "zip"
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return "tar"
    if name.endswith(".exe"):
        return "setup"
    return ""


def apply_local_file(path: str) -> dict[str, Any]:
    """מתקין עדכון מקובץ שהמשתמש בחר, או שהורד מהרשת."""
    if not path or not os.path.isfile(path):
        return {"ok": False, "message": "הקובץ לא נמצא."}
    kind = _looks_like_update(path)
    if not kind:
        return {"ok": False, "message": "צריך קובץ StudyApp (setup.exe, zip או tar.gz)."}
    if kind == "setup":
        return _launch_setup(path)
    if kind == "zip":
        return _apply_zip(path)
    return _open_folder(path)


def _launch_setup(path: str) -> dict[str, Any]:
    try:
        os.startfile(path)  # noqa: S606
    except Exception as exc:
        return {"ok": False, "message": f"לא הצלחתי לפתוח את קובץ ההתקנה: {exc}"}
    return {
        "ok": True,
        "restart": True,
        "message": "נפתח קובץ ההתקנה. אשרו את האשף, ואז פתחו שוב את StudyApp.",
    }


def _zip_root_has_exe(zf: zipfile.ZipFile) -> str:
    names = zf.namelist()
    for name in names:
        base = name.replace("\\", "/").rstrip("/")
        if base.lower().endswith("studyapp.exe") and base.lower().count("/") <= 1:
            return name
    return ""


def _apply_zip(path: str) -> dict[str, Any]:
    if not zipfile.is_zipfile(path):
        return {"ok": False, "message": "ה-ZIP פגום."}
    dest = install_dir()
    if not is_frozen():
        return _extract_and_open(path)
    staging = os.path.join(os.path.dirname(dest), "StudyApp_update_staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    with zipfile.ZipFile(path, "r") as zf:
        if not _zip_root_has_exe(zf) and not any(
            n.replace("\\", "/").lower().endswith("studyapp.exe") for n in zf.namelist()
        ):
            return {"ok": False, "message": "ב-ZIP אין StudyApp.exe."}
        zf.extractall(staging)
    payload = staging
    inner = os.path.join(staging, "StudyApp")
    if os.path.isdir(inner) and os.path.isfile(os.path.join(inner, "StudyApp.exe")):
        payload = inner
    else:
        for root, _dirs, files in os.walk(staging):
            if "StudyApp.exe" in files:
                payload = root
                break
    script = _write_swap_script(payload, dest)
    try:
        os.startfile(script)  # noqa: S606
    except Exception as exc:
        return {"ok": False, "message": f"לא הצלחתי להפעיל את מחליף הקבצים: {exc}"}
    return {
        "ok": True,
        "restart": True,
        "message": "העדכון יותקן אחרי שהחלון ייסגר. התוכנה תיפתח שוב לבד.",
    }


def _extract_and_open(path: str) -> dict[str, Any]:
    folder = tempfile.mkdtemp(prefix="studyapp-update-")
    with zipfile.ZipFile(path, "r") as zf:
        zf.extractall(folder)
    try:
        os.startfile(folder)  # noqa: S606
    except Exception:
        pass
    return {
        "ok": True,
        "restart": False,
        "message": f"הקבצים חולצו אל:\n{folder}\nהעתיקו את התיקייה החדשה במקום הישנה.",
    }


def _open_folder(path: str) -> dict[str, Any]:
    folder = os.path.dirname(path)
    try:
        if os.name == "nt":
            os.startfile(path)  # noqa: S606
        else:
            shutil.copy2(path, folder)
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
    return {"ok": True, "restart": False, "message": "הקובץ נפתח. התקינו אותו ואז פתחו שוב את StudyApp."}


def _write_swap_script(src: str, dest: str) -> str:
    pid = os.getpid()
    exe = os.path.join(dest, "StudyApp.exe")
    bat = os.path.join(os.environ.get("LOCALAPPDATA") or dest, "StudyApp", "updates", "apply_update.bat")
    os.makedirs(os.path.dirname(bat), exist_ok=True)
    body = f"""@echo off
chcp 65001 >nul
set SRC={src}
set DEST={dest}
:wait
tasklist /FI "PID eq {pid}" | find "{pid}" >nul
if not errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto wait
)
robocopy "%SRC%" "%DEST%" /E /IS /IT /NFL /NDL /NJH /NJS
if exist "{exe}" (
  start "" "{exe}"
)
"""
    with open(bat, "w", encoding="utf-8") as handle:
        handle.write(body)
    return bat


def download_and_apply(info: dict[str, Any], on_progress=None) -> dict[str, Any]:
    url = str(info.get("download") or preferred_download(info) or "")
    if not url:
        page = info.get("page") or ""
        if page:
            try:
                os.startfile(page)  # noqa: S606
            except Exception:
                pass
        return {"ok": False, "message": "אין קישור הורדה. פורסם עמוד ההורדות, או התקינו מקובץ."}
    folder = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "StudyApp", "updates")
    os.makedirs(folder, exist_ok=True)
    name = url.split("?")[0].rstrip("/").split("/")[-1] or "studyapp-update.bin"
    dest = os.path.join(folder, name)
    try:
        download_file(url, dest, on_progress)
    except Exception as exc:
        return {"ok": False, "message": f"ההורדה נכשלה: {exc}"}
    return apply_local_file(dest)
