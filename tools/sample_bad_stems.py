# -*- coding: utf-8 -*-
"""Spot common mangled stem patterns still in banks."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PATTERNS = [
    ("mahu_verb", re.compile(r"^מהו\s+.+\s+(נמצא|נמצאים|עוזר|עוזרת|שווה)\b")),
    ("mahi_shave", re.compile(r"^מהי\s+.+\s+שווה\s*\??$")),
    ("series_next", re.compile(r"\.\.\.\s*הבא\s*\??$")),
    ("trail_speed", re.compile(r"המהירות\s*$")),
    ("mahi_gil", re.compile(r"^מהי\s+גיל\b")),
    ("mahu_shear", re.compile(r"^מהו\s+השארית\b")),
    ("pct_shave", re.compile(r"%\s*מ.+\s+שווה")),
    ("no_qmark_fact", re.compile(r"^(?!מה|מי|מתי|כמה|איז|השל|למה|באי).{12,80}[^.!?]$")),
]

folder = ROOT / "data" / "questions"
counts = {k: 0 for k, _ in PATTERNS}
samples = {k: [] for k, _ in PATTERNS}
for path in sorted(folder.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    for q in data.get("questions") or []:
        stem = str(q.get("question") or "").strip()
        for name, pat in PATTERNS:
            if pat.search(stem):
                counts[name] += 1
                if len(samples[name]) < 4:
                    samples[name].append((path.stem, stem[:90]))
print(counts)
for name, rows in samples.items():
    print("==", name)
    for row in rows:
        print(" ", row)
