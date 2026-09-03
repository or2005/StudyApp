"""אנליסט תקלות: בודק, מתקן, ומסביר בשפת העזר."""
from __future__ import annotations

import json
import os
import shutil
import time

from core.config import QUESTIONS_DIR, VERSION
from core.i18n import block, get_lang, he, t
from core.storage import DATA_DIR, PROFILE_PATH

STATE_PATH = os.path.join(DATA_DIR, "health_state.json")


def _can_write(folder: str) -> bool:
    os.makedirs(folder, exist_ok=True)
    probe = os.path.join(folder, ".write_probe")
    try:
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False


def _json_ok(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as handle:
            json.load(handle)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def _line(key: str, **kwargs) -> str:
    hebrew = he(key, **kwargs)
    lang = get_lang()
    if lang == "he":
        return hebrew
    other = t(key, **kwargs)
    if other and other != hebrew:
        return f"{hebrew} / {other}"
    return hebrew


def _load_state() -> dict:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False)


def _consume_crash() -> bool:
    from core.applog import CRASH_FLAG

    if not os.path.isfile(CRASH_FLAG):
        return False
    try:
        os.remove(CRASH_FLAG)
    except OSError:
        return True
    return True


def _fix_display() -> list[str]:
    fixed: list[str] = []
    try:
        from core import textfix

        info = textfix.apply_text_engine()
        state = _load_state()
        os_lang = str(info.get("os_lang") or "")
        if os_lang not in {"he", "iw", ""} and not state.get("told_display"):
            fixed.append(_line("health.display_fixed", os_lang=os_lang))
            if info.get("utf8"):
                fixed.append(_line("health.utf8"))
            state["told_display"] = True
            _save_state(state)
    except Exception:
        pass
    return fixed


def _fix_font(root=None) -> tuple[list[str], list[str], list[str]]:
    fixed: list[str] = []
    problems: list[str] = []
    advice: list[str] = []
    try:
        from core import textfix
        from core.config import ADHD_CONFIG

        family = textfix.pick_hebrew_font(root)
        old = ADHD_CONFIG.get("font_family")
        ADHD_CONFIG["font_family"] = family
        if root is not None and not textfix.font_has_hebrew(root, family):
            problems.append(_line("health.font_missing"))
            advice.append(_line("health.reinstall"))
        elif family and family != old:
            fixed.append(_line("health.font_fixed"))
    except Exception:
        pass
    return fixed, problems, advice


def _clear_stale_update() -> list[str]:
    try:
        from core.updates import is_newer
        from core.storage import UserStorage

        storage = UserStorage()
        pending = storage.get_pref("pending_update") or {}
        if isinstance(pending, dict) and pending.get("newer"):
            latest = str(pending.get("latest") or "")
            if latest and not is_newer(latest, VERSION):
                storage.set_pref("pending_update", {})
                return [_line("health.stale_update")]
    except Exception:
        pass
    return []


def _maybe_alert(problems: list[str]) -> str:
    state = _load_state()
    if not problems:
        state["fails"] = 0
        _save_state(state)
        return ""
    fails = int(state.get("fails") or 0) + 1
    state["fails"] = fails
    state["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save_state(state)
    if fails < 2:
        return ""
    try:
        from core import telemetry
        from core.storage import UserStorage

        telemetry.send_ping(UserStorage(), "health_stuck", force=True)
    except Exception:
        pass
    return _line("health.stuck")


def scan_and_repair(root=None) -> dict:
    fixed: list[str] = []
    problems: list[str] = []
    advice: list[str] = []

    saw_crash = _consume_crash()
    if saw_crash:
        fixed.append(_line("health.crash"))
        advice.append(_line("health.reboot"))

    fixed.extend(_fix_display())
    font_fixed, font_problems, font_advice = _fix_font(root)
    fixed.extend(font_fixed)
    problems.extend(font_problems)
    advice.extend(font_advice)
    fixed.extend(_clear_stale_update())

    if not os.path.isdir(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            fixed.append(_line("health.data_created"))
        except OSError:
            problems.append(_line("health.no_save"))
    if not _can_write(DATA_DIR):
        problems.append(_line("health.no_save"))
        advice.append(_line("health.admin"))

    logs = os.path.join(DATA_DIR, "logs")
    if not _can_write(logs):
        problems.append(_line("health.no_save"))
        advice.append(_line("health.close_reopen"))

    if os.path.isfile(PROFILE_PATH) and not _json_ok(PROFILE_PATH):
        broken = PROFILE_PATH + ".broken"
        try:
            shutil.copy2(PROFILE_PATH, broken)
            os.remove(PROFILE_PATH)
            fixed.append(_line("health.profile_fixed"))
            advice.append(_line("health.close_reopen"))
        except OSError:
            problems.append(_line("health.profile_bad"))
            advice.append(_line("health.reboot_pc"))

    if not os.path.isdir(QUESTIONS_DIR):
        problems.append(_line("health.no_questions"))
        advice.append(_line("health.reinstall"))
    else:
        banks = [name for name in os.listdir(QUESTIONS_DIR) if name.endswith(".json")]
        if not banks:
            problems.append(_line("health.no_questions"))
            advice.append(_line("health.reinstall"))
        bad = [name for name in banks if not _json_ok(os.path.join(QUESTIONS_DIR, name))]
        if bad:
            problems.append(_line("health.bad_banks"))
            advice.append(_line("health.reinstall"))

    staging = os.path.join(os.path.dirname(DATA_DIR), "StudyApp_update_staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)
        if not os.path.isdir(staging):
            fixed.append(_line("health.staging"))

    if problems:
        advice.append(_line("health.update_hint"))

    stuck = _maybe_alert(problems)
    if stuck:
        advice.append(stuck)

    if not problems and not fixed:
        return {
            "ok": True,
            "fixed": [],
            "problems": [],
            "crash": saw_crash,
            "message": block("health.ok", version=VERSION),
        }

    lines = [block("health.title", version=VERSION)]
    if fixed:
        lines.append(block("health.fixed_head"))
        lines.extend(f"• {item}" for item in fixed)
    if problems:
        lines.append(block("health.left_head"))
        lines.extend(f"• {item}" for item in problems)
    if advice:
        seen = []
        for item in advice:
            if item not in seen:
                seen.append(item)
        lines.append(block("health.do_head"))
        lines.extend(f"• {item}" for item in seen)
    else:
        lines.append(block("health.reboot"))
    return {
        "ok": not problems,
        "fixed": fixed,
        "problems": problems,
        "crash": saw_crash,
        "message": "\n".join(lines),
    }
