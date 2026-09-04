"""שיוך המחשות להיסטוריה — לפחות מחצית מהשיעורים והשאלות."""
from __future__ import annotations

import hashlib
from typing import Any

from core.illustrations.schema import VISUAL_KEY, make_visual

# סף כיסוי מינימלי
MIN_COVERAGE = 0.50


def _blob(item: dict[str, Any]) -> str:
    return " ".join(
        str(item.get(k) or "")
        for k in ("title", "topic", "category", "question", "content", "correct_answer", "explanation")
    )


def _stable_bucket(key: str, n: int = 100) -> int:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % n


def _match_rule(text: str) -> tuple[str, dict] | None:
    t = text
    rules: list[tuple[tuple[str, ...], str, dict]] = [
        (("מגילת", "הכרז", "עצמאות", "הכרזה"), "scroll", {
            "title": "מגילת העצמאות",
            "caption": "מסמך ההכרזה: ערכים ומסגרת, לא חוקה סגורה.",
            "alt": "מגילה מגולגלת",
            "years": ["1948"],
            "reveal_note": "1948: הכרזת המדינה",
        }),
        (("בלפור", "הצהרת בלפור"), "document", {
            "title": "הצהרת בלפור",
            "caption": "1917: תמיכה בריטית בבית לאומי לעם היהודי.",
            "alt": "מסמך הצהרה",
            "years": ["1917"],
        }),
        (("חלוקה", "181", "או״ם", "אום"), "document", {
            "title": "החלטת החלוקה",
            "caption": "1947: החלטה 181 באו״ם.",
            "alt": "מסמך החלטה",
            "years": ["1947"],
        }),
        (("ששת הימים", "1967", "ירושלים המזרחית", "יום ירושלים"), "war", {
            "title": "מערכות מרכזיות",
            "caption": "1948 · 1967 · 1973. שלוש נקודות על ציר הביטחון.",
            "alt": "שלוש שנים על כרטיסים",
            "years": ["1948", "1967", "1973"],
            "labels": ["עצמאות", "ששת הימים", "יום כיפור"],
        }),
        (("יום כיפור", "1973", "תשל״ד"), "war", {
            "title": "מלחמת יום כיפור",
            "caption": "1973: נקודת מפנה ביטחונית ומדינית.",
            "alt": "כרטיסי שנים",
            "years": ["1948", "1967", "1973"],
            "labels": ["עצמאות", "ששת הימים", "יום כיפור"],
        }),
        (("עצמאות", "1948", "תש״ח", "בן־גוריון", "בן גוריון"), "scroll", {
            "title": "קום המדינה",
            "caption": "1948: הכרזה, מלחמה, ומוסדות מתעצבים.",
            "alt": "מגילה",
            "years": ["1948"],
        }),
        (("שלום", "מצרים", "ירדן", "קמפ", "סאדאת", "בגין", "1994", "1979"), "peace", {
            "title": "הסכמי שלום",
            "caption": "1979 מצרים · 1994 ירדן. הסכמים מדיניים.",
            "alt": "ידיים וענף זית",
            "years": ["1979", "1994"],
        }),
        (("עלייה", "העפלה", "מעפילים", "כנפי נשרים", "קליטה", "ברה״מ", "תימן"), "aliyah", {
            "title": "עליות והעפלה",
            "caption": "גלים של עלייה, חוקית ובלתי חוקית, וקליטה.",
            "alt": "ספינה וגלים",
        }),
        (("שואה", "סנש", "בדולח", "זיכרון", "גבורה", "כ״ז בניסן"), "memory", {
            "title": "זיכרון וגבורה",
            "caption": "זיכרון השואה והגבורה. לא רק תאריך בלוח.",
            "alt": "נר זיכרון",
        }),
        (("הרצל", "באזל", "קונגרס", "ציונות", "ז׳בוטינסקי", "בילטמור"), "congress", {
            "title": "ציונות מוסדית",
            "caption": "מקונגרס באזל ועד מוסדות היישוב והמדינה.",
            "alt": "בניין קונגרס",
            "years": ["1897"],
        }),
        (("הגנה", "אצ״ל", "לח״י", "מחתרת", "צה״ל", "ביטחון"), "war", {
            "title": "ביטחון ומחתרות",
            "caption": "מהיישוב וארגוני המחתרת עד צבא המדינה.",
            "alt": "כרטיסי שנים",
            "years": ["1939", "1948", "1967"],
            "labels": ["יישוב", "עצמאות", "ששת הימים"],
        }),
        (("דגל", "מנורה", "סמל", "בירה", "ירושלים"), "flag", {
            "title": "סמלים לאומיים",
            "caption": "דגל, מנורה וירושלים כבירה לפי החוק.",
            "alt": "דגל ישראל",
        }),
        (("מנורה", "סמל המדינה"), "menorah", {
            "title": "סמל המדינה",
            "caption": "מנורה וענפי זית, סמל הריבונות.",
            "alt": "מנורה וענפי זית",
        }),
        (("מנדט", "בריטי", "יישוב", "סוכנות"), "map", {
            "title": "יישוב ומנדט",
            "caption": "הקשר הגאוגרפי־מדיני לפני ואחרי 1948.",
            "alt": "מפת סכמה",
        }),
        (("כנסת", "נשיא", "ממשלה", "חוק השבות", "חוק יסוד", "רשות"), "state", {
            "title": "מוסדות וחוקים",
            "caption": "רשויות המדינה וחוקים מכוננים כמו חוק השבות.",
            "alt": "שלושה מוסדות",
            "labels": ["כנסת", "ממשלה", "חוק"],
        }),
        (("אוסלו", "רבין", "הסכמי אוסלו"), "peace", {
            "title": "תהליך מדיני",
            "caption": "שנות ה־90: הסכמים ותהליכים מדיניים.",
            "alt": "הסכם מדיני",
            "years": ["1993", "1994"],
        }),
        (("סיני", "קדש", "1956"), "war", {
            "title": "מבצע קדש",
            "caption": "1956: מערכה מוקדמת בציר הביטחון.",
            "alt": "כרטיסי שנים",
            "years": ["1948", "1956", "1967"],
            "labels": ["עצמאות", "קדש", "ששת הימים"],
        }),
        (("ציר זמן", "מאה ה־20", "כרונולוג", "שנה"), "timeline", {
            "title": "ציר זמן",
            "caption": "שנים כעוגנים, לא שינון בלי הקשר.",
            "alt": "ציר זמן",
            "years": ["1917", "1947", "1948", "1967", "1973", "1979"],
        }),
    ]
    for keys, kind, meta in rules:
        if any(k in t for k in keys):
            return kind, meta
    return None


def _fallback_for(item: dict[str, Any], index: int) -> tuple[str, dict]:
    """המחשות כלליות למילוי כיסוי — עדיין לימודיות, לא קישוט ריק."""
    catalog = [
        ("timeline", {
            "title": "ציר זמן היסטורי",
            "caption": "מסמנים שנים כדי לקשור אירוע להקשר.",
            "alt": "ציר זמן לימודי",
            "years": ["1917", "1947", "1948", "1967", "1973", "1979"],
        }),
        ("map", {
            "title": "הקשר גאוגרפי",
            "caption": "היסטוריה קורית במקום. סכמה לימודית של הארץ.",
            "alt": "מפת סכמה לימודית",
        }),
        ("document", {
            "title": "מסמכים מעצבים",
            "caption": "הצהרות, החלטות וחוקים משנים מציאות.",
            "alt": "איור מסמך היסטורי",
            "years": ["1948"],
        }),
        ("flag", {
            "title": "זהות וסמלים",
            "caption": "סמלים מספרים סיפור לאומי בקצרה.",
            "alt": "דגל סכמטי",
        }),
        ("state", {
            "title": "מדינה מתעצבת",
            "caption": "מוסדות, חוקים ואזרחות אחרי העצמאות.",
            "alt": "עמודי מוסדות המדינה",
            "labels": ["כנסת", "ממשלה", "חוק"],
        }),
        ("aliyah", {
            "title": "אנשים בתנועה",
            "caption": "עליות וקליטה הם חלק מהסיפור, לא הערת שוליים.",
            "alt": "ספינת עלייה סכמטית",
        }),
    ]
    key = str(item.get("id") or item.get("title") or item.get("question") or index)
    return catalog[_stable_bucket(key, len(catalog))]


def build_visual_for(item: dict[str, Any], *, index: int = 0, force: bool = False) -> dict[str, Any] | None:
    text = _blob(item)
    matched = _match_rule(text)
    if matched is None and not force:
        return None
    if matched is None:
        kind, meta = _fallback_for(item, index)
    else:
        kind, meta = matched
    return make_visual(kind=kind, **meta)


def attach_history_visuals(bank: dict[str, Any]) -> dict[str, Any]:
    """מצמיד בלוק visual לשיעורים ולשאלות בהיסטוריה בלבד."""
    bank = dict(bank)
    bank.setdefault("subject", "history")
    lessons = [dict(row) for row in (bank.get("lessons") or [])]
    questions = [dict(row) for row in (bank.get("questions") or [])]

    def _apply(rows: list[dict[str, Any]]) -> None:
        strong: list[int] = []
        weak: list[int] = []
        for i, row in enumerate(rows):
            visual = build_visual_for(row, index=i, force=False)
            if visual:
                row[VISUAL_KEY] = visual
                strong.append(i)
            else:
                weak.append(i)
        need = max(0, int(len(rows) * MIN_COVERAGE + 0.999) - len(strong))
        weak_sorted = sorted(weak, key=lambda i: _stable_bucket(str(rows[i].get("id") or i)))
        for i in weak_sorted[:need]:
            rows[i][VISUAL_KEY] = build_visual_for(rows[i], index=i, force=True)

    _apply(lessons)
    _apply(questions)
    bank["lessons"] = lessons
    bank["questions"] = questions
    return bank


def coverage_stats(bank: dict[str, Any]) -> dict[str, float | int]:
    def _cov(rows: list) -> tuple[int, int, float]:
        total = len(rows)
        hit = sum(1 for r in rows if isinstance(r.get(VISUAL_KEY), dict))
        return hit, total, (hit / total if total else 0.0)

    lh, lt, lr = _cov(bank.get("lessons") or [])
    qh, qt, qr = _cov(bank.get("questions") or [])
    return {
        "lessons_with": lh,
        "lessons_total": lt,
        "lessons_ratio": lr,
        "questions_with": qh,
        "questions_total": qt,
        "questions_ratio": qr,
    }
