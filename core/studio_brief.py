"""מידע לחדר מפתח: מאגר, שורות קוד, סיכום להדבקה."""
from __future__ import annotations

import os
import sys
from collections import Counter

from core import applog, custom_questions
from core.config import ALL_SUBJECTS, BASE_DIR, QUESTIONS_DIR, VERSION, subject_label
from core.loader import load_subject
from core.storage import DATA_DIR

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "_qa_shots",
    ".cursor",
}
SKIP_TOP = {"dist", "build"}


def bank_census() -> list[dict]:
    rows = []
    for key in ALL_SUBJECTS:
        data = load_subject(key) or {}
        questions = list(data.get("questions") or [])
        kinds = Counter(str(q.get("kind") or "normal") for q in questions)
        rows.append(
            {
                "key": key,
                "name": subject_label(key),
                "lessons": len(data.get("lessons") or []),
                "questions": len(questions),
                "custom": len(custom_questions.load_for_subject(key)),
                "kinds": dict(kinds),
            }
        )
    return rows


def count_code_lines(root: str | None = None) -> dict:
    """סופר קבצי פייתון ושורות, בלי סביבה ובילדים."""
    root = os.path.abspath(root or BASE_DIR)
    files = 0
    lines = 0
    nonempty = 0
    by_folder: Counter[str] = Counter()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        top = rel_dir.split(os.sep, 1)[0] if rel_dir != "." else ""
        if top.lower() in SKIP_TOP:
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if name.lower() not in SKIP_DIRS and not name.endswith(".egg-info")
        ]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            files += 1
            folder = top or "שורש"
            file_lines = 0
            file_nonempty = 0
            try:
                with open(full, encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        file_lines += 1
                        if line.strip():
                            file_nonempty += 1
            except OSError:
                continue
            lines += file_lines
            nonempty += file_nonempty
            by_folder[folder] += file_lines
    return {
        "files": files,
        "lines": lines,
        "nonempty": nonempty,
        "by_folder": dict(by_folder),
    }


def info_snapshot(storage=None) -> dict:
    rows = bank_census()
    code = count_code_lines()
    student = (storage.get_student() or {}) if storage is not None else {}
    return {
        "version": VERSION,
        "python": sys.version.split()[0],
        "frozen": bool(getattr(sys, "frozen", False)),
        "code_files": code["files"],
        "code_lines": code["lines"],
        "code_nonempty": code["nonempty"],
        "questions": sum(row["questions"] for row in rows),
        "lessons": sum(row["lessons"] for row in rows),
        "custom": sum(row["custom"] for row in rows),
        "subjects": rows,
        "profile": student.get("name") or "-",
        "xp": storage.get("xp", 0) if storage is not None else 0,
        "mistakes": len(storage.get_mistakes() or []) if storage is not None else 0,
        "unlock": bool(storage.get_pref("studio_unlock_gates")) if storage is not None else False,
        "data_dir": DATA_DIR,
        "code_dir": BASE_DIR,
    }


def info_text(storage=None) -> str:
    snap = info_snapshot(storage)
    mode = "הפעלה מקוד" if not snap["frozen"] else "הפעלה מתוכנה בנויה"
    lines = [
        "מידע על התוכנה",
        f"גרסה: {snap['version']}",
        f"מצב: {mode}",
        f"פייתון: {snap['python']}",
        "",
        "קוד",
        f"שורות קוד: {snap['code_lines']:,}",
        f"שורות עם תוכן: {snap['code_nonempty']:,}",
        f"קבצי פייתון: {snap['code_files']}",
        "",
        "מאגר",
        f"שאלות בכל המקצועות: {snap['questions']:,}",
        f"שיעורים: {snap['lessons']:,}",
        f"שאלות שהוספת: {snap['custom']:,}",
        "",
        "פרופיל פתוח",
        f"שם: {snap['profile']}",
        f"נקודות: {snap['xp']}",
        f"טעויות פתוחות: {snap['mistakes']}",
        f"מבחנים פתוחים: {'כן' if snap['unlock'] else 'לא'}",
        "",
        "StudyApp Files = כל קבצי הקוד.",
        "מחלצים את התיקייה ופותחים",
        "אותה ב-VS Code כדי לערוך.",
    ]
    return "\n".join(lines)


def briefing(storage=None) -> str:
    lines = [
        f"StudyApp {VERSION}",
        f"BASE_DIR={BASE_DIR}",
        f"DATA_DIR={DATA_DIR}",
        f"QUESTIONS_DIR={QUESTIONS_DIR}",
        f"LOG_PATH={applog.LOG_PATH}",
        "",
        "BANK",
    ]
    code = count_code_lines()
    lines.append(
        f"CODE files={code['files']} lines={code['lines']} nonempty={code['nonempty']}"
    )
    lines.append("")
    total_q = total_l = total_c = 0
    for row in bank_census():
        total_q += row["questions"]
        total_l += row["lessons"]
        total_c += row["custom"]
        lines.append(
            f"  {row['key']:12} {row['questions']:5}q  {row['lessons']:3}L  "
            f"custom={row['custom']}  {row['name']}"
        )
    lines.append(f"TOTAL questions={total_q} lessons={total_l} custom={total_c}")
    if storage is not None:
        student = storage.get_student() or {}
        lines.extend(
            [
                "",
                "PROFILE",
                f"  name={student.get('name') or '-'}",
                f"  xp={storage.get('xp', 0)}",
                f"  mistakes={len(storage.get_mistakes() or [])}",
                f"  unlock={bool(storage.get_pref('studio_unlock_gates'))}",
            ]
        )
    lines.extend(["", "RECENT LOG", applog.read_recent(12)])
    return "\n".join(lines)


def census_text() -> str:
    rows = bank_census()
    lines = [
        "סיכום מאגר לפי מקצוע",
        "",
        f"{'מקצוע':<16} {'שאלות':>6} {'שיעורים':>8} {'מותאם':>6}",
    ]
    total_q = total_l = total_c = 0
    for row in rows:
        total_q += row["questions"]
        total_l += row["lessons"]
        total_c += row["custom"]
        lines.append(
            f"{row['key']:16} {row['questions']:6} {row['lessons']:8} {row['custom']:6}  {row['name']}"
        )
    lines.append("")
    lines.append(f"סהכ שאלות: {total_q}   שיעורים: {total_l}   מותאם: {total_c}")
    return "\n".join(lines)
