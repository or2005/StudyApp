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
    exp = str(explanation or "").strip()
    answer = str(correct or "").strip()
    guide = teaching(subject, topic, extra=exp)
    rule = guide.get("rule") or ""

    filler = rule or guide.get("recap") or guide.get("mistakes") or ""
    if not exp:
        parts = []
        if answer:
            parts.append(f"התשובה הנכונה היא «{answer}».")
        if filler:
            parts.append(filler)
        elif topic:
            parts.append(f"זה שייך לנושא «{topic}». חזרו לשיעור הקצר ואז ענו לאט.")
        text = " ".join(parts) or "קראו שוב את השאלה וחזרו לשיעור הקצר."
        if len(text) < 40:
            extra = guide.get("recap") or guide.get("mistakes") or ""
            if extra and extra[:20] not in text:
                text = f"{text} {extra}".strip()
        return text

    if answer and answer not in exp[:160]:
        exp = f"התשובה הנכונה היא «{answer}». {exp}"
    if len(exp) < 70 and filler and filler[:28] not in exp:
        exp = f"{exp} {filler}"
    if len(exp) < 40:
        extra = guide.get("recap") or guide.get("mistakes") or guide.get("why") or ""
        if extra and extra[:20] not in exp:
            exp = f"{exp} {extra}".strip()
    return exp.strip()


def display_explanation(question: dict[str, Any] | None, subject: str = "") -> str:
    q = question or {}
    opts = q.get("options") or []
    idx = q.get("answer")
    correct = str(q.get("correct_answer") or "").strip()
    if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
        correct = str(opts[idx])
    return enrich_explanation(
        correct,
        q.get("explanation") or "",
        q.get("topic") or "",
        subject or q.get("subject") or "",
    )


def live_hint(question: dict[str, Any] | None, subject: str = "") -> str:
    q = question or {}
    existing = str(q.get("hint") or "").strip()
    if existing and existing not in GENERIC_HINTS:
        return existing
    guide = teaching(subject or q.get("subject") or "", q.get("topic") or "", extra=q.get("question") or "")
    if guide.get("rule"):
        return f"כלל קצר: {guide['rule']}"
    how = str(guide.get("how") or "")
    first_how = how.split("\n", 1)[0].strip()
    return first_how or existing or "קראו את כל השאלה, ואז פסלו מה שלא מתאים."


def feedback_note(question: dict[str, Any] | None, *, correct: bool, subject: str = "") -> str:
    """שורה אחת אחרי תשובה: טעות נפוצה אם שגו, כלל קצר אם נכון."""
    q = question or {}
    guide = teaching(
        subject or q.get("subject") or "",
        q.get("topic") or "",
        extra=q.get("question") or "",
    )
    if correct:
        return guide.get("rule") or ""
    mistake = guide.get("mistakes") or ""
    rule = guide.get("rule") or ""
    if mistake and rule and rule[:24] not in mistake:
        return f"{mistake} {rule}"
    return mistake or rule


_QUOTE_MARKS = " «»\"'"


def _clean_word(text: str) -> str:
    return str(text or "").strip().strip(_QUOTE_MARKS)


def _unwrap_weak_stem(stem: str) -> str:
    """מסיר ניסוח גנרי ישן כדי שאפשר יהיה לנסח מחדש."""
    text = stem.strip()
    if text.startswith(_GENERIC_PREFIX):
        text = text[len(_GENERIC_PREFIX):].strip()
    inverted_pct = re.match(
        r"^מה\s+(\d+(?:[.,]\d+)?)\s*%\s*מ[־\-]?\s*(\d+(?:[.,]\d+)?)\s+הם\s*\??$",
        text,
    )
    if inverted_pct:
        return f"{inverted_pct.group(1)}% מ־{inverted_pct.group(2)} הם"
    inverted = _INVERTED_COP.match(text)
    if (
        inverted
        and not text.startswith(("מהו ", "מהי ", "מהם ", "מהן "))
        and "." not in inverted.group(1)
        and len(inverted.group(1)) <= 48
    ):
        return f"{inverted.group(1)} {inverted.group(2)}"
    return text


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
    if _HEB.search(text):
        return f"מה {text}?"
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
    if re.search(r"(קשור(?:ים|ה)|שייכת|המשותף)\s*ל?\s*\??$", stem):
        return f"לאיזה שורש או נושא {stem.rstrip('?').strip()}?"
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
        noun, verb = copula.group(1).strip(" «»\"'"), copula.group(2)
        prefix = _COPULA_WORD.get(verb, "מהו")
        return f"{prefix} {noun}?"
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
    stem = str((question or {}).get("question") or "").strip()
    if not stem:
        return ""
    if stem.startswith("איזו מילה ") or stem.startswith("השלימו את החסר") or stem.startswith("מה צורת"):
        return stem
    if stem.startswith("מה המשמעות של") or stem.startswith("כמה הם ") or stem.startswith("למה משמש"):
        return stem
    rewritten = _rewrite_stem(_unwrap_weak_stem(stem))
    if rewritten.startswith(_GENERIC_PREFIX):
        rewritten = _rewrite_stem(_unwrap_weak_stem(rewritten))
    return rewritten


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
