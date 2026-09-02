"""בונה חבילות הורדה: Windows 10/11 ולינוקס (כל הפצה נפוצה)."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import VERSION  # noqa: E402


def _run(cmd: list[str]) -> None:
    print(">", " ".join(cmd), flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    code = subprocess.call(cmd, cwd=ROOT, env=env)
    if code:
        raise SystemExit(code)


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except Exception:
        _run([sys.executable, "-m", "pip", "install", "pyinstaller"])


def _write_text(path: str, text: str, *, lf: bool = False) -> None:
    data = text.replace("\r\n", "\n")
    if not lf:
        data = data.replace("\n", "\r\n") if os.name == "nt" else data
    encoding = "utf-8-sig" if path.lower().endswith(".txt") and not lf else "utf-8"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    newline = "\n" if lf else None
    with open(path, "w", encoding=encoding, newline=newline) as handle:
        handle.write(text.replace("\r\n", "\n") if lf else text)


def _desktop() -> str | None:
    path = os.path.join(os.path.expanduser("~"), "Desktop")
    return path if os.path.isdir(path) else None


def _copy_to_desktop(src: str) -> None:
    dest_dir = _desktop()
    if dest_dir:
        shutil.copy2(src, os.path.join(dest_dir, os.path.basename(src)))
        print("copied", os.path.basename(src), "to Desktop")


def _windows_readme() -> str:
    return f"""StudyApp {VERSION}
================

תוכנת לימוד בעברית למחשב Windows 10 ו-Windows 11 (64 ביט).
אין צורך בפייתון. אין דפדפן.

איך מפעילים
-----------
1. חלצו את כל התיקייה למקום קבוע.
2. אל תעבירו רק את StudyApp.exe, צריך את כל התיקייה ביחד.
3. לחצו פעמיים על StudyApp.exe.

ההתקדמות נשמרת ב-%LOCALAPPDATA%\\StudyApp

תמיכה: אור דדשב · dadshaev@gmail.com
© 2026 אור דדשב. כל הזכויות שמורות.
"""


def _linux_readme() -> str:
    return f"""StudyApp {VERSION}, Linux
=========================

חבילה ניידת לכל הפצות לינוקס הנפוצות:
Ubuntu, Debian, Linux Mint, Fedora, RHEL, Arch, Manjaro,
openSUSE, Elementary, Pop!_OS, Raspberry Pi OS, Alpine.

דרישה: Python 3.10+ עם Tkinter (python3-tk / python3-tkinter).

הפעלה מהירה
------------
chmod +x StudyApp.sh
./StudyApp.sh

התקנה לתפריט היישומים
----------------------
chmod +x install.sh
./install.sh

אם חסר Tkinter
--------------
Ubuntu/Debian/Mint:  sudo apt install python3 python3-venv python3-tk python3-pip
Fedora:              sudo dnf install python3 python3-tkinter python3-pip
Arch/Manjaro:        sudo pacman -S python python-pip tk
openSUSE:            sudo zypper install python3 python3-tk python3-pip
Alpine:              sudo apk add python3 py3-tkinter py3-pip

הנתונים נשמרים ב- ~/.local/share/StudyApp

תמיכה: אור דדשב · dadshaev@gmail.com
"""


def build_linux_portable() -> str:
    staging = os.path.join(ROOT, "build", "linux-portable", "StudyApp")
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)

    for name in ("main.py", "requirements.txt", "LICENSE"):
        shutil.copy2(os.path.join(ROOT, name), os.path.join(staging, name))
    for folder in ("core", "ui", "data", "assets"):
        dest = os.path.join(staging, folder)
        shutil.copytree(
            os.path.join(ROOT, folder),
            dest,
            ignore=lambda _d, names: [n for n in names if n == "__pycache__" or n.endswith(".pyc")],
        )
    os.makedirs(os.path.join(staging, "docs"), exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "docs", "TERMS.md"), os.path.join(staging, "docs", "TERMS.md"))
    shutil.copy2(os.path.join(ROOT, "docs", "latest.json"), os.path.join(staging, "docs", "latest.json"))

    for script in ("StudyApp.sh", "install.sh"):
        src = os.path.join(ROOT, "packaging", "linux", script)
        dest = os.path.join(staging, script)
        text = open(src, "r", encoding="utf-8").read().replace("\r\n", "\n")
        with open(dest, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        try:
            os.chmod(dest, 0o755)
        except OSError:
            pass
    shutil.copy2(
        os.path.join(ROOT, "packaging", "linux", "studyapp.desktop"),
        os.path.join(staging, "studyapp.desktop"),
    )
    _write_text(os.path.join(staging, "README.txt"), _linux_readme(), lf=True)

    dist_dir = os.path.join(ROOT, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    tar_path = os.path.join(dist_dir, f"StudyApp-{VERSION}-linux-portable.tar.gz")
    if os.path.isfile(tar_path):
        os.remove(tar_path)
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(staging, arcname="StudyApp")
    _copy_to_desktop(tar_path)
    print("LINUX portable", tar_path, f"({os.path.getsize(tar_path) / 1024 / 1024:.1f} MB)")
    return tar_path


def _zip_dir(src_dir: str, zip_path: str, inner: str) -> None:
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, _, files in os.walk(src_dir):
            for name in files:
                full = os.path.join(folder, name)
                rel = os.path.join(inner, os.path.relpath(full, src_dir))
                zf.write(full, rel)


def build_pyinstaller() -> str:
    _ensure_pyinstaller()
    _run([sys.executable, os.path.join(ROOT, "tools", "make_icon.py")])
    spec = os.path.join(ROOT, "studyapp.spec")
    _run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", spec])
    dist_dir = os.path.join(ROOT, "dist", "StudyApp")
    exe_name = "StudyApp.exe" if sys.platform.startswith("win") else "StudyApp"
    exe_path = os.path.join(dist_dir, exe_name)
    if not os.path.isfile(exe_path):
        print("ERROR: binary missing", exe_path, file=sys.stderr)
        raise SystemExit(1)
    return dist_dir


def build_windows() -> str:
    dist_dir = build_pyinstaller()
    _write_text(os.path.join(dist_dir, "קרא אותי.txt"), _windows_readme())
    shutil.copy2(os.path.join(ROOT, "LICENSE"), os.path.join(dist_dir, "LICENSE.txt"))
    shutil.copy2(os.path.join(ROOT, "docs", "TERMS.md"), os.path.join(dist_dir, "תקנון.txt"))
    zip_path = os.path.join(ROOT, "dist", f"StudyApp-{VERSION}-windows.zip")
    _zip_dir(dist_dir, zip_path, "StudyApp")
    _copy_to_desktop(zip_path)
    print("WINDOWS", zip_path, f"({os.path.getsize(zip_path) / 1024 / 1024:.1f} MB)")
    return zip_path


def build_linux_binary() -> str:
    if not sys.platform.startswith("linux"):
        print("Linux binary can only be built on Linux (or GitHub Actions).", file=sys.stderr)
        raise SystemExit(2)
    dist_dir = build_pyinstaller()
    _write_text(os.path.join(dist_dir, "README.txt"), _linux_readme(), lf=True)
    tar_path = os.path.join(ROOT, "dist", f"StudyApp-{VERSION}-linux-x86_64.tar.gz")
    if os.path.isfile(tar_path):
        os.remove(tar_path)
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(dist_dir, arcname="StudyApp")
    print("LINUX binary", tar_path)
    return tar_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build StudyApp download packages")
    parser.add_argument("--windows", action="store_true", help="PyInstaller zip for Windows 10/11")
    parser.add_argument("--linux-portable", action="store_true", help="Source+launcher tarball for all Linux distros")
    parser.add_argument("--linux-binary", action="store_true", help="PyInstaller tarball (run on Linux)")
    args = parser.parse_args(argv)

    os.chdir(ROOT)
    _run([sys.executable, os.path.join(ROOT, "tools", "make_icon.py")])

    selected = args.windows or args.linux_portable or args.linux_binary
    if not selected:
        args.linux_portable = True
        if sys.platform.startswith("win"):
            args.windows = True
        elif sys.platform.startswith("linux"):
            args.linux_binary = True

    if args.linux_portable:
        build_linux_portable()
    if args.windows:
        if not sys.platform.startswith("win"):
            print("skip --windows (not on Windows)")
        else:
            build_windows()
    if args.linux_binary:
        build_linux_binary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
