"""מצב יצור: התלמיד כותב את התשובה, לא בוחר מארבע אפשרויות."""
from __future__ import annotations

import re

_NIKUD = re.compile(r"[\u0591-\u05C7]")
_MARKS = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
_PUNCT = re.compile(r"[\"'׳״„”`,.;:!?()\[\]{}]+")
_SPACE = re.compile(r"\s+")
_FINALS = str.maketrans({"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"})
_NEED_OPTIONS = re.compile(
    r"(איזה משפט|איזו אפשרות|איזה מה|מה מהבאים|מה מהמשפטים|"
    r"בחרו את|סמנו את|איזו תשובה|which (sentence|option|of the following)|"
    r"choose the correct|^מה נכון|^מה לא נכון|^איך כותבים נכון\??$|"
    r"^איך כותבים\??$|^what is (correct|true)\??$)",
    re.I,
)
_ALREADY_WRITE = re.compile(
    r"(כתבו|רשמו|השלימו|חשבו וכתבו|Write |Complete |Fill )",
    re.I,
)
_HEBREW = re.compile(r"[\u0590-\u05FF]")


def normalize_answer(text: str) -> str:
    raw = _MARKS.sub("", str(text or ""))
    raw = _NIKUD.sub("", raw)
    raw = raw.replace("–", "-").replace("—", "-")
    raw = raw.replace("²", "2").replace("₃", "3").replace("₂", "2").replace("₀", "0")
    raw = _PUNCT.sub(" ", raw)
    raw = _SPACE.sub(" ", raw).strip().casefold()
    return raw.translate(_FINALS)


def _as_number(text: str) -> float | None:
    raw = str(text or "").strip().replace(",", "").replace("%", "")
    raw = _MARKS.sub("", raw).replace("\u200f", "")
    if re.fullmatch(r"-?\d+(\.\d+)?", raw):
        return float(raw)
    return None


def _he_forms(text: str) -> set[str]:
    forms = {text}
    if not text or not _HEBREW.search(text):
        return forms
    if text.startswith("ה") and len(text) > 2:
        forms.add(text[1:])
    else:
        forms.add("ה" + text)
    return forms


def accepted_list(question: dict | None) -> list[str]:
    item = question or {}
    extras = item.get("accepted") or item.get("accept") or []
    values = [str(item.get("correct_answer") or "").strip()]
    values.extend(str(x).strip() for x in extras)
    answer_idx = item.get("answer")
    options = item.get("options") or []
    if isinstance(answer_idx, int) and 0 <= answer_idx < len(options):
        values.append(str(options[answer_idx]).strip())
    return [v for v in values if v]


def answers_match(typed: str, question: dict | None = None, expected: str = "") -> bool:
    got = normalize_answer(typed)
    if not got:
        return False
    targets = accepted_list(question)
    if expected:
        targets.append(expected)
    norms = {normalize_answer(item) for item in targets if item}
    if got in norms:
        return True
    compact = got.replace(" ", "")
    if compact in {item.replace(" ", "") for item in norms}:
        return True
    # סובלנות ליחידות: 3A / 3 אמפר / 3
    unit = re.compile(
        r"(?:a|v|w|ω|ohm|amps?|volts?|watts?|אמפר|וולט|אוהם|ואט|קילוואט|kwh|hz|f|h|ma|kω|mω)\s*$",
        re.I,
    )
    got_bare = unit.sub("", compact).strip()
    for item in norms:
        bare = unit.sub("", item.replace(" ", "")).strip()
        if got_bare and bare and got_bare == bare:
            return True
    got_num = _as_number(typed)
    if got_num is None:
        got_num = _as_number(got)
    if got_num is None and got_bare:
        got_num = _as_number(got_bare)
    if got_num is not None:
        for item in list(targets) + list(norms):
            other = _as_number(item)
            if other is None:
                other = _as_number(unit.sub("", normalize_answer(item).replace(" ", "")))
            if other is not None and abs(got_num - other) < 1e-9:
                return True
    got_forms = _he_forms(got)
    for item in norms:
        if _he_forms(item) & got_forms:
            return True
    if got.startswith("the ") and got[4:] in norms:
        return True
    return False


def infer_write_guide(question: dict | None) -> str:
    item = question or {}
    custom = str(item.get("write_guide") or "").strip()
    if custom:
        return custom
    answer = str(item.get("correct_answer") or "").strip()
    if not answer:
        return "כתבו תשובה קצרה: מילה, מספר או שתיים-שלוש מילים."
    digits = answer.replace(",", "").replace(".", "").replace("-", "")
    if answer.isdigit() or (digits.isdigit() and len(answer) <= 8):
        if len(answer) == 4 and answer.startswith(("12", "13", "14", "15", "16", "17", "18", "19", "20")):
            return "כתבו שנה בת 4 ספרות בלבד, בלי המילה «שנת»."
        return "כתבו מספר בלבד, בלי מילים ובלי יחידות."
    if re.fullmatch(r"[A-Za-z0-9₂₀₃]+", answer):
        if any(ch.isdigit() or ch in "₂₀₃" for ch in answer):
            return "כתבו את הסימן או הנוסחה באנגלית, כמו H2O."
        return "כתבו מילה אחת באנגלית, בלי משפט."
    words = answer.split()
    if len(words) == 1:
        return "כתבו מילה אחת בלבד. איות רגיל, בלי נקודה ובלי משפט."
    if len(words) <= 3:
        return "כתבו תשובה קצרה של שתיים-שלוש מילים, בלי משפט שלם."
    return "כתבו את התשובה הקצרה בדיוק כמו שמבקשים בשאלה."


def is_writable(question: dict) -> bool:
    """רק שאלות שאפשר לענות עליהן בלי לראות ארבע אפשרויות."""
    if not question or question.get("kind") in {"trick", "passage"}:
        return False
    answer = str(question.get("correct_answer") or "").strip()
    if question.get("compose") or question.get("kind") == "compose":
        return bool(answer)
    prompt = str(question.get("question") or "").strip()
    if not prompt or not answer:
        return False
    if _NEED_OPTIONS.search(prompt):
        return False
    if len(answer) > 40 or answer.startswith("לא נכון"):
        return False
    if "____" in prompt or "___" in prompt:
        return True
    return bool(_ALREADY_WRITE.search(prompt))


def as_compose(question: dict) -> dict:
    item = dict(question)
    item["kind"] = "compose"
    item["compose"] = True
    item["write_guide"] = infer_write_guide(item)
    item.setdefault("hint", item["write_guide"])
    return item


def make_compose(
    subject: str,
    topic: str,
    qid: str,
    prompt: str,
    answer: str,
    explanation: str,
    accepted: list[str] | None = None,
    difficulty: str = "Easy",
    write_guide: str = "",
    hint: str = "",
) -> dict:
    from core.quiz import polish_explanation

    expl = polish_explanation(answer, explanation, topic, subject).strip()
    if len(expl) < 40:
        guide = (write_guide or "").strip() or "כתבו תשובה קצרה ומדויקת."
        expl = f"{expl} {guide}".strip()
        if len(expl) < 40:
            expl = f"{expl} בדקו איות ויחידות לפני השליחה."
    item = {
        "id": qid,
        "subject": subject,
        "topic": topic,
        "question": prompt,
        "correct_answer": answer,
        "accepted": accepted or [],
        "explanation": expl,
        "difficulty": difficulty,
        "kind": "compose",
        "compose": True,
        "options": [],
        "answer": -1,
        "tags": [subject, topic, "compose", difficulty],
    }
    item["write_guide"] = write_guide or infer_write_guide(item)
    item["hint"] = hint or item["write_guide"]
    return item


def compose_pool(subject: str, base_questions: list[dict] | None = None) -> list[dict]:
    from core.compose_bank import COMPOSE_BANK

    items = [dict(item) for item in COMPOSE_BANK.get(subject) or []]
    seen = {item.get("id") for item in items}
    for question in base_questions or []:
        if not is_writable(question):
            continue
        item = as_compose(question)
        qid = item.get("id")
        if qid in seen:
            continue
        seen.add(qid)
        items.append(item)
    return items
