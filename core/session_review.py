"""סיכום סשן: נושאים חלשים, וקטלוג נושאים לתרגול ממוקד."""
from __future__ import annotations


def session_weak_topics(answers: list[dict] | None, limit: int = 3) -> list[dict]:
    """נושאים שנכשלו בסשן הנוכחי, ממוינים מהחלש לחזק."""
    buckets: dict[str, dict] = {}
    for ans in answers or []:
        topic = str(ans.get("topic") or "").strip()
        if not topic:
            continue
        rec = buckets.setdefault(
            topic, {"topic": topic, "total": 0, "correct": 0, "missed": 0}
        )
        rec["total"] += 1
        if ans.get("correct"):
            rec["correct"] += 1
        else:
            rec["missed"] += 1
    weak = []
    for rec in buckets.values():
        if rec["missed"] <= 0:
            continue
        rec["accuracy"] = round(100 * rec["correct"] / max(1, rec["total"]))
        weak.append(rec)
    weak.sort(key=lambda row: (row["accuracy"], -row["missed"], -row["total"]))
    return weak[: max(1, int(limit))]


def subject_topic_catalog(data: dict | None, compose_items: list[dict] | None = None) -> list[dict]:
    """רשימת נושאים במקצוע, עם כמה שאלות יש לתרגול וליצור."""
    counts: dict[str, dict] = {}

    def _touch(name: str) -> dict:
        item = counts.setdefault(name, {"name": name, "practice": 0, "compose": 0})
        return item

    for block in (data or {}).get("topics") or []:
        name = str(block.get("topic") if isinstance(block, dict) else block or "").strip()
        if name:
            _touch(name)
    for question in (data or {}).get("questions") or []:
        name = str(question.get("topic") or "").strip()
        if not name:
            continue
        _touch(name)["practice"] += 1
    for question in compose_items or []:
        name = str(question.get("topic") or "").strip()
        if not name:
            continue
        _touch(name)["compose"] += 1
    return [row for row in sorted(counts.values(), key=lambda item: item["name"]) if row["practice"] or row["compose"]]
