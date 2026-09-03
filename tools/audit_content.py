"""סריקת איכות למאגר: שאלות לא ברורות, מסיחים מזויפים, עיוני דל."""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.curriculum import build_all

VAGUE = (
    "מה נכון?",
    "מה נכון",
    "איך כותבים נכון?",
    "איך כותבים נכון",
    "choose correct",
    "choose the correct",
    "what is correct",
)
DUMMY = ("לא נכון (", "גרסה שגויה", "only wrong")
LEAK = ("only wrong", "wrong option", "לא זו התשובה")


def main() -> None:
    banks = build_all()
    dummy = []
    vague = []
    leak = []
    short_q = []
    short_why = []
    short_theory = []
    dups = defaultdict(list)
    same_opts = []
    for key, bank in banks.items():
        seen: dict[str, str] = {}
        for q in bank.get("questions") or []:
            qid = str(q.get("id") or "")
            stem = " ".join(str(q.get("question") or "").split())
            opts = [str(o) for o in (q.get("options") or [])]
            blob = " | ".join(opts)
            exp = str(q.get("explanation") or "")
            if any(mark in blob for mark in DUMMY):
                dummy.append((key, qid, stem[:80], opts))
            if any(mark in blob.lower() for mark in LEAK):
                leak.append((key, qid, opts))
            low = stem.lower().strip()
            if low in {v.lower() for v in VAGUE} or stem.strip() in VAGUE:
                vague.append((key, qid, stem, q.get("correct_answer")))
            if len(stem) < 12:
                short_q.append((key, qid, stem))
            raw_why = exp
            if len(raw_why) < 28:
                short_why.append((key, qid, raw_why[:80]))
            if len(set(opts)) < 4:
                same_opts.append((key, qid, opts))
            norm = stem.replace(" ", "")
            if norm:
                dups[f"{key}:{norm}"].append(qid)
        for lesson in bank.get("lessons") or []:
            body = str(lesson.get("content") or "")
            # theory before the auto-expand marker
            core = body.split("למה זה חשוב")[0].strip()
            if len(core) < 80:
                short_theory.append((key, lesson.get("title"), len(core), core[:90]))

    print("SUBJECTS", {k: len(v.get("questions") or []) for k, v in banks.items()})
    print("DUMMY_OPTIONS", len(dummy))
    for row in dummy[:25]:
        print("  D", row[0], row[1], row[2], row[3])
    print("VAGUE_STEMS", len(vague))
    for row in vague[:25]:
        print("  V", row)
    print("LEAKS", len(leak))
    for row in leak[:15]:
        print("  L", row)
    print("SHORT_STEMS", len(short_q))
    for row in short_q[:15]:
        print("  S", row)
    print("SHORT_WHY", len(short_why))
    print("DUP_STEMS", sum(1 for ids in dups.values() if len(ids) > 1))
    print("SAME_OPTS", len(same_opts))
    print("THIN_THEORY", len(short_theory))
    for row in short_theory[:20]:
        print("  T", row[0], row[1], row[2], row[3])


if __name__ == "__main__":
    main()
