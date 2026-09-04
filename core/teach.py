"""הוראה מתוך החומר הקיים: הסבר, רמז וטעות נפוצה לפי נושא."""
from __future__ import annotations

import re
from typing import Any

from core.config import subject_key, subject_label
from core.theory_library import DEPTH, VOICE

_SYN_QUOTED = re.compile(
    r"^(?:מילה\s+)?נרדפת(?:\s+קרובה)?\s+ל\s*[«\"']([^»\"']+)[»\"']\s*(.*)$"
)
_SYN_BARE = re.compile(r"^(?:מילה\s+)?נרדפת(?:\s+קרובה)?\s+ל(\S+)\s*$")
_ANT = re.compile(
    r"^(?:ה)?(?:ניגוד|הפך)\s+של\s*[«\"']?(.+?)[»\"']?\s*$"
)
_ROOT_FORM = re.compile(r"^שורש\s+(\S+)\s+ב(עבר|הווה|עתיד)\s*(?:\(([^)]+)\))?\s*$")
_HE_COPULA = re.compile(r"^(.{2,48}?)\s+(הוא|היא|הם|הן)\s*\??$")
_CHOOSE_EN = re.compile(r"^Choose\s+(.+)$", re.I)
_MATH_ONLY = re.compile(r"^[\d\s+\-×xX*/÷=().]+$")
_EN_SHORT = re.compile(r"^[A-Za-z][A-Za-z0-9 '!?.,:]{0,48}$")
_HEB = re.compile(r"[\u0590-\u05FF]")
# גבול מילה אחרי מי/מה, כדי לא לפספס «מים» / «מהיר» / «מילת».
_ALREADY_ASK = re.compile(
    r"^(?:מה(?:ו|י|ם|ן)?|מי|איזה|איזו|מתי|כמה|איפה|למה|בחרו|כתבו|השלימו|קראו)(?:\s|$|\?)"
)
_GENERIC_PREFIX = "מה מתאים כאן:"
_COPULA_WORD = {"הוא": "מהו", "היא": "מהי", "הם": "מהם", "הן": "מהן"}
_PCT = re.compile(
    r"^(\d+(?:[.,]\d+)?)\s*%\s*מ[־\-]?\s*(\d+(?:[.,]\d+)?)\s*(?:הם|הן|הוא)?\s*\??$"
)
_INVERTED_COP = re.compile(r"^מה (.+?) (הוא|היא|הם|הן)\s*\??$")
_ZEH = re.compile(r"^(.+?)\s+זה\s*\??$")
_USES = re.compile(r"^(.+?)\s+(משמש(?:ות|ים)?)\s+ל\s*(.*?)\s*\??$")
_ROOT_OF = re.compile(r"^שורש של\s*[«\"']?(.+?)[»\"']?\s*\??$")
_GERUND = re.compile(r"^שם פעולה של\s*[«\"']?(.+?)[»\"']?\s*\??$")
_EN_PAST = re.compile(r"^The past of\s+(\S+)\s+is\s*$", re.I)
_EN_OPP = re.compile(r"^The opposite of\s+(.+?)\s+is\s*$", re.I)
_EN_SYN = re.compile(r"^A synonym of\s+(.+?)\s+is\s*$", re.I)
_SIGN = re.compile(r"^[«\"']([^»\"']+)[»\"']\s*\??$")
_ASKS = re.compile(r"^(.+?)\s+שואל\s*\??$")
_MEANS = re.compile(r"^(.+?)\s+(?:פירושו|פירושה|משמע|משמעו)\s*\??$")
_SAYS = re.compile(r"^(.+?)\s+אומר(?:ת)?(?:\s+למורה)?\s*\??$")
_CLOSE_HE = re.compile(r"^(.+?)\s+קרוב למילה העברית\s*\??$")
_ROLE_IN = re.compile(r"^(פועל|לוואי|נשוא|נושא|מושא|פסוקית זיקה)\s+(ב.*)$")
_WAS = re.compile(r"^(.+?)\s+(היה|הייתה|היו)\s*\??$")
_PLURAL_OF = re.compile(r"^(?:מה\s+)?רבים של\s*[«\"']?(.+?)[»\"']?\s*\??$")
_BELONGS = re.compile(r"^(.+?)\s+(שייכת|קשורה|קשור)\s+ל\s*\??$")
_EQ_EN = re.compile(r"^([A-Za-z][A-Za-z '\-]{1,40})\s*=\s*$")
_BAD_MAHU = re.compile(r"^מהו\s+(.+?)\s*\??$")
_BAD_MA_WAS = re.compile(r"^מה\s+(.+?)\s+(היה|הייתה|היו)\s*\??$")
_BAD_MA_INF = re.compile(r"^מה\s+(ל[א-ת][\u0590-\u05FF].*?)\s*\??$")
_TENSE_HINT = re.compile(r"(אתמול|מחר|עכשיו|היום|תמיד)")
_IMP_HINT = re.compile(r"^אל\s+")

GENERIC_HINTS = {
    "קראו שוב את השאלה. מה בדיוק מבקשים למצוא?",
    "כבר טעית כאן פעם. קראו לאט.",
    "כבר טעית כאן. קראו לאט ובדקו מה נשאל.",
    "חזרו לקטע. התשובה כתובה שם או נובעת ממנו.",
}


def first_sentence(text: str, limit: int = 160) -> str:
    blob = " ".join(str(text or "").split())
    if not blob:
        return ""
    for sep in (". ", "? ", "! "):
        if sep in blob:
            cut = blob.split(sep, 1)[0].strip()
            if cut:
                return cut + sep.strip()
    return blob[:limit].rstrip(" ,;") + ("…" if len(blob) > limit else "")


def match_depth(subject: str, blob: str) -> str:
    """בוחר את מאמר העומק שהכי מתאים לכותרת ולנושא."""
    text = str(blob or "")
    if not text:
        return ""
    lowered = text.lower()
    best = ""
    best_score = 0
    for keywords, essay in DEPTH.get(subject_key(subject), ()) or []:
        score = 0
        for word in keywords:
            token = str(word or "").strip()
            if not token:
                continue
            if token in text:
                score += 3 if len(token) >= 4 else 2
            elif token.lower() in lowered:
                score += 2 if len(token) >= 4 else 1
        if score > best_score:
            best_score = score
            best = essay
    return best if best_score else ""


def teaching(subject: str, topic: str = "", extra: str = "") -> dict[str, str]:
    key = subject_key(subject)
    name = subject_label(key)
    topic_clean = str(topic or "").replace(f"{key}_", "").strip() or name
    voice = VOICE.get(key) or VOICE.get("_default") or {}
    depth = match_depth(key, f"{topic_clean} {extra}")
    ctx = {"topic": topic_clean, "subject": name}

    def _fmt(field: str, fallback: str) -> str:
        raw = str(voice.get(field) or fallback)
        try:
            return raw.format(**ctx)
        except (KeyError, ValueError):
            return raw

    return {
        "subject": key,
        "topic": topic_clean,
        "depth": depth,
        "rule": first_sentence(depth),
        "why": _fmt("why", "הנושא הזה חוזר במבחן. מי שמבין אותו לא צריך לנחש."),
        "how": _fmt("how", "קראו פעם אחת, סמנו מילה אחת, ואז תרגלו לאט."),
        "mistakes": _fmt("mistakes", "הטעות השכיחה: קוראים חצי שאלה ובוחרים מילה מוכרת."),
        "recap": _fmt("recap", "אמרו בקול משפט אחד, ואז ענו על שלוש שאלות."),
    }


def enrich_explanation(
    correct: str,
    explanation: str,
    topic: str = "",
    subject: str = "",
) -> str:
    """משלים הסבר קצר בהוראה אמיתית מהנושא, בלי מלל גנרי."""
    from core.stem_fix import clean_student_text

    exp = clean_student_text(explanation)
    answer = str(correct or "").strip()
    guide = teaching(subject, topic, extra=exp)
    rule = clean_student_text(guide.get("rule") or "")
    how = clean_student_text((guide.get("how") or "").split("\n", 1)[0])
    mistake = clean_student_text(guide.get("mistakes") or "")

    # מסירים שאריות גנריות שחוזרות על עצמן במאגר
    for junk in (
        "סיבה, אירוע, תוצאה. אחר כך התאריך של משפט נכון בהיסטוריה, ניסוח עדין בהיסטוריה.",
        "סיבה, אירוע, תוצאה.",
        "ניסוח עדין בהיסטוריה.",
        "משפט נכון בהיסטוריה,",
    ):
        exp = exp.replace(junk, " ").strip()
    exp = re.sub(r"\s{2,}", " ", exp).strip(" .")

    parts: list[str] = []
    if answer and answer not in exp[:120]:
        parts.append(f"התשובה הנכונה היא «{answer}».")
    if exp:
        parts.append(exp)
    elif rule:
        parts.append(rule)
    if how and how[:20] not in " ".join(parts):
        parts.append(f"איך לחשוב: {how}")
    if mistake and mistake[:20] not in " ".join(parts) and len(" ".join(parts)) < 120:
        parts.append(f"טעות נפוצה: {mistake}")
    text = " ".join(parts).strip()
    return text or "קראו שוב את השאלה, סמנו מילה אחת חשובה, ואז בחרו."


def teach_after_answer(
    question: dict[str, Any] | None,
    *,
    is_correct: bool,
    subject: str = "",
) -> dict[str, str]:
    """בלוקים ברורים אחרי תשובה: למה, איך לחשוב, ומה להיזהר."""
    from core.stem_fix import clean_student_text

    q = question or {}
    opts = q.get("options") or []
    idx = q.get("answer")
    correct = str(q.get("correct_answer") or "").strip()
    if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
        correct = str(opts[idx])
    subj = subject_key(subject or q.get("subject") or "")
    topic = str(q.get("topic") or "")
    stem = str(q.get("question") or "")
    guide = teaching(subj, topic, extra=stem)
    keep_ctx = f"{stem} {correct} {topic}"
    body = clean_student_text(q.get("explanation") or "", keep_years_from=keep_ctx)
    for junk in (
        "סיבה, אירוע, תוצאה. אחר כך התאריך של משפט נכון בהיסטוריה, ניסוח עדין בהיסטוריה.",
        "סיבה, אירוע, תוצאה.",
        "ניסוח עדין בהיסטוריה.",
    ):
        body = body.replace(junk, " ")
    body = re.sub(r"\s{2,}", " ", body).strip(" .")

    why_parts: list[str] = []
    if correct:
        why_parts.append(f"התשובה הנכונה: «{correct}».")
    if body:
        # אם ההסבר רק חוזר על התשובה — מוסיפים כלל מהנושא
        if correct and correct in body and len(body) < len(correct) + 28:
            rule = clean_student_text(guide.get("rule") or "", keep_years_from=keep_ctx)
            why_parts.append(body)
            if rule and rule[:20] not in body:
                why_parts.append(rule)
        else:
            why_parts.append(body)
    else:
        rule = clean_student_text(guide.get("rule") or "", keep_years_from=keep_ctx)
        if rule:
            why_parts.append(rule)
        elif topic:
            why_parts.append(f"זה שייך לנושא «{topic}».")

    how = _how_to_think(subj, topic=topic, stem=stem, correct=correct, guide=guide)
    watch = _watch_tip(subj, guide=guide, is_correct=is_correct, correct=correct)
    picture = _picture_tip(q, correct=correct, topic=topic)

    return {
        "status": "נכון. כל הכבוד." if is_correct else "לא מדויק. קוראים לאט וממשיכים.",
        "why": " ".join(why_parts).strip(),
        "how": how,
        "watch": watch,
        "picture": picture,
    }


_THINK: dict[str, str] = {
    "history": (
        "חשבו בשרשרת: מי פעל, באיזו תקופה, ומה השתנה אחרי כן. "
        "אם מופיעה שנה, בדקו שהיא מתאימה לאירוע ולא למושג כללי."
    ),
    "civics": (
        "הגדירו את המושג במשפט, ואז שאלו איזו רשות או זכות קשורה בישראל. "
        "אל תערבבו כנסת עם ממשלה."
    ),
    "geography": (
        "שימו את המקום במפה בראש: אקלים, משאב, והשפעה על אנשים. "
        "שם בלי הקשר כמעט תמיד מסיח."
    ),
    "physics": (
        "כתבו מה נתון ומה מחפשים, בדקו יחידות וכיוון, ורק אז בחרו נוסחה. "
        "מילה מוכרת בשאלה אינה התשובה."
    ),
    "chemistry": (
        "שאלו מה היחידה (אטום, מולקולה, יון), מה משתנה ומה נשמר. "
        "אחר כך חברו לדוגמה מהמטבח או מהמעבדה."
    ),
    "math": (
        "רשמו נתון ומבוקש, בחרו פעולה אחת, ובדקו אם התוצאה הגיונית. "
        "אחוז ומספר אינם אותו דבר."
    ),
    "hebrew": (
        "קראו את המשפט בקול, סמנו את המילה הקובעת, ורק אז בחרו. "
        "צליל דומה אינו כתיב נכון."
    ),
    "english": (
        "סמנו רמז זמן או מבנה במשפט באנגלית, בלי לתרגם מילה־מילה. "
        "yesterday לא הולך עם present פשוט."
    ),
    "biology": (
        "שאלו מה התהליך בגוף או בתא, ומה התוצאה. "
        "שם של איבר בלי תפקיד הוא מסיח."
    ),
    "arabic": (
        "הבדילו שורש מצורה, ואז קראו את המשפט בקול לפני הבחירה."
    ),
    "first_aid": (
        "סדר פעולה: בטיחות, בדיקת הכרה, קריאה לעזרה, ואז טיפול לפי ההנחיה. "
        "לא ממציאים תרופות."
    ),
}


def _how_to_think(
    subject: str,
    *,
    topic: str,
    stem: str,
    correct: str,
    guide: dict[str, str],
) -> str:
    from core.stem_fix import clean_student_text

    base = _THINK.get(subject) or (
        "קראו פעם אחת בלי לענות, סמנו מילה אחת חשובה, ורק אז בחרו."
    )
    # דוגמה קצרה מהשאלה עצמה — השראה לתלמיד
    example = ""
    if correct and stem:
        short_stem = first_sentence(stem, limit=72).rstrip("?.!")
        example = f" כאן: בשאלה על «{short_stem}» מחפשים משהו כמו «{correct}»."
    elif correct:
        example = f" שמרו דוגמה: «{correct}»."
    # משלבים לכל היותר משפט שיטה אחד מהמדריך, בלי מספור
    steps = [ln.strip(" .") for ln in str(guide.get("how") or "").split("\n") if ln.strip()]
    steps = [re.sub(r"^\d+\.\s*", "", s) for s in steps]
    tip = clean_student_text(steps[0]) if steps else ""
    if tip and (len(tip) < 12 or tip[:24] in base):
        tip = ""
    parts = [base]
    if tip:
        parts.append(tip)
    if example:
        parts.append(example.strip())
    text = ". ".join(p.strip(" .") for p in parts if p).strip()
    if text and not text.endswith((".", "?", "!")):
        text += "."
    return clean_student_text(text)


def _watch_tip(
    subject: str,
    *,
    guide: dict[str, str],
    is_correct: bool,
    correct: str,
) -> str:
    from core.stem_fix import clean_student_text

    mistakes = clean_student_text(guide.get("mistakes") or "")
    recap = clean_student_text(guide.get("recap") or "")
    if not is_correct:
        parts = [p for p in (mistakes, recap) if p]
        return " ".join(parts).strip()
    # גם אחרי תשובה נכונה: משפט לקיחה הביתה
    if recap:
        return recap
    if correct:
        return f"חזרו בקול על «{correct}» פעם אחת, כדי שהרעיון יישאר גם בלי האפשרויות."
    return mistakes


def _picture_tip(question: dict[str, Any], *, correct: str, topic: str) -> str:
    from core.stem_fix import clean_student_text

    try:
        from core.illustrations.schema import get_visual

        visual = get_visual(question)
    except Exception:
        visual = None
    if not visual:
        return ""
    title = clean_student_text(visual.get("title") or topic or "המחשה")
    cap = clean_student_text(
        visual.get("reveal_note") or visual.get("caption") or ""
    )
    if correct and cap:
        return (
            f"האיור «{title}»: {cap} "
            f"אמרו בקול משפט שמחבר את התמונה לתשובה «{correct}». כך זוכרים גם בלי לראות שוב."
        )
    if cap:
        return (
            f"האיור «{title}»: {cap} "
            "השתמשו בו כעוגן זיכרון, לא במקום לקרוא את השאלה."
        )
    return (
        f"האיור «{title}» מזכיר את הרעיון המרכזי. "
        "תארו בקול מה רואים, ואז חברו לתשובה."
    )


def display_explanation(question: dict[str, Any] | None, subject: str = "") -> str:
    blocks = teach_after_answer(question, is_correct=True, subject=subject)
    parts = [blocks.get("why") or ""]
    if blocks.get("how"):
        parts.append(f"איך לחשוב: {blocks['how']}")
    return " ".join(p for p in parts if p).strip()


def live_hint(question: dict[str, Any] | None, subject: str = "") -> str:
    q = question or {}
    existing = str(q.get("hint") or "").strip()
    if existing and existing not in GENERIC_HINTS:
        from core.stem_fix import clean_student_text

        return clean_student_text(existing)
    guide = teaching(subject or q.get("subject") or "", q.get("topic") or "", extra=q.get("question") or "")
    if guide.get("rule"):
        from core.stem_fix import clean_student_text

        return f"כלל קצר: {clean_student_text(guide['rule'])}"
    how = str(guide.get("how") or "")
    first_how = how.split("\n", 1)[0].strip()
    from core.stem_fix import clean_student_text

    return clean_student_text(first_how) or existing or "קראו את כל השאלה, ואז פסלו מה שלא מתאים."


def feedback_note(question: dict[str, Any] | None, *, correct: bool, subject: str = "") -> str:
    """שורה אחת אחרי תשובה: טעות נפוצה אם שגו, כלל קצר אם נכון."""
    blocks = teach_after_answer(question, is_correct=correct, subject=subject)
    if correct:
        return blocks.get("how") or ""
    return blocks.get("watch") or blocks.get("how") or ""


_QUOTE_MARKS = " «»\"'"


def _clean_word(text: str) -> str:
    return str(text or "").strip().strip(_QUOTE_MARKS)


def _unwrap_weak_stem(stem: str) -> str:
    """מסיר ניסוח גנרי או הפוך ישן כדי שאפשר יהיה לנסח מחדש."""
    text = stem.strip()
    if text.startswith(_GENERIC_PREFIX):
        text = text[len(_GENERIC_PREFIX):].strip()
    inverted_pct = re.match(
        r"^מה\s+(\d+(?:[.,]\d+)?)\s*%\s*מ[־\-]?\s*(\d+(?:[.,]\d+)?)\s+הם\s*\??$",
        text,
    )
    if inverted_pct:
        return f"{inverted_pct.group(1)}% מ־{inverted_pct.group(2)} הם"
    bad_was = _BAD_MA_WAS.match(text)
    if bad_was:
        return f"{bad_was.group(1)} {bad_was.group(2)}"
    bad_inf = _BAD_MA_INF.match(text)
    if bad_inf:
        return bad_inf.group(1)
    if text.startswith("מה רבים של "):
        return text.removeprefix("מה ").rstrip("?").strip()
    if text.startswith("מה לוואי מתאר"):
        return "לוואי מתאר"
    if text.startswith((
        "מהו חלקי הדיבר", "באיזה זמן ", "מה צורת ", "מה המשמעות של ",
        "כמה הם ", "את מה מתאר", "מה היה ", "מה הייתה ", "מה היו ",
        "מה פירוש ", "מי היה ", "לאיזה שורש ", "איזו מילה ",
    )):
        return text
    mahu = _BAD_MAHU.match(text)
    if mahu:
        body = mahu.group(1).strip(" «»\"'")
        if _TENSE_HINT.search(body) or _IMP_HINT.match(body):
            return f"'{body}' הוא"
    inverted = _INVERTED_COP.match(text)
    if (
        inverted
        and not text.startswith(("מהו ", "מהי ", "מהם ", "מהן "))
        and "." not in inverted.group(1)
        and len(inverted.group(1)) <= 48
    ):
        return f"{inverted.group(1)} {inverted.group(2)}"
    return text


def _copula_question(noun: str, verb: str) -> str:
    """«X הוא» — זמן / ציווי / חלקי דיבר / הגדרה."""
    clean = _clean_word(noun)
    if _IMP_HINT.match(clean):
        return f"מה צורת הציווי במשפט «{clean}»?"
    if _TENSE_HINT.search(clean):
        return f"באיזה זמן כתוב «{clean}»?"
    if len(clean.split()) == 1 and _HEB.search(clean):
        return f"מהו חלקי הדיבר של «{clean}»?"
    prefix = _COPULA_WORD.get(verb, "מהו")
    return f"{prefix} {clean}?"


def _as_question(stem: str) -> str:
    text = stem.strip().rstrip("?").strip()
    if not text:
        return stem
    if _ALREADY_ASK.match(text + " "):
        return text if text.endswith("?") else f"{text}?"
    if re.search(r"(?:\s|^)(ל|ב|עם|של|מ|כ)$", text):
        return f"השלימו: {text} ____"
    if re.search(r"(נכון|נכונה|תקין|תקינה|תקין יותר)$", text):
        return f"איזו אפשרות היא {text}?"
    if re.match(r"^(משפט|ציטוט|רשימה|ציווי)\b", text):
        return f"איזה {text}?"
    if text.startswith(("בירת ", "יחידת ")):
        return f"מהי {text}?"
    if text.startswith("ל") and len(text) >= 5 and " " in text and _HEB.search(text):
        return f"מה פירוש «{text}»?"
    if re.match(r"^(הקמת|מלחמת|הצהרת)\b", text):
        return f"מה הייתה {text}?"
    if text.startswith("הסכמי ") or text.startswith("רצח "):
        return f"מה היו {text}?"
    if text.startswith("קונגרס "):
        return f"מה היה {text}?"
    # שני שמות פרטיים/משפחה בלי פועל — לרוב דמות בהיסטוריה.
    words = text.split()
    if len(words) == 2 and all(_HEB.search(w) and len(w) >= 2 for w in words):
        if not any(w in {"של", "את", "על", "עם", "מן", "אל"} for w in words):
            from core.stem_fix import _looks_like_person

            if _looks_like_person(text):
                return f"מי היה {text}?"
            return f"מהו {text}?"
    if len(words) <= 4 and _HEB.search(text):
        if text.endswith(("ה", "ת", "ות", "ים", "ין")) and len(words) <= 3:
            return f"מהי {text}?"
        return f"מהו {text}?"
    return text


def _rewrite_stem(stem: str) -> str:
    quoted = _SYN_QUOTED.match(stem)
    if quoted:
        word = quoted.group(1).strip(" «»\"'")
        extra = quoted.group(2).strip()
        line = f"איזו מילה קרובה במשמעות ל«{word}»?"
        return f"{line} {extra}".strip() if extra else line
    bare = _SYN_BARE.match(stem)
    if bare:
        word = bare.group(1).strip(" «»\"'")
        return f"איזו מילה קרובה במשמעות ל«{word}»?"
    antonym = _ANT.match(stem)
    if antonym:
        word = antonym.group(1).strip(" «»\"'")
        return f"איזו מילה הפוכה במשמעות ל«{word}»?"
    root = _ROOT_FORM.match(stem)
    if root:
        when = root.group(2)
        who = root.group(3) or "יחיד"
        return f"מה צורת ה{when} ({who}) של השורש {root.group(1)}?"
    pct = _PCT.match(stem)
    if pct:
        return f"כמה הם {pct.group(1)}% מ־{pct.group(2)}?"
    plural = _PLURAL_OF.match(stem)
    if plural:
        return f"מה צורת הרבים של «{_clean_word(plural.group(1))}»?"
    if re.match(r"^לוואי מתאר\s*\??$", stem):
        return "את מה מתאר הלוואי במשפט?"
    was = _WAS.match(stem)
    if was and not _ALREADY_ASK.match(stem):
        noun = was.group(1).strip(" «»\"'")
        verb = was.group(2)
        if verb == "היו":
            return f"מה היו {noun}?"
        return f"מה {verb} {noun}?"
    belongs = _BELONGS.match(stem)
    if belongs:
        return f"לאיזה שורש {belongs.group(2)} «{_clean_word(belongs.group(1))}»?"
    eq_en = _EQ_EN.match(stem)
    if eq_en:
        return f"מה המשמעות של «{eq_en.group(1).strip()}» באנגלית?"
    zeh = _ZEH.match(stem)
    if zeh:
        body = zeh.group(1).strip(" «»\"'")
        words = body.split()
        if "." in body or "!" in body or len(words) >= 7:
            return f"מה הקשר או המסקנה מהמשפט: {body}?"
        return f"מה המשמעות של «{body}»?"
    uses = _USES.match(stem)
    if uses:
        noun = uses.group(1).strip()
        verb = uses.group(2)
        extra = re.sub(r"\s*כי\s*$", "", uses.group(3) or "").strip(" ?")
        line = f"למה {verb} {noun}"
        if extra:
            line += f" ל{extra}" if not extra.startswith("ל") else f" {extra}"
        return f"{line}?"
    root_of = _ROOT_OF.match(stem)
    if root_of:
        return f"מה השורש של «{_clean_word(root_of.group(1))}»?"
    gerund = _GERUND.match(stem)
    if gerund:
        return f"מה שם הפעולה של «{_clean_word(gerund.group(1))}»?"
    sign = _SIGN.match(stem)
    if sign:
        return f"מה משמעות השלט או המשפט: «{sign.group(1).strip()}»?"
    asks = _ASKS.match(stem)
    if asks:
        return f"מה שואלת המילה או הביטוי «{asks.group(1).strip()}»?"
    means = _MEANS.match(stem)
    if means:
        return f"מה פירוש «{means.group(1).strip()}»?"
    says = _SAYS.match(stem)
    if says:
        return f"מה אומר הביטוי «{says.group(1).strip()}»?"
    close_he = _CLOSE_HE.match(stem)
    if close_he:
        return f"לאיזו מילה עברית קרוב «{close_he.group(1).strip()}»?"
    role = _ROLE_IN.match(stem)
    if role:
        return f"מהו ה{role.group(1)} {role.group(2).rstrip('?')}?"
    if " כמו " in stem and re.search(r"\sל\s*\??$", stem):
        return f"השלימו את האנלוגיה: {stem.rstrip('?').strip()} ____"
    choose = _CHOOSE_EN.match(stem)
    if choose:
        rest = choose.group(1).strip(" :.")
        return f"בחרו באנגלית: {rest}" if rest else "בחרו את הצורה או את המשפט התקינים באנגלית."
    past = _EN_PAST.match(stem)
    if past:
        return f"מה צורת העבר של {past.group(1)}?"
    opp = _EN_OPP.match(stem)
    if opp:
        return f"מה ההפך באנגלית של {opp.group(1).strip()}?"
    syn = _EN_SYN.match(stem)
    if syn:
        return f"איזו מילה קרובה במשמעות ל־{syn.group(1).strip()}?"
    if _MATH_ONLY.match(stem) and any(ch.isdigit() for ch in stem):
        return f"כמה יוצא {stem}?"
    if "___" in stem or "____" in stem:
        if stem.startswith("השלימו"):
            return stem
        return f"השלימו את החסר במשפט: {stem}"
    if stem.startswith("Look!"):
        return f"השלימו לפי מה שקורה עכשיו: {stem}"
    if _EN_SHORT.fullmatch(stem):
        return f"בחרו את הביטוי או את המשפט שמתאים ל: {stem}"
    copula = _HE_COPULA.match(stem)
    if copula and not _ALREADY_ASK.match(stem):
        return _copula_question(copula.group(1), copula.group(2))
    # כבר שאלה טובה — לא לגעת.
    if stem.startswith((
        "איזו מילה ", "באיזה זמן ", "מה צורת ", "מה המשמעות של ", "כמה הם ",
        "למה משמש", "את מה מתאר", "מה היה ", "מה הייתה ", "מה היו ",
        "מה פירוש ", "מי היה ", "לאיזה שורש ",
    )):
        return stem
    if _ALREADY_ASK.match(stem):
        return stem if stem.endswith("?") or len(stem) > 18 else f"{stem.rstrip('?')}?"
    if (
        len(stem) <= 70
        and _HEB.search(stem)
        and not stem.endswith("?")
        and "___" not in stem
    ):
        return _as_question(stem)
    return stem


def clarify_stem(question: dict[str, Any] | None) -> str:
    """מרחיב ניסוח קצר או מקוטע, בלי לחשוף תשובה. בטוח להריץ פעמיים."""
    from core.stem_fix import polish_stem

    raw = str((question or {}).get("question") or "").strip()
    if not raw:
        return ""
    # קודם ניקוי מקפים / «מי היה בידוד» וכו׳ — גם אם כבר נשמר במאגר
    stem = polish_stem(raw, question)
    if stem.startswith((
        "איזו מילה ", "באיזה זמן ", "מה צורת ", "מה המשמעות של ", "כמה הם ",
        "למה משמש", "את מה מתאר", "מה היה ", "מה הייתה ", "מה היו ",
        "מה פירוש ", "לאיזה שורש ", "מהו חלקי הדיבר",
        "השלימו את החסר", "מה עושה ", "מה מודד ", "מה מייצגת ", "מה אומר ",
        "איזו אפשרות נכונה",
    )):
        return stem if stem.endswith("?") or len(stem) > 24 else (stem if stem.endswith("?") else f"{stem.rstrip('?')}?")
    # «מי היה» רק לדמויות — אחרת polish_stem כבר תיקן
    if stem.startswith("מי היה ") and "בידוד" not in stem and "מטר" not in stem:
        from core.stem_fix import _looks_like_person

        body = stem.removeprefix("מי היה ").rstrip("?").strip()
        if _looks_like_person(body):
            return stem if stem.endswith("?") else f"{stem}?"
    rewritten = _rewrite_stem(_unwrap_weak_stem(stem))
    again = _rewrite_stem(_unwrap_weak_stem(rewritten))
    return polish_stem(again, question)


def task_prompt(question: dict[str, Any] | None) -> str:
    """מה השאלה מבקשת לעשות. רק משימה, בלי התשובה."""
    q = question or {}
    stem = str(q.get("question") or "").strip()
    kind = str(q.get("kind") or "").strip()
    subject = subject_key(q.get("subject") or "")
    topic = str(q.get("topic") or "")
    tags = " ".join(str(tag) for tag in (q.get("tags") or []))
    blob = f"{stem} {kind} {topic} {tags}"
    low = blob.lower()

    if kind == "compose" or q.get("compose"):
        from core.compose import infer_write_guide

        return infer_write_guide(q)
    if q.get("passage") or kind in {"headline", "passage"}:
        return "התשובה כתובה בקטע או נובעת ממנו. לא לפי ידע מבחוץ ולא לפי ניחוש."
    if kind == "tutor":
        return "קראו מה שכתבו. מצאו מה שגוי, ואז בחרו את התיקון."
    if kind == "estimate":
        return "אין צורך לחשב עד הסוף. העריכו סדר גודל ובחרו את הקרוב."
    if kind == "family":
        return "המילים מאותו שורש או מאותה משפחה. בחרו את זו שמתאימה למשפט."
    if kind == "analogy" or "אנלוגיה" in blob or " : " in stem:
        return "מוצאים איך שתי המילים הראשונות קשורות, ואז בוחרים זוג עם אותו סוג קשר."
    if any(token in blob for token in ("נרדפת", "מילה נרדפת", "קרובה במשמעות", "synonym")):
        return "מחפשים מילה קרובה במשמעות, שמתאימה גם למשפט."
    if any(token in blob for token in ("הפך", "ניגוד", "הפוכה", "antonym")):
        return "מחפשים מילה הפוכה במשמעות, לא מילה דומה."
    if stem.startswith("השלימו") or "___" in stem or "____" in stem:
        return "השלימו את החסר. קראו את כל המשפט לפני הבחירה."
    if low.startswith("choose") or "correct sentence" in low or "correct form" in low:
        return "בחרו את הצורה או את המשפט התקין באנגלית."
    if any(token in blob for token in ("כמה הם", "חשבו", "פתרו", "מה ערך", "אחוז", "% מ־", "% מ-")):
        return "זו שאלת חישוב. קראו מה צריך למצוא, ואז בחרו."
    if subject == "english":
        return "שאלה באנגלית. קראו את כל המשפט, שימו לב לזמן ולגוף, ואז בחרו."
    if subject == "math":
        return "קראו מה צריך למצוא, חשבו, ואז בחרו."
    if subject == "hebrew":
        return "קראו את כל השאלה. בחרו לפי משמעות והקשר."
    if subject == "civics":
        return "בחרו לפי הכלל שלמדתם באזרחות, לא לפי תחושה."
    return "קראו את כל השאלה עד הסוף, פסלו מה שלא מתאים, ואז בחרו."


def topic_label(topic: str, subject: str = "") -> str:
    """כותרת נושא לתלמיד. בלי שורה אנגלית גולמית באמצע מסך עברי."""
    raw = str(topic or "").strip() or "תרגול"
    if re.search(r"[\u0590-\u05FF]", raw):
        return raw
    key = subject_key(subject)
    if key == "english":
        return "תרגול באנגלית"
    if key == "math":
        return "תרגול בחשבון"
    return "תרגול"
