"""ארכיוני מפתח: כל הקבצים, וחבילת דיסק און קי."""
from __future__ import annotations

import os
import shutil
import sys
import zipfile
from typing import Iterable

from core.config import BASE_DIR, VERSION

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".qpanda",
    "node_modules",
    "_qa_shots",
    "_qa_play",
    ".cursor",
    "main.build",
    "main.dist",
}
SKIP_FILES = {".ds_store", "thumbs.db"}
SOURCE_SKIP_TOP = {"dist", "build", "main.build", "main.dist"}


def project_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return BASE_DIR


def _skip_dir(name: str) -> bool:
    return name.lower() in SKIP_DIRS or name.endswith(".egg-info")


def _iter_source_files(root: str) -> Iterable[tuple[str, str]]:
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        top = rel_dir.split(os.sep, 1)[0] if rel_dir != "." else ""
        if top.lower() in SOURCE_SKIP_TOP:
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if not _skip_dir(name)]
        for name in filenames:
            if name.lower() in SKIP_FILES:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            yield full, rel.replace("\\", "/")


VSCODE_BAT = """@echo off
cd /d "%~dp0"
where code >nul 2>&1 && (
  code .
  goto :eof
)
if exist "%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe" (
  "%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe" .
  goto :eof
)
if exist "%ProgramFiles%\\Microsoft VS Code\\Code.exe" (
  "%ProgramFiles%\\Microsoft VS Code\\Code.exe" .
  goto :eof
)
echo VS Code was not found.
echo Open this folder in VS Code: File ^> Open Folder
pause
"""

VSCODE_SETTINGS = """{
  "python.analysis.extraPaths": ["."],
  "files.exclude": {
    "**/__pycache__": true,
    ".venv": true
  }
}
"""

HOWTO_VSCODE = """StudyApp Files - קבצי התוכנה
==============================
זה כל קוד המקור של StudyApp. לא קובץ התקנה לתלמיד.
אם המחשב נמחק או שהפרויקט נעלם, כאן אפשר להחזיר את הקוד
ולפתוח אותו ישר ב-VS Code כדי לערוך.

איך פותחים:
1. חלצו את קובץ ה-zip.
2. תתקבל תיקייה בשם StudyAppFiles.
3. ב-VS Code: File, אחר כך Open Folder, ואז בחרו את StudyAppFiles.
   או לחצו פעמיים על הקובץ: פתח-ב-VS-Code.bat

אחרי הפתיחה, בטרמינל של VS Code:
    python -m venv .venv
    .venv\\Scripts\\activate
    pip install -r requirements.txt
    python main.py

בלי .venv, בלי build, בלי .git. אלה נוצרים מחדש אצלך.
להתקנה לתלמיד על דיסק און קי השתמשו בחבילת הדיסק, לא כאן.
"""


def write_source_zip(dest: str, root: str | None = None) -> str:
    root = os.path.abspath(root or project_root())
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for full, rel in _iter_source_files(root):
            archive.write(full, f"StudyAppFiles/{rel}")
        archive.writestr(
            "StudyAppFiles/README-STUDIO.txt",
            (
                f"StudyApp Files {VERSION}\n"
                "כל קבצי הקוד של התוכנה, מוכנים לפתיחה ב-VS Code.\n"
                "ראו את הקובץ: איך-לפתוח-ב-VS-Code.txt\n"
            ),
        )
        archive.writestr("StudyAppFiles/איך-לפתוח-ב-VS-Code.txt", HOWTO_VSCODE)
        archive.writestr("StudyAppFiles/פתח-ב-VS-Code.bat", VSCODE_BAT.replace("\n", "\r\n"))
        archive.writestr("StudyAppFiles/.vscode/settings.json", VSCODE_SETTINGS)
    return dest


def _dist_exe(root: str) -> str | None:
    for candidate in (
        os.path.join(root, "dist", "StudyApp", "StudyApp.exe"),
        os.path.join(root, "StudyApp.exe"),
        os.path.abspath(sys.executable) if getattr(sys, "frozen", False) else "",
    ):
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def _write_usb_readme(folder: str, has_exe: bool) -> None:
    text = (
        f"StudyApp {VERSION}  -  דיסק און קי\n"
        "==============================\n\n"
        "העתיקו את כל התיקייה הזו לדיסק און קי. אל תעתיקו קובץ בודד.\n\n"
    )
    if has_exe:
        text += (
            "הפעלה ב-Windows: לחצו פעמיים על StudyApp.exe\n"
            "או על הקובץ הפעל-מהדיסק.bat\n"
        )
    else:
        text += (
            "אין עדיין קובץ exe בנוי. על המחשב צריך Python.\n"
            "לחצו על הפעל-מהדיסק.bat או הריצו: python main.py\n"
            "כדי לבנות exe: python tools/build_release.py --windows\n"
        )
    text += "\nההתקדמות של התלמיד נשמרת במחשב שלו, לא על הדיסק.\n"
    with open(os.path.join(folder, "קרא-אותי.txt"), "w", encoding="utf-8") as handle:
        handle.write(text)


def _write_usb_launcher(folder: str, has_exe: bool) -> None:
    if has_exe:
        bat = (
            "@echo off\n"
            "cd /d \"%~dp0\"\n"
            "start \"\" \"StudyApp.exe\"\n"
        )
    else:
        bat = (
            "@echo off\n"
            "cd /d \"%~dp0\"\n"
            "where python >nul 2>&1 && python main.py && goto :eof\n"
            "where py >nul 2>&1 && py main.py && goto :eof\n"
            "echo Python is required to run this copy.\n"
            "pause\n"
        )
    with open(os.path.join(folder, "הפעל-מהדיסק.bat"), "w", encoding="utf-8") as handle:
        handle.write(bat)


def write_usb_zip(dest: str, root: str | None = None) -> str:
    root = os.path.abspath(root or project_root())
    staging = dest + ".staging"
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    exe = _dist_exe(root)
    has_exe = False
    if exe:
        exe_dir = os.path.dirname(exe)
        if os.path.basename(exe_dir).lower() == "studyapp" or os.path.isfile(
            os.path.join(exe_dir, "StudyApp.exe")
        ):
            for name in os.listdir(exe_dir):
                src = os.path.join(exe_dir, name)
                target = os.path.join(staging, name)
                if os.path.isdir(src):
                    shutil.copytree(src, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, target)
            has_exe = os.path.isfile(os.path.join(staging, "StudyApp.exe"))
    if not has_exe:
        # ברירת מחדל: לא שולחים קוד מקור לתלמיד (הגנה על הקוד).
        # לפיתוח מקומי: set STUDYAPP_REQUIRE_EXE=0
        if os.environ.get("STUDYAPP_REQUIRE_EXE", "1") not in {"0", "false", "False"}:
            shutil.rmtree(staging, ignore_errors=True)
            raise FileNotFoundError(
                "לא נמצא StudyApp.exe ב-dist. בנו קודם עם "
                "python tools/build_release.py --windows ואז חבילת דיסק."
            )
        for full, rel in _iter_source_files(root):
            target = os.path.join(staging, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(target) or staging, exist_ok=True)
            shutil.copy2(full, target)
    _write_usb_readme(staging, has_exe)
    _write_usb_launcher(staging, has_exe)
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for dirpath, dirnames, filenames in os.walk(staging):
            dirnames[:] = [name for name in dirnames if not _skip_dir(name)]
            for name in filenames:
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, staging).replace("\\", "/")
                archive.write(full, f"StudyApp-USB/{rel}")
    shutil.rmtree(staging, ignore_errors=True)
    return dest
