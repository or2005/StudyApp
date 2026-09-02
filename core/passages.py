"""קטעי קריאה מקוריים + שאלות עליהם.

הקטע נשמר בכל שאלה (passage + passage_id) כדי שהמסך יוכל להציג אותו קבוע
בזמן שהשאלות מתחלפות.
"""
from __future__ import annotations

from core.quiz import make_question

# קטעים מקוריים קצרים ברמת מימ״ד / בגרות 3 יח״ל. לא הועתקו מספר.


def _block(subject: str, topic: str, pid: str, passage: str, rows: list[tuple]) -> list[dict]:
    out = []
    for i, row in enumerate(rows, start=1):
        question, ans, wrong, why, diff = row[:5]
        item = make_question(
            subject, topic, f"{pid}_q{i}", question, ans, wrong, why, diff,
            hint="חזרו לקטע. התשובה כתובה שם או נובעת ממנו.",
        )
        item["kind"] = "passage"
        item["passage"] = passage
        item["passage_id"] = pid
        out.append(item)
    return out


def packs_for(key: str) -> list[tuple[str, str, list[dict]]]:
    """מחזיר (נושא, תיאוריה, רשימת שאלות מוכנות)."""
    return PASSAGES.get(key) or []


HE_PASSAGE = """\
בשנים האחרונות יותר בני נוער עובדים אחרי הלימודים. חלקם עוזרים בפרנסת הבית, ואחרים רוצים כסף עצמאי לבילויים. מחקר קטן בבית ספר במרכז הארץ מצא שרוב העובדים לומדים פחות בערבים, אבל לא כולם מורידים ציונים: מי שתכנן לוח זמנים קבוע, שעה אחת של שיעורים לפני העבודה, שמר על ממוצע דומה. המסקנה של החוקרים לא הייתה "אסור לעבוד", אלא שצריך גבול: יותר מ־15 שעות בשבוע נקשרה לירידה חדה בנוכחות בשיעורים. המלצה מעשית שעולה מהקטע: לדבר עם המורה על עומס, ולא להסתיר את העבודה.
"""

EN_PASSAGE = """\
Many teenagers in Israel volunteer after school. They help in libraries, visit elderly people, or clean parks. A short school survey found that students who volunteer two hours a week feel more connected to their town. However, some students cannot volunteer because they work in the afternoon. The writer does not say volunteering is easy for everyone. The last line of the survey suggests schools should offer short volunteer projects on Fridays, so more students can join without missing a job.
"""

CIV_PASSAGE = """\
חופש הביטוי הוא זכות יסוד בדמוקרטיה, אבל הוא אינו מוחלט. מותר לבקר את השלטון ומותר להפגין, ובלבד שההפגנה חוקית ואינה כוללת אלימות. בתי המשפט בישראל הכירו בכך שגם דיבור פוגעני יכול להיות מוגן, כל עוד אינו הסתה לאלימות או לשון הרע שיש בה עבירה. הקטע מדגיש איזון: החברה צריכה מרחב לביקורת, והמדינה צריכה להגן על ביטחון הציבור. לכן השאלה איננה "האם מותר לדבר" אלא "איפה עובר הגבול בחוק".
"""

MATH_PASSAGE = """\
טבלה: מחיר כרטיס למוזיאון. מבוגר 40 ₪, ילד 20 ₪, קבוצה מעל 10 אנשים מקבלת 10% הנחה על הסכום. משפחה של שני מבוגרים ושלושה ילדים משלמת לפי המחיר הרגיל, כי הם חמישה אנשים, פחות מעשרה. קבוצת בית ספר של 12 ילדים ומורה אחד (מבוגר) מקבלת הנחה. חשוב: ההנחה היא על הסכום הכולל, לא רק על כרטיסי הילדים.
"""


PASSAGES: dict[str, list[tuple[str, str, list[dict]]]] = {
    "hebrew": [
        (
            "הבנת הנקרא, עבודה ולימודים",
            "קוראים קטע שלם, ורק אז עונים. כל תשובה חייבת להישען על מה שכתוב, לא על דעה כללית.",
            _block(
                "hebrew",
                "הבנת הנקרא, עבודה ולימודים",
                "he_work",
                HE_PASSAGE,
                [
                    ("מה מצא המחקר לגבי מי שתכנן שעת לימוד לפני העבודה?", "שמר על ממוצע דומה", ["הפסיק לעבוד", "הוריד ציון תמיד", "לא עבד בכלל"], "כתוב במפורש.", "Easy"),
                    ("מה לא הייתה מסקנת החוקרים?", "שאסור לעבוד בכלל", ["שצריך גבול של שעות", "שיש קשר ל־15 שעות", "שתכנון עוזר"], "כתוב: לא 'אסור לעבוד'.", "Medium"),
                    ("יותר מ־15 שעות בשבוע נקשרו ל", "ירידה חדה בנוכחות", ["עלייה בציונים", "ביטול בית הספר", "פרס מהמורה"], "נוכחות בשיעורים.", "Easy"),
                    ("ההמלצה המעשית בקטע היא", "לדבר עם המורה על עומס", ["להסתיר את העבודה", "לעזוב את בית הספר", "לעבוד 20 שעות"], "השורה האחרונה.", "Medium"),
                    ("הקטע מציג בעיקר", "קשר בין היקף עבודה ללימודים, עם סייג", ["איסור גורף על בני נוער", "חוק חדש של הכנסת", "סיפור בדיוני בלי נתון"], "מחקר קטן + סייג.", "Hard"),
                ],
            ),
        )
    ],
    "english": [
        (
            "Unseen, volunteering",
            "Read the whole text first. Answers must come from the passage, not from general knowledge.",
            _block(
                "english",
                "Unseen, volunteering",
                "en_vol",
                EN_PASSAGE,
                [
                    ("According to the passage, volunteers help in", "libraries, with elderly people, or parks", ["hospitals only", "the army only", "no places are named"], "first sentences.", "Easy"),
                    ("Students who volunteer two hours a week", "feel more connected to their town", ["always get paid", "stop going to school", "cannot have a job"], "survey finding.", "Easy"),
                    ("Why can't some students volunteer?", "They work in the afternoon", ["The school bans it", "Libraries are closed", "The writer forbids jobs"], "because they work.", "Medium"),
                    ("The writer does NOT say that volunteering is", "easy for everyone", ["done after school", "sometimes two hours a week", "connected to the town"], "explicit sentence.", "Medium"),
                    ("The last suggestion is to offer projects", "on Fridays so more students can join", ["only at night", "instead of school", "in another country"], "last line.", "Hard"),
                ],
            ),
        )
    ],
    "civics": [
        (
            "הבנת קטע, חופש ביטוי",
            "קטע קצר בסגנון אזרחות: קוראים, מאתרים טענה, ומבחינים בין זכות לבין גבול בחוק.",
            _block(
                "civics",
                "הבנת קטע, חופש ביטוי",
                "civ_speech",
                CIV_PASSAGE,
                [
                    ("לפי הקטע, חופש הביטוי", "זכות יסוד שאינה מוחלטת", ["מוחלט תמיד", "לא קיים בישראל", "שייך רק לשלטון"], "משפט הפתיחה.", "Easy"),
                    ("הפגנה מותרת כשהיא", "חוקית ובלי אלימות", ["אלימה אם הצודקים", "רק בלילה", "רק נגד עיתון"], "כתוב במפורש.", "Easy"),
                    ("דיבור פוגעני, לפי הקטע, יכול להיות מוגן כל עוד", "אינו הסתה לאלימות או לשון הרע עבריינית", ["תמיד אסור", "תמיד חובה", "רק אם השלטון כועס"], "בתי המשפט הכירו באיזון.", "Medium"),
                    ("השאלה המרכזית שהקטע מציג", "איפה עובר הגבול בחוק", ["האם מותר לנשום", "מי ראש הממשלה", "כמה חברי כנסת יש"], "משפט הסיום.", "Medium"),
                    ("הקטע מדגיש בעיקר", "איזון בין ביקורת לביטחון הציבור", ["ביטול כל זכות", "רק צנזורה", "רק הפגנות אלימות"], "איזון.", "Hard"),
                ],
            ),
        )
    ],
    "math": [
        (
            "קריאת טבלה, כרטיסים",
            "במימ״ד יש שאלות על נתון כתוב. קודם מבינים את הכלל, אחר כך מחשבים.",
            _block(
                "math",
                "קריאת טבלה, כרטיסים",
                "ma_tickets",
                MATH_PASSAGE,
                [
                    ("מחיר מבוגר לפי הטבלה", "40 ₪", ["20 ₪", "10 ₪", "60 ₪"], "שורה ראשונה.", "Easy"),
                    ("משפחה: 2 מבוגרים + 3 ילדים, בלי הנחה. הסכום", "140 ₪", ["200 ₪", "100 ₪", "80 ₪"], "80+60=140. חמישה אנשים, אין הנחה.", "Medium"),
                    ("למה למשפחה אין הנחה?", "הם רק חמישה, מתחת לעשרה", ["ילדים לא משלמים", "המוזיאון סגור", "ההנחה רק למבוגרים"], "כתוב: פחות מעשרה.", "Easy"),
                    ("קבוצה: 12 ילדים + מורה. לפני הנחה", "280 ₪", ["240 ₪", "40 ₪", "12 ₪"], "240+40=280.", "Medium"),
                    ("אותה קבוצה אחרי 10% הנחה", "252 ₪", ["280 ₪", "28 ₪", "240 ₪"], "הנחה על הסכום הכולל: 0.9×280=252.", "Hard"),
                ],
            ),
        )
    ],
}
