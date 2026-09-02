"""מבחן כללי בסגנון אמריקאי, 50 שאלות רב־ברירה מכל המקצועות.

בלי משוב באמצע, ציון בסולם 200-800, ודוח לימודי לפי מקצוע ונושא.
נפתח אחרי שהתלמיד תרגל לפחות 50% מיעד הכיסוי בכל מקצוע.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from core.adaptive_engine import pick_by_mix
from core.config import HOME_SUBJECTS, SUBJECTS, subject_label

GENERAL_EXAM_SIZE = 50
GENERAL_EXAM_MINUTES = 50
GENERAL_EXAM_SECONDS = GENERAL_EXAM_MINUTES * 60
GENERAL_EXAM_COVERAGE = 0.50
# 40 שאלות ייחודיות = 100% כיסוי לשער הנעילה. 20 לכל מקצוע פותחות את המבחן.
GENERAL_EXAM_SAMPLE = 40

# 50 שאלות: דגש קל על לשון / אנגלית / חשבון (מימ״ד), ושאר המקצועות מכוסים.
SUBJECT_COUNTS: dict[str, int] = {
    "hebrew": 7,
    "english": 7,
    "math": 7,
    "history": 6,
    "geography": 6,
    "civics": 6,
    "chemistry": 6,
    "physics": 5,
}

# תמהיל בסגנון SAT: רוב בינוני, קצת קשה, בסיס קל.
EXAM_MIX = {"Easy": 0.22, "Medium": 0.46, "Hard": 0.32}

LETTERS = ("A", "B", "C", "D")


def coverage_for_subject(stats: dict | None) -> dict[str, Any]:
    stats = stats or {}
    seen = [item for item in (stats.get("seen_ids") or []) if item]
    attempts = int(stats.get("total", 0) or 0)
    unique = len(set(str(item) for item in seen))
    covered = unique if unique else min(attempts, GENERAL_EXAM_SAMPLE)
    need = max(1, int(round(GENERAL_EXAM_SAMPLE * GENERAL_EXAM_COVERAGE)))
    pct = round(100.0 * min(covered, GENERAL_EXAM_SAMPLE) / GENERAL_EXAM_SAMPLE, 1)
    return {
        "covered": covered,
        "target": GENERAL_EXAM_SAMPLE,
        "need": need,
        "pct": pct,
        "ready": covered >= need,
    }


def coverage_map(storage: Any) -> dict[str, dict[str, Any]]:
    progress = storage.get_progress() if storage and hasattr(storage, "get_progress") else {}
    result = {}
    for key in HOME_SUBJECTS:
        row = coverage_for_subject((progress or {}).get(key) or {})
        row["name"] = subject_label(key)
        result[key] = row
    return result


def can_take_general_exam(storage: Any) -> bool:
    if getattr(storage, "get_pref", None) and storage.get_pref("studio_unlock_gates"):
        return True
    return all(row.get("ready") for row in coverage_map(storage).values())


def unlock_progress(storage: Any) -> dict[str, Any]:
    rows = coverage_map(storage)
    ready = sum(1 for row in rows.values() if row.get("ready"))
    missing = [row["name"] for key, row in rows.items() if not row.get("ready")]
    return {
        "ready_subjects": ready,
        "total_subjects": len(rows),
        "unlocked": ready == len(rows) and len(rows) > 0,
        "missing": missing,
        "rows": rows,
    }


def _clean(pool: list[dict]) -> list[dict]:
    return [q for q in (pool or []) if q.get("kind") != "trick" and q.get("options")]


def build_general_exam(load_subject, rng: random.Random | None = None) -> list[dict]:
    """50 שאלות אמריקאיות, A-D, מכל המקצועות, בלי כפילויות."""
    roller = rng or random.Random()
    picked: list[dict] = []
    used_ids: set[str] = set()

    def take(pool: list[dict], count: int) -> list[dict]:
        available = [q for q in _clean(pool) if str(q.get("id")) not in used_ids]
        if not available or count <= 0:
            return []
        chosen = pick_by_mix(available, EXAM_MIX, min(count, len(available)), rng=roller)
        for item in chosen:
            used_ids.add(str(item.get("id")))
        return chosen

    leftover_need = 0
    for key, count in SUBJECT_COUNTS.items():
        data = load_subject(key) or {}
        got = take(data.get("questions") or [], count)
        leftover_need += max(0, count - len(got))
        picked.extend(got)

    if leftover_need:
        extra_pool = []
        for key in HOME_SUBJECTS:
            extra_pool.extend((load_subject(key) or {}).get("questions") or [])
        picked.extend(take(extra_pool, leftover_need))

    roller.shuffle(picked)
    exam = []
    for index, question in enumerate(picked[:GENERAL_EXAM_SIZE], start=1):
        row = dict(question)
        row["exam_number"] = index
        row["letter_options"] = True
        exam.append(row)
    return exam


def letter_grade(percent: float) -> str:
    if percent >= 90:
        return "A"
    if percent >= 80:
        return "B"
    if percent >= 70:
        return "C"
    if percent >= 60:
        return "D"
    return "F"


def scaled_score(correct: int, total: int = GENERAL_EXAM_SIZE) -> int:
    """סולם בסגנון SAT: 200-800."""
    safe_total = max(1, int(total))
    ratio = max(0.0, min(1.0, int(correct) / safe_total))
    return int(round(200 + 600 * ratio))


def overall_level(percent: float) -> tuple[str, str]:
    if percent >= 85:
        return "advanced", "מתקדם"
    if percent >= 70:
        return "proficient", "גבוה"
    if percent >= 55:
        return "intermediate", "בינוני"
    return "beginner", "מתחיל"


def _subject_advice(name: str, percent: float, weak_topics: list[str]) -> str:
    topics = " · ".join(weak_topics[:3]) if weak_topics else "השיעורים הבסיסיים במקצוע"
    if percent >= 85:
        return f"{name} חזק. שמרו על זה במבחני דמה, וחזקו נקודות שוליות: {topics}."
    if percent >= 70:
        return f"{name} טוב. עוד תרגול ממוקד ב־{topics} יעלה את הציון לרמה גבוהה."
    if percent >= 55:
        return f"{name} בינוני. חזרו לשיעור הקצר ואז 15 שאלות על: {topics}."
    return f"{name} דורש חיזוק יסודי. התחילו מהשיעור העיוני ואז תרגול יומי על: {topics}."


def build_report(answers: list[dict], total: int | None = None) -> dict[str, Any]:
    """דוח לימודי מקיף אחרי המבחן הכללי."""
    rows = list(answers or [])
    total = int(total if total is not None else max(len(rows), 1))
    correct = sum(1 for item in rows if item.get("correct"))
    percent = round(100.0 * correct / total, 1) if total else 0.0
    level, level_he = overall_level(percent)
    grade = letter_grade(percent)
    scaled = scaled_score(correct, total)

    by_subject: dict[str, dict[str, Any]] = {}
    by_topic: dict[tuple[str, str], dict[str, int]] = {}
    times: list[float] = []

    for item in rows:
        key = str(item.get("subject") or "כללי")
        topic = str(item.get("topic") or "כללי")
        sub = by_subject.setdefault(key, {"correct": 0, "total": 0, "topics": defaultdict(lambda: {"ok": 0, "bad": 0})})
        sub["total"] += 1
        ok = bool(item.get("correct"))
        if ok:
            sub["correct"] += 1
            sub["topics"][topic]["ok"] += 1
        else:
            sub["topics"][topic]["bad"] += 1
        slot = by_topic.setdefault((key, topic), {"ok": 0, "bad": 0})
        slot["ok" if ok else "bad"] += 1
        try:
            times.append(float(item.get("time_sec") or 0))
        except (TypeError, ValueError):
            pass

    subjects = []
    for key in HOME_SUBJECTS:
        stats = by_subject.get(key) or {"correct": 0, "total": 0, "topics": {}}
        sub_total = int(stats["total"] or 0)
        sub_ok = int(stats["correct"] or 0)
        sub_pct = round(100.0 * sub_ok / sub_total, 1) if sub_total else 0.0
        weak_topics = [
            topic
            for topic, counts in sorted(
                (stats.get("topics") or {}).items(),
                key=lambda pair: (pair[1].get("bad", 0), -pair[1].get("ok", 0)),
                reverse=True,
            )
            if counts.get("bad", 0) > 0
        ][:4]
        name = subject_label(key) if key in SUBJECTS else key
        _, sub_level_he = overall_level(sub_pct if sub_total else 0)
        subjects.append(
            {
                "key": key,
                "name": name,
                "correct": sub_ok,
                "total": sub_total,
                "percent": sub_pct,
                "grade": letter_grade(sub_pct) if sub_total else "-",
                "level_he": sub_level_he if sub_total else "לא נבדק",
                "weak_topics": weak_topics,
                "advice": _subject_advice(name, sub_pct, weak_topics) if sub_total else f"לא הופיעו שאלות ב{name}.",
            }
        )

    ranked = [row for row in subjects if row["total"]]
    weak_subjects = sorted(ranked, key=lambda row: (row["percent"], -row["total"]))[:3]
    strong_subjects = sorted(ranked, key=lambda row: (row["percent"], row["total"]), reverse=True)[:3]

    topic_rows = []
    for (key, topic), counts in by_topic.items():
        t_total = counts["ok"] + counts["bad"]
        topic_rows.append(
            {
                "subject": key,
                "subject_name": subject_label(key),
                "topic": topic,
                "correct": counts["ok"],
                "total": t_total,
                "percent": round(100.0 * counts["ok"] / t_total, 1) if t_total else 0.0,
                "missed": counts["bad"],
            }
        )
    topic_rows.sort(key=lambda row: (row["percent"], -row["missed"]))
    weak_topics = [row for row in topic_rows if row["missed"] > 0][:8]

    recommendations = []
    if weak_subjects:
        recommendations.append(
            "חזקו קודם את: " + " · ".join(f"{row['name']} ({row['percent']}%)" for row in weak_subjects) + "."
        )
    for row in weak_subjects[:2]:
        recommendations.append(row["advice"])
    if percent < 55:
        recommendations.append("חזרו לשיעורים העיוניים במקצועות החלשים, ורק אחרי זה מבחן דמה.")
    elif percent < 80:
        recommendations.append("תרגלו 15 שאלות ביום במקצוע החלש ביותר, עם הסבר אחרי כל תשובה.")
    else:
        recommendations.append("הרמה גבוהה. שמרו עליה במבחנים אמיתיים לפי מקצוע, ושימו לב לנושאים השוליים בדוח.")

    plan = []
    for row in weak_subjects[:3]:
        topic = (row.get("weak_topics") or ["הנושא הבסיסי"])[0]
        plan.append(f"{row['name']}: שיעור קצר + תרגול 15 שאלות בנושא «{topic}».")
    if not plan:
        plan.append("אין חולשה בולטת. מבחן אמיתי באחד המקצועות ישמור על הכושר.")

    avg_time = round(sum(times) / len(times), 1) if times else 0.0
    if percent >= 85:
        headline = "רמה גבוהה מאוד. המבחן הכללי מראה שליטה רחבה."
    elif percent >= 70:
        headline = "רמה טובה. יש מקצועות חזקים ונקודות שדורשות חיזוק."
    elif percent >= 55:
        headline = "רמה בינונית. הדוח מציין בדיוק איפה להשקיע."
    else:
        headline = "רמת בסיס. כדאי לחזור לשיעורים במקצועות שירדו בדוח."

    narrative_lines = [
        f"מבחן כללי אמריקאי, {correct}/{total}  ({percent}%)",
        f"ציון בסולם 200-800: {scaled}   ·   ציון אות: {grade}   ·   רמה: {level_he}",
        headline,
        "",
        "פירוט לפי מקצוע:",
    ]
    for row in subjects:
        if not row["total"]:
            continue
        topics = ", ".join(row["weak_topics"]) if row["weak_topics"] else "אין נושא חלש בולט"
        narrative_lines.append(
            f"• {row['name']}: {row['correct']}/{row['total']} ({row['percent']}%)  "
            f"ציון {row['grade']}  ·  {row['level_he']}  ·  לחזק: {topics}"
        )
    narrative_lines.extend(["", "תוכנית קרובה:"])
    narrative_lines.extend(f"• {step}" for step in plan)
    narrative_lines.extend(["", "המלצות:"])
    narrative_lines.extend(f"• {rec}" for rec in recommendations)

    return {
        "score": correct,
        "total": total,
        "percent": percent,
        "scaled": scaled,
        "grade": grade,
        "level": level,
        "level_he": level_he,
        "headline": headline,
        "avg_time_sec": avg_time,
        "subjects": subjects,
        "weak_subjects": [row["key"] for row in weak_subjects],
        "strong_subjects": [row["key"] for row in strong_subjects],
        "weak_topics": weak_topics,
        "recommendations": recommendations,
        "plan": plan,
        "narrative": "\n".join(narrative_lines),
    }
