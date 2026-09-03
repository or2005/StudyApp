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
    return _dedupe_questions(bank)


def _question_rank(question: dict) -> tuple:
    tags = question.get("tags") or []
    return (
        1 if question.get("level") == "3units" else 0,
        1 if "bagrut" in tags or "3units" in tags else 0,
        len(str(question.get("explanation") or "")),
    )


def _dedupe_questions(bank: dict) -> dict:
    """אותה שאלה פעמיים מבלבלת. משאירים נוסח אחד, ומעדיפים בגרות 3 יח״ל."""
    best: dict[str, dict] = {}
    order: list[str] = []
    for question in bank.get("questions") or []:
        stem = " ".join(str(question.get("question") or "").split())
        if not stem:
            continue
        if stem not in best:
            order.append(stem)
            best[stem] = question
        elif _question_rank(question) > _question_rank(best[stem]):
            best[stem] = question
    kept = [best[stem] for stem in order]
    bank["questions"] = kept
    keep_ids = {str(item.get("id")) for item in kept}
    for topic in bank.get("topics") or []:
        topic["questions"] = [
            item for item in (topic.get("questions") or []) if str(item.get("id")) in keep_ids
        ]
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
            "סמיכות וניקוד\n\nסמיכות מחברת שני שמות ליחידה אחת: בית ספר הוא מוסד, לא בית ועוד ספר.\nכותבים בשתי מילים, אלא אם זו מילה אחת קבועה שלמדתם.\nניקוד עוזר לקרוא, אבל במבחן לרוב אין ניקוד — בודקים לפי הצליל והכלל.\n\nדוגמה: בית ספר, על הכיסא, ליד הבית. לא ביתספר ולא עלהכיסא.",
            [
                ("בחרו את הכתיב הנכון למוסד הלימודים", "בית ספר", ["ביתספר", "בית-ספרר", "בת ספר"], "בית ספר בשתי מילים נפרדות.", "Easy"),
                ("בחרו את הכתיב הנכון: דואר + אלקטרוני", "דואר אלקטרוני", ["דואראלקטרוני", "דואר אלקטרוניי", "דואר אלקטרונייי"], "דואר אלקטרוני בשתי מילים.", "Medium"),
                ("בחרו את הצירוף הכתוב נכון", "על הכיסא", ["עלהכיסא", "על הכסאא", "עלכיסא"], "על הכיסא, שתי מילים.", "Easy"),
                ("בחרו את הצירוף הכתוב נכון", "ליד הבית", ["לידבית", "ליד הבת", "ליד הביתת"], "ליד הבית, שתי מילים.", "Easy"),
                ("בחרו את הצירוף הכתוב נכון", "מאחורי הגדר", ["מאחוריגדר", "מאחורי גדר", "מאחורי הגדרר"], "מאחורי הגדר, עם ה׳ הידיעה.", "Medium"),
                ("בחרו את הצירוף הכתוב נכון", "כמו שאמרתי", ["כמושאמרתי", "כמו שאמרת", "כמו שאמרתיי"], "כמו שאמרתי, שתי מילים.", "Easy"),
            ],
        ),
        (
            "חלקי דיבר",
            "חלקי דיבר\n\n1. שם עצם, אדם, חפץ, מקום (כלב, בית, תלמיד).\n2. פועל, פעולה (רץ, כותב, למדה).\n3. שם תואר, תיאור (גדול, ירוק, מהיר).\n4. תואר הפועל, איך עושים (לאט, היטב).\n\nדוגמה: הכלב השחור רץ מהר. עצם: כלב. תואר: שחור. פועל: רץ. תואר הפועל: מהר.",
            [
                ("במשפט 'הכלב רץ' הפועל הוא", "רץ", ["הכלב", "ה", "אין פועל"], "הפעולה.", "Easy"),
                ("במשפט 'בית גדול' שם התואר הוא", "גדול", ["בית", "שם עצם", "אין תואר כאן"], "מתאר את הבית.", "Easy"),
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
            "Present Perfect\n\nבונים כך: have או has + V3 (הצורה השלישית).\nמשתמשים כשיש חוויה עד עכשיו, או תוצאה שנשארת עכשיו.\nsince מצטרף לשנת התחלה. for מצטרף למשך זמן.\n\nדוגמה: I have eaten — כבר אכלתי. We have lived here since 2015 — מאז אותה שנה.",
            [
                ("בחרו את המשפט התקין באנגלית", "I have seen that film.", ["I have saw that film.", "I has seen that film.", "I have see that film."], "have + seen (V3).", "Medium"),
                ("השלימו: She ___ her homework. (present perfect)", "has finished", ["have finished", "has finish", "had finished now"], "she → has + V3.", "Medium"),
                ("השלימו: Have you ever ___ to Paris?", "been", ["be", "went", "go"], "Have you ever been = חוויה עד עכשיו.", "Medium"),
                ("השלימו: They ___ just arrived.", "have", ["has", "had", "are"], "they → have, לא has.", "Easy"),
                ("השלימו: I haven't ___ yet.", "eaten", ["ate", "eat", "eating"], "haven't + V3: eaten.", "Medium"),
                ("השלימו: We have lived here ___ 2015.", "since", ["for", "at", "in"], "since + שנה; for + משך זמן.", "Medium"),
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
