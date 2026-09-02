from __future__ import annotations

import json
import os
from functools import lru_cache

from core.config import QUESTIONS_DIR


def _flatten(subject_key: str, data: dict) -> dict:
    topics = data.get("topics") or []
    questions = list(data.get("questions") or [])
    if not questions:
        for topic in topics:
            for item in topic.get("questions") or []:
                row = dict(item)
                row.setdefault("topic", topic.get("topic", subject_key))
                row.setdefault("subject", subject_key)
                questions.append(row)
    data["questions"] = questions

    if not data.get("lessons"):
        lessons = []
        for idx, topic in enumerate(topics, start=1):
            theory = topic.get("theory_content") or ""
            if not theory:
                continue
            lessons.append(
                {
                    "id": f"{subject_key}_lesson_{idx}",
                    "title": topic.get("topic", f"שיעור {idx}"),
                    "category": "שיעור עיוני",
                    "content": theory,
                    "topic": topic.get("topic", subject_key),
                }
            )
        data["lessons"] = lessons
    return data


@lru_cache(maxsize=16)
def load_subject(subject_key: str) -> dict | None:
    path = os.path.join(QUESTIONS_DIR, f"{subject_key}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data = _flatten(subject_key, data)
    try:
        from core.custom_questions import merge_into

        data = merge_into(subject_key, data)
    except Exception:
        pass
    try:
        from core.theory_enrich import expand_lessons

        data = expand_lessons(subject_key, data)
    except Exception:
        pass
    return data


def questions_for_topic(subject_key: str, topic: str) -> list[dict]:
    data = load_subject(subject_key) or {}
    return [q for q in data.get("questions") or [] if q.get("topic") == topic]


def clear_cache() -> None:
    load_subject.cache_clear()
