"""תוכן שיעורים נוסף, מתמזג למאגר הקיים בלי לדרוס."""
from __future__ import annotations

from core.bagrut_3units import packs_for as units3_packs_for
from core.bagrut_packs import packs_for
from core.extra_packs import packs_for as extra_packs_for
from core.level_packs import packs_for as level_packs_for
from core.math_packs import packs_for as math_packs_for
from core.passages import packs_for as passage_packs_for
from core.quiz import make_question
from core.release_drills import packs_for as drill_packs_for
from core.release_volume import packs_for as volume_packs_for
from core.moe_wave import packs_for as moe_wave_packs_for
from core.wave3_packs import packs_for as wave3_packs_for
from core.learn_pack import packs_for as learn_packs_for


def _append_topic(
    bank: dict,
    topic: str,
    theory: str,
    rows: list,
    category: str = "שיעור עיוני",
    extra_tags: list | None = None,
    level: str | None = None,
) -> None:
    key = bank.get("subject", "")
    idx = len(bank.get("lessons") or []) + 1
    qs = []
    for i, row in enumerate(rows):
        q, ans, wrong, why = row[:4]
        diff = row[4] if len(row) > 4 else "Easy"
        hint = row[5] if len(row) > 5 else ""
        item = make_question(key, topic, f"{key}_L{idx}_{i+1}", q, ans, wrong, why, diff, hint=hint)
        if extra_tags:
            tags = list(item.get("tags") or [])
            for tag in extra_tags:
                if tag not in tags:
                    tags.append(tag)
            item["tags"] = tags
        if level:
            item["level"] = level
        qs.append(item)
    bank.setdefault("topics", []).append({"topic": topic, "theory_content": theory, "questions": qs})
    bank.setdefault("questions", []).extend(qs)
    lesson = {
        "id": f"{key}_lesson_{idx}",
        "title": f"{idx}. {topic}",
        "category": category,
        "content": theory,
        "topic": topic,
    }
    if level:
        lesson["level"] = level
    bank.setdefault("lessons", []).append(lesson)


def enrich_bank(bank: dict) -> dict:
    key = bank.get("subject", "")
    for topic, theory, rows in EXTRA.get(key) or []:
        _append_topic(bank, topic, theory, rows)
    for topic, theory, rows in packs_for(key):
        _append_topic(bank, topic, theory, rows, category="מימ״ד / בגרות")
    for topic, theory, rows, category in level_packs_for(key):
        _append_topic(bank, topic, theory, rows, category=category)
    for topic, theory, rows, category in extra_packs_for(key):
        _append_topic(bank, topic, theory, rows, category=category)
    for topic, theory, rows, category in wave3_packs_for(key):
        _append_topic(bank, topic, theory, rows, category=category)
    for topic, theory, rows, category in moe_wave_packs_for(key):
        _append_topic(bank, topic, theory, rows, category=category)
    for topic, theory, rows in units3_packs_for(key):
        _append_topic(
            bank,
            topic,
            theory,
            rows,
            category="בגרות 3 יח״ל",
            extra_tags=["3units", "bagrut"],
            level="3units",
        )
    for topic, theory, rows in math_packs_for(key):
        _append_topic(bank, topic, theory, rows, category="מימ״ד, כמותי")
    for topic, theory, questions in passage_packs_for(key):
        _append_ready(bank, topic, theory, questions, category="הבנת הנקרא")
    for topic, theory, rows, category in volume_packs_for(key):
        _append_topic(bank, topic, theory, rows, category=category)
    for topic, theory, rows, category in drill_packs_for(key):
        _append_topic(bank, topic, theory, rows, category=category)
    for topic, theory, questions, category in learn_packs_for(key):
        _append_ready(bank, topic, theory, questions, category=category)
    try:
        from core.theory_enrich import expand_lessons

        bank = expand_lessons(key, bank)
    except Exception:
        pass
    return bank


def _append_ready(bank: dict, topic: str, theory: str, questions: list[dict], category: str) -> None:
    """שאלות שכבר בנויות (קטעי קריאה), בלי לעבור שוב ב־make_question."""
    key = bank.get("subject", "")
    idx = len(bank.get("lessons") or []) + 1
    qs = []
    for item in questions:
        row = dict(item)
        row.setdefault("subject", key)
        row.setdefault("topic", topic)
        qs.append(row)
    bank.setdefault("topics", []).append({"topic": topic, "theory_content": theory, "questions": qs})
    bank.setdefault("questions", []).extend(qs)
    bank.setdefault("lessons", []).append(
        {
            "id": f"{key}_lesson_{idx}",
            "title": f"{idx}. {topic}",
            "category": category,
            "content": theory + "\n\n" + (qs[0].get("passage") or "") if qs else theory,
            "topic": topic,
        }
    )


EXTRA: dict[str, list] = {
    "hebrew": [
        (
            "סמיכות וניקוד בסיסי",
            "סמיכות וניקוד\n\n1. שתי מילים שיוצרות יחידה אחת, לפעמים נכתבות יחד.\n2. ניקוד עוזר לקרוא נכון אבל לא תמיד מופיע בטקסט יומיומי.\n3. בודקים: האם המילה נשמעת טבעית כשמקריאים בקול?\n\nדוגמה: בית ספר, שתי מילים, לא ביתספר.",
            [
                ("איך כותבים נכון?", "בית ספר", ["ביתספר", "בית-ספרר", "בת ספר"], "שתי מילים נפרדות.", "Easy"),
                ("איך כותבים נכון?", "דואר אלקטרוני", ["דואראלקטרוני", "דואר אלקטרוניי", "דואר אלקטרונייי"], "שלוש מילים.", "Medium"),
                ("מה נכון?", "על הכיסא", ["עלהכיסא", "על הכסאא", "עלכיסא"], "על + הכיסא.", "Easy"),
                ("מה נכון?", "ליד הבית", ["לידבית", "ליד הבת", "ליד הביתת"], "ליד הבית.", "Easy"),
                ("מה נכון?", "מאחורי הגדר", ["מאחוריגדר", "מאחורי גדר", "מאחורי הגדרר"], "מאחורי + הגדר.", "Medium"),
                ("מה נכון?", "כמו שאמרתי", ["כמושאמרתי", "כמו שאמרת", "כמו שאמרתיי"], "כמו שאמרתי.", "Easy"),
            ],
        ),
        (
            "חלקי דיבר",
            "חלקי דיבר\n\n1. שם עצם, אדם, חפץ, מקום (כלב, בית, תלמיד).\n2. פועל, פעולה (רץ, כותב, למדה).\n3. שם תואר, תיאור (גדול, ירוק, מהיר).\n4. תואר הפועל, איך עושים (לאט, היטב).\n\nדוגמה: הכלב השחור רץ מהר. עצם: כלב. תואר: שחור. פועל: רץ. תואר הפועל: מהר.",
            [
                ("במשפט 'הכלב רץ' הפועל הוא", "רץ", ["הכלב", "ה", "אין פועל"], "הפעולה.", "Easy"),
                ("במשפט 'בית גדול' שם התואר הוא", "גדול", ["בית", "ב", "אין"], "מתאר את הבית.", "Easy"),
                ("'תלמידה' הוא", "שם עצם", ["פועל", "תואר הפועל", "מילת יחס"], "אדם.", "Easy"),
                ("'לאט' במשפט 'הולך לאט' הוא", "תואר הפועל", ["שם עצם", "פועל", "שם מספר"], "מתאר איך הולכים.", "Medium"),
                ("'ירוק' ב'עלה ירוק' הוא", "שם תואר", ["פועל", "שם עצם חובה", "שאלה"], "צבע מתאר.", "Easy"),
                ("מילת יחס ב'על השולחן'", "על", ["השולחן", "ה", "אין"], "על מקשרת.", "Medium"),
            ],
        ),
    ],
    "english": [
        (
            "Present Perfect בסיסי",
            "Present Perfect\n\n1. have/has + V3 (past participle).\n2. מדבר על חוויה או תוצאה עד עכשיו.\n3. I have visited London. She has finished.\n\nדוגמה: I have eaten. (כבר אכלתי, יש תוצאה עכשיו)",
            [
                ("Choose correct", "I have seen that film.", ["I have saw that film.", "I has seen that film.", "I have see that film."], "have + V3.", "Medium"),
                ("She ___ her homework.", "has finished", ["have finished", "has finish", "had finish now"], "she → has.", "Medium"),
                ("Have you ever ___ to Paris?", "been", ["be", "went", "go"], "have been.", "Medium"),
                ("They ___ just arrived.", "have", ["has", "had", "are have"], "they have.", "Easy"),
                ("I haven't ___ yet.", "eaten", ["ate", "eat", "eating"], "haven't + V3.", "Medium"),
                ("We have lived here ___ 2015.", "since", ["for 2015 only wrong", "at", "in since"], "since + year.", "Medium"),
            ],
        ),
    ],
    "history": [
        (
            "המהפכה התעשייתית",
            "המהפכה התעשייתית\n\n1. מעבר מייצור ידני לייצור במכונות.\n2. התרחבה במאה ה-18-19 באירופה.\n3. שינוי בחקלאות, תחבורה ועבודה.\n\nדוגמה: מכונת הקיטור שינתה תחבורה וייצור.",
            [
                ("המהפכה התעשייתית התרחבה בעיקר ב", "אירופה", ["אמריקה הדרומית בלבד", "אנטארקטיקה", "האוקיינוס השקט"], "אירופה.", "Easy"),
                ("מה שינתה המהפכה התעשייתית?", "ייצור במכונות", ["רק חקלאות בלי מכונות", "רק אמנות", "רק דת"], "מכונות.", "Easy"),
                ("מכונת הקיטור קשורה ל", "תחבורה וייצור", ["רק ציור", "רק מוזיקה", "רק ספורט"], "קיטור.", "Easy"),
                ("תוצאה אפשרית של התעשייה", "עיירות גדלו", ["כולם חזרו לכפרים", "הפסיקו כל מסחר", "ביטלו כל טכנולוגיה"], "עיור.", "Medium"),
                ("לפני המהפכה התעשייתית רבים עבדו ב", "חקלאות ומלאכה ידנית", ["מפעלי מחשבים", "חלל", "רק בבנקים"], "ידני.", "Easy"),
                ("אחת הסיבות לשינוי בתחבורה", "מכונות ורכבות", ["רק גמלים", "רק סירות מפרש בלבד", "אין שינוי"], "רכבות.", "Medium"),
            ],
        ),
    ],
    "geography": [
        (
            "אקלים וגשם",
            "אקלים\n\n1. אקלים = דפוס מזג אוויר לאורך זמן.\n2. מדבר, יבש. טרופי, חם ולח.\n3. גשם חשוב לחקלאות ולמקורות מים.\n\nדוגמה: ישראל, אקלים ים תיכוני: חורף גשום יחסית, קיץ יבש.",
            [
                ("אקלים ים תיכוני מאופיין ב", "קיץ יבש וחורף גשום יחסית", ["שלג כל השנה", "גשם כל יום", "אין עונות"], "ים תיכוני.", "Easy"),
                ("מדבר הוא אזור", "יבש", ["רטוב תמיד", "מכוסה קרח", "תמיד מעונן"], "מעט גשם.", "Easy"),
                ("גשם חשוב ל", "חקלאות ומקורות מים", ["רק לבנייה", "רק לרכב", "לא חשוב"], "מים.", "Easy"),
                ("הרים משפיעים על", "כמות הגשם וטמפרטורה", ["צבע הים בלבד", "מספר הכוכבים", "שום דבר"], "גובה משנה אקלים.", "Medium"),
                ("אקלים טרופי, בדרך כלל", "חם ולח", ["קר מאוד", "יבש לגמרי תמיד", "רק שלג"], "טרופי.", "Easy"),
                ("מקור מים מתוקים יכול להיות", "נהר או אגם", ["רק אוקיינוס מלוח", "רק אש", "רק רוח"], "נהרות.", "Easy"),
            ],
        ),
    ],
    "civics": [
        (
            "בחירות ודמוקרטיה",
            "בחירות בדמוקרטיה\n\n1. אזרחים בוחרים נציגים.\n2. בחירות חופשיות וסודיות.\n3. רוב קובע, אבל זכויות מיעוט נשמרות.\n\nדוגמה: בישראל בוחרים לכנסת כל כמה שנים.",
            [
                ("בדמוקרטיה בוחרים", "נציגים", ["מלך לבד", "רק שופטים", "אף אחד"], "בחירות.", "Easy"),
                ("בחירות סודיות פירושן", "אף אחד לא יודע למי הצבעת", ["כולם רואים", "אין קלפי", "רק בכיתה"], "סודיות.", "Easy"),
                ("בישראל בוחרים ל", "כנסת", ["בית משפט בלבד", "צבא", "עירייה בלבד תמיד"], "כנסת.", "Easy"),
                ("זכות הצבעה היא חלק מ", "זכויות אזרח", ["עונש פלילי", "מס חובה בלבד", "צבא בלבד"], "אזרחות.", "Easy"),
                ("רוב קובע אבל", "זכויות מיעוט נשמרות", ["מיעוט בלי זכויות", "אין חוקים", "אין בית משפט"], "איזון.", "Medium"),
                ("מי שמגיע לגיל הבחירה", "יכול להצביע אם עומד בתנאי החוק", ["אסור לכולם", "רק מורים", "רק שוטרים"], "גיל 18.", "Medium"),
            ],
        ),
    ],
    "chemistry": [
        (
            "תגובות כימיות בסיסיות",
            "תגובות כימיות\n\n1. חומרים מתחברים או מתפרקים ליצור חומרים חדשים.\n2. שומרים על חוק שימור המסה (במערכת סגורה).\n3. דוגמה: בעירה, חמצן + דלק → פחמן דו-חמצני + מים + אנרגיה.\n\nדוגמה: נר בוער, חומרים משתנים.",
            [
                ("בתגובה כימית נוצרים", "חומרים חדשים", ["אותם חומרים בדיוק תמיד", "רק צבע בלי שינוי", "כלום"], "שינוי כימי.", "Easy"),
                ("בעירה דורשת בדרך כלל", "חמצן", ["רק מים", "רק זהב", "רק חנקן בלבד תמיד"], "חמצן.", "Easy"),
                ("שימור מסה במערכת סגורה", "המסה הכוללת נשמרת", ["המסה נעלמת", "המסה תמיד גדלה", "אין חוק"], "שימור.", "Medium"),
                ("סימן לתגובה כימית יכול להיות", "שינוי צבע או גז", ["רק הזזת כוס", "רק קריאת ספר", "שום דבר"], "שינוי נראה.", "Easy"),
                ("מים (H₂O) מורכב מ", "מימן וחמצן", ["זהב וכסף", "רק חנקן", "רק נתרן"], "H ו-O.", "Easy"),
                ("תגובה הפיכה היא", "יכולה ללכת לשני הכיוונים בתנאים מתאימים", ["אף פעם לא", "רק פיצוץ", "רק במעבדה בלי חומרים"], "הפיכות.", "Hard"),
            ],
        ),
    ],
    "physics": [
        (
            "אנרגיה ועבודה",
            "אנרגיה ועבודה\n\n1. אנרגיה = יכולת לבצע עבודה.\n2. קינטית, תנועה. פוטנציאלית, גובה או מתיחה.\n3. אנרגיה לא נעלמת, משנה צורה.\n\nדוגמה: כדור גולל מגבעה, פוטנציאלית הופכת לקינטית.",
            [
                ("אנרגיה קינטית קשורה ל", "תנועה", ["מנוחה בלבד", "צבע", "טעם"], "מהירות.", "Easy"),
                ("אנרגיה פוטנציאלית בגובה קשורה ל", "מיקום בגובה", ["רק צבע", "רק קול", "רק ריח"], "גובה.", "Easy"),
                ("כדור גולל מגבעה, האנרגיה", "עוברת מפוטנציאלית לקינטית", ["נעלמת", "רק גדלה בלי גבול", "לא משתנה"], "המרה.", "Medium"),
                ("יחידת אנרגיה במערכת הבינלאומית", "ג'אול (J)", ["קילוגרם", "מטר בלבד", "שנייה"], "J.", "Medium"),
                ("עבודה בפיזיקה קורית כש", "מפעילים כוח והתזוזה בכיוון הכוח", ["רק מסתכלים", "אין תזוזה", "רק שינוי צבע"], "כוח × דרך.", "Medium"),
                ("חוק שימור אנרגיה אומר", "אנרגיה משנה צורה אבל לא נעלמת", ["נעלמת תמיד", "נוצרת מהכלום", "רק בלילה"], "שימור.", "Easy"),
            ],
        ),
    ],
}
