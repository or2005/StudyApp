import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from core.curriculum import build_all
from core.config import QUESTIONS_DIR

banks = build_all()
total_q = total_l = 0
print("IN-MEMORY BUILD")
for k, b in banks.items():
    q = len(b.get("questions") or [])
    l = len(b.get("lessons") or [])
    total_q += q
    total_l += l
    print(f"  {k}: {q} questions, {l} lessons")
print("TOTAL", total_q, "lessons", total_l)

print("\nSERIALIZED")
sq = sl = 0
for name in os.listdir(QUESTIONS_DIR):
    if not name.endswith(".json"):
        continue
    with open(os.path.join(QUESTIONS_DIR, name), encoding="utf-8") as f:
        data = json.load(f)
    q = len(data.get("questions") or [])
    l = len(data.get("lessons") or [])
    sq += q
    sl += l
    print(f"  {name}: {q} q, {l} lessons")
print("SERIAL TOTAL", sq, "lessons", sl)
print("30% target new questions", int(total_q * 0.30))
