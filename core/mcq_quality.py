# -*- coding: utf-8 -*-
"""מסיחים סבירים למבחן אמריקאי — קרובים לנושא, לא אבסורדיים."""
from __future__ import annotations

import re

_ABSURD = re.compile(
    r"בנזין|תמרור|צמיג|לחץ אוויר|חום השמש|רישיון|מדא|וינדוס|שמן מנוע|"
    r"רק אור$|רק מים$|שותים$|פטיש|עץ|בטן|כדורגל",
    re.I,
)

# בריכות מסיחים לפי מילות מפתח בנושא/שאלה
_POOLS: list[tuple[tuple[str, ...], list[str]]] = [
    (
        ("אוהם", "מתח", "זרם", "התנגדות", "V =", "I =", "מעגל"),
        [
            "V = I / R (נוסחה הפוכה)",
            "התנגדות נמדדת בוולט",
            "זרם נמדד באוהם",
            "מתח = זרם + התנגדות",
            "ככל שההתנגדות גדלה הזרם גדל (במתח קבוע)",
            "אוהם הוא יחידת הספק",
        ],
    ),
    (
        ("הספק", "ואט", "kWh", "אנרגיה"),
        [
            "P = V / I",
            "kWh היא יחידת זרם",
            "הספק = מתח − זרם",
            "אנרגיה נמדדת באמפר בלבד",
            "ואט = אוהם × שנייה",
        ],
    ),
    (
        ("טור", "מקביל", "Req"),
        [
            "בטור המתחים זהים תמיד",
            "במקביל הזרם זהה בכל ענף תמיד",
            "בטור מחברים התנגדויות כמכפלה",
            "במקביל Req = R1 + R2 תמיד",
            "נורה אחת בטור מכבה רק את עצמה תמיד",
        ],
    ),
    (
        ("AC", "DC", "שנאי", "הארקה", "פחת"),
        [
            "שנאי רגיל עובד מצוין על DC יציב",
            "הארקה וניטרל הם אותו מוליך תמיד",
            "רשת הבית בישראל היא DC 12V",
            "מפסק פחת מגיב לצבע הכבל",
            "AC ו־DC זהים בכל מעגל",
        ],
    ),
    (
        ("מולטימטר", "מדידה", "COM", "צבת"),
        [
            "מתח מודדים תמיד בטור לעומס",
            "התנגדות מודדים במעגל חי בלי ניתוק",
            "מצב A מודד תמיד מתח",
            "טווח נמוך מדי משפר דיוק בלי סיכון",
            "גשש אדום מתחבר ל־COM",
        ],
    ),
    (
        ("בטיחות", "ניתוק", "רטיבות", "לוטו"),
        [
            "אפשר לעבוד על לוח חי אם נזהרים",
            "רטיבות משפרת בידוד",
            "תכשיט מתכת מגן מפני התחשמלות",
            "ריח שריפה אומר להוסיף עומס",
            "לוטו־טאג מיועד רק לצביעה",
        ],
    ),
    (
        ("מנוע", "התנעה"),
        [
            "זרם התנעה תמיד נמוך מזרם עבודה",
            "מנוע חסום מתקרר מהר יותר",
            "מנוע ממיר אור לחום בלבד",
            "אין צורך בהגנה תרמית",
            "שינוי קוטביות ב־DC לא משנה כיוון",
        ],
    ),
    (
        ("תאורה", "מפסק", "שקע", "LED"),
        [
            "מפסק דו־כיווני מגדיל את מתח הרשת",
            "שקע חלש תמיד עדיף לעומס כבד",
            "LED צורך יותר הספק מליבון לאותו אור",
            "הארקה בשקע מיותרת",
            "נתיך נועד להגביר אור",
        ],
    ),
    (
        ("נגד", "קבל", "סליל", "פאראד", "הנרי"),
        [
            "קבל מעביר DC יציב אחרי טעינה כמו קצר",
            "סליל ב־DC יציב נשאר פתוח תמיד",
            "נגד אוגר מטען כמו קבל",
            "קבל אלקטרוליטי בלי קיטוב",
            "פאראד הוא יחידת התנגדות",
        ],
    ),
    (
        ("דיודה", "מיישר", "זנר", "LED", "0.7"),
        [
            "דיודה מוליכה באותה מידה בשני הכיוונים",
            "נפילת סיליקון בהולכה היא בערך 12V",
            "LED מתחברים ישר ל־230V בלי נגד",
            "גשר דיודות מגביר קול",
            "פס על הדיודה מסמן תמיד אנודה",
        ],
    ),
    (
        ("טרנזיסטור", "BJT", "MOSFET", "β", "מיתוג"),
        [
            "BJT נשלט במתח שער כמו MOSFET",
            "MOSFET נשלט בזרם בסיס",
            "β = V / R",
            "טרנזיסטור זהה לדיודה דו־הדקית",
            "במיתוג אין חימום לעולם",
        ],
    ),
    (
        ("AND", "OR", "NOT", "דיגיטלי", "XOR", "pull-up", "ביט"),
        [
            "AND עם 1 ו־0 נותן 1",
            "OR עם 0 ו־0 נותן 1",
            "NOT של 1 הוא 1",
            "ביט הוא יחידת הספק",
            "pull-up מבטל את השעון",
        ],
    ),
    (
        ("חיישן", "ADC", "PWM", "אנלוגי", "NTC"),
        [
            "ADC ממיר ספרתי לאנלוגי תמיד",
            "אות אנלוגי הוא רק 0 ו־1",
            "חיישן טמפרטורה מודד לחץ צמיגים",
            "PWM מבטל דיודות",
            "כיול חיישן מיותר",
        ],
    ),
    (
        ("ספק", "יישור", "ווסת", "TVS", "7805"),
        [
            "סדר נכון: ייצוב ואז יישור בלי סינון",
            "ווסת ליניארי תמיד קר ב־100% יעילות",
            "TVS מחליף שנאי רשת",
            "נתיך בספק מגדיל רעש בכוונה",
            "בדיקה בלי מדידה עדיפה תמיד",
        ],
    ),
    (
        ("אופ", "משוב", "הגבר", "אופ־אמפ"),
        [
            "אופ־אמפ הוא סוג נתיך",
            "משוב שלילי מוחק הזנות",
            "רוויה אומרת שאין הגבר אפשרי",
            "אופ־אמפ עובד בלי הזנת חשמל",
            "Rf/Rg קובעים לחץ אוויר",
        ],
    ),
    (
        ("555", "טיימר", "RC", "אסטבילי"),
        [
            "555 משמש להארקת בניין",
            "RC לא משפיע על זמנים",
            "אסטבילי נותן פעימה אחת בלבד תמיד",
            "555 מניע מנוע ענק בלי דרייבר בבטחה",
            "ספק לא יציב משפר דיוק 555",
        ],
    ),
    (
        ("הלחמה", "בדיל", "flux", "ESD"),
        [
            "חיבור הלחמה קר הוא הכי אמין",
            "אוורור מיותר בהלחמה",
            "עודף בדיל אף פעם לא גורם לקצר",
            "אנטי־סטטי מיותר ל־MOSFET",
            "מלחם על עור משפר דיוק",
        ],
    ),
    (
        ("UART", "I2C", "I²C", "SPI", "baud", "SDA"),
        [
            "UART עובד בלי אותו baud בשני הצדדים",
            "I²C משתמש ב־230V בלבד",
            "בלי GND משותף התקשורת תמיד מושלמת",
            "3.3V ו־5V אפשר לערבב בלי המרה",
            "CS ב־SPI מחליף סוללה",
        ],
    ),
    (
        ("מבוא", "חשמל", "אלקטרוניקה"),
        [
            "חשמל ואלקטרוניקה הם אותו מקצוע בלי הבדל",
            "אפשר לדלג על בטיחות במעגלים קטנים",
            "יחידות לא חשובות בחישוב",
            "כל רכיב עובד בלי מתח",
            "מדידה מיותרת אחרי חיבור",
        ],
    ),
]


def is_absurd_option(text: str) -> bool:
    return bool(_ABSURD.search(str(text or "")))


_NUM_UNIT = re.compile(
    r"^\s*(-?\d+(?:[.,]\d+)?)\s*([A-Za-zΩωμu°%]*)\s*$",
    re.U,
)


def _fmt_num(value: float, unit: str) -> str:
    if abs(value - round(value)) < 1e-9:
        body = str(int(round(value)))
    else:
        body = f"{value:.4f}".rstrip("0").rstrip(".")
    return f"{body}{unit}"


def parse_quantity(text: str) -> tuple[float, str] | None:
    raw = str(text or "").strip().replace(",", ".")
    match = _NUM_UNIT.match(raw)
    if not match:
        return None
    return float(match.group(1)), match.group(2) or ""


def numeric_near_misses(
    correct: str,
    *,
    v: float | None = None,
    r: float | None = None,
    need: int = 6,
) -> list[str]:
    """מסיחים מספריים קרובים — טעויות תלמיד נפוצות, לא ערכים מטורפים."""
    parsed = parse_quantity(correct)
    if not parsed:
        return []
    value, unit = parsed
    if abs(value) < 1e-12:
        return []
    out: list[str] = []
    candidates = [
        value * 2,
        value / 2,
        value + 1 if abs(value) >= 1 else value + 0.1,
        value - 1 if abs(value) > 1 else value * 0.9,
        -value if value > 0 else abs(value),
    ]
    if v is not None and r is not None and abs(r) > 1e-12:
        # טעויות נוסחה ב־I=V/R
        candidates.extend([v + r, r / v if abs(v) > 1e-12 else 0, v / (r + 1), v / max(r - 1, 0.5)])
    for cand in candidates:
        if abs(cand - value) < 1e-9:
            continue
        # לא לתת מסיח מטורף (פי 20+)
        if abs(value) > 0 and abs(cand / value) > 12:
            continue
        if cand <= 0 and value > 0 and unit in {"A", "V", "W", "Ω", "ohm"}:
            continue
        text = _fmt_num(cand, unit)
        if text not in out and text != str(correct).strip():
            out.append(text)
        if len(out) >= need:
            break
    return out


def looks_too_easy(correct: str, option: str) -> bool:
    """מסיח «קל מדי»: אבסורד, או מספר רחוק בטירוף מהנכון."""
    if is_absurd_option(option):
        return True
    left = parse_quantity(correct)
    right = parse_quantity(option)
    if left and right and left[1].casefold() == right[1].casefold():
        a, b = abs(left[0]), abs(right[0])
        if a > 1e-12 and (b / a > 12 or a / max(b, 1e-12) > 12):
            return True
    return False


def distractors_for(topic: str, prompt: str, correct: str, need: int = 6) -> list[str]:
    blob = f"{topic} {prompt} {correct}".casefold()
    out: list[str] = []
    out.extend(numeric_near_misses(correct, need=need))
    for keys, pool in _POOLS:
        if any(k.casefold() in blob for k in keys):
            out.extend(pool)
    # מסיחים כלליים קרובים למקצוע — לא אבסורד
    out.extend(
        [
            "הגדרה נכונה למושג אחר באותו שיעור",
            "נוסחה הפוכה או יחידה שגויה",
            "תוצאה שמבלבלת סיבה ותוצאה",
            "פרט נכון שלא עונה על מה שנשאל",
            "תיאור חלקי שמפספס את העיקר",
        ]
    )
    want = str(correct or "").strip()
    clean: list[str] = []
    seen = {want.casefold()}
    for item in out:
        text = str(item).strip()
        key = text.casefold()
        if not text or key in seen or text == want:
            continue
        if looks_too_easy(want, text):
            continue
        clean.append(text)
        seen.add(key)
        if len(clean) >= need:
            break
    return clean


def harden_options(
    options: list[str],
    answer: int,
    *,
    topic: str = "",
    prompt: str = "",
) -> tuple[list[str], int]:
    """מחליף מסיחים אבסורדיים/רחוקים במסיחים סבירים; שומר על התשובה הנכונה."""
    opts = [str(o).strip() for o in options]
    while len(opts) < 4:
        opts.append("")
    answer = max(0, min(3, int(answer)))
    correct = opts[answer] if opts else ""
    if not correct:
        return opts[:4], answer
    pool = distractors_for(topic, prompt, correct, need=12)
    pi = 0
    for i, text in enumerate(opts):
        if i == answer:
            continue
        bad = (
            not text
            or text in {"—", "-", "?"}
            or looks_too_easy(correct, text)
            or text == correct
        )
        if not bad:
            continue
        while pi < len(pool) and pool[pi] in opts:
            pi += 1
        if pi < len(pool):
            opts[i] = pool[pi]
            pi += 1
    # השלמה ל־4 שונים
    seen = set()
    fresh: list[str] = []
    for text in opts:
        key = text.casefold()
        if text and key not in seen:
            fresh.append(text)
            seen.add(key)
    for text in pool:
        if len(fresh) >= 4:
            break
        key = text.casefold()
        if key not in seen and text != correct and not looks_too_easy(correct, text):
            fresh.append(text)
            seen.add(key)
    if correct not in fresh:
        fresh = [correct] + [x for x in fresh if x != correct]
    # שמירת אינדקס התשובה המקורי ככל האפשר
    if correct in fresh[:4]:
        answer = fresh.index(correct)
    else:
        fresh[0] = correct
        answer = 0
    while len(fresh) < 4:
        fresh.append(f"אפשרות שגויה הקשורה לנושא ({len(fresh)})")
    return fresh[:4], answer
