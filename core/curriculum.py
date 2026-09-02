from __future__ import annotations

import json
from pathlib import Path

from core.config import BASE_DIR, QUESTIONS_DIR, SUBJECTS
from core.curriculum_arabic import build_arabic
from core.curriculum_first_aid import build_first_aid
from core.curriculum_geo import build_geography
from core.curriculum_lang import (
    build_civics,
    build_english,
    build_hebrew,
    build_history,
    build_math,
)
from core.curriculum_stem import build_chemistry, build_physics
from core.lesson_expansion import enrich_bank

BUILDERS = {
    "hebrew": build_hebrew,
    "english": build_english,
    "math": build_math,
    "history": build_history,
    "geography": build_geography,
    "civics": build_civics,
    "chemistry": build_chemistry,
    "physics": build_physics,
    "arabic": build_arabic,
    "first_aid": build_first_aid,
}


def build_all() -> dict[str, dict]:
    """רק שאלות אמיתיות. שאלות ההטעיה האוטומטיות (inflate) הוסרו, הן ניפחו
    את המאגר בלי ללמד כלום, ולפעמים יצרו ניסוח שבור."""
    return {key: enrich_bank(builder()) for key, builder in BUILDERS.items()}


def write_subjects(keys: list[str] | None = None) -> list[tuple[str, int, int]]:
    Path(QUESTIONS_DIR).mkdir(parents=True, exist_ok=True)
    chosen = list(keys) if keys else list(BUILDERS)
    written = []
    for key in chosen:
        builder = BUILDERS[key]
        data = enrich_bank(builder())
        path = Path(QUESTIONS_DIR) / f"{key}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        written.append((key, len(data.get("questions") or []), len(data.get("lessons") or [])))
    return written


def write_all() -> list[tuple[str, int, int]]:
    return write_subjects()


if __name__ == "__main__":
    print("BASE", BASE_DIR)
    total_q = 0
    for key, q, lessons in write_all():
        total_q += q
        print(f"{key}: {q} questions, {lessons} lessons  ({SUBJECTS.get(key, {}).get('name', key)})")
    print("TOTAL", total_q)
