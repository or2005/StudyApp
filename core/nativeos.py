"""שילוב אמיתי עם Windows ולינוקס: תיקיות, התראות, הפעלה אוטומטית, תזכורות."""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from typing import Sequence

from core.platformutil import is_linux, is_windows

APP_AUMID = "Dadshaev.StudyApp"
TASK_NAME = "StudyAppDailyReminder"
STARTUP_NAME = "StudyApp"
LINUX_DESKTOP_ID = "studyapp.desktop"
LINUX_TIMER_UNIT = "studyapp-remind.timer"
LINUX_SERVICE_UNIT = "studyapp-remind.service"


def bind_app_identity() -> None:
    """משייך את התהליך ל־StudyApp ב־Windows (התראות, שורת המשימות)."""
    if not is_windows():
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_AUMID)
    except Exception:
        pass


def app_script_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))


def launch_argv(*extra: str) -> list[str]:
    extra_list = [str(item) for item in extra if item]
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), *extra_list]
    return [sys.executable, app_script_path(), *extra_list]


def quote_cmd(parts: Sequence[str]) -> str:
    if is_windows():
        chunks = []
        for part in parts:
            text = str(part).replace('"', '\\"')
            chunks.append(f'"{text}"')
        return " ".join(chunks)
    return " ".join(shlex.quote(str(part)) for part in parts)


def documents_dir() -> str:
    if is_windows():
        home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        candidate = os.path.join(home, "Documents")
        return candidate if os.path.isdir(candidate) else home
    try:
        raw = subprocess.check_output(["xdg-user-dir", "DOCUMENTS"], text=True, timeout=3)
        path = raw.strip()
        if path and os.path.isdir(path):
            return path
    except Exception:
        pass
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    return docs if os.path.isdir(docs) else home


def _creation_flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0) if is_windows() else 0


def open_path(path: str) -> bool:
    """פותח קובץ או תיקייה בסייר / מנהל הקבצים של המערכת."""
    if not path:
        return False
    target = os.path.abspath(path)
    try:
        if is_windows():
            os.startfile(target)  # noqa: S606
            return True
        opener = "xdg-open" if is_linux() else "open"
        subprocess.Popen(
            [opener, target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False


def open_in_vscode(path: str) -> bool:
    """פותח תיקייה או קובץ ב-VS Code, אם התוכנה מותקנת."""
    if not path:
        return False
    target = os.path.abspath(path)
    candidates = []
    for name in ("code", "code.cmd", "code.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    if is_windows():
        local = os.environ.get("LOCALAPPDATA") or ""
        program_files = os.environ.get("ProgramFiles") or r"C:\Program Files"
        program_files_x86 = os.environ.get("ProgramFiles(x86)") or ""
        for candidate in (
            os.path.join(local, "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(program_files, "Microsoft VS Code", "Code.exe"),
            os.path.join(program_files_x86, "Microsoft VS Code", "Code.exe"),
        ):
            if candidate and os.path.isfile(candidate):
                candidates.append(candidate)
    seen = set()
    for exe in candidates:
        if not exe or exe in seen:
            continue
        seen.add(exe)
        try:
            subprocess.Popen(
                [exe, target],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=not is_windows(),
            )
            return True
        except Exception:
            continue
    return False


def reveal_in_file_manager(path: str) -> bool:
    if not path:
        return False
    target = os.path.abspath(path)
    if is_windows() and os.path.exists(target):
        try:
            subprocess.Popen(
                ["explorer", "/select,", target],
                creationflags=_creation_flags(),
            )
            return True
        except Exception:
            return open_path(os.path.dirname(target) if os.path.isfile(target) else target)
    folder = target if os.path.isdir(target) else os.path.dirname(target)
    return open_path(folder or target)


def notify(title: str, body: str) -> bool:
    title = (title or "StudyApp").strip() or "StudyApp"
    body = (body or "").strip() or "זמן לתרגול."
    if is_windows():
        return _notify_windows(title, body)
    if is_linux():
        return _notify_linux(title, body)
    return _notify_macos(title, body)


def _ps_quote(text: str) -> str:
    return (text or "").replace("'", "''")


def _notify_windows(title: str, body: str) -> bool:
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
        "$n.Visible = $true; "
        f"$n.ShowBalloonTip(8000, '{_ps_quote(title)}', '{_ps_quote(body)}', "
        "[System.Windows.Forms.ToolTipIcon]::Info); "
        "Start-Sleep -Seconds 8; "
        "$n.Dispose()"
    )
    try:
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-Command",
                script,
            ],
            creationflags=_creation_flags(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _notify_linux(title: str, body: str) -> bool:
    binary = shutil.which("notify-send")
    if not binary:
        return False
    cmd = [binary, "-a", "StudyApp", "-u", "normal", title, body]
    try:
        from core.config import ICON_PNG_PATH

        if os.path.isfile(ICON_PNG_PATH):
            cmd.extend(["-i", ICON_PNG_PATH])
    except Exception:
        pass
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False


def _notify_macos(title: str, body: str) -> bool:
    try:
        script = f'display notification "{body.replace(chr(34), "")}" with title "{title.replace(chr(34), "")}"'
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _startup_dir_windows() -> str:
    appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def _start_menu_dir_windows() -> str:
    appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "StudyApp")


def _linux_autostart_path() -> str:
    config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(config, "autostart", LINUX_DESKTOP_ID)


def _linux_app_desktop_path() -> str:
    data = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(data, "applications", LINUX_DESKTOP_ID)


def _desktop_body(exec_line: str) -> str:
    icon = ""
    try:
        from core.config import ICON_PNG_PATH

        if os.path.isfile(ICON_PNG_PATH):
            icon = f"Icon={ICON_PNG_PATH}\n"
    except Exception:
        pass
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        "Name=StudyApp\n"
        "Comment=תרגול לבגרות 3 יחידות ולמימ״ד\n"
        f"Exec={exec_line}\n"
        f"{icon}"
        "Terminal=false\n"
        "Categories=Education;\n"
        "StartupNotify=true\n"
    )


def autostart_enabled() -> bool:
    if is_windows():
        folder = _startup_dir_windows()
        return any(
            os.path.isfile(os.path.join(folder, f"{STARTUP_NAME}{ext}"))
            for ext in (".cmd", ".bat", ".lnk")
        )
    return os.path.isfile(_linux_autostart_path())


def set_autostart(enabled: bool) -> bool:
    if enabled:
        return _install_autostart()
    return _remove_autostart()


def _install_autostart() -> bool:
    command = quote_cmd(launch_argv())
    try:
        if is_windows():
            folder = _startup_dir_windows()
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{STARTUP_NAME}.cmd")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("@echo off\r\n")
                handle.write(f"start \"\" {command}\r\n")
            return True
        path = _linux_autostart_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(_desktop_body(command))
        try:
            os.chmod(path, 0o644)
        except Exception:
            pass
        return True
    except Exception:
        return False


def _remove_autostart() -> bool:
    try:
        if is_windows():
            folder = _startup_dir_windows()
            for ext in (".cmd", ".bat", ".lnk"):
                path = os.path.join(folder, f"{STARTUP_NAME}{ext}")
                if os.path.isfile(path):
                    os.remove(path)
            return True
        path = _linux_autostart_path()
        if os.path.isfile(path):
            os.remove(path)
        return True
    except Exception:
        return False


def install_user_shortcuts() -> bool:
    """קיצור בתפריט התחל / יישומים, בלי הרשאות מנהל."""
    ok = False
    command = quote_cmd(launch_argv())
    try:
        if is_windows():
            ok = _windows_start_menu_shortcut() and _windows_app_path()
        else:
            path = _linux_app_desktop_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(_desktop_body(command))
            try:
                os.chmod(path, 0o644)
            except Exception:
                pass
            try:
                subprocess.Popen(
                    ["update-desktop-database", os.path.dirname(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
            ok = True
    except Exception:
        ok = False
    return ok


def _windows_start_menu_shortcut() -> bool:
    folder = _start_menu_dir_windows()
    os.makedirs(folder, exist_ok=True)
    target = launch_argv()[0]
    workdir = os.path.dirname(app_script_path())
    lnk = os.path.join(folder, "StudyApp.lnk")
    args = ""
    if not getattr(sys, "frozen", False):
        args = quote_cmd(launch_argv()[1:])
    icon = target
    try:
        from core.config import ICON_PATH

        if os.path.isfile(ICON_PATH):
            icon = ICON_PATH
    except Exception:
        pass
    script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{_ps_quote(lnk)}'); "
        f"$s.TargetPath = '{_ps_quote(target)}'; "
        f"$s.Arguments = '{_ps_quote(args)}'; "
        f"$s.WorkingDirectory = '{_ps_quote(workdir)}'; "
        f"$s.IconLocation = '{_ps_quote(icon)}'; "
        "$s.Description = 'StudyApp'; "
        "$s.Save()"
    )
    try:
        subprocess.check_call(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
            creationflags=_creation_flags(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _windows_app_path() -> bool:
    if not is_windows() or not getattr(sys, "frozen", False):
        return True
    try:
        import winreg

        target = os.path.abspath(sys.executable)
        key = winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\App Paths\StudyApp.exe",
        )
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, target)
        winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, os.path.dirname(target))
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def reminder_installed() -> bool:
    if is_windows():
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", TASK_NAME],
                capture_output=True,
                creationflags=_creation_flags(),
                timeout=8,
            )
            return result.returncode == 0
        except Exception:
            return False
    timer = os.path.join(
        os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config"),
        "systemd",
        "user",
        LINUX_TIMER_UNIT,
    )
    return os.path.isfile(timer)


def set_daily_reminder(enabled: bool, hour: int = 17, minute: int = 0) -> bool:
    if enabled:
        return install_daily_reminder(hour, minute)
    return remove_daily_reminder()


def install_daily_reminder(hour: int = 17, minute: int = 0) -> bool:
    hour = max(0, min(23, int(hour)))
    minute = max(0, min(59, int(minute)))
    command = quote_cmd(launch_argv("--remind"))
    stamp = f"{hour:02d}:{minute:02d}"
    try:
        if is_windows():
            subprocess.check_call(
                [
                    "schtasks",
                    "/Create",
                    "/TN",
                    TASK_NAME,
                    "/TR",
                    command,
                    "/SC",
                    "DAILY",
                    "/ST",
                    stamp,
                    "/RL",
                    "LIMITED",
                    "/F",
                ],
                creationflags=_creation_flags(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            )
            return True
        return _install_linux_timer(hour, minute, command)
    except Exception:
        return False


def remove_daily_reminder() -> bool:
    try:
        if is_windows():
            subprocess.run(
                ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                capture_output=True,
                creationflags=_creation_flags(),
                timeout=12,
            )
            return True
        return _remove_linux_timer()
    except Exception:
        return False


def _systemd_user_dir() -> str:
    config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(config, "systemd", "user")


def _install_linux_timer(hour: int, minute: int, command: str) -> bool:
    folder = _systemd_user_dir()
    os.makedirs(folder, exist_ok=True)
    service = os.path.join(folder, LINUX_SERVICE_UNIT)
    timer = os.path.join(folder, LINUX_TIMER_UNIT)
    with open(service, "w", encoding="utf-8") as handle:
        handle.write(
            "[Unit]\nDescription=StudyApp daily reminder\n\n"
            "[Service]\nType=oneshot\n"
            f"ExecStart={command}\n"
        )
    with open(timer, "w", encoding="utf-8") as handle:
        handle.write(
            "[Unit]\nDescription=StudyApp daily reminder\n\n"
            "[Timer]\n"
            f"OnCalendar=*-*-* {hour:02d}:{minute:02d}:00\n"
            "Persistent=true\n\n"
            "[Install]\nWantedBy=timers.target\n"
        )
    systemctl = shutil.which("systemctl")
    if systemctl:
        subprocess.run(
            [systemctl, "--user", "daemon-reload"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
        )
        subprocess.run(
            [systemctl, "--user", "enable", "--now", LINUX_TIMER_UNIT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
        )
    return True


def _remove_linux_timer() -> bool:
    systemctl = shutil.which("systemctl")
    if systemctl:
        subprocess.run(
            [systemctl, "--user", "disable", "--now", LINUX_TIMER_UNIT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
        )
    folder = _systemd_user_dir()
    for name in (LINUX_TIMER_UNIT, LINUX_SERVICE_UNIT):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass
    return True


def parse_hhmm(raw: str, default_hour: int = 17, default_minute: int = 0) -> tuple[int, int]:
    text = (raw or "").strip().replace(".", ":")
    hour, minute = default_hour, default_minute
    if ":" in text:
        left, right = text.split(":", 1)
        try:
            hour = int(left)
            minute = int("".join(ch for ch in right if ch.isdigit())[:2] or "0")
        except ValueError:
            pass
    elif text.isdigit():
        hour = int(text)
    return max(0, min(23, hour)), max(0, min(59, minute))
