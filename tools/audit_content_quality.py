# -*- coding: utf-8 -*-
"""Audit StudyApp question banks for remaining content-quality defects (read-only)."""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.illustrations.history import build_visual_for
from core.stem_fix import (
    _PERSON_PHRASES,
    _PERSON_ROLE,
    _PERSON_WORDS,
    _ROUND,
    _VAGUE,
    clean_topic_label,
    polish_stem,
)
from core.teach import clarify_stem

QUESTIONS_DIR = ROOT / "data" / "questions"
SAMPLE_N = 8

# Broken lead patterns that polish should remove / rewrite but may leave residue.
_BROKEN_AFTER = (
    re.compile(r"^סבב\b", re.I),
    re.compile(r"^[\-\u2013\u2014\u05be\|]+\s*"),
    re.compile(r"^י[\-\u2013\u2014\u05be]\s*"),
    re.compile(r"^(?:הנקודה העדינה|ניסוח עדין|שימו לב)\s*[:：]", re.I),
    re.compile(r"^מי היה (?:בידוד|מטר)\b"),
)

_MAHU_PERSON = re.compile(r"^(מהו|מהי)\s+(.+?)\s*\??$")
_VAGUE_LOOSE = re.compile(r"מה נכון|מה מתאים")
_YEAR_LIST_ONLY = re.compile(
    r"^[\d\s;؛,.\-/–—־:]+$"
)
_PERSON_NAME_ANS = re.compile(
    r"^(?:דוד\s+)?(?:בן[\s־\-]גוריון|הרצל|גולדה(?:\s+מאיר)?|רבין|בגין|"
    r"ויצמן|סנש|ז׳בוטינסקי|ז'בוטינסקי|חיים\s+ויצמן|משה\s+דיין|"
    r"יצחק\s+רבין|מנחם\s+בגין|תאודור\s+הרצל)(?:\s+\S+){0,2}$"
)
_ZION_FLUFF = "הציונות המודרנית"
_CONGRESS_HINTS = ("הרצל", "באזל", "קונגרס")


def _looks_person_role(body: str) -> bool:
    b = body.strip()
    if _PERSON_ROLE.search(b):
        return True
    if any(p in b for p in _PERSON_PHRASES):
        return True
    words = set(re.findall(r"[\w׳'״\"־\-]+", b, re.UNICODE))
    return bool(words & _PERSON_WORDS)


def _first_line(text: str) -> str:
    for line in str(text or "").splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def _is_year_list_section(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or "סבב" in raw:
        return False
    # Strip a short Hebrew header like "דוגמאות:" then test body
    body = re.sub(r"^(?:דוגמאות|לדוגמה|שנים|תאריכים)\s*[:：]\s*", "", raw, flags=re.I)
    body = body.strip()
    if len(body) < 6:
        return False
    if ";" not in body and "؛" not in body:
        # still allow pure digit/semicolon-ish blocks with commas
        if not re.search(r"\d{3,4}", body):
            return False
    # Mostly digits + separators
    letters = re.findall(r"[A-Za-zא-ת]", body)
    digits = re.findall(r"\d", body)
    if len(digits) < 4:
        return False
    if letters and len(letters) > max(3, len(digits) // 8):
        return False
    return bool(_YEAR_LIST_ONLY.match(re.sub(r"[A-Za-zא-ת]{0,12}", "", body)) or (
        len(digits) >= 8 and len(letters) <= 4
    ))


def _extract_example_sections(lesson: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (label, text) example-like sections from a lesson."""
    out: list[tuple[str, str]] = []
    for key in ("examples", "example", "examples_text", "דוגמאות"):
        val = lesson.get(key)
        if isinstance(val, str) and val.strip():
            out.append((key, val.strip()))
        elif isinstance(val, list):
            joined = " ; ".join(str(x).strip() for x in val if str(x).strip())
            if joined:
                out.append((key, joined))
    content = str(lesson.get("content") or "")
    # Split on common example headers
    parts = re.split(
        r"(?m)^(?:#{1,3}\s*)?(?:דוגמאות|לדוגמה|דוגמה|Examples?)\s*[:：]?\s*$",
        content,
        flags=re.I,
    )
    if len(parts) > 1:
        for chunk in parts[1:]:
            # take until next major header or blank block end (~12 lines)
            block = []
            for line in chunk.splitlines():
                if re.match(r"^#{1,3}\s+\S", line) or re.match(
                    r"^(?:סיכום|זכרו|שימו לב|תרגול)\b", line.strip()
                ):
                    break
                block.append(line)
            text = "\n".join(block).strip()
            if text:
                out.append(("content:דוגמאות", text))
    # Inline "דוגמאות: 1948; 1967; ..."
    for m in re.finditer(
        r"(?:דוגמאות|לדוגמה|שנים)\s*[:：]\s*([^\n]{6,200})",
        content,
        flags=re.I,
    ):
        out.append(("inline:דוגמאות", m.group(0).strip()))
    return out


def _load_banks() -> dict[str, dict[str, Any]]:
    banks: dict[str, dict[str, Any]] = {}
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        subj = str(data.get("subject") or path.stem)
        banks[subj] = data
    return banks


def _add(
    bucket: dict[str, list],
    subject: str,
    row: tuple,
) -> None:
    bucket[subject].append(row)


def main() -> None:
    banks = _load_banks()

    cat_stem_savav: dict[str, list] = defaultdict(list)
    cat_stem_broken: dict[str, list] = defaultdict(list)
    cat_topic_savav: dict[str, list] = defaultdict(list)
    cat_gender: dict[str, list] = defaultdict(list)
    cat_short: dict[str, list] = defaultdict(list)
    cat_zion: dict[str, list] = defaultdict(list)
    cat_visual_mismatch: dict[str, list] = defaultdict(list)
    cat_theory_savav: dict[str, list] = defaultdict(list)
    cat_year_examples: dict[str, list] = defaultdict(list)

    visual_total = 0
    visual_congress = 0
    visual_mismatch = 0

    totals_q = {}
    totals_lessons = {}

    for subject, bank in banks.items():
        questions = bank.get("questions") or []
        lessons = bank.get("lessons") or []
        totals_q[subject] = len(questions)
        totals_lessons[subject] = len(lessons)

        for q in questions:
            qid = str(q.get("id") or "")
            raw_stem = str(q.get("question") or "")
            polished = polish_stem(raw_stem, q)
            clarified = clarify_stem({**q, "question": raw_stem})
            # Prefer clarify (includes polish); also check polished alone
            final_stem = clarified or polished
            topic_raw = str(q.get("topic") or "")
            topic_clean = clean_topic_label(topic_raw)
            ans = str(q.get("correct_answer") or q.get("answer") or "").strip()
            exp = str(q.get("explanation") or "").strip()

            if "סבב" in final_stem:
                _add(
                    cat_stem_savav,
                    subject,
                    (qid, final_stem[:100], raw_stem[:80]),
                )
            elif any(p.search(final_stem) for p in _BROKEN_AFTER):
                _add(
                    cat_stem_broken,
                    subject,
                    (qid, final_stem[:100], raw_stem[:80]),
                )
            # Also flag if ROUND prefix somehow remains
            if _ROUND.match(final_stem.strip()):
                if (qid, final_stem[:100], raw_stem[:80]) not in cat_stem_savav[subject]:
                    _add(cat_stem_savav, subject, (qid, final_stem[:100], raw_stem[:80]))

            if "סבב" in topic_clean:
                _add(cat_topic_savav, subject, (qid, topic_clean[:100], topic_raw[:80]))

            m = _MAHU_PERSON.match(final_stem.strip())
            if m and _looks_person_role(m.group(2)):
                _add(
                    cat_gender,
                    subject,
                    (qid, final_stem[:110], m.group(1), m.group(2)[:60]),
                )

            stem_compact = " ".join(final_stem.split())
            if len(stem_compact) < 12 or _VAGUE.match(stem_compact) or _VAGUE_LOOSE.search(
                stem_compact
            ):
                # avoid double-count noise: "מה נכון" inside long stems still flagged per request
                if len(stem_compact) < 12 or _VAGUE_LOOSE.search(stem_compact):
                    _add(
                        cat_short,
                        subject,
                        (qid, len(stem_compact), stem_compact[:90]),
                    )

            if _ZION_FLUFF in exp:
                # person-name answer
                ans_is_person = bool(_PERSON_NAME_ANS.match(ans)) or (
                    _looks_person_role(ans) and len(ans) <= 40 and not re.search(r"\d{3,4}", ans)
                )
                if ans_is_person:
                    # generic fluff: explanation is mostly the fluff phrase
                    exp_core = re.sub(r"\s+", " ", exp)
                    if len(exp_core) < 120 or exp_core.count(".") <= 2:
                        _add(
                            cat_zion,
                            subject,
                            (qid, ans[:40], exp_core[:110]),
                        )

            if subject == "history":
                visual_total += 1
                visual = build_visual_for(q, index=visual_total, force=False)
                title = str((visual or {}).get("title") or "")
                blob = " ".join(
                    [
                        str(q.get("question") or ""),
                        str(ans),
                        " ".join(str(o) for o in (q.get("options") or [])),
                    ]
                )
                if title == "ציונות מוסדית":
                    visual_congress += 1
                    if not any(h in blob for h in _CONGRESS_HINTS):
                        visual_mismatch += 1
                        _add(
                            cat_visual_mismatch,
                            subject,
                            (qid, stem_compact[:80], ans[:40]),
                        )

            # per-question theory_content if present
            tc = q.get("theory_content")
            if tc:
                first = _first_line(str(tc))
                if "סבב" in first:
                    _add(cat_theory_savav, subject, (f"q:{qid}", first[:100]))

        for lesson in lessons:
            lid = str(lesson.get("id") or lesson.get("title") or "")
            for field in ("theory_content", "content"):
                val = lesson.get(field)
                if not val:
                    continue
                first = _first_line(str(val))
                if "סבב" in first:
                    _add(
                        cat_theory_savav,
                        subject,
                        (f"lesson:{lid}:{field}", first[:110]),
                    )
            for label, text in _extract_example_sections(lesson):
                if _is_year_list_section(text):
                    _add(
                        cat_year_examples,
                        subject,
                        (f"lesson:{lid}:{label}", text[:100]),
                    )
            # topic on lesson
            tclean = clean_topic_label(str(lesson.get("topic") or ""))
            if "סבב" in tclean:
                _add(cat_topic_savav, subject, (f"lesson:{lid}", tclean[:100], str(lesson.get("topic"))[:80]))

    def _print_cat(name: str, bucket: dict[str, list], extra: str = "") -> int:
        total = sum(len(v) for v in bucket.values())
        print()
        print("=" * 72)
        print(f"{name}: TOTAL={total}" + (f"  {extra}" if extra else ""))
        print("-" * 72)
        for subj in sorted(bucket.keys()):
            rows = bucket[subj]
            if not rows:
                continue
            print(f"  [{subj}] {len(rows)}")
            for row in rows[:SAMPLE_N]:
                print(f"    • {row}")
            if len(rows) > SAMPLE_N:
                print(f"    … +{len(rows) - SAMPLE_N} more")
        if total == 0:
            print("  (none)")
        return total

    print("StudyApp content-quality audit (read-only)")
    print(f"banks: {QUESTIONS_DIR}")
    print("questions per subject:", dict(sorted(totals_q.items())))
    print("lessons per subject:", dict(sorted(totals_lessons.items())))
    print(f"total questions: {sum(totals_q.values())}  lessons: {sum(totals_lessons.values())}")

    t1a = _print_cat(
        "1a. Stems still containing סבב after polish_stem/clarify_stem",
        cat_stem_savav,
    )
    t1b = _print_cat(
        "1b. Stems starting with broken patterns after polish",
        cat_stem_broken,
    )
    t2 = _print_cat("2. Topics still containing סבב after clean_topic_label", cat_topic_savav)
    t3 = _print_cat(
        "3. Gender-wrong מהו/מהי with person roles after polish",
        cat_gender,
    )
    t4 = _print_cat(
        "4. Very short/vague stems (len<12 or מה נכון/מה מתאים)",
        cat_short,
    )
    t5 = _print_cat(
        "5. Explanations = Zionism fluff while answer is a person name",
        cat_zion,
    )
    t6 = _print_cat(
        "6. History visuals: ציונות מוסדית without הרצל/באזל/קונגרס in Q+A",
        cat_visual_mismatch,
        extra=f"(history Qs={visual_total}, title=ציונות מוסדית={visual_congress}, mismatch={visual_mismatch})",
    )
    t7 = _print_cat(
        "7. theory_content/lesson content first lines still containing סבב",
        cat_theory_savav,
    )
    t8 = _print_cat(
        "8. Example sections that are only year lists",
        cat_year_examples,
    )

    print()
    print("=" * 72)
    print("SUMMARY TOTALS")
    print("-" * 72)
    summary = {
        "1_stem_savav": t1a,
        "1_stem_broken": t1b,
        "2_topic_savav": t2,
        "3_gender_mahu": t3,
        "4_short_vague": t4,
        "5_zion_fluff_person": t5,
        "6_visual_congress_mismatch": t6,
        "7_theory_savav": t7,
        "8_year_list_examples": t8,
    }
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # per-subject rollup
    print()
    print("PER-SUBJECT DEFECT COUNTS")
    all_cats = [
        ("stem_savav", cat_stem_savav),
        ("stem_broken", cat_stem_broken),
        ("topic_savav", cat_topic_savav),
        ("gender", cat_gender),
        ("short_vague", cat_short),
        ("zion_fluff", cat_zion),
        ("visual_mismatch", cat_visual_mismatch),
        ("theory_savav", cat_theory_savav),
        ("year_examples", cat_year_examples),
    ]
    subjects = sorted(banks.keys())
    hdr = f"{'subject':12} " + " ".join(f"{n:>14}" for n, _ in all_cats) + f" {'TOTAL':>8}"
    print(hdr)
    for subj in subjects:
        counts = [len(bucket.get(subj, [])) for _, bucket in all_cats]
        line = f"{subj:12} " + " ".join(f"{c:14d}" for c in counts) + f" {sum(counts):8d}"
        print(line)

    print()
    print("Done. No bank JSON files were modified.")


if __name__ == "__main__":
    main()
