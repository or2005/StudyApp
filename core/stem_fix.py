# -*- coding: utf-8 -*-
"""תיקון ניסוחי שאלות שבורים במאגר + runtime."""
from __future__ import annotations

import re
from typing import Any

_LEAD_JUNK = re.compile(r"^[\s\u200f\u200e]*[\-\u2013\u2014\u05be\|]+\s*")
_Y_DASH = re.compile(r"^י[\-\u2013\u2014\u05be]\s*")
_MI = re.compile(r"^מי\s+(היה|היתה|הייתה)\s+(.+?)\s*\??$")
_MAHU_SHORT = re.compile(r"^(מהו|מהי)\s+([A-Za-z0-9₀-₉pPH=\+\-\(\)]+)\s*\??$")
_VAGUE = re.compile(r"^(מה נכון(?: כאן)?|מה מתאים כאן|איזו תשובה נכונה)\s*\??$", re.I)
_HEB_ASCII_HYPHEN = re.compile(r"(?<=[\u0590-\u05FF])-(?=[\u0590-\u05FF])")
_SOFT_PREFIX = re.compile(r"^(?:הנקודה העדינה|ניסוח עדין|שימו לב)\s*[:：]\s*", re.I)
# שנה בודדת בתחילת הסבר בלי הקשר (שיבוש נפוץ אחרי ניקוי מאגר)
_ORPHAN_YEAR = re.compile(r"^(?:ב)?(?:שנת\s+)?(\d{3,4})\s+")

# מושגים ארוכים יותר קודם; מילים קצרות רק כמילה שלמה
_NON_PERSON_LONG = re.compile(
    r"(בידוד|מתכת|חומר|נוסחה|מספר|אחוז|זווית|משפט|מילה|פועל|"
    r"תנועה|זרם|מתח|התנגדות|חום|לחץ|מסה|נפח|צפיפות|גז|נוזל|מוצק|"
    r"אטום|מולקולה|יסוד|תרכובת|תגובה|משוואה|גרף|פונקציה|מטר|"
    r"אנרגיה|כוח|מהירות|תאוצה|מוליך|מבודד|פחמן|חמצן|מימן|pH|"
    r"דמוקרטיה|כנסת|ממשלה|רשות|חוק|זכות|חובה|אזרח|"
    r"מדינה|עיר|נהר|יבשת|אקלים|רקמה|איבר|עצם|שריר|"
    r"מודד|טוב|רע|חלש|חזק)"
)
_NON_PERSON_WORDS = frozenset({
    "שם", "ים", "הר", "תא", "דם", "ס״מ", "ק״ג",
})

_PERSON_WORDS = frozenset({
    "מלך", "נשיא", "שר", "מנהיג", "רב", "רופא", "מדען",
    "סופר", "משורר", "חייל", "קצין", "גנרל", "קיסר", "נביא", "שופט",
    "הרצל", "רבין", "בגין", "סאדאת", "ויצמן", "סנש",
    "דוד", "משה", "אהרן", "כהן", "לוי",
})
_PERSON_PHRASES = (
    "ראש ממשלה", "ראש הממשלה", "בן גוריון", "בן-גוריון", "בן־גוריון",
    "ז׳בוטינסקי", "רמטכ״ל",
)


def strip_stem_junk(stem: str) -> str:
    text = str(stem or "").strip()
    text = _LEAD_JUNK.sub("", text)
    text = _Y_DASH.sub("", text)
    while text and text[0] in "-–—־|":
        text = text[1:].lstrip()
    return text.strip()


def clean_student_text(text: str, *, keep_years_from: str = "") -> str:
    """מנקה מקפי ASCII בין מילים עבריות וקידומות גנריות בהסברים."""
    raw = str(text or "").strip()
    raw = _SOFT_PREFIX.sub("", raw)
    raw = _HEB_ASCII_HYPHEN.sub(" ", raw)
    raw = raw.replace(" — ", ". ").replace(" – ", ", ")
    context = str(keep_years_from or "")
    year_hit = _ORPHAN_YEAR.match(raw)
    if year_hit:
        year = year_hit.group(1)
        rest = raw[year_hit.end():].lstrip(" ,.;:")
        # שנה קצרה+עובדה נשארת; שנה זרה לפני הגדרה ארוכה נמחקת
        if year not in context and len(rest) >= 48:
            raw = rest
    raw = re.sub(r"\s{2,}", " ", raw)
    return raw.strip()


def _looks_like_person(body: str) -> bool:
    text = str(body or "").strip()
    words = [w.strip(" «»\"'?.,") for w in text.split()]
    if _NON_PERSON_LONG.search(text):
        return False
    if any(w in _NON_PERSON_WORDS for w in words):
        return False
    if any(p in text for p in _PERSON_PHRASES):
        return True
    if any(w in _PERSON_WORDS for w in words):
        return True
    if len(words) == 2 and all(re.search(r"[\u0590-\u05FF]", w) for w in words):
        if not any(w.endswith(("ים", "ות", "יון", "ציה")) for w in words):
            return True
    return False


def fix_false_who(stem: str, question: dict[str, Any] | None = None) -> str:
    """«מי היה בידוד טוב?» → שאלה הגיונית לפי הנושא."""
    text = strip_stem_junk(stem)
    match = _MI.match(text)
    if not match:
        return text
    body = match.group(2).strip(" «»\"'")
    if _looks_like_person(body):
        return text if text.endswith("?") else f"{text}?"

    q = question or {}
    correct = str(q.get("correct_answer") or "").strip()
    opts = [str(x) for x in (q.get("options") or [])]

    if "מודד" in body:
        thing = body.replace(" מודד", "").replace("מודד", "").strip()
        if thing:
            return f"מה מודד ה{thing}?" if not thing.startswith("ה") else f"מה מודד {thing}?"
        return "מה מודדים כאן?"
    if body.endswith(" טוב") or " טוב" in body:
        thing = body.replace(" טוב", "").strip()
        return f"מה עושה {thing} טוב?" if thing else "מה נחשב בידוד טוב?"
    if body.endswith(" רע") or " רע" in body:
        thing = body.replace(" רע", "").strip()
        return f"מה מאפיין {thing} רע?" if thing else f"מהו {body}?"
    if re.search(r"(מוליך|מבודד|חומר|גז|נוזל|מתכת)", body):
        return f"מהו {body}?"
    if correct and correct in opts and len(correct) <= 48:
        if re.search(r"(מאט|מגדיל|מקטין|מונע|יוצר|שומר)", correct):
            return f"מה עושה {body}?"
        if re.search(r"^(אורך|מסה|זמן|חום|מתח|זרם|נפח)$", correct):
            return f"מה מודדים ב{body}?" if "מודד" not in body else f"מה מודד {body}?"
    return f"מהו {body}?"


def expand_short_formula(stem: str) -> str:
    text = strip_stem_junk(stem)
    match = _MAHU_SHORT.match(text)
    if not match:
        return text
    formula = match.group(2).strip()
    if "pH" in formula or "ph" in formula.lower():
        return f"מה אומר הערך {formula}?"
    if re.fullmatch(r"[A-Za-z0-9₀-₉\+\-\(\)]+", formula):
        return f"מה מייצגת הנוסחה {formula}?"
    return f"מהו {formula}?"


def fix_vague(stem: str, question: dict[str, Any] | None = None) -> str:
    text = strip_stem_junk(stem)
    if not _VAGUE.match(text):
        return text
    q = question or {}
    topic = str(q.get("topic") or "").strip()
    if topic:
        return f"איזו אפשרות נכונה בנושא {topic}?"
    return "איזו אפשרות נכונה לפי מה שלמדתם?"


def polish_stem(stem: str, question: dict[str, Any] | None = None) -> str:
    """סדר ניקוי אחד לכל שאלה לפני תצוגה או שמירה."""
    text = strip_stem_junk(stem)
    text = fix_false_who(text, question)
    text = expand_short_formula(text)
    text = fix_vague(text, question)
    text = clean_student_text(text)
    return text.strip()
