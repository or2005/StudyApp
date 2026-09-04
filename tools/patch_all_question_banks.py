# -*- coding: utf-8 -*-
"""מרפא ניסוחי שאלות בכל מאגרי JSON — שמירה לדיסק אחרי align_stem."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.stem_fix import align_stem_to_answer, is_vague_stem  # noqa: E402

OUT = ROOT / "data" / "questions"


def _patch_question(q: dict) -> tuple[dict, bool]:
    row = dict(q)
    stem = str(row.get("question") or "")
    if is_vague_stem(stem) or stem.startswith("איזו אפשרות נכונה"):
        row["question"] = align_stem_to_answer(stem, row)
        # יישור answer ↔ correct_answer בלי לערבב הכל
        opts = [str(x) for x in (row.get("options") or [])]
        ca = str(row.get("correct_answer") or "").strip()
        idx = row.get("answer")
        if isinstance(idx, int) and 0 <= idx < len(opts):
            if not ca:
                row["correct_answer"] = opts[idx]
            elif ca in opts:
                row["answer"] = opts.index(ca)
                row["correct_answer"] = ca
        return row, True
    return row, False


def patch_file(path: Path) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixed = 0
    total = 0
    for topic in data.get("topics") or []:
        rows = []
        for q in topic.get("questions") or []:
            total += 1
            neo, changed = _patch_question(q)
            if changed:
                fixed += 1
            rows.append(neo)
        topic["questions"] = rows
    if data.get("questions"):
        rows = []
        for q in data.get("questions") or []:
            total += 1
            neo, changed = _patch_question(q)
            if changed:
                fixed += 1
            rows.append(neo)
        data["questions"] = rows
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return fixed, total


def main() -> None:
    skip = {"driving_theory"}  # מאגר רשמי — לא לדרוס
    for path in sorted(OUT.glob("*.json")):
        if path.stem in skip:
            print("skip", path.name)
            continue
        fixed, total = patch_file(path)
        print(f"{path.name}: fixed {fixed}/{total}")


if __name__ == "__main__":
    main()
