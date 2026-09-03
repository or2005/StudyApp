"""
StudyApp, מנוע אבחון ראשוני
20 שאלות רב-ברירה המכסות את כלל המקצועות, בקושי מדורג (קל → בינוני → מתקדם),
חישוב רמת התלמיד אוטומטית והתאמת תכני הלימוד.
"""

import random
from collections import defaultdict

from core.config import rtl

DIAGNOSTIC_BANK = [
    ("math", "חשבון בסיסי", "כמה התוצאה של 7 + 8?", ["13", "14", "15", "16"], 2, 1),
    ("math", "כפל", "מה התוצאה של 6 × 7?", ["36", "42", "48", "54"], 1, 1),
    (
        "english",
        "אוצר מילים",
        "מה המשמעות של המילה BOOK?",
        ["דלת", "ספר", "שולחן", "חלון"],
        1,
        1,
    ),
    (
        "english",
        "פעלים",
        "מה העברית של TO RUN?",
        ["לרוץ", "לשיר", "לישון", "לקרוא"],
        0,
        1,
    ),
    (
        "hebrew",
        "כתיב",
        "בחרו את הכתיב הנכון: חברה + שלי",
        ["חברה שלי", "חברה שליי", "חברר שלי", "חברה שלייי"],
        0,
        1,
    ),
    (
        "physics",
        "מושגי יסוד",
        "מה מודד המדחום?",
        ["מהירות", "טמפרטורה", "משקל", "גובה"],
        1,
        1,
    ),
    (
        "chemistry",
        "מושגי יסוד",
        "איזה גז הכי נפוץ באוויר שאנחנו נושמים?",
        ["חנקן", "חמצן בלבד", "מימן", "הליום"],
        0,
        1,
    ),
    (
        "history",
        "כרונולוגיה",
        "מתי הוקמה מדינת ישראל?",
        ["1917", "1948", "1967", "1973"],
        1,
        1,
    ),
    (
        "civics",
        "יסודות הדמוקרטיה",
        "כמה חברי כנסת יש במלוא הכנסת?",
        ["100", "110", "120", "130"],
        2,
        1,
    ),
    (
        "math",
        "חשיבה",
        "מה המספר הבא בסדרה: 2, 4, 6, 8, ...?",
        ["9", "10", "11", "12"],
        1,
        1,
    ),
    ("math", "אחוזים", "כמה הם 25% מתוך 80?", ["16", "18", "20", "24"], 2, 2),
    ("math", "שברים", "מה התוצאה של 1/2 + 1/4?", ["2/6", "3/4", "1/4", "3/8"], 1, 2),
    (
        "geography",
        "בירות",
        "מהי בירת ישראל?",
        ["תל אביב", "ירושלים", "חיפה", "באר שבע"],
        1,
        2,
    ),
    ("english", "דקדוק", "מה העבר של GO?", ["goed", "went", "going", "go'ed"], 1, 2),
    (
        "hebrew",
        "לשון",
        "מהו מילה נרדפת למילה 'מהיר'?",
        ["איטי", "קל", "זריז", "כבד"],
        2,
        2,
    ),
    (
        "physics",
        "מהירות",
        'רכב נוסע 100 ק"מ בשעתיים. מה מהירותו הממוצעת?',
        ['30 קמ"ש', '40 קמ"ש', '50 קמ"ש', '60 קמ"ש'],
        2,
        2,
    ),
    (
        "chemistry",
        "טבלה מחזורית",
        "מהו הסמל הכימי של מים?",
        ["H₂O", "CO₂", "O₂", "NaCl"],
        0,
        2,
    ),
    (
        "history",
        "היסטוריה עולמית",
        "באיזו שנה הסתיימה מלחמת העולם השנייה?",
        ["1918", "1939", "1945", "1949"],
        2,
        2,
    ),
    (
        "civics",
        "זכויות",
        "מהו המקור העליון של החוק בישראל?",
        ["הממשלה", "הכנסת", "בית המשפט העליון", "חוק-יסוד: כבוד האדם"],
        1,
        2,
    ),
    ("math", "אלגברה", "אם 3x + 6 = 21, מהו x?", ["3", "5", "7", "9"], 1, 3),
    (
        "civics",
        "היגיון",
        "כל הפרחים יפים. הורד הוא פרח. מה המסקנה?",
        ["הורד יפה", "הורד לא יפה", "כל היפים הם ורדים", "לא ניתן להסיק"],
        0,
        3,
    ),
    (
        "physics",
        "ניוטון",
        "מהו החוק השני של ניוטון?",
        ["F = m·a", "E = mc²", "PV = nRT", "V = IR"],
        0,
        3,
    ),
]

EXAM_LENGTH = 20


def build_diagnostic() -> list:
    """בונה מבחן אבחון של בדיוק 20 שאלות: קל→בינוני→מתקדם, מעורבב."""
    easy = [q for q in DIAGNOSTIC_BANK if q[5] == 1]
    mid = [q for q in DIAGNOSTIC_BANK if q[5] == 2]
    hard = [q for q in DIAGNOSTIC_BANK if q[5] == 3]
    picked = random.sample(easy, 10) + random.sample(mid, 8) + random.sample(hard, 2)
    random.shuffle(picked)
    return [
        {
            "subject": s,
            "topic": t,
            "question": q,
            "options": [
                rtl(o) if any("\u0590" <= c <= "\u05ea" for c in o) else o for o in opts
            ],
            "answer": a,
            "difficulty": d,
        }
        for (s, t, q, opts, a, d) in picked
    ]


def _subject_name(subject: str) -> str:
    from core.config import SUBJECTS

    return SUBJECTS.get(subject, {}).get("name") or subject


def compute_level(
    correct: int, total: int = EXAM_LENGTH, answers: list | None = None
) -> dict:
    """מחשב את רמת התלמיד לפי אחוז ההצלחה + המלצות מותאמות."""
    safe_total = max(1, int(total))
    safe_correct = max(0, int(correct))
    pct = 100.0 * safe_correct / safe_total
    if pct >= 80:
        level, title = "advanced", rtl("🚀 מתקדם")
    elif pct >= 55:
        level, title = "intermediate", rtl("📈 בינוני")
    else:
        level, title = "beginner", rtl("🌱 מתחיל")

    recs = {
        "beginner": [
            rtl("התחל מהשיעורים הבסיסיים בכל מקצוע (מצב 📚 שיעורים)"),
            rtl("תרגל 10 שאלות ביום במצב 🎯 תרגול עם הסבר מיידי"),
            rtl("עבור על ההסברים אחרי כל טעות, הם מותאמים במיוחד לך"),
        ],
        "intermediate": [
            rtl("שלב שיעורים עם תרגול יומי (🎯) בנושאים שבהם טעית באבחון"),
            rtl("בצע מבחן 📝 פעם בשבוע למדידת התקדמות"),
            rtl("חזור על הנושאים: חיזוק נקודות החולשה שזוהו באבחון"),
        ],
        "advanced": [
            rtl("התמקד במבחנים מלאים (📝) לתרגול מצב בגרות"),
            rtl("תרגל שאלות מתקדמות ושמור על מהירות מענה"),
            rtl("חזור על נושאים שבהם פחת מ-80% הצלחה"),
        ],
    }[level]

    weak = find_weak_areas(answers)
    return {
        "pct": round(pct, 1),
        "level": level,
        "level_title": title,
        "recommendations": recs,
        "weak_topics": weak,
    }


def find_weak_areas(answers: list | None = None) -> list:
    """מזהה נושאים (מקצועות) שבהם התשובות באבחון היו חלשות, מחזיר שמות מקצוע להצגה."""
    if not answers:
        from core.config import HOME_SUBJECTS

        return list(HOME_SUBJECTS)

    fail_count = defaultdict(int)
    for item in answers:
        subject = item.get("subject")
        if not subject:
            continue
        if not item.get("correct", False):
            fail_count[subject] += 1

    if not fail_count:
        return []

    ranked = sorted(fail_count.items(), key=lambda x: x[1], reverse=True)
    return [subject for subject, _ in ranked[:3]]
