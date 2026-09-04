from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime

from core import applog
from core.adaptive_engine import RUSH_SEC, normalize_difficulty, wilson_lower

log = applog.get_logger("analytics")

MIN_TOPIC_SAMPLE = 3
TREND_WINDOW = 12


def _parse_timestamp(raw) -> datetime | None:
    text = str(raw or "").strip().replace("Z", "")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


class AnalyticsEngine:
    """אנליסט ביצועים: דיוק אמיתי, נושאים חלשים, מגמה והמלצה אחת ברורה."""

    def __init__(self, db_path=None):
        if db_path is None:
            from core.profiles import current_files, ensure_migrated

            ensure_migrated()
            db_path = current_files()["user_stats"]
        self.db_path = db_path
        self._cache = None
        self._cache_mtime = None

    def _load_raw_data(self):
        if not os.path.exists(self.db_path):
            return {"history": [], "topic_stats": {}}

        try:
            mtime = os.path.getmtime(self.db_path)
            if self._cache is not None and self._cache_mtime == mtime:
                return self._cache

            with open(self.db_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self._cache = data or {"history": [], "topic_stats": {}}
            self._cache_mtime = mtime
            return self._cache
        except Exception as exc:
            log.warning("failed to load analytics data: %s", exc)
            return {"history": [], "topic_stats": {}}

    def _normalize_data(self, data):
        if not data:
            return {"history": [], "topic_stats": {}}

        history = data.get("history") or []
        topic_stats = data.get("topic_stats") or {}

        normalized_history = []
        for item in history:
            if not isinstance(item, dict):
                continue
            stamp = item.get("timestamp") or item.get("date") or item.get("ts") or ""
            normalized_history.append(
                {
                    "topic": str(item.get("topic") or "כללי"),
                    "subject": str(item.get("subject") or ""),
                    "difficulty": normalize_difficulty(item.get("difficulty", "Easy")),
                    "correct": bool(item.get("correct", False)),
                    "time_sec": float(item.get("time_sec", 0) or 0),
                    "timestamp": stamp,
                    "_dt": _parse_timestamp(stamp),
                }
            )
        normalized_history.sort(key=lambda row: row["_dt"] or datetime.min)

        normalized_topics = {}
        for topic, stats in topic_stats.items():
            if not isinstance(stats, dict):
                continue
            total = int(stats.get("total_questions", 0) or 0)
            correct = int(stats.get("correct_answers", 0) or 0)
            if total <= 0:
                continue
            normalized_topics[str(topic)] = {
                "total_questions": total,
                "correct_answers": correct,
            }

        return {"history": normalized_history, "topic_stats": normalized_topics}

    def _filtered_history(self, subject: str | None = None) -> list[dict]:
        data = self._normalize_data(self._load_raw_data())
        history = data["history"]
        if not subject:
            return history
        key = str(subject)
        matched = [row for row in history if row.get("subject") == key]
        return matched or history

    def _aggregate(self, rows: list[dict], label_key: str = "topic") -> list[dict]:
        stats = defaultdict(lambda: {"total_questions": 0, "correct_answers": 0, "total_time": 0.0})
        for item in rows:
            label = item.get(label_key) or item.get("topic") or "כללי"
            if not label:
                continue
            stats[label]["total_questions"] += 1
            stats[label]["total_time"] += item["time_sec"]
            if item["correct"]:
                stats[label]["correct_answers"] += 1

        breakdown = []
        for label, values in stats.items():
            total = values["total_questions"]
            if total <= 0:
                continue
            correct = values["correct_answers"]
            breakdown.append(
                {
                    "topic": label,
                    "total_questions": total,
                    "correct_answers": correct,
                    "accuracy": round((correct / total) * 100, 1),
                    "avg_time_sec": round(values["total_time"] / total, 1),
                    "confidence": round(wilson_lower(correct, total) * 100, 1),
                }
            )
        breakdown.sort(key=lambda item: (item["confidence"], item["total_questions"]))
        return breakdown

    def get_subject_breakdown(self, subject: str | None = None):
        data = self._normalize_data(self._load_raw_data())
        history = self._filtered_history(subject) if subject else data["history"]
        if history:
            breakdown = self._aggregate(history)
            breakdown.sort(key=lambda item: (item["accuracy"], item["total_questions"]), reverse=True)
            return breakdown

        breakdown = []
        for topic, topic_stats in (data.get("topic_stats") or {}).items():
            total = int(topic_stats.get("total_questions", 0) or 0)
            correct = int(topic_stats.get("correct_answers", 0) or 0)
            if total <= 0:
                continue
            breakdown.append(
                {
                    "topic": topic,
                    "total_questions": total,
                    "correct_answers": correct,
                    "accuracy": round((correct / total) * 100, 1),
                    "avg_time_sec": 0.0,
                    "confidence": round(wilson_lower(correct, total) * 100, 1),
                }
            )
        breakdown.sort(key=lambda item: (item["accuracy"], item["total_questions"]), reverse=True)
        return breakdown

    def get_recent_activity(self, limit=5):
        history = self._filtered_history()
        recent = list(history)
        recent.reverse()
        return [{k: v for k, v in row.items() if k != "_dt"} for row in recent[:limit]]

    def _pace_insight(self, history: list[dict]) -> str | None:
        times = [row["time_sec"] for row in history if row["time_sec"] > 0]
        if len(times) < 6:
            return None
        avg = sum(times) / len(times)
        rushed = sum(1 for item in times if item < RUSH_SEC)
        if rushed / len(times) >= 0.45:
            return "יש הרבה מענים מהירים מאוד. עדיף לקרוא את השאלה עד הסוף לפני שבוחרים."
        if avg > 85:
            return "המענה איטי מהרגיל. אפשר לתרגל בלי שעון קודם, ורק אחר כך לחזור למבחן מדורג."
        return None

    def get_recommendations(self, subject_breakdown=None, history: list[dict] | None = None):
        breakdown = list(subject_breakdown or self.get_subject_breakdown())
        rows = history if history is not None else self._filtered_history()
        if not breakdown and not rows:
            return ["התחל לתרגל כדי לקבל המלצות מותאמות אישית."]

        recommendations: list[str] = []
        sampled = [item for item in breakdown if item["total_questions"] >= MIN_TOPIC_SAMPLE]
        weak = sorted(sampled, key=lambda item: (item.get("confidence", item["accuracy"]), item["total_questions"]))
        strong = [item for item in sampled if item["accuracy"] >= 85 and item["total_questions"] >= 5]

        for item in weak[:2]:
            if item["accuracy"] <= 72:
                recommendations.append(
                    f"חיזוק ב«{item['topic']}»: {item['correct_answers']}/{item['total_questions']} "
                    f"({item['accuracy']}%). עוד 8–10 שאלות שם, לא מקצוע אחר."
                )

        pace = self._pace_insight(rows[-TREND_WINDOW * 2 :] if rows else [])
        if pace:
            recommendations.append(pace)

        total_questions = sum(item["total_questions"] for item in breakdown) or len(rows)
        correct_answers = sum(item["correct_answers"] for item in breakdown)
        if not total_questions and rows:
            total_questions = len(rows)
            correct_answers = sum(1 for row in rows if row["correct"])
        overall = (correct_answers / total_questions) if total_questions else 0.0
        trend = self.get_performance_trend(history=rows)

        if overall < 0.55:
            recommendations.append("עדיף לחזור לשיעור הקצר בנושא החלש, ורק אחריו לתרגל 6 שאלות.")
        elif trend.get("trend") == "down":
            recommendations.append("הדיוק ירד לאחרונה. סשן קצר ברמה הנוכחית, בלי לקפוץ למבחן אמיתי.")
        elif trend.get("trend") == "up" and strong:
            recommendations.append(
                f"«{strong[0]['topic']}» כבר יציב. אפשר מבחן דמה, ואת החיזוק להשאיר לנושא החלש."
            )
        elif overall < 0.80:
            recommendations.append("המשך עם תרגול ממוקד: נושא אחד חלש בכל סשן, לא שלושה ביחד.")
        else:
            recommendations.append("העשייה חזקה. מבחן דמה יבדוק אם הדיוק מחזיק גם בלי משוב אחרי כל שאלה.")

        seen: list[str] = []
        for line in recommendations:
            if line not in seen:
                seen.append(line)
        return seen[:3] or ["המשך לתרגל בקצב קצר ויציב."]

    def get_overview(self, subject: str | None = None):
        history = self._filtered_history(subject)
        breakdown = self.get_subject_breakdown(subject)

        if not history and not breakdown:
            return {
                "has_data": False,
                "total_questions": 0,
                "correct_questions": 0,
                "accuracy": 0.0,
                "avg_time_sec": 0.0,
                "study_minutes": 0.0,
                "subject_breakdown": [],
                "recommendations": ["התחל לתרגל כדי לקבל ניתוח מותאם אישית."],
                "trend": self.get_performance_trend(history=[]),
            }

        if history:
            total_questions = len(history)
            correct_questions = sum(1 for item in history if item["correct"])
            total_time_sec = sum(item["time_sec"] for item in history)
        else:
            total_questions = sum(item["total_questions"] for item in breakdown)
            correct_questions = sum(item["correct_answers"] for item in breakdown)
            total_time_sec = 0.0

        accuracy = round((correct_questions / total_questions) * 100, 1) if total_questions else 0.0
        avg_time_sec = round(total_time_sec / total_questions, 1) if total_questions and total_time_sec else 0.0
        study_minutes = round(total_time_sec / 60, 1)
        trend = self.get_performance_trend(history=history)

        return {
            "has_data": True,
            "total_questions": total_questions,
            "correct_questions": correct_questions,
            "accuracy": accuracy,
            "avg_time_sec": avg_time_sec,
            "study_minutes": study_minutes,
            "subject_breakdown": breakdown,
            "recommendations": self.get_recommendations(breakdown, history=history),
            "trend": trend,
        }

    def get_insight_card(self, subject: str | None = None) -> dict:
        """כרטיס קצר למסך התוצאות, בלי בלוק טקסט גולמי."""
        overview = self.get_overview(subject)
        sampled = [
            item
            for item in overview.get("subject_breakdown") or []
            if item.get("total_questions", 0) >= MIN_TOPIC_SAMPLE
        ]
        weak = sorted(sampled, key=lambda item: item.get("confidence", item["accuracy"]))
        weak = [item for item in weak if item["accuracy"] <= 72][:3]
        recs = list(overview.get("recommendations") or [])
        trend = overview.get("trend") or {}
        pred = self.predict_exam_score(subject)
        return {
            "has_data": bool(overview.get("has_data")),
            "accuracy": overview.get("accuracy", 0),
            "trend_label": trend.get("label") or "",
            "trend": trend.get("trend") or "no_data",
            "weak_topics": [item["topic"] for item in weak],
            "recommendation": recs[0] if recs else "",
            "recommendations": recs[:2],
            "exam_prediction": pred.get("score"),
            "exam_label": pred.get("label") or "",
        }

    def get_summary(self, subject: str | None = None):
        overview = self.get_overview(subject)
        if not overview["has_data"]:
            return (
                "אין עדיין מספיק נתונים להפקת דוח.\n"
                "התחל לתרגל או לבצע מבחנים כדי לראות ניתוח ביצועים בזמן אמת!"
            )

        breakdown = overview["subject_breakdown"]
        weak_lines = []
        sampled = [item for item in breakdown if item["total_questions"] >= MIN_TOPIC_SAMPLE]
        weak = sorted(sampled, key=lambda item: item.get("confidence", item["accuracy"]))[:3]
        for item in weak:
            weak_lines.append(
                f"• {item['topic']}: {item['accuracy']}% הצלחה ({item['correct_answers']}/{item['total_questions']} שאלות)"
            )
        # אם אין דגימה מספקת — מציגים את החזקים כמו קודם, כדי שהדוח לא יהיה ריק.
        if not weak_lines:
            for item in breakdown[:3]:
                weak_lines.append(
                    f"• {item['topic']}: {item['accuracy']}% הצלחה ({item['correct_answers']}/{item['total_questions']} שאלות)"
                )

        topic_text = "\n".join(weak_lines) if weak_lines else "אין נתונים לפי נושא."
        recs_text = "\n".join(f"- {r}" for r in overview["recommendations"])
        trend = overview.get("trend") or {}
        trend_line = trend.get("label") or "אין מספיק נתונים למגמה"
        time_line = (
            f"• זמן מענה ממוצע לשאלה: {overview['avg_time_sec']} שניות\n"
            if overview["avg_time_sec"]
            else ""
        )

        return (
            "סיכום ביצועים\n"
            "───────────────────────────\n"
            f"• סך הכל שאלות שנענו: {overview['total_questions']}\n"
            f"• תשובות נכונות: {overview['correct_questions']}\n"
            f"• אחוז הצלחה כללי: {overview['accuracy']}%\n"
            f"{time_line}"
            f"• זמן לימוד מצטבר: {overview['study_minutes']} דקות\n"
            f"• מגמה: {trend_line}\n\n"
            "לפי נושאים:\n"
            f"{topic_text}\n\n"
            "מה כדאי:\n"
            f"{recs_text}"
        )

    def get_performance_trend(self, history: list[dict] | None = None):
        rows = history if history is not None else self._filtered_history()
        if len(rows) < 8:
            return {"trend": "no_data", "label": "אין מספיק נתונים", "value": 0.0}

        latest = rows[-TREND_WINDOW:]
        previous = rows[-TREND_WINDOW * 2 : -TREND_WINDOW] if len(rows) >= TREND_WINDOW * 2 else rows[:- max(4, len(latest) // 2)]
        if not previous:
            return {"trend": "no_data", "label": "אין מספיק נתונים", "value": 0.0}

        def acc(chunk: list[dict]) -> float:
            return round(sum(1 for item in chunk if item["correct"]) / len(chunk) * 100, 1)

        recent_accuracy = acc(latest)
        previous_accuracy = acc(previous)
        delta = round(recent_accuracy - previous_accuracy, 1)
        if delta > 6:
            return {"trend": "up", "label": f"מגמת עלייה: +{delta}%", "value": delta}
        if delta < -6:
            return {"trend": "down", "label": f"מגמת ירידה: {delta}%", "value": delta}
        return {"trend": "stable", "label": "ביצועים יציבים", "value": delta}

    def get_latest_timestamp(self):
        history = self._filtered_history()
        dated = [row for row in history if row.get("_dt")]
        if dated:
            latest = max(dated, key=lambda row: row["_dt"])
            return latest.get("timestamp")
        timestamps = [row.get("timestamp") for row in history if row.get("timestamp")]
        return timestamps[-1] if timestamps else None

    def predict_exam_score(self, subject: str | None = None) -> dict:
        """תחזית גסה לאחוז במבחן, לפי דיוק אחרון + ביטחון נושאים."""
        history = self._filtered_history(subject)
        if len(history) < 6:
            return {
                "has_data": False,
                "score": None,
                "label": "עדיין אין מספיק נתונים לתחזית",
            }
        recent = history[-TREND_WINDOW:]
        acc = sum(1 for row in recent if row["correct"]) / len(recent)
        breakdown = self.get_subject_breakdown(subject)
        weak = [
            item
            for item in breakdown
            if item["total_questions"] >= MIN_TOPIC_SAMPLE and item["accuracy"] <= 72
        ]
        penalty = min(0.18, 0.04 * len(weak))
        pace = self._pace_insight(history[-TREND_WINDOW * 2 :])
        if pace and "מהירים" in pace:
            penalty += 0.05
        score = max(0.0, min(100.0, round((acc - penalty) * 100, 1)))
        if score >= 85:
            label = "צפוי ציון גבוה, אם שומרים על קצב קריאה"
        elif score >= 70:
            label = "צפוי ציון בינוני-גבוה; כדאי לחזק נושא חלש אחד"
        elif score >= 55:
            label = "עדיין על הגבול; תרגול ממוקד לפני מבחן"
        else:
            label = "מוקדם למבחן; לחזק בסיס קודם"
        return {"has_data": True, "score": score, "label": label, "weak_count": len(weak)}

    def get_deep_report(self, subject: str | None = None) -> str:
        """דוח מילולי לחדר מפתח / הורה."""
        overview = self.get_overview(subject)
        if not overview.get("has_data"):
            return "אין עדיין מספיק נתוני ביצועים לדוח עמוק."
        pred = self.predict_exam_score(subject)
        lines = [
            "אנליסט ביצועים (עמוק)",
            "─" * 28,
            f"שאלות: {overview['total_questions']} · דיוק: {overview['accuracy']}%",
            f"מגמה: {(overview.get('trend') or {}).get('label') or 'אין'}",
        ]
        if pred.get("has_data"):
            lines.append(f"תחזית מבחן: {pred['score']}% · {pred['label']}")
        for rec in (overview.get("recommendations") or [])[:3]:
            lines.append(f"• {rec}")
        weak = [
            item
            for item in overview.get("subject_breakdown") or []
            if item.get("total_questions", 0) >= MIN_TOPIC_SAMPLE and item.get("accuracy", 100) <= 72
        ][:5]
        if weak:
            lines.append("נושאים חלשים:")
            for item in weak:
                lines.append(
                    f"  {item['topic']}: {item['accuracy']}% "
                    f"({item['correct_answers']}/{item['total_questions']})"
                )
        return "\n".join(lines)
