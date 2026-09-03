"""סורק תקלות עדין: בודק, מתקן מה שאפשר, ומסביר לתלמיד מה לעשות."""
from __future__ import annotations

import json
import os
import shutil

from core.config import QUESTIONS_DIR, VERSION
from core.storage import DATA_DIR, PROFILE_PATH


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


def scan_and_repair() -> dict:
    fixed: list[str] = []
    problems: list[str] = []
    advice: list[str] = []

    if not os.path.isdir(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            fixed.append("תיקיית הנתונים חסרה, יצרתי אותה מחדש.")
        except OSError:
            problems.append("אין גישה לתיקיית השמירה.")
    if not _can_write(DATA_DIR):
        problems.append("אי אפשר לשמור התקדמות בתיקייה הרגילה.")
        advice.append("סגרו את התוכנה, פתחו אותה שוב בתור מנהל רק אם צריך, ואז נסו שוב.")

    logs = os.path.join(DATA_DIR, "logs")
    if not _can_write(logs):
        problems.append("אי אפשר לכתוב לקובץ היומן.")
        advice.append("סגרו את StudyApp לגמרי ופתחו אותה מחדש.")

    if os.path.isfile(PROFILE_PATH) and not _json_ok(PROFILE_PATH):
        broken = PROFILE_PATH + ".broken"
        try:
            shutil.copy2(PROFILE_PATH, broken)
            os.remove(PROFILE_PATH)
            fixed.append("קובץ הפרופיל היה פגום. שמרתי עותק ושחזרתי שמירה נקייה.")
            advice.append("אם חסר שם או התקדמות, סגרו את התוכנה ופתחו שוב.")
        except OSError:
            problems.append("קובץ הפרופיל פגום ואי אפשר לתקן אותו עכשיו.")
            advice.append("סגרו את התוכנה, הדליקו את המחשב מחדש, ואז פתחו את StudyApp.")

    if not os.path.isdir(QUESTIONS_DIR):
        problems.append("חסרה תיקיית השאלות.")
        advice.append("התקינו שוב את StudyApp מהקישור של המפתח. הלמידה השמורה לא נמחקת.")
    else:
        banks = [name for name in os.listdir(QUESTIONS_DIR) if name.endswith(".json")]
        if not banks:
            problems.append("אין קבצי שאלות.")
            advice.append("התקינו שוב את התוכנה. ההתקדמות נשארת במחשב.")
        bad = [name for name in banks if not _json_ok(os.path.join(QUESTIONS_DIR, name))]
        if bad:
            problems.append("חלק מקבצי השאלות פגומים.")
            advice.append("התקינו שוב את StudyApp. אל תמחקו את תיקיית המשתמש.")

    staging = os.path.join(os.path.dirname(DATA_DIR), "StudyApp_update_staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)
        if not os.path.isdir(staging):
            fixed.append("ניקיתי שאריות של עדכון ישן.")

    if not problems and not fixed:
        message = (
            f"הסורק בדק את StudyApp {VERSION}.\n"
            "לא מצאתי תקלה. אם משהו עדיין תקוע: סגרו את התוכנה ופתחו שוב. "
            "אם גם זה לא עוזר, כבו את המחשב והדליקו."
        )
        return {"ok": True, "fixed": [], "problems": [], "message": message}

    lines = [f"בדיקת תקלות, גרסה {VERSION}"]
    if fixed:
        lines.append("תיקנתי לבד:")
        lines.extend(f"• {item}" for item in fixed)
    if problems:
        lines.append("מה שנשאר:")
        lines.extend(f"• {item}" for item in problems)
    if advice:
        seen = []
        for item in advice:
            if item not in seen:
                seen.append(item)
        lines.append("מה לעשות:")
        lines.extend(f"• {item}" for item in seen)
        if "כבו את המחשב" not in " ".join(seen):
            lines.append("• אם עדיין לא עובד: סגרו את התוכנה, ואם צריך כבו את המחשב והדליקו.")
    else:
        lines.append("אם משהו עדיין תקוע: סגרו את התוכנה ופתחו שוב.")
    return {
        "ok": not problems,
        "fixed": fixed,
        "problems": problems,
        "message": "\n".join(lines),
    }
