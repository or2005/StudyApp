"""דוח שבועי להורה או למורה, קובץ שאפשר לשמור ולשלוח."""
from __future__ import annotations

import html
import os
import time
from datetime import datetime, timedelta

from core.config import VERSION, subject_label


def _parse_when(raw: str) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if "T" in text else text[:16], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", ""))
    except ValueError:
        return None


def _week_sessions(storage) -> list[dict]:
    cutoff = datetime.now() - timedelta(days=7)
    rows = []
    for item in storage.get_sessions() or []:
        when = _parse_when(str(item.get("date") or ""))
        if when is None or when < cutoff:
            continue
        rows.append(item)
    return rows


def build_report(storage, insight: str = "") -> dict[str, str]:
    student = storage.get_student() or {}
    name = str(student.get("name") or "תלמיד")
    overall = storage.get_overall_stats() or {}
    mastery = storage.get_mastery_by_subject() or {}
    streak = storage.get_streak() or {}
    daily = storage.get_daily_goal() or {}
    diagnostic = storage.get_diagnostic() or {}
    mistakes = storage.get_mistakes() or []
    week = _week_sessions(storage)
    week_total = sum(int(item.get("total", 0) or 0) for item in week)
    week_correct = sum(int(item.get("score", 0) or 0) for item in week)
    week_acc = round(100 * week_correct / week_total, 1) if week_total else 0.0
    last_activity = str(storage.get("last_activity") or "אין עדיין")
    generated = time.strftime("%Y-%m-%d %H:%M")

    weak = []
    for key, info in sorted(
        mastery.items(),
        key=lambda pair: (pair[1].get("accuracy", 0), pair[1].get("total", 0)),
    ):
        if int(info.get("total", 0) or 0) >= 5 and float(info.get("accuracy", 0) or 0) < 70:
            weak.append(f"{subject_label(key)} ({info.get('accuracy')}%)")

    insight = str(insight or "").strip()

    lines = [
        f"דוח שבועי, StudyApp {VERSION}",
        f"תלמיד: {name}",
        f"נוצר: {generated}",
        "",
        "סיכום כללי",
        f"• שאלות מצטברות: {overall.get('total', 0)}",
        f"• דיוק כללי: {overall.get('accuracy', 0)}%",
        f"• רצף ימים: {streak.get('current', 0)} (שיא {streak.get('best', 0)})",
        f"• יעד היום: {daily.get('completed', 0)}/{daily.get('target', 15)}",
        f"• פעילות אחרונה: {last_activity}",
        f"• טעויות פתוחות: {len(mistakes)}",
        "",
        "שבעת הימים האחרונים",
        f"• תרגולים: {len(week)}",
        f"• שאלות השבוע: {week_total}",
        f"• דיוק השבוע: {week_acc}%",
        "",
        "דיוק לפי מקצוע",
    ]
    if mastery:
        for key, info in mastery.items():
            lines.append(
                f"• {subject_label(key)}: {info.get('accuracy', 0)}% "
                f"({info.get('correct', 0)}/{info.get('total', 0)})"
            )
    else:
        lines.append("• עדיין אין תרגול שמור.")

    if diagnostic:
        level = diagnostic.get("level_he") or diagnostic.get("level") or ""
        lines.extend(["", f"אבחון ראשוני: {level}".strip()])

    lines.extend(["", "נקודות לחיזוק"])
    if weak:
        for item in weak:
            lines.append(f"• {item}")
    else:
        lines.append("• אין מקצוע חלש במיוחד לפי הנתונים הנוכחיים.")

    if insight:
        lines.extend(["", "המלצת האנליסט", insight])

    lines.extend(
        [
            "",
            "הדוח נוצר מתוך הנתונים במחשב המקומי בלבד.",
            "StudyApp אינה מחליפה מורה, ואין בה ציונים רשמיים.",
        ]
    )
    text = "\n".join(lines)

    mastery_html = "".join(
        (
            "<li>"
            f"{html.escape(subject_label(key))}: {html.escape(str(info.get('accuracy', 0)))}% "
            f"({html.escape(str(info.get('correct', 0)))}/{html.escape(str(info.get('total', 0)))})"
            "</li>"
        )
        for key, info in mastery.items()
    ) or "<li>עדיין אין תרגול שמור.</li>"
    weak_html = "".join(f"<li>{html.escape(item)}</li>" for item in weak) or (
        "<li>אין מקצוע חלש במיוחד לפי הנתונים הנוכחיים.</li>"
    )
    html_doc = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>דוח שבועי, {html.escape(name)}</title>
</head>
<body style="font-family: Arial, Helvetica, sans-serif; max-width: 720px; margin: 24px auto; color: #111; line-height: 1.5;">
<h1>דוח שבועי, StudyApp</h1>
<p>תלמיד: <strong>{html.escape(name)}</strong><br>
נוצר: {html.escape(generated)} · גרסה {html.escape(VERSION)}</p>
<h2>סיכום כללי</h2>
<ul>
<li>שאלות מצטברות: {html.escape(str(overall.get("total", 0)))}</li>
<li>דיוק כללי: {html.escape(str(overall.get("accuracy", 0)))}%</li>
<li>רצף ימים: {html.escape(str(streak.get("current", 0)))} (שיא {html.escape(str(streak.get("best", 0)))})</li>
<li>יעד היום: {html.escape(str(daily.get("completed", 0)))}/{html.escape(str(daily.get("target", 15)))}</li>
<li>פעילות אחרונה: {html.escape(last_activity)}</li>
<li>טעויות פתוחות: {html.escape(str(len(mistakes)))}</li>
</ul>
<h2>שבעת הימים האחרונים</h2>
<ul>
<li>תרגולים: {html.escape(str(len(week)))}</li>
<li>שאלות השבוע: {html.escape(str(week_total))}</li>
<li>דיוק השבוע: {html.escape(str(week_acc))}%</li>
</ul>
<h2>דיוק לפי מקצוע</h2>
<ul>{mastery_html}</ul>
<h2>נקודות לחיזוק</h2>
<ul>{weak_html}</ul>
{f"<h2>המלצת האנליסט</h2><p>{html.escape(insight)}</p>" if insight else ""}
<p style="color:#555; font-size: 13px;">הדוח נוצר מתוך הנתונים במחשב המקומי בלבד. StudyApp אינה מחליפה מורה, ואין בה ציונים רשמיים.</p>
</body>
</html>
"""
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in " _-").strip() or "student"
    filename = f"studyapp-weekly-{safe_name}-{time.strftime('%Y-%m-%d')}.html"
    return {
        "title": f"דוח שבועי, {name}",
        "text": text,
        "html": html_doc,
        "filename": filename,
        "name": name,
    }


def write_report(path: str, report: dict[str, str]) -> str:
    folder = os.path.dirname(os.path.abspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    payload = report.get("html") if path.lower().endswith(".html") else report.get("text")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload or "")
    return path
