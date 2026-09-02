"""שאלות הבנה שמתמזגות למאגר: מורה ליום, הערכה, מקרה, משפחת שורש."""
from __future__ import annotations

from core.quiz import make_question


def _ready(subject, topic, qid, question, correct, wrongs, why, difficulty="Medium",
           kind="tutor", stem="", passage="", hint=""):
    item = make_question(
        subject, topic, qid, question, correct, wrongs, why, difficulty, hint=hint, kind=kind,
    )
    item["kind"] = kind
    if stem:
        item["stem"] = stem
    if passage:
        item["passage"] = passage
        item["kind"] = kind
    return item


def packs_for(key: str) -> list[tuple[str, str, list[dict], str]]:
    builder = {
        "hebrew": _hebrew,
        "math": _math,
        "civics": _civics,
        "history": _history,
        "english": _english,
        "geography": _geography,
        "physics": _physics,
        "chemistry": _chemistry,
    }.get(key)
    if not builder:
        return []
    topic, theory, questions = builder()
    return [(topic, theory, questions, "הבנה")]


def _hebrew():
    topic = "הבנה בלשון"
    theory = (
        "כאן לא מנחשים בין ארבע תשובות יבשות. קוראים משפט של תלמיד, "
        "או משפחת מילים מאותו שורש, ומאתרים מה באמת שבור."
    )
    rows = [
        _ready(
            "hebrew", topic, "learn_he_tutor_1",
            "מה הטעות?",
            "הפועל לא מתאים לרבים",
            ["חסרה נקודה בסוף המשפט", "מילת היחס שגויה", "אין טעות, המשפט תקין"],
            "«ילדים» ברבים, לכן הפועל הוא «רצו» ולא «רצה».",
            "Easy", "tutor",
            stem="הילדים רצה לחצר.",
        ),
        _ready(
            "hebrew", topic, "learn_he_tutor_2",
            "מה הטעות?",
            "כתיב חסר: חסר ו׳ התנועה",
            ["סדר המילים הפוך", "זו סמיכות לא תקינה", "המשפט תקין לגמרי"],
            "«אוויר» נכתב בשתי וו״ים: ו׳ התנועה ו־ו׳ העיצור.",
            "Medium", "tutor",
            stem="האויר בחוץ קר מאוד הבוקר.",
        ),
        _ready(
            "hebrew", topic, "learn_he_fam_1",
            "איזו מילה שייכת לאותו שורש?",
            "מכתב",
            ["כתר", "כתף", "כיסא"],
            "מכתב, כתיבה וכתב כולם מהשורש כ.ת.ב. כתר וכתף רק נשמעים דומה.",
            "Easy", "family",
            stem="כתב, כתיבה, מכתב",
        ),
        _ready(
            "hebrew", topic, "learn_he_fam_2",
            "איזו מילה לא מאותו שורש?",
            "שמלה",
            ["שמר", "משמרת", "שמירה"],
            "שמר, שמירה ומשמרת מהשורש ש.מ.ר. שמלה לא קשורה.",
            "Medium", "family",
            stem="שמר, שמירה, משמרת",
        ),
        _ready(
            "hebrew", topic, "learn_he_tutor_3",
            "מה הטעות?",
            "חסר יידוע אחרי אות היחס",
            ["הפועל בזמן עבר במקום הווה", "זו מילת שאלה מיותרת", "אין כאן טעות"],
            "אחרי «ל־» לפני שם מיודע כותבים «לבית» או «אל הבית», לא «ל בית» כשתי מילים רשלניות בלי כלל.",
            "Hard", "tutor",
            stem="הלכנו ל בית ספר בבוקר.",
            hint="בדקו את החיבור בין האות למילה שאחריה.",
        ),
        _ready(
            "hebrew", topic, "learn_he_tutor_4",
            "מה הטעות?",
            "גוף הפועל לא מתאים לנוכחת",
            ["חסר פיסוק אחרי השם", "מילת קישור שגויה", "המשפט תקין"],
            "«את» נוכחת, לכן «כתבת» ולא «כתבתם».",
            "Easy", "tutor",
            stem="את כתבתם את התשובה במחברת.",
        ),
    ]
    return topic, theory, rows


def _math():
    topic = "הערכה וכמותי"
    theory = (
        "לפני החישוב המדויק שואלים: זה גדול או קטן, קרוב למאה או לאלף. "
        "מי שמעריך נכון פחות נופל למסיחים מטופשים."
    )
    rows = [
        _ready(
            "math", topic, "learn_ma_est_1",
            "19 × 21 קרוב ביותר ל־",
            "400",
            ["200", "800", "40"],
            "20×20=400. 19×21 קרוב מאוד לזה, לא לחצי ולא לפי שניים.",
            "Easy", "estimate",
        ),
        _ready(
            "math", topic, "learn_ma_est_2",
            "48% מ־200 קרוב ל־",
            "100",
            ["50", "20", "200"],
            "50% מ־200 הם 100. 48% כמעט אותו דבר.",
            "Easy", "estimate",
        ),
        _ready(
            "math", topic, "learn_ma_tutor_1",
            "מה הטעות בדרך?",
            "חיברו במקום להכפיל אחוז",
            ["שכחו את האפס", "הפכו מונה ומכנה", "אין טעות בדרך"],
            "20% מ־50 זה 0.2×50=10, לא 20+50.",
            "Medium", "tutor",
            stem="20% מ־50: 20 + 50 = 70",
        ),
        _ready(
            "math", topic, "learn_ma_est_3",
            "1/4 + 1/5 קרוב ל־",
            "חצי",
            ["אחד", "עשירית", "שתיים"],
            "רבע זה 0.25, חמישית 0.20, יחד בערך 0.45. קרוב לחצי, לא לשלם.",
            "Medium", "estimate",
        ),
        _ready(
            "math", topic, "learn_ma_tutor_2",
            "מה הטעות בדרך?",
            "חילקו את המכנה במקום למצוא מכנה משותף",
            ["חיברו מונים בלי מכנים", "שכחו את הסימן", "הדרך נכונה"],
            "1/2 + 1/6: מכנה משותף 6, לא «2÷6».",
            "Hard", "tutor",
            stem="1/2 + 1/6 = 1/3 כי 2+6=8 ו־1/8 קרוב",
        ),
        _ready(
            "math", topic, "learn_ma_est_4",
            "שלוש שעות ו־40 דקות בקרוב, בדקות",
            "220",
            ["180", "340", "100"],
            "3×60=180, ועוד 40 הן 220. לא 340 ולא רק שלוש שעות.",
            "Easy", "estimate",
        ),
    ]
    return topic, theory, rows


def _civics():
    topic = "מקרה אזרחי"
    theory = (
        "קוראים מקרה קצר, כמו ידיעה, ואז שואלים איזו זכות או רשות נכנסת לתמונה. "
        "אזרחות חיה בסיפור, לא ברשימת הגדרות."
    )
    rows = [
        _ready(
            "civics", topic, "learn_ci_head_1",
            "איזו זכות נפגעה בעיקר?",
            "חופש הביטוי וההפגנה",
            ["חופש העיסוק", "הזכות לקניין", "חובת השירות"],
            "איסור הפגנה בלי בסיס בחוק פוגע בחופש הביטוי ובהפגנה, לא בעסק או ברכוש.",
            "Easy", "headline",
            passage="עירייה אסרה על תושבים להפגין מול בניין העירייה, בלי צו ובלי הסבר בחוק.",
        ),
        _ready(
            "civics", topic, "learn_ci_head_2",
            "מי אמור לבדוק אם המשטרה חרגה?",
            "בתי המשפט",
            ["שר הספורט", "ועדת קישוט", "מנהל בית ספר"],
            "ביקורת שיפוטית: בית משפט בודק אם רשות חרגה מסמכות, לא גוף מקצועי אחר.",
            "Medium", "headline",
            passage="משטרה פזרה אסיפה שקטה בפארק, בלי שהייתה שם אלימות.",
        ),
        _ready(
            "civics", topic, "learn_ci_head_3",
            "איזה עיקרון דמוקרטי נפגע?",
            "שלטון החוק",
            ["הפרדת רשויות רק בספורט", "חובת הצבעה", "איסור עיתונות"],
            "פקיד שמחליט נגד החוק שובר את שלטון החוק: כולם כפופים לאותם כללים.",
            "Medium", "headline",
            passage="פקיד בעירייה נתן לקרוב משפחה היתר בנייה, למרות שהבקשה נדחתה לפי החוק.",
        ),
        _ready(
            "civics", topic, "learn_ci_tutor_1",
            "מה הטעות בהסבר?",
            "מערבבים זכות עם חובה",
            ["שוכחים את שם הכנסת", "טועים במספר הממשלה", "ההסבר תקין"],
            "הצבעה היא זכות. חובה היא משהו שהחוק מחייב, כמו תשלום מס.",
            "Easy", "tutor",
            stem="«חובה דמוקרטית להצביע, אחרת זה לא חוקי לגור בארץ.»",
        ),
        _ready(
            "civics", topic, "learn_ci_head_4",
            "מה הכלי המתאים לאזרח כאן?",
            "עתירה לבג״ץ או לבית משפט",
            ["לשנות את המנון המדינה", "לבטל את הכנסת לבד", "לסגור את העיתון"],
            "כשרשות פוגעת בזכות, פונים לבית משפט. לא מבטלים מוסדות לבד.",
            "Hard", "headline",
            passage="רשות מקומית סגרה עיתון מקומי כי לא אהבה כתבת ביקורת.",
        ),
    ]
    return topic, theory, rows


def _history():
    topic = "הבחנה בין אירועים"
    theory = (
        "שני תאריכים שנראים דומים. המשימה היא לא לשנן מספר, אלא לא לערבב בין מלחמות, "
        "החלטות והכרזות."
    )
    rows = [
        _ready(
            "history", topic, "learn_hi_tutor_1",
            "מה הטעות?",
            "מערבבים 1948 עם 1967",
            ["טועים בשם האו״ם", "שוכחים את בלפור", "אין טעות"],
            "הקמת המדינה: 1948. ששת הימים: 1967. לא אותה מלחמה.",
            "Easy", "tutor",
            stem="«מדינת ישראל קמה ב־1967 אחרי ששת הימים.»",
        ),
        _ready(
            "history", topic, "learn_hi_est_1",
            "מה קדם למה?",
            "הצהרת בלפור לפני החלטת האו״ם",
            ["החלטת האו״ם לפני בלפור", "ששת הימים לפני הקמת המדינה", "יום כיפור לפני 1948"],
            "בלפור 1917, החלטת או״ם 1947, הקמת המדינה 1948. הסדר הזה קבוע.",
            "Medium", "estimate",
        ),
        _ready(
            "history", topic, "learn_hi_tutor_2",
            "מה הטעות?",
            "יום הכיפורים הוא 1973, לא 1967",
            ["בלפור הייתה ב־1948", "אין קשר למלחמות", "המשפט תקין"],
            "1967: ששת הימים. 1973: יום הכיפורים. שתיהן מלחמות, תאריכים שונים.",
            "Medium", "tutor",
            stem="«ב־1967 פרצה מלחמת יום הכיפורים בהפתעה.»",
        ),
        _ready(
            "history", topic, "learn_hi_head_1",
            "לאיזה אירוע זה מתאים?",
            "החלטת כ״ט בנובמבר 1947",
            ["הצהרת בלפור", "מלחמת ששת הימים", "עלייה ראשונה"],
            "האו״ם החליט על חלוקה ב־1947, לפני ההכרזה על המדינה.",
            "Easy", "headline",
            passage="העצרת הכללית של האומות המאוחדות מצביעה על תוכנית חלוקה לשתי מדינות.",
        ),
        _ready(
            "history", topic, "learn_hi_tutor_3",
            "מה הטעות?",
            "חוקי נירנברג הם בגרמניה של שנות ה־30, לא בישראל",
            ["אושוויץ היה בלונדון", "אין קשר לשואה", "המשפט תקין"],
            "נירנברג: חוקי גזע בגרמניה הנאצית. לא חוקי מדינת ישראל.",
            "Hard", "tutor",
            stem="«חוקי נירנברג הם החוקים הראשונים של הכנסת ב־1949.»",
        ),
    ]
    return topic, theory, rows


def _english():
    topic = "Same family, right form"
    theory = (
        "A short wrong sentence. Find the grammar break: tense, to+verb, or a look-alike word."
    )
    rows = [
        _ready(
            "english", topic, "learn_en_tutor_1",
            "What is wrong?",
            "After to we need the base verb",
            ["The noun is plural", "A comma is missing", "The sentence is fine"],
            "to + work, not to working. The base form follows to.",
            "Easy", "tutor",
            stem="The teacher asked the class to working quietly.",
        ),
        _ready(
            "english", topic, "learn_en_fam_1",
            "Which word fits this family?",
            "writer",
            ["white", "right", "wait"],
            "write, writer, writing share a root. white only sounds close.",
            "Easy", "family",
            stem="write, writing, writer",
        ),
        _ready(
            "english", topic, "learn_en_tutor_2",
            "What is wrong?",
            "Past tense needed, not present",
            ["Missing a capital letter only", "Wrong plural", "Nothing is wrong"],
            "Yesterday points to past: went, not go.",
            "Medium", "tutor",
            stem="Yesterday she go to the library.",
        ),
        _ready(
            "english", topic, "learn_en_tutor_3",
            "What is wrong?",
            "Subject and verb do not agree",
            ["The article is extra", "A preposition is missing", "It is correct"],
            "He walks, not he walk. Third person singular takes -s.",
            "Easy", "tutor",
            stem="He walk to school every morning.",
        ),
    ]
    return topic, theory, rows


def _geography():
    topic = "קריאה של מקום"
    theory = (
        "בלי מפה על המסך: תיאור קצר של מקום, וצריך לשייך אותו לאזור הנכון. "
        "זה מאמן תמונה בראש, לא ניחוש בין שמות."
    )
    rows = [
        _ready(
            "geography", topic, "learn_ge_head_1",
            "על איזה אזור מדובר?",
            "השפלה",
            ["החרמון", "הערבה הדרומית", "חוף אילת"],
            "גבעות נמוכות בין ההר לחוף הן השפלה, לא פסגת חרמון ולא ערבה.",
            "Easy", "headline",
            passage="אזור של גבעות נמוכות בין הרי יהודה למישור החוף, חקלאות ושדות.",
        ),
        _ready(
            "geography", topic, "learn_ge_head_2",
            "על איזה מקום מדובר?",
            "ים המלח",
            ["כנרת", "ים סוף", "הירדן התיכון"],
            "הנקודה הנמוכה בעולם, מליחות גבוהה: ים המלח, לא כנרת מתוקה.",
            "Easy", "headline",
            passage="אגם מלוח מאוד, הנקודה היבשתית הנמוכה בעולם, בין ישראל לירדן.",
        ),
        _ready(
            "geography", topic, "learn_ge_tutor_1",
            "מה הטעות?",
            "חיפה היא עיר נמל בצפון, לא בנגב",
            ["ירושלים היא עיר נמל", "אין נמל בישראל", "המשפט תקין"],
            "חיפה על הכרמל והמפרץ. באר שבע בנגב. לא מחליפים.",
            "Medium", "tutor",
            stem="«חיפה היא עיר הבירה של הנגב, ליד אילת.»",
        ),
        _ready(
            "geography", topic, "learn_ge_head_3",
            "לאן זה שייך?",
            "הגליל",
            ["הערבה", "מישור החוף הדרומי", "הנגב המערבי"],
            "הרים בצפון, כפרים ויישובים: גליל, לא ערבה יבשה בדרום.",
            "Medium", "headline",
            passage="רכסי הרים בצפון הארץ, כפרים ערביים ויהודיים, גשם רב יחסית.",
        ),
    ]
    return topic, theory, rows


def _physics():
    topic = "שגיאה בדרך"
    theory = (
        "מישהו פתר שאלה בפיזיקה ומסר הסבר. אתם מחפשים את השבר בדרך, לא את המספר הסופי."
    )
    rows = [
        _ready(
            "physics", topic, "learn_ph_tutor_1",
            "מה הטעות?",
            "ערבבו מסה עם משקל",
            ["שכחו יחידות זמן", "השתמשו באור במקום במהירות", "אין טעות"],
            "מסה בקילוגרם. משקל הוא כוח, בניוטון. לא אותה כמות.",
            "Easy", "tutor",
            stem="«המסה של הילד היא 400 ניוטון.»",
        ),
        _ready(
            "physics", topic, "learn_ph_est_1",
            "רכב נוסע 20 מ׳ ב־2 שניות. המהירות הממוצעת",
            "10 מ׳ לשנייה",
            ["40 מ׳ לשנייה", "2 מ׳ לשנייה", "0.1 מ׳ לשנייה"],
            "דרך חלקי זמן: 20÷2=10. לא מכפילים.",
            "Easy", "estimate",
        ),
        _ready(
            "physics", topic, "learn_ph_tutor_2",
            "מה הטעות?",
            "כוח ומסה הפוכים בנוסחה",
            ["שכחו את היחידה מטר", "אין כאן תאוצה", "הדרך נכונה"],
            "F=ma, כלומר a=F/m. לא F×m.",
            "Medium", "tutor",
            stem="«תאוצה = כוח כפול מסה.»",
        ),
        _ready(
            "physics", topic, "learn_ph_tutor_3",
            "מה הטעות?",
            "אנרגיה קינטית תלויה במהירות בריבוע, לא בחיבור",
            ["אין קשר למסה", "יחידת האנרגיה היא מטר", "המשפט תקין"],
            "Ek=½mv². מכפילים במהירות בריבוע, לא מוסיפים אותה.",
            "Hard", "tutor",
            stem="«אנרגיה קינטית = מסה ועוד מהירות.»",
        ),
    ]
    return topic, theory, rows


def _chemistry():
    topic = "שגיאה במעבדה"
    theory = (
        "מסקנה חפוזה מניסוי. אתם אומרים מה לא נכון במסקנה, לא ממציאים ניסוי חדש."
    )
    rows = [
        _ready(
            "chemistry", topic, "learn_ch_tutor_1",
            "מה הטעות?",
            "ערבבו אטום עם מולקולה",
            ["שכחו את הצבע של הגז", "אין פרוטונים", "המסקנה תקינה"],
            "מולקולת חמצן היא O₂, שני אטומים. אטום הוא יחידה אחת.",
            "Easy", "tutor",
            stem="«מולקולת חמצן היא אטום אחד של O.»",
        ),
        _ready(
            "chemistry", topic, "learn_ch_est_1",
            "pH 3 לעומת pH 7. החומציות",
            "חומצי יותר ממים",
            ["בסיסי כמו סבון", "נייטרלי לגמרי", "זהה ל־7"],
            "מתחת ל־7 חומצי. 3 חומצי יותר מ־7, לא בסיסי.",
            "Easy", "estimate",
        ),
        _ready(
            "chemistry", topic, "learn_ch_tutor_2",
            "מה הטעות?",
            "איזוטופים נבדלים בנויטרונים, לא בפרוטונים",
            ["אין להם גרעין", "כולם גזים", "המשפט תקין"],
            "אותו מספר פרוטונים (אותו יסוד), מספר נויטרונים שונה.",
            "Medium", "tutor",
            stem="«איזוטופים הם יסודות עם מספר פרוטונים שונה.»",
        ),
        _ready(
            "chemistry", topic, "learn_ch_tutor_3",
            "מה הטעות?",
            "מלח בישול הוא תרכובת, לא יסוד",
            ["אין יונים במלח", "נתרן הוא מולקולה", "המסקנה תקינה"],
            "NaCl תרכובת מנתרן וכלור. יסוד הוא סוג אטום אחד.",
            "Medium", "tutor",
            stem="«מלח בישול הוא יסוד כימי בשם נתרן.»",
        ),
    ]
    return topic, theory, rows
