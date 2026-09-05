"""עדכוני תוכנה, בדיקה ברשת, הורדה, והתקנה מקובץ מקומי."""
from __future__ import annotations

import json
import os
import re
import shutil
import ssl
import sys
import tempfile
import time
import webbrowser
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

USER_AGENT = (
    f"StudyApp/{VERSION} (+https://github.com/or2005/StudyApp) "
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TIMEOUT = 18
DOWNLOAD_TIMEOUT = 420
MAX_DOWNLOAD = 450 * 1024 * 1024
DOWNLOAD_RETRIES = 2

# מראות מובנות (גם אם latest.json במטמון ישן).
_BUILTIN_MIRRORS = {
    "5.0.1": (
        "https://raw.githubusercontent.com/or2005/StudyApp/downloads/StudyApp-5.0.1-setup.exe",
        "https://raw.githubusercontent.com/or2005/StudyApp/downloads/StudyApp-5.0.1-windows.zip",
        "https://github.com/or2005/StudyApp/releases/download/v5.0.1/StudyApp-5.0.1-setup.exe",
        "https://github.com/or2005/StudyApp/releases/download/v5.0.1/StudyApp-5.0.1-windows.zip",
    ),
    "5.0.0": (
        "https://raw.githubusercontent.com/or2005/StudyApp/downloads/StudyApp-5.0.0-setup.exe",
        "https://raw.githubusercontent.com/or2005/StudyApp/downloads/StudyApp-5.0.0-windows.zip",
        "https://github.com/or2005/StudyApp/releases/download/v5.0.0/StudyApp-5.0.0-setup.exe",
        "https://github.com/or2005/StudyApp/releases/download/v5.0.0/StudyApp-5.0.0-windows.zip",
    ),
}

# מראות לקבצי Release כש־github.com / release-assets חסומים (בתי ספר, רשתות).
# jsDelivr מחזיר 403 לקבצי exe/zip גדולים — raw.githubusercontent אמין יותר.
_MIRROR_PREFIXES = (
    "https://raw.githubusercontent.com/or2005/StudyApp/downloads/",
    "https://ghfast.top/",
    "https://mirror.ghproxy.com/",
)


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


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get_json(url: str) -> dict | list | None:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=TIMEOUT, context=_ssl_context()) as resp:
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
    local = None
    if os.path.isfile(bundled):
        try:
            with open(bundled, "r", encoding="utf-8") as handle:
                local = json.load(handle)
            if not (isinstance(local, dict) and local.get("version")):
                local = None
        except Exception:
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


def _collect_urls(blob: dict[str, Any] | None) -> list[str]:
    if not isinstance(blob, dict):
        return []
    keys = (
        "download",
        "windows_setup",
        "windows_zip",
        "windows_setup_alt",
        "windows_zip_alt",
        "linux_portable",
    )
    found: list[str] = []
    for key in keys:
        url = str(blob.get(key) or "").strip()
        if url and url not in found:
            found.append(url)
    mirrors = blob.get("mirrors")
    if isinstance(mirrors, list):
        for item in mirrors:
            url = str(item or "").strip()
            if url and url not in found:
                found.append(url)
    return found


def _merge_remote(github: dict | None, manifest: dict | None) -> dict[str, Any] | None:
    if not github and not manifest:
        return None
    if not github:
        out = dict(manifest or {})
    else:
        out = dict(github)
        if manifest:
            for key in (
                "windows_setup", "windows_zip", "linux_portable", "page", "notes",
                "windows_setup_alt", "windows_zip_alt",
            ):
                if not str(out.get(key) or "").strip() and manifest.get(key):
                    out[key] = manifest[key]
            if manifest.get("version") and not out.get("version"):
                out["version"] = manifest["version"]
            out["source"] = f"{out.get('source') or 'github'}+manifest"

    # מראות מובנות + מניפסט קודם (CDN), כדי לעקוף חסימות GitHub Releases.
    mirrors: list[str] = []
    version = str(out.get("version") or "").lstrip("vV")
    for url in (
        list(_BUILTIN_MIRRORS.get(version) or ())
        + list((manifest or {}).get("mirrors") or [])
        + _collect_urls(manifest)
    ):
        url = str(url or "").strip()
        if url and url not in mirrors:
            mirrors.append(url)
    if mirrors:
        out["mirrors"] = mirrors
        if out.get("windows_setup") and not out.get("windows_setup_alt"):
            if "raw.githubusercontent" not in str(out.get("windows_setup")):
                out["windows_setup_alt"] = out["windows_setup"]
        if out.get("windows_zip") and not out.get("windows_zip_alt"):
            if "raw.githubusercontent" not in str(out.get("windows_zip")):
                out["windows_zip_alt"] = out["windows_zip"]
        for key, suffix in (("windows_setup", "-setup.exe"), ("windows_zip", "-windows.zip")):
            man_url = str((manifest or {}).get(key) or "").strip()
            if man_url and ("raw.githubusercontent" in man_url or "jsdelivr" in man_url):
                out[key] = man_url
                continue
            for url in mirrors:
                if "raw.githubusercontent.com" in url and suffix in url:
                    out[key] = url
                    break
    return out


def check_latest(current: str = VERSION) -> dict[str, Any]:
    """בודק אם יש גרסה חדשה. לא מוריד."""
    remote = _merge_remote(_from_github(), _from_manifest())
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
        "version": latest,
        "windows_setup": remote.get("windows_setup") or "",
        "windows_zip": remote.get("windows_zip") or "",
        "linux_portable": remote.get("linux_portable") or "",
        "mirrors": list(remote.get("mirrors") or []) + list(_BUILTIN_MIRRORS.get(latest) or ()),
        "page": remote.get("page") or "",
        "source": remote.get("source") or "",
        "message": message,
    }


def preferred_download(info: dict[str, Any]) -> str:
    urls = download_candidates(info)
    return urls[0] if urls else ""


def _filename_of(url: str) -> str:
    return url.split("?")[0].rstrip("/").split("/")[-1] or "studyapp-update.bin"


def expand_mirrors(url: str) -> list[str]:
    """מרחיב קישור GitHub למראות CDN / proxy (רק חבילות Windows שקיימות בענף downloads)."""
    url = str(url or "").strip()
    if not url:
        return []
    out = [url]
    name = _filename_of(url)
    lower = url.lower()
    if "github.com" in lower and "/releases/download/" in lower and name:
        is_win_pkg = name.endswith((".exe", ".zip")) and "linux" not in name
        for prefix in _MIRROR_PREFIXES:
            if "raw.githubusercontent" in prefix:
                if not is_win_pkg:
                    continue
                alt = prefix + name
            else:
                alt = prefix + url
            if alt not in out:
                out.append(alt)
    return out


def download_candidates(info: dict[str, Any]) -> list[str]:
    """סדר: מראות CDN קודם (רשתות שחוסמות GitHub), אחר כך setup/zip הרשמיים."""
    if os.name == "nt":
        keys = ("download", "windows_setup", "windows_zip", "windows_setup_alt", "windows_zip_alt")
    else:
        keys = ("download", "linux_portable")
    seed: list[str] = []
    version = str(info.get("version") or info.get("latest") or "").lstrip("vV")
    for url in list(info.get("mirrors") or []) + list(_BUILTIN_MIRRORS.get(version) or ()):
        url = str(url or "").strip()
        if url and url not in seed:
            # ב־Windows לא לערבב לינוקס בראש הרשימה
            if os.name == "nt" and "linux" in url.lower():
                continue
            seed.append(url)
    for key in keys:
        url = str(info.get(key) or "").strip()
        if url and url not in seed:
            seed.append(url)

    found: list[str] = []
    for url in seed:
        for alt in expand_mirrors(url):
            if alt not in found:
                found.append(alt)
    return found


def _looks_like_payload(path: str, url: str) -> bool:
    try:
        size = os.path.getsize(path)
    except OSError:
        return False
    if size < 64_000:
        return False
    try:
        with open(path, "rb") as handle:
            magic = handle.read(8)
    except OSError:
        return False
    name = _filename_of(url).lower()
    if name.endswith(".zip") or magic[:2] == b"PK":
        return magic[:2] == b"PK"
    if name.endswith(".exe") or magic[:2] == b"MZ":
        return magic[:2] == b"MZ"
    if name.endswith(".gz") or name.endswith(".tgz"):
        return magic[:2] == b"\x1f\x8b"
    return True


def download_file(url: str, dest: str, on_progress: Callable[[int, int], None] | None = None) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        tmp = dest + f".part{attempt}"
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
            req = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/octet-stream,*/*",
                    "Accept-Language": "he,en;q=0.8",
                },
            )
            with urlopen(req, timeout=DOWNLOAD_TIMEOUT, context=_ssl_context()) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                ctype = str(resp.headers.get("Content-Type") or "").lower()
                if "text/html" in ctype and total and total < 500_000:
                    raise OSError("השרת החזיר דף HTML במקום קובץ (כנראה חסימת רשת).")
                if total > MAX_DOWNLOAD:
                    raise OSError("קובץ העדכון גדול מדי.")
                got = 0
                os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
                with open(tmp, "wb") as handle:
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
            if not _looks_like_payload(tmp, url):
                raise OSError("הקובץ שהתקבל פגום או אינו חבילת StudyApp.")
            os.replace(tmp, dest)
            return dest
        except Exception as exc:
            last_exc = exc
            _log().info("download attempt %s failed %s: %s", attempt, url, exc)
            try:
                if os.path.isfile(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(1.2 * attempt)
    assert last_exc is not None
    raise last_exc


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


def _dir_is_writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".studyapp_write_probe")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("1")
        os.remove(probe)
        return True
    except OSError:
        return False


def _desktop_dir() -> str:
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")
    if os.path.isdir(desktop):
        return desktop
    return home


def _apply_zip(path: str) -> dict[str, Any]:
    if not zipfile.is_zipfile(path):
        return {"ok": False, "message": "ה-ZIP פגום."}
    dest = install_dir()
    if not is_frozen():
        return _extract_and_open(path)

    parent = os.path.dirname(dest)
    staging_root = parent if _dir_is_writable(parent) else os.path.join(
        os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "StudyApp"
    )
    staging = os.path.join(staging_root, "StudyApp_update_staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)
    try:
        os.makedirs(staging, exist_ok=True)
        with zipfile.ZipFile(path, "r") as zf:
            if not _zip_root_has_exe(zf) and not any(
                n.replace("\\", "/").lower().endswith("studyapp.exe") for n in zf.namelist()
            ):
                return {"ok": False, "message": "ב-ZIP אין StudyApp.exe."}
            zf.extractall(staging)
    except OSError as exc:
        return _extract_to_desktop(path, reason=str(exc))

    payload = staging
    inner = os.path.join(staging, "StudyApp")
    if os.path.isdir(inner) and os.path.isfile(os.path.join(inner, "StudyApp.exe")):
        payload = inner
    else:
        for root, _dirs, files in os.walk(staging):
            if "StudyApp.exe" in files:
                payload = root
                break

    if not _dir_is_writable(dest):
        return _extract_to_desktop(path, reason="אין הרשאת כתיבה לתיקיית ההתקנה")

    script = _write_swap_script(payload, dest)
    try:
        os.startfile(script)  # noqa: S606
    except Exception as exc:
        return _extract_to_desktop(path, reason=str(exc))
    return {
        "ok": True,
        "restart": True,
        "message": "העדכון יותקן אחרי שהחלון ייסגר. התוכנה תיפתח שוב לבד.",
    }


def _extract_to_desktop(path: str, reason: str = "") -> dict[str, Any]:
    folder = os.path.join(_desktop_dir(), f"StudyApp_{VERSION}_new")
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder, exist_ok=True)
    with zipfile.ZipFile(path, "r") as zf:
        zf.extractall(folder)
    try:
        os.startfile(folder)  # noqa: S606
    except Exception:
        pass
    hint = f" ({reason})" if reason else ""
    return {
        "ok": True,
        "restart": False,
        "message": (
            f"לא ניתן היה להחליף את ההתקנה הקיימת{hint}.\n"
            f"חולצה תיקייה חדשה לשולחן העבודה:\n{folder}\n"
            "הפעילו משם את StudyApp.exe. ההתקדמות נשמרת."
        ),
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
    try:
        if os.name == "nt":
            os.startfile(path)  # noqa: S606
        else:
            webbrowser.open(path)
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


def open_in_browser(info: dict[str, Any] | None = None) -> str:
    """פותח קישור הורדה בדפדפן (למקרה שההורדה הפנימית נחסמת)."""
    info = info or {}
    url = preferred_download(info) or str(info.get("page") or "").strip()
    if not url:
        url = f"https://github.com/{GITHUB_REPO}/releases/latest"
    try:
        webbrowser.open(url)
    except Exception:
        try:
            os.startfile(url)  # noqa: S606
        except Exception:
            pass
    return url


def download_and_apply(info: dict[str, Any], on_progress=None) -> dict[str, Any]:
    urls = download_candidates(info)
    page = str(info.get("page") or "")
    from core.i18n import block

    if not urls:
        open_in_browser(info if page else {"page": page})
        return {"ok": False, "message": block("update.no_url")}
    folder = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "StudyApp", "updates")
    os.makedirs(folder, exist_ok=True)
    last_err: Exception | None = None
    for url in urls:
        name = _filename_of(url)
        # שמירה בשם יציב לפי סיומת, בלי query של פרוקסי
        if name.endswith(".exe"):
            dest = os.path.join(folder, name if "studyapp" in name.lower() else "StudyApp-setup.exe")
        elif name.endswith(".zip"):
            dest = os.path.join(folder, name if "studyapp" in name.lower() else "StudyApp-windows.zip")
        else:
            dest = os.path.join(folder, name)
        try:
            download_file(url, dest, on_progress)
        except Exception as exc:
            last_err = exc
            _log().info("download failed %s: %s", url, exc)
            continue
        return apply_local_file(dest)

    opened = open_in_browser(info)
    hint = f"\n{block('update.manual')}\n{opened}"
    return {"ok": False, "message": block("update.download_fail", err=last_err) + hint}
