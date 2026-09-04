# -*- coding: utf-8 -*-
"""תיקון ניסוחי שאלות שבורים במאגר + runtime."""
from __future__ import annotations

import re
from typing import Any

_LEAD_JUNK = re.compile(r"^[\s\u200f\u200e]*[\-\u2013\u2014\u05be\|]+\s*")
_Y_DASH = re.compile(r"^י[\-\u2013\u2014\u05be]\s*")
_ROUND = re.compile(r"^סבב\s+[A-Za-z0-9א-ת]+\s*[:：\-–—·.]*\s*", re.I)
_MI = re.compile(r"^מי\s+(היה|היתה|הייתה)\s+(.+?)\s*\??$")
_MAHU_SHORT = re.compile(r"^(מהו|מהי)\s+([A-Za-z0-9₀-₉pPH=\+\-\(\)]+)\s*\??$")
_VAGUE = re.compile(r"^(מה נכון(?: כאן)?|מה מתאים כאן|איזו תשובה נכונה)\s*\??$", re.I)
_HEB_ASCII_HYPHEN = re.compile(r"(?<=[\u0590-\u05FF])-(?=[\u0590-\u05FF])")
_SOFT_PREFIX = re.compile(r"^(?:הנקודה העדינה|ניסוח עדין|שימו לב)\s*[:：]\s*", re.I)
# שנה בודדת בתחילת הסבר בלי הקשר (שיבוש נפוץ אחרי ניקוי מאגר)
_ORPHAN_YEAR = re.compile(r"^(?:ב)?(?:שנת\s+)?(\d{3,4})\s+")
_FILLER_CHUNKS = (
    re.compile(
        r"קראו שוב את השאלה(?:,|\s)+בדקו יחידות(?:,|\s)+ופסלו מה שלא מתאים\.?",
        re.I,
    ),
    re.compile(r"אם טעיתם,?\s*חזרו לשיעור[^.]*(?:\.|$)", re.I),
    re.compile(r"פסלו מה שלא מתאים להגדרה,?\s*ובדקו מה בדיוק נשאל\.?", re.I),
    re.compile(r"קראו שוב את השאלה,?\s*סמנו מילה אחת חשובה,?\s*ואז בחרו\.?", re.I),
    re.compile(
        r"סיבה,?\s*אירוע,?\s*תוצאה\.?(?:\s*אחר כך התאריך של[^.]*\.?)?",
        re.I,
    ),
    re.compile(r"ניסוח עדין בהיסטוריה\.?", re.I),
    re.compile(r"משפט נכון בהיסטוריה,?", re.I),
)

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
    "מלך", "מלכה", "נשיא", "נשיאה", "שר", "שרה", "מנהיג", "מנהיגה", "רב", "רופא", "מדען",
    "סופר", "משורר", "חייל", "קצין", "גנרל", "קיסר", "נביא", "שופט",
    "הרצל", "רבין", "בגין", "סאדאת", "ויצמן", "סנש", "גולדה",
    "דוד", "משה", "אהרן", "כהן", "לוי",
})
_PERSON_PHRASES = (
    "ראש ממשלה", "ראש הממשלה", "ראשת ממשלה", "ראשת הממשלה",
    "בן גוריון", "בן-גוריון", "בן־גוריון",
    "ז׳בוטינסקי", "רמטכ״ל", "גולדה מאיר",
)
_PERSON_ROLE = re.compile(
    r"(ראש(?:ת)?\s+ה?ממשלה|נשיא(?:ה)?|רמטכ״ל|מלך|מלכה|שר(?:ת)?\s|"
    r"הרצל|גולדה|רבין|בגין|בן[\s־\-]גוריון|סנש|ויצמן)"
)
_MAHU_ANY = re.compile(r"^(מהו|מהי)\s+(.+?)\s*\??$")
_MI_BARE = re.compile(r"^מי\s+(?!היה\b|הייתה\b|היתה\b|הם\b|הן\b)(.+?)\s*\??$")
# כולל מקף עברי ־ (U+05BE) שמופיע במאגר: «היסטוריה ־ סבב C: …»
_TOPIC_ROUND = re.compile(
    r"(?:^|[\s־—\-–]+)סבב\s*[:：]?\s*[A-Za-z0-9א-ת\-]*\s*[:：\-–—·.]*\s*",
    re.I,
)
_ROUND_PAREN = re.compile(r"[\(（]\s*סבב[^\)）]*[\)）]", re.I)
_NON_PERSON_START = re.compile(
    r"^(?:אתמול|היום|מחר|מילה|משפט|פועל|שם|תואר|זמן|צורת|רבים|יחיד|"
    r"אחוז|מספר|נוסחה|ערך|חום|מתח|זרם)"
)
_PCT_SHAVE = re.compile(
    r"^(?:מהו|מהי)\s+(\d+(?:[.,]\d+)?)\s*%\s*מ[־\-]?\s*(\d+(?:[.,]\d+)?)\s*שווה\s*\??$"
)
_SHEERIT = re.compile(r"^(?:מהו|מהי)\s+ה?שארית\s+ב[־\-]?\s*(.+?)\s*\??$")
_ATOMIC_NUM = re.compile(r"^(?:מהו|מהי)\s+(?:ה)?מספר אטומי של\s+(.+?)\s*\??$")
_NIMTZA = re.compile(
    r"^(?:מהו|מהי)\s+(.+?)\s+נמצא(?:ים|ות)?(?:\s+(.+?))?\s*\??$"
)
_OZER_KI = re.compile(r"^(?:מהו|מהי)\s+(.+?)\s+עוזר(?:ת)?(?:\s+כי)?\s*\??$")
_SERIES_NEXT = re.compile(r"^(.+?),\s*\.\.\.\s*הבא\s*\??$")
_TRAIL_SPEED = re.compile(r"^(.*?)\.?[\s]*המהירות\s*$")
_TRAIL_SHAVE = re.compile(r"^(.+?)\s+שווה\s*$")
_UNIT_SHAVE = re.compile(r"^(?:מהו|מהי)\s+(.+?)\s+שווה\s*\??$")
_MAHI_MASC = re.compile(r"^מהי\s+(גיל|חוק|שארית|מספר|לחץ|זרם|הספק|תנע)\b(.*)$")



def strip_stem_junk(stem: str) -> str:
    text = str(stem or "").strip()
    text = _LEAD_JUNK.sub("", text)
    text = _Y_DASH.sub("", text)
    text = _ROUND.sub("", text)
    text = strip_round_noise(text)
    while text and text[0] in "-–—־|":
        text = text[1:].lstrip()
    return text.strip()


def strip_round_noise(text: str) -> str:
    """מסיר «סבב C» / «(סבב B)» מכל מקום בטקסט לתלמיד. שומר מעברי שורה."""
    raw = str(text or "")
    raw = _ROUND_PAREN.sub(" ", raw)
    raw = _TOPIC_ROUND.sub(" ", raw)
    raw = re.sub(r"[^\S\n]*סבב\s+[A-Za-z0-9א-ת\-]+[^\S\n]*", " ", raw, flags=re.I)
    # רק רווחים אופקיים — לא בולעים \n של שיעור עיוני
    raw = re.sub(r"[^\S\n]{2,}", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip(" —–-־·.|")


def scrub_explanation(text: str, *, keep_years_from: str = "", stem: str = "") -> str:
    """מנקה הסבר לתלמיד: בלי מלל גנרי, בלי כפילויות, בלי הגדרה לא קשורה."""
    raw = clean_student_text(text, keep_years_from=keep_years_from or stem)
    for pat in _FILLER_CHUNKS:
        raw = pat.sub(" ", raw)
    # כששואלים על תואר — לא מדביקים הגדרת שם עצם
    ask = str(stem or "")
    if re.search(r"תואר|שם התואר|Adjective", ask, re.I):
        raw = re.sub(r"שם עצם הוא[^.]*\.?", " ", raw)
    if re.search(r"שם עצם|Noun", ask, re.I) and "תואר" not in ask:
        raw = re.sub(r"שם תואר (?:הוא|מתאר)[^.]*\.?", " ", raw)
    raw = re.sub(r"\s{2,}", " ", raw).strip(" .;,")
    # לכל היותר שני משפטים קצרים
    parts = re.split(r"(?<=[.!?])\s+", raw)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) > 2:
        raw = " ".join(parts[:2])
    if len(raw) > 180:
        cut = raw[:180]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        raw = cut.rstrip(" ,;") + "…"
    return raw.strip()


def clean_student_text(text: str, *, keep_years_from: str = "") -> str:
    """מנקה מקפי ASCII בין מילים עבריות וקידומות גנריות בהסברים."""
    raw = str(text or "").strip()
    raw = _SOFT_PREFIX.sub("", raw)
    raw = _HEB_ASCII_HYPHEN.sub(" ", raw)
    raw = raw.replace("\u2014", ": ").replace("\u2013", ", ")
    raw = raw.replace(" — ", ": ").replace(" – ", ", ")
    raw = re.sub(r"חשבו לפי הכלל:\s*", "", raw)
    raw = re.sub(r":\s*:", ": ", raw)
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
    if not text:
        return False
    if _NON_PERSON_START.search(text):
        return False
    # ציטוט / משפט קצר — לא שם אדם
    if " " in text and re.search(r"(רצתי|הלכתי|אמר|הוא|היא|כתוב)", text):
        return False
    if _PERSON_ROLE.search(text):
        return True
    words = [w.strip(" «»\"'?.,") for w in text.split()]
    if any(p in text for p in _PERSON_PHRASES):
        return True
    if any(w in _PERSON_WORDS for w in words):
        return True
    if _NON_PERSON_LONG.search(text):
        return False
    if any(w in _NON_PERSON_WORDS for w in words):
        return False
    # בלי ניחוש על שני מילים אקראיות — רק שמות מוכרים / תפקידים
    return False


def fix_false_what_who(stem: str, question: dict[str, Any] | None = None) -> str:
    """«מהו ראשת הממשלה הראשונה?» → «מי הייתה…»."""
    text = strip_stem_junk(stem)
    match = _MAHU_ANY.match(text)
    if not match:
        return text
    body = match.group(2).strip(" «»\"'")
    if not _looks_like_person(body):
        return text
    feminine = (
        match.group(1) == "מהי"
        or bool(re.search(r"ראשת|נשיאה|מלכה|הראשונה|היחידה|שרה\b", body))
    )
    who = "מי הייתה" if feminine else "מי היה"
    return f"{who} {body}?"


def fix_bare_who(stem: str) -> str:
    """«מי גולדה מאיר?» → «מי הייתה גולדה מאיר?»."""
    text = strip_stem_junk(stem)
    match = _MI_BARE.match(text)
    if not match:
        return text
    body = match.group(1).strip(" «»\"'")
    if not body or not _looks_like_person(body):
        return text if text.endswith("?") else f"{text}?"
    feminine = bool(re.search(r"גולדה|ראשת|נשיאה|מלכה|סנש|שרה\b|הראשונה", body))
    who = "מי הייתה" if feminine else "מי היה"
    return f"{who} {body}?"


def clean_topic_label(topic: str) -> str:
    """מסיר «סבב C:» וכותרות יבוא מכוערות משורת המטא."""
    raw = strip_round_noise(str(topic or "").strip())
    raw = re.sub(r"(?:^|[\s־—\-–]+)[A-Za-z]\s*[:：]\s*", " ", raw)
    raw = re.sub(r"\s*\(\d+\)\s*", " ", raw)
    raw = re.sub(r"\s{2,}", " ", raw).strip(" —–-־·.")
    return raw or "תרגול"


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


_VAGUE_STEM = re.compile(
    r"^(?:"
    r"איזו אפשרות נכונה(?:\s+בנושא\s+.+?)?"
    r"|איזה משפט נכון"
    r"|מה נכון(?: כאן)?"
    r"|מה מתאים כאן"
    r"|איזו תשובה נכונה"
    r"|איזו אפשרות היא .+?"
    r")\s*\??$",
    re.I,
)

_ANSWER_TO_STEM: dict[str, str] = {
    "ניוטון": "מהי יחידת הכוח?",
    "ג׳אול": "מהי יחידת האנרגיה (או העבודה)?",
    "ג'אול": "מהי יחידת האנרגיה (או העבודה)?",
    "ואט": "מהי יחידת ההספק?",
    "וואט": "מהי יחידת ההספק?",
    "פסקל": "מהי יחידת הלחץ?",
    "פאסקל": "מהי יחידת הלחץ?",
    "קילוגרם": "מהי יחידת המסה במערכת SI?",
    "ק״ג": "מהי יחידת המסה במערכת SI?",
    "ק\"ג": "מהי יחידת המסה במערכת SI?",
    "אמפר": "מהי יחידת הזרם החשמלי?",
    "וולט": "מהי יחידת המתח?",
    "אוהם": "מהי יחידת ההתנגדות?",
    "אום": "מהי יחידת ההתנגדות?",
    "הרץ": "מהי יחידת התדירות?",
    "מטר": "מהי יחידת האורך במערכת SI?",
    "שנייה": "מהי יחידת הזמן במערכת SI?",
    "NaCl": "מהי הנוסחה הכימית של מלח בישול?",
    "H2O": "מהי הנוסחה הכימית של מים?",
    "CO2": "מהי הנוסחה הכימית של פחמן דו־חמצני?",
    "חומצי": "איך מסווגים תמיסה עם pH נמוך מ־7?",
    "בסיסי": "איך מסווגים תמיסה עם pH גבוה מ־7?",
    "ניטרלי": "איך מסווגים תמיסה עם pH שווה ל־7?",
    "הים התיכון": "איזה ים גובל בחוף המערבי של ישראל?",
    "ים סוף": "איזה ים נמצא בדרום ישראל (אילת)?",
    "הנגב": "מהו האזור הצחיח הגדול בדרום ישראל?",
    "מדבר יהודה ליד ים המלח": "היכן נמצא מדבר יהודה ביחס לים המלח?",
    "ירושלים": "מהי בירת מדינת ישראל?",
    "1917": "באיזו שנה פורסמה הצהרת בלפור?",
    "כ״ז בניסן": "מתי חל יום הזיכרון לשואה ולגבורה?",
    "כ\"ז בניסן": "מתי חל יום הזיכרון לשואה ולגבורה?",
    "צנחנית ומשוררת": "מי הייתה חנה סנש בעיקר?",
}


def is_vague_stem(stem: str) -> bool:
    """רק ניסוחים גנריים באמת — לא כל משפט קצר."""
    text = strip_stem_junk(stem)
    if _VAGUE_STEM.match(text) or _VAGUE.match(text):
        return True
    return False


def _correct_of(question: dict[str, Any] | None) -> str:
    q = question or {}
    correct = str(q.get("correct_answer") or "").strip()
    opts = [str(x) for x in (q.get("options") or [])]
    idx = q.get("answer")
    if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
        correct = opts[idx]
    return correct.strip()


def _expl_clue(explanation: str, correct: str) -> str:
    text = scrub_explanation(str(explanation or ""))
    text = re.sub(
        r"^התשובה הנכונה היא\s*[«\"'].*?[»\"']\s*[.．]?\s*",
        "",
        text,
        flags=re.I,
    ).strip()
    if correct and text.casefold().startswith(correct.casefold()):
        text = text[len(correct) :].lstrip(" .־-,:").strip()
    return text


def align_stem_to_answer(stem: str, question: dict[str, Any] | None = None) -> str:
    """כשהשאלה גנרית — בונים ניסוח שמתאים לתשובה/הסבר."""
    text = strip_stem_junk(stem)
    if not is_vague_stem(text):
        return text
    q = question or {}
    correct = _correct_of(q)
    for ans, ask in _ANSWER_TO_STEM.items():
        if correct.casefold() == ans.casefold():
            return ask
    clue = _expl_clue(str(q.get("explanation") or ""), correct)
    clue_l = clue.casefold()
    if clue in {"<7", "< 7"}:
        return "איך מסווגים תמיסה עם pH נמוך מ־7?"
    if clue in {">7", "> 7"}:
        return "איך מסווגים תמיסה עם pH גבוה מ־7?"
    if clue.strip() == "7":
        return "איך מסווגים תמיסה עם pH שווה ל־7?"
    if "x²" in clue or "x^2" in clue_l:
        return f"מה הפתרונות של {clue.split()[0]}?"
    if "פירוק" in clue or "(x" in clue:
        return f"מה השורשים לפי הפירוק: {clue}?" if clue else "מה השורשים של המשוואה הריבועית?"
    unit_map = {
        "n": "מהי יחידת הכוח?",
        "j": "מהי יחידת האנרגיה (או העבודה)?",
        "w": "מהי יחידת ההספק?",
        "pa": "מהי יחידת הלחץ?",
        "hz": "מהי יחידת התדירות?",
    }
    if clue_l in unit_map:
        return unit_map[clue_l]
    if clue in {"מערב", "מזרח", "צפון", "דרום"} and correct:
        return f"מה נמצא ב{clue} של ישראל לפי השיעור?"
    if re.search(r"\d+\s*j\b", correct.casefold()) or correct.endswith("J"):
        return "מה התוצאה הנכונה בחישוב, ביחידות ג׳אול?"
    if correct.endswith(".") and len(correct.split()) >= 2:
        return "איזה משפט חיווי כתוב נכון (עם נקודה בסוף)?"
    if correct.endswith("?") and len(correct.split()) >= 2:
        return "איזו שאלה כתובה נכון (עם סימן שאלה)?"
    hint = str(q.get("hint") or "")
    if "בלפור" in hint or "בלפור" in clue:
        return "באיזו שנה פורסמה הצהרת בלפור?"
    if "שואה" in hint or "שואה" in clue:
        if "ניסן" in correct:
            return "מתי חל יום הזיכרון לשואה ולגבורה?"
        if "צנח" in correct or "משורר" in correct:
            return "מי הייתה חנה סנש בעיקר?"
    if correct and len(correct) <= 48:
        topic = clean_topic_label(str(q.get("topic") or ""))
        if topic and topic not in {"תרגול", "פיזיקה", "כימיה", "היסטוריה", "גאוגרפיה", "מתמטיקה", "עברית", "אנגלית"}:
            return f"מה התשובה המדויקת בנושא «{topic}»?"
        return "מה מהאפשרויות מתאים להגדרה בשיעור?"
    topic = clean_topic_label(str(q.get("topic") or "").strip())
    if topic and topic != "תרגול":
        return f"מה הערך או המשפט הנכון בנושא «{topic}»?"
    return "מה התשובה הנכונה לפי השיעור?"


def fix_vague(stem: str, question: dict[str, Any] | None = None) -> str:
    text = strip_stem_junk(stem)
    if is_vague_stem(text):
        return align_stem_to_answer(text, question)
    return text


def polish_stem(stem: str, question: dict[str, Any] | None = None) -> str:
    """סדר ניקוי אחד לכל שאלה לפני תצוגה או שמירה."""
    text = strip_stem_junk(stem)
    text = expand_known_stems(text)
    text = fix_mangled_phrasing(text, question)
    text = fix_false_what_who(text, question)
    text = fix_false_who(text, question)
    text = fix_bare_who(text)
    text = expand_short_formula(text)
    text = fix_role_is_mainly(text)
    text = fix_bare_topic_question(text)
    text = fix_vague(text, question)
    text = clean_student_text(text)
    if text and not text.endswith(("?", "!", ".")):
        if re.match(
            r"^(?:מה|מי|מתי|כמה|איזה|איזו|השלימו|למה|היכן|ליד|בחרו|כתבו)",
            text,
        ):
            text = f"{text}?"
        elif re.search(r"(המהירות|התאוצה|הכוח|שווה)$", text):
            text = f"{text}?"
    return text.strip()


def fix_mangled_phrasing(stem: str, question: dict[str, Any] | None = None) -> str:
    """מתקן ניסוחים שבורים נפוצים מהמאגר."""
    text = strip_stem_junk(stem)
    q = question or {}

    m = _PCT_SHAVE.match(text)
    if m:
        return f"כמה הם {m.group(1)}% מ־{m.group(2)}?"

    m = _SHEERIT.match(text)
    if m:
        return f"מה השארית ב־{m.group(1).strip()}?"

    m = _ATOMIC_NUM.match(text)
    if m:
        return f"מהו המספר האטומי של {m.group(1).strip()}?"

    m = _MAHI_MASC.match(text)
    if m:
        return f"מהו {m.group(1)}{m.group(2)}".rstrip("?") + "?"

    m = _OZER_KI.match(text)
    if m:
        thing = m.group(1).strip()
        feminine = bool(re.search(r"(^|\s)(מפה|מנורה|סוללה|זכוכית)\b", thing))
        verb = "עוזרת" if feminine else "עוזר"
        return f"למה {thing} {verb}?"

    m = _NIMTZA.match(text)
    if m:
        thing = m.group(1).strip()
        where = (m.group(2) or "").strip()
        plural = bool(re.search(r"(ים|ות)$", thing)) or "אלקטרונים" in thing
        loc_verb = "נמצאים" if plural else "נמצא"
        if "ליד" in where or where.startswith("בטבלה"):
            return f"ליד מה נמצא {thing} בטבלה המחזורית?"
        if where:
            return f"היכן {loc_verb} {thing} {where}?"
        return f"היכן {loc_verb} {thing}?"

    m = _SERIES_NEXT.match(text)
    if m:
        return f"מה האיבר הבא בסדרה: {m.group(1).strip()}, ...?"

    m = _TRAIL_SPEED.match(text)
    if m and not re.match(r"^(?:מה|כמה)\b", text):
        body = m.group(1).strip().rstrip(".")
        if body:
            return f"{body}. מה המהירות?"

    m = _TRAIL_SHAVE.match(text)
    if m and not re.match(r"^(?:מה|כמה|מהו|מהי)\b", text):
        body = m.group(1).strip()
        return f"כמה שווה: {body}?"

    m = _UNIT_SHAVE.match(text)
    if m and "%" not in text:
        return f"לכמה שווה {m.group(1).strip()}?"

    # «מהו במשולש שווה־צלעות כל זווית?»
    m = re.match(r"^(?:מהו|מהי)\s+ב(משולש\s+שווה[־\-]צלעות)\s+כל\s+זווית\s*\??$", text)
    if m:
        return f"מה גודל כל זווית ב{m.group(1)}?"

    # משפט עובדתי בלי סימן שאלה — הופכים לשאלה כשיש תשובה במאגר
    if (
        not text.endswith("?")
        and 12 <= len(text) <= 90
        and not re.match(r"^(?:מה|מי|מתי|כמה|איזה|איזו|השלימו|למה|בחרו|כתבו|היכן)", text)
        and str(q.get("correct_answer") or "").strip()
    ):
        if re.search(r"(היא לרוב|מציינת|שואלת|זו שאלת)$", text) or text.endswith(
            ("לרוב", "מציינת", "שואלת")
        ):
            return f"מה מתאים להשלים: {text}?"

    return text


# מושגים קצרים במאגר שצריך להרחיב לשאלה מלאה
_KNOWN_STEMS = {
    "מהו היישוב": "מהו «היישוב» היהודי בארץ ישראל לפני קום המדינה?",
    "מהו היישוב?": "מהו «היישוב» היהודי בארץ ישראל לפני קום המדינה?",
    "מנורת המדינה": "מה מייצגת מנורת המדינה בסמל ישראל?",
    "מנורת המדינה?": "מה מייצגת מנורת המדינה בסמל ישראל?",
    "שביתות נשק אחרי העצמאות": "באיזו שנה נחתמו הסכמי שביתת הנשק אחרי העצמאות?",
    "שביתות נשק אחרי העצמאות?": "באיזו שנה נחתמו הסכמי שביתת הנשק אחרי העצמאות?",
    "מהו מבחנה שוברים אז": "מה עושים כשמבחנה נשברת במעבדה?",
    "מהו מבחנה שוברים אז?": "מה עושים כשמבחנה נשברת במעבדה?",
    "מהי עיניים": "מה כלל הבטיחות לגבי הגנה על העיניים במעבדה?",
    "מהי עיניים?": "מה כלל הבטיחות לגבי הגנה על העיניים במעבדה?",
    "מהי חלקיק חיובי בגרעין": "מהו החלקיק החיובי בגרעין האטום?",
    "מהי חלקיק חיובי בגרעין?": "מהו החלקיק החיובי בגרעין האטום?",
    "מהו חלקיק בלי מטען בגרעין": "מהו החלקיק בלי מטען בגרעין האטום?",
    "מהו חלקיק בלי מטען בגרעין?": "מהו החלקיק בלי מטען בגרעין האטום?",
}


def expand_known_stems(stem: str) -> str:
    text = strip_stem_junk(stem)
    return _KNOWN_STEMS.get(text, text)


def fix_role_is_mainly(stem: str) -> str:
    """«מהו נשיא המדינה הוא בעיקר?» → «מהו תפקיד נשיא המדינה בעיקר?»."""
    text = strip_stem_junk(stem)
    match = re.match(r"^(מהו|מהי)\s+(.+?)\s+הוא\s+בעיקר\s*\??$", text)
    if not match:
        return text
    role = match.group(2).strip(" «»\"'")
    if not role:
        return text
    return f"מהו תפקיד {role} בעיקר?"


def fix_bare_topic_question(stem: str) -> str:
    """«תוכנית בילטמור?» / «מנורת המדינה?» → שאלה עם פועל שאלה."""
    text = strip_stem_junk(stem)
    if re.match(r"^(?:מה|מי|מתי|כמה|איזה|איזו|השלימו|למה|באיזה|באיזו|מעגל|חשבו|בחרו)", text):
        # «מהו X?» קצר מדי כש־X מילה אחת
        m = re.match(r"^(מהו|מהי)\s+(.{1,18})\s*\?$", text)
        if m and " " not in m.group(2).strip():
            word = m.group(2).strip(" «»\"'")
            if word:
                return f"מה משמעות המושג «{word}»?"
        return text
    # כבר יש שאלת־משנה בתוך המשפט
    if re.search(r"(?:מה|מי|מתי|כמה|איזה|איזו)\s+", text):
        return text if text.endswith("?") else f"{text}?"
    if text.endswith("?") and 4 <= len(text) <= 48:
        body = text.rstrip("?").strip()
        if re.search(r"(תוכנית|הצהר|החלט|חוק|מלחמ|עלייה|קונגרס|מנורה|סמל|דגל|הסכם|שבית)", body):
            return f"מהי {body}?" if not body.startswith("ה") else f"מהו {body}?"
        if " " in body and len(body) <= 28 and not re.search(r"\d", body):
            return f"למה קשור/ה: {body}?"
    return text
