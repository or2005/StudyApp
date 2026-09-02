"""מאגר שחרור: שיעורים ותרגולים מקוריים לפי רמה, מתחיל / בינוני / מתקדם.

השאלות נוצרות מטבלאות ידע ומנוסחאות אמיתיות (אחוזים, יחס, דקדוק, עובדות
ציבוריות). לא הטעיות, לא העתקת שאלונים. כל פריט מקבל הסבר מלא.
"""
from __future__ import annotations

from core.bagrut_packs import T

EASY = "שיעור עיוני"
MID = "רמה בינונית"
ADV = "מימ״ד / בגרות"


def _q(question, correct, wrongs, why, diff, hint=""):
    return (question, correct, wrongs, why, diff, hint)


def _why(lead: str, detail: str) -> str:
    return (
        f"{lead} {detail} "
        "אם טעיתם, חזרו לשיעור, פסלו תשובות שלא מתאימות ליחידות או להגדרה, "
        "ובדקו שוב מה בדיוק נשאל."
    )


def packs_for(key: str) -> list[tuple[str, str, list, str]]:
    return PACKS.get(key) or []


# ---------------------------------------------------------------------------
# חשבון, תרגול כמותי אמיתי, מספרים שונים בכל שאלה
# ---------------------------------------------------------------------------
def _math_percent() -> list:
    rows = []
    cases = []
    for n in (40, 50, 60, 80, 100, 120, 150, 160, 200, 240, 250, 300, 360, 400, 480):
        for p in (10, 20, 25, 50):
            if (n * p) % 100 == 0:
                cases.append((n, p))
    for n, p in cases:
        val = n * p // 100
        rest = n - val
        wrong = [str(x) for x in (rest, p, n + val, n // max(1, p)) if str(x) != str(val)]
        rows.append(_q(
            f"{p}% מ־{n} הם",
            str(val),
            wrong[:3],
            _why(f"{p}% מ־{n} = ({p}/100)×{n} = {val}.", "זה כפל בשבר עשרוני, לא חיבור האחוז למספר."),
            "Easy" if p in (10, 50) and n <= 200 else "Medium",
        ))
    # עלייה / ירידה
    for start, p, up in ((100, 10, True), (200, 20, True), (80, 25, True), (50, 10, False), (120, 20, False), (250, 10, False)):
        if up:
            val = start + start * p // 100
            rows.append(_q(
                f"מחיר {start} עלה ב־{p}%. המחיר החדש",
                str(val),
                [str(start - start * p // 100), str(p), str(start + p)],
                _why(f"מכפילים ב־(1+{p}/100) = {val}.", "עלייה באחוזים היא כפל, לא «מוסיפים את מספר האחוז»."),
                "Medium",
            ))
        else:
            val = start - start * p // 100
            rows.append(_q(
                f"מחיר {start} ירד ב־{p}%. מה נשאר?",
                str(val),
                [str(start + start * p // 100), str(p), str(start - p)],
                _why(f"מכפילים ב־(1−{p}/100) = {val}.", "הנחה של {p}% אינה מורידה {p} שקלים אלא {p} אחוז."),
                "Medium",
            ))
    return rows


def _math_ratio() -> list:
    rows = []
    triples = [
        (1, 3, 40), (1, 4, 50), (2, 3, 50), (1, 1, 30), (3, 5, 80),
        (2, 5, 70), (1, 2, 45), (4, 5, 90), (1, 5, 60), (3, 7, 100),
        (2, 7, 90), (5, 5, 80), (1, 9, 50), (3, 6, 90), (2, 8, 50),
    ]
    for a, b, total in triples:
        parts = a + b
        if total % parts:
            continue
        unit = total // parts
        small, big = a * unit, b * unit
        rows.append(_q(
            f"יחס {a}:{b} מסכום {total}. החלק הקטן",
            str(small),
            [str(big), str(unit), str(total - unit)],
            _why(f"סך {parts} חלקים, כל חלק {unit}. הקטן {a}×{unit}={small}.", "קודם מוצאים את גודל החלק, אחר כך כופלים."),
            "Easy" if a == 1 and b <= 4 else "Medium",
        ))
        rows.append(_q(
            f"יחס {a}:{b} מסכום {total}. החלק הגדול",
            str(big),
            [str(small), str(unit), str(total)],
            _why(f"החלק הגדול {b}×{unit}={big}.", "בודקים: {small}+{big} חייב להיות {total}."),
            "Medium",
        ))
    props = [(2, 5, 8), (3, 4, 12), (1, 6, 4), (5, 2, 10), (4, 3, 16), (7, 2, 14), (6, 5, 18), (8, 3, 24)]
    for a, b, c in props:
        # a/b = c/x → x = b*c/a
        if (b * c) % a:
            continue
        x = b * c // a
        rows.append(_q(
            f"{a}/{b} = {c}/X. X שווה",
            str(x),
            [str(a * c), str(b + c), str(abs(x - a) or x + 1)],
            _why(f"כפל צלב: {a}·X = {b}·{c} → X={x}.", "פרופורציה: מכפלות האלכסונים שוות."),
            "Hard",
        ))
    return rows


def _math_avg() -> list:
    rows = []
    triples = [(4, 8, 12), (5, 7, 9), (10, 20, 30), (6, 6, 6), (2, 8, 12), (1, 4, 7), (11, 13, 15), (0, 10, 20)]
    for a, b, c in triples:
        s = a + b + c
        avg = s // 3 if s % 3 == 0 else None
        if avg is None:
            continue
        rows.append(_q(
            f"ממוצע {a}, {b}, {c}",
            str(avg),
            [str(s), str(c - a), str(avg + 2)],
            _why(f"סכום {s} חלקי 3 = {avg}.", "ממוצע הוא סכום חלקי מספר האיברים, לא האיבר האמצעי תמיד."),
            "Easy",
        ))
    # missing value
    for avg, n, known_sum in ((10, 5, 38), (8, 4, 21), (12, 6, 60), (7, 5, 28), (15, 4, 45), (9, 3, 20)):
        missing = avg * n - known_sum
        rows.append(_q(
            f"ממוצע {n} מספרים הוא {avg}. סכום {n - 1} מהם {known_sum}. החסר",
            str(missing),
            [str(avg), str(known_sum // n), str(abs(missing - avg) or missing + 3)],
            _why(f"הסכום הכולל {avg}×{n}={avg * n}. החסר {avg * n}−{known_sum}={missing}.", "מוצאים קודם סכום, אחר כך את האיבר החסר."),
            "Hard",
        ))
    return rows


def _math_seq() -> list:
    rows = []
    # arithmetic
    for start, step, k in ((2, 2, 5), (3, 3, 6), (10, 5, 4), (1, 4, 5), (7, 7, 4), (20, -2, 6), (15, 10, 4), (0, 6, 5)):
        seq = [start + i * step for i in range(k)]
        nxt = start + k * step
        shown = ", ".join(str(x) for x in seq)
        rows.append(_q(
            f"{shown}, ... הבא?",
            str(nxt),
            [str(seq[-1] + (1 if step > 0 else -1)), str(seq[-1] * 2), str(step)],
            _why(f"סדרה חשבונית עם הפרש {step}. אחרי {seq[-1]} מגיע {nxt}.", "בודקים את ההפרש בין שני איברים רצופים, לא רק את הראשון."),
            "Easy" if abs(step) <= 5 else "Medium",
        ))
    # geometric
    for start, mul, k in ((2, 2, 5), (3, 3, 4), (5, 2, 5), (1, 4, 4), (10, 2, 4)):
        seq = [start * (mul ** i) for i in range(k)]
        nxt = start * (mul ** k)
        shown = ", ".join(str(x) for x in seq)
        rows.append(_q(
            f"{shown}, ... הבא?",
            str(nxt),
            [str(seq[-1] + mul), str(seq[-1] * (mul + 1)), str(mul)],
            _why(f"סדרה הנדסית: כופלים ב־{mul}. אחרי {seq[-1]} מגיע {nxt}.", "אם היחס קבוע, זה כפל, לא חיבור."),
            "Medium" if mul == 2 else "Hard",
        ))
    return rows


def _math_word() -> list:
    rows = []
    pairs = [(20, 4), (30, 6), (18, 5), (40, 8), (25, 7), (16, 3), (50, 12), (28, 9), (36, 11), (22, 8)]
    for total, gone in pairs:
        left = total - gone
        rows.append(_q(
            f"היו {total} פריטים, נתנו {gone}. כמה נשארו?",
            str(left),
            [str(total + gone), str(gone), str(total)],
            _why(f"{total}−{gone}={left}.", "השאלה היא כמה נשאר, לא כמה נתנו."),
            "Easy",
        ))
    for hours, rate in ((2, 60), (3, 40), (1, 90), (4, 25), (5, 12)):
        dist = hours * rate
        rows.append(_q(
            f"רכב {hours} שעות במהירות {rate} קמ״ש. הדרך",
            f"{dist} ק״מ",
            [f"{hours + rate} ק״מ", f"{rate} ק״מ", f"{hours * 10} ק״מ"],
            _why(f"דרך = מהירות × זמן = {rate}×{hours}={dist}.", "יחידות: קמ״ש × שעות = קילומטרים."),
            "Medium",
        ))
    for price, extra in ((80, 20), (50, 25), (120, 30), (200, 40), (60, 15)):
        pct = 100 * extra // price
        rows.append(_q(
            f"קנה ב־{price} ומכר ב־{price + extra}. הרווח באחוזים",
            f"{pct}%",
            [f"{extra}%", f"{100 * extra // (price + extra)}%", "50%"],
            _why(f"רווח {extra} מתוך {price} = {pct}%.", "אחוז רווח נמדד ממחיר הקנייה, לא מהמכירה."),
            "Hard",
        ))
    return rows


def _math_packs() -> list:
    theory_p = T("אחוזים לתרגול", ["X% מ־N = N×X/100.", "עלייה: כפל ב־(1+p/100).", "ירידה: כפל ב־(1−p/100)."], "20% מ־150 = 30.")
    theory_r = T("יחס", ["סך החלקים = סכום איברי היחס.", "כל חלק = הסכום חלקי מספר החלקים."], "1:3 מ־40 → 10 ו־30.")
    theory_a = T("ממוצע", ["סכום חלקי N.", "איבר חסר = סכום רצוי פחות סכום ידוע."], "ממוצע 6 ו־10 הוא 8.")
    theory_s = T("סדרות", ["חשבונית: הפרש קבוע.", "הנדסית: יחס כפל קבוע."], "2,4,8,16, כופלים ב־2.")
    theory_w = T("בעיות מילוליות", ["מסמנים נעלם.", "יחידות זהות.", "בודקים אם המספר הגיוני."], "סכום 20 הפרש 4 → 8 ו־12.")
    return [
        ("אחוזים, תרגול מודרג", theory_p, _math_percent(), EASY),
        ("יחס ופרופורציה, תרגול", theory_r, _math_ratio(), MID),
        ("ממוצע ואיבר חסר", theory_a, _math_avg(), MID),
        ("סדרות חשבוניות והנדסיות", theory_s, _math_seq(), ADV),
        ("בעיות מילוליות כמותיות", theory_w, _math_word(), ADV),
    ]


# ---------------------------------------------------------------------------
# אנגלית, משפטים מקוריים לפי דפוס דקדוקי
# ---------------------------------------------------------------------------
def _eng_tenses() -> list:
    verbs = [
        ("play", "plays", "played", "playing", "football"),
        ("work", "works", "worked", "working", "in a shop"),
        ("live", "lives", "lived", "living", "in Haifa"),
        ("study", "studies", "studied", "studying", "English"),
        ("visit", "visits", "visited", "visiting", "her aunt"),
        ("cook", "cooks", "cooked", "cooking", "dinner"),
        ("watch", "watches", "watched", "watching", "a film"),
        ("help", "helps", "helped", "helping", "his brother"),
        ("clean", "cleans", "cleaned", "cleaning", "the kitchen"),
        ("walk", "walks", "walked", "walking", "to school"),
        ("call", "calls", "called", "calling", "her friend"),
        ("open", "opens", "opened", "opening", "the window"),
        ("close", "closes", "closed", "closing", "the door"),
        ("need", "needs", "needed", "needing", "help"),
        ("want", "wants", "wanted", "wanting", "a ticket"),
    ]
    rows = []
    for base, s, ed, ing, obj in verbs:
        rows.append(_q(
            f"She ___ {obj} every week.",
            s,
            [base, ed, ing],
            _why(f"Present simple, he/she/it → {s}.", "every week מסמן הרגל, לא עכשיו ולא עבר."),
            "Easy",
        ))
        rows.append(_q(
            f"They ___ {obj} yesterday.",
            ed,
            [base, s, ing],
            _why(f"yesterday = עבר פשוט → {ed}.", "לא מוסיפים s ב־they, ולא ing בלי be."),
            "Easy",
        ))
        rows.append(_q(
            f"Look! He is ___ {obj}.",
            ing,
            [base, s, ed],
            _why(f"Present continuous: be + V-ing → is {ing}.", "Look! מצביע על פעולה ברגע זה."),
            "Medium",
        ))
    return rows


def _eng_prep() -> list:
    rows = []
    days = ["Sunday", "Monday", "Tuesday", "Friday", "Saturday"]
    for d in days:
        rows.append(_q(f"The shop is closed ___ {d}.", "on", ["in", "at", "to"],
                       _why("on + יום בשבוע.", "in לחודש/שנה, at לשעה."), "Easy"))
    months = ["July", "April", "October", "December"]
    for m in months:
        rows.append(_q(f"We travel ___ {m}.", "in", ["on", "at", "to"],
                       _why("in + חודש.", "on ליום, at לשעה."), "Easy"))
    cities = ["Tel Aviv", "London", "Paris", "Haifa", "Eilat"]
    for c in cities:
        rows.append(_q(f"They arrived ___ {c} at night.", "in", ["on", "at the", "to at"],
                       _why("in + עיר.", "arrive in a city; arrive at a small place."), "Medium"))
    rows += [
        _q("The train leaves ___ 7:30.", "at", ["on", "in", "to"], _why("at + שעה.", "on ליום."), "Easy"),
        _q("Wait ___ me, please.", "for", ["to", "on", "at"], _why("wait for someone.", "לא wait to a person."), "Medium"),
        _q("She is good ___ maths.", "at", ["in", "on", "for"], _why("good at + skill.", "good in לא מדויק כאן."), "Medium"),
        _q("I look forward ___ seeing you.", "to", ["for", "on", "at"], _why("look forward to + V-ing.", "to כאן מילת יחס."), "Hard"),
        _q("The book is ___ the table.", "on", ["in", "at", "to"], _why("on = על משטח.", "in = בתוך."), "Easy"),
        _q("He has lived here ___ 2019.", "since", ["for", "from at", "during"], _why("since + נקודת התחלה.", "for + משך."), "Hard"),
        _q("We stayed ___ three days.", "for", ["since", "at", "on"], _why("for + משך זמן.", "since לנקודה."), "Medium"),
    ]
    return rows


def _eng_vocab() -> list:
    pairs = [
        ("The opposite of cheap is", "expensive", ["cheaply", "short", "early"], "cheap ↔ expensive."),
        ("A person who teaches is a", "teacher", ["teach", "taught", "school"], "verb teach → noun teacher."),
        ("We ___ breakfast in the morning.", "eat / have", ["sleep the", "write the always", "open the"], "collocation: have breakfast."),
        ("The place you borrow books is a", "library", ["kitchen", "garage", "stadium"], "library = ספרייה."),
        ("If something is not easy it is", "difficult", ["easy always", "happy", "green"], "difficult = קשה."),
        ("A ___ forecasts the weather.", "forecast / weather report", ["kitchen", "pencil", "shoe"], "weather forecast."),
        ("To ___ a bus is to go on it.", "take / catch", ["eat", "write", "wear"], "take a bus."),
        ("The ___ of a book is its name.", "title", ["window", "meal", "storm"], "title = כותרת."),
    ]
    # fix messy ones - unique clean
    clean = [
        _q("The opposite of cheap is", "expensive", ["cheaply", "short", "early"], _why("cheap ↔ expensive.", "לא בוחרים מילה שנראית דומה."), "Easy"),
        _q("A person who teaches is a", "teacher", ["teach", "taught", "school"], _why("teach → teacher.", "שם עצם של מקצוע."), "Easy"),
        _q("We ___ breakfast at 8:00.", "have", ["sleep", "write", "open"], _why("have breakfast, צירוף קבוע.", "לא eat breakfast חובה, אבל have הוא התשובה כאן."), "Easy"),
        _q("You borrow books from a", "library", ["kitchen", "garage", "stadium"], _why("library = ספרייה.", "bookshop מוכרים, לא משאילים."), "Easy"),
        _q("If a task is not easy it is", "difficult", ["happy", "green", "loud"], _why("difficult = קשה.", "ניגוד ישיר."), "Easy"),
        _q("The name of a book is its", "title", ["window", "meal", "storm"], _why("title = כותרת.", "author הוא הסופר."), "Easy"),
        _q("To get on a bus we ___ it.", "take", ["eat", "wear", "drink"], _why("take a bus.", "צירוף תנועה."), "Medium"),
        _q("A shop assistant ___ customers.", "helps", ["sleeps the", "writes rain", "opens sky"], _why("help customers.", "מקצוע ושירות."), "Easy"),
        _q("If you feel ill you go to a", "doctor", ["baker only", "pilot only", "driver only"], _why("doctor = רופא.", "ill = חולה."), "Easy"),
        _q("We recycle paper to help the", "environment", ["noise", "color", "taste"], _why("recycle → environment.", "שמירת סביבה."), "Medium"),
        _q("The past of go is", "went", ["goed", "goes", "going"], _why("go-went-gone.", "פועל לא סדיר."), "Easy"),
        _q("The past of buy is", "bought", ["buyed", "buys", "buying"], _why("buy-bought-bought.", "לא מוסיפים ed."), "Easy"),
        _q("The past of make is", "made", ["maked", "makes", "making"], _why("make-made-made.", "לא סדיר."), "Easy"),
        _q("Choose the correct form: there ___ two chairs.", "are", ["is", "was always only", "be"], _why("two chairs = רבים → are.", "there is ליחיד."), "Medium"),
        _q("I have already ___ my homework.", "done", ["did", "do", "doing"], _why("present perfect: have + V3 → done.", "already אופייני לזמן הזה."), "Hard"),
        _q("She has lived here ___ 2018.", "since", ["for at", "ago", "during the"], _why("since + year.", "for + period."), "Hard"),
        _q("If it rains, we ___ at home.", "will stay", ["stayed always", "are stay", "staying will"], _why("First conditional: if + present, will + verb.", "לא עבר אחרי if כאן."), "Hard"),
        _q("This is the book ___ I told you about.", "which / that", ["who always", "where the", "when the"], _why("which/that לדבר.", "who לאנשים."), "Hard"),
        _q("He is taller ___ his brother.", "than", ["then", "that", "to"], _why("comparative + than.", "then = אחר כך."), "Medium"),
        _q("There aren't ___ eggs in the fridge.", "any", ["some always in negative", "much egg", "a"], _why("any בשלילה/שאלה.", "some בחיוב בדרך כלל."), "Medium"),
    ]
    return clean + [
        _q(f"A ___ works in a hospital.", "nurse / doctor", ["farmer only", "pilot only", "baker only"], _why("hospital → medical job.", "הקשר מקום-מקצוע."), "Easy"),
    ]
    # The last one has slash answer - unique_options needs exact correct in options. BAD.
    # I'll not include slash answers.


def _eng_vocab_clean() -> list:
    return [
        _q("The opposite of cheap is", "expensive", ["cheaply", "short", "early"], _why("cheap ↔ expensive.", "לא בוחרים מילה שנראית דומה."), "Easy"),
        _q("A person who teaches is a", "teacher", ["teach", "taught", "school"], _why("teach → teacher.", "שם עצם של מקצוע."), "Easy"),
        _q("We ___ breakfast at 8:00.", "have", ["sleep", "write", "open"], _why("have breakfast, צירוף קבוע.", "have ולא open."), "Easy"),
        _q("You borrow books from a", "library", ["kitchen", "garage", "stadium"], _why("library = ספרייה.", "משאילים בספרייה."), "Easy"),
        _q("If a task is not easy it is", "difficult", ["happy", "green", "loud"], _why("difficult = קשה.", "ניגוד ישיר."), "Easy"),
        _q("The name of a book is its", "title", ["window", "meal", "storm"], _why("title = כותרת.", "author הוא הסופר."), "Easy"),
        _q("To get on a bus we ___ it.", "take", ["eat", "wear", "drink"], _why("take a bus.", "צירוף תנועה."), "Medium"),
        _q("A shop assistant ___ customers.", "helps", ["sleeps", "writes", "opens"], _why("help customers.", "מקצוע ושירות."), "Easy"),
        _q("If you feel ill you go to a", "doctor", ["baker", "pilot", "driver"], _why("doctor = רופא.", "ill = חולה."), "Easy"),
        _q("We recycle paper to help the", "environment", ["noise", "color", "taste"], _why("recycle → environment.", "שמירת סביבה."), "Medium"),
        _q("The past of go is", "went", ["goed", "goes", "going"], _why("go-went-gone.", "פועל לא סדיר."), "Easy"),
        _q("The past of buy is", "bought", ["buyed", "buys", "buying"], _why("buy-bought-bought.", "לא מוסיפים ed."), "Easy"),
        _q("The past of make is", "made", ["maked", "makes", "making"], _why("make-made-made.", "לא סדיר."), "Easy"),
        _q("There ___ two chairs in the room.", "are", ["is", "was", "be"], _why("two chairs = רבים → are.", "there is ליחיד."), "Medium"),
        _q("I have already ___ my homework.", "done", ["did", "do", "doing"], _why("present perfect: have + V3 → done.", "already אופייני לזמן הזה."), "Hard"),
        _q("She has lived here ___ 2018.", "since", ["for", "ago", "during"], _why("since + year.", "for + period."), "Hard"),
        _q("If it rains, we ___ at home.", "will stay", ["stayed", "are stay", "staying"], _why("First conditional: if + present, will + verb.", "לא עבר אחרי if כאן."), "Hard"),
        _q("This is the book ___ I told you about.", "that", ["who", "where", "when"], _why("that/which לדבר.", "who לאנשים."), "Hard"),
        _q("He is taller ___ his brother.", "than", ["then", "that", "to"], _why("comparative + than.", "then = אחר כך."), "Medium"),
        _q("There aren't ___ eggs in the fridge.", "any", ["some", "much", "a"], _why("any בשלילה/שאלה.", "some בחיוב בדרך כלל."), "Medium"),
        _q("A ___ works in a hospital.", "nurse", ["farmer", "pilot", "baker"], _why("hospital → medical job.", "הקשר מקום-מקצוע."), "Easy"),
        _q("Please ___ the light before you leave.", "turn off", ["look for", "give up", "take off"], _why("turn off = לכבות.", "phrasal verb."), "Medium"),
        _q("I look forward to ___ you.", "seeing", ["see", "saw", "seen"], _why("look forward to + V-ing.", "to כאן מילת יחס."), "Hard"),
        _q("How ___ water do we need?", "much", ["many", "a few people", "several"], _why("water = uncountable → much.", "many לספירים."), "Medium"),
        _q("She ___ never been to Eilat.", "has", ["have", "is", "was"], _why("she has + V3.", "have ל־I/you/we/they."), "Medium"),
        _q("The film was ___ than the book.", "better", ["more good", "gooder", "best than"], _why("good → better → best.", "לא more good."), "Hard"),
        _q("Could you ___ me the salt?", "pass", ["passing", "passed to", "passes"], _why("Could you + base verb.", "בקשה מנומסת."), "Medium"),
        _q("I'm interested ___ history.", "in", ["on", "at", "for"], _why("interested in.", "צירוף קבוע."), "Medium"),
        _q("He didn't ___ the email.", "send", ["sent", "sends", "sending"], _why("didn't + V1.", "אחרי did לא V2."), "Medium"),
        _q("Let's ___ a break.", "take", ["taking", "took", "taken"], _why("let's + V1.", "take a break."), "Easy"),
    ]


def _eng_packs() -> list:
    return [
        ("Present, past and -ing, drills", T("Tenses", ["every / usually → present simple.", "yesterday → past simple.", "look! / now → be + V-ing."], "She plays; they played; he is playing."), _eng_tenses(), EASY),
        ("Prepositions of time and place", T("Prepositions", ["on + day, in + month/city, at + hour.", "since + point, for + period."], "on Sunday / in July / at 7:30."), _eng_prep(), MID),
        ("Vocabulary and sentence completion", T("Words", ["Learn opposite pairs.", "Irregular past forms.", "Conditionals and perfects at Bagrut 3 units."], "cheap → expensive; go → went."), _eng_vocab_clean(), ADV),
    ]


# ---------------------------------------------------------------------------
# לשון
# ---------------------------------------------------------------------------
def _heb_spelling() -> list:
    pairs = [
        ("כתיב מלא: בית ספר בכתיב מלא", "בית־ספר / בית ספר", ["ביתספר בלי רווח חובה תמיד", "בת ספר", "ביית ספרר"], "יש מקף או רווח, לא מילה אחת דבוקה בלי כלל."),
        ("שורש כ.ת.ב בבניין קל עבר יחיד", "כתב", ["כתיב כפועל עבר", "כותב חובה עבר", "יכתוב עבר"], "עבר: כתב. כותב הוא הווה."),
        ("ניגוד של רחב", "צר", ["ארוך תמיד", "גבוה תמיד", "כבד"], "רחב ↔ צר."),
        ("מילה נרדפת למהיר", "זריז / מהיר", ["איטי", "כבד", "רדום"], "נרדפות: מהיר≈זריז."),
    ]
    # Avoid slash-correct. Clean list:
    items = [
        ("ניגוד של רחב", "צר", ["ארוך", "גבוה", "כבד"], "רחב ↔ צר."),
        ("ניגוד של גבוה", "נמוך", ["רחב", "כבד", "חד"], "גבוה ↔ נמוך."),
        ("ניגוד של חם", "קר", ["לח", "יבש", "מתוק"], "חם ↔ קר."),
        ("ניגוד של אור", "חושך", ["צבע", "רעש", "טעם"], "אור ↔ חושך."),
        ("נרדפת למהיר", "זריז", ["איטי", "כבד", "רדום"], "מהיר ≈ זריז."),
        ("נרדפת לשמח", "עליז", ["עצוב", "כועס", "עייף"], "שמח ≈ עליז."),
        ("נרדפת לגדול", "עצום", ["זעיר", "צר", "דק"], "בהקשר של גודל."),
        ("שורש ש.מ.ר בפועל עבר", "שמר", ["שומר", "ישמור", "שמירה"], "עבר: שמר."),
        ("שורש ל.מ.ד בהווה יחיד", "לומד", ["למד", "ילמד", "לימוד"], "הווה: לומד."),
        ("שם פעולה של כתב", "כתיבה", ["כתבתי", "כותב", "יכתוב"], "שם פעולה: כתיבה."),
        ("שם פעולה של קרא", "קריאה", ["קראתי", "קורא", "יקרא"], "שם פעולה: קריאה."),
        ("רבים של ספר", "ספרים", ["ספרות תמיד כאן", "ספרי", "ספררים"], "ספר → ספרים."),
        ("רבים של מילה", "מילים", ["מילות חובה תמיד", "מילהים", "מלין"], "מילה → מילים."),
        ("נקבה של מורה (צורת שייכות נפוצה)", "מורה", ["מור", "מוראים", "מורון"], "מורה משמש לשני המינים; ההקשר קובע."),
        ("פיסוק: אחרי שאלה שמים", "סימן שאלה", ["נקודה בלבד תמיד", "פסיק בלבד", "נקודתיים בלבד"], "משפט שאלה נגמר ב־?."),
        ("פיסוק: רשימה קצרה מופרדת ב", "פסיקים", ["סימני קריאה בכל מילה", "נקודתיים בכל מילה", "סוגריים בכל מילה"], "פריטים ברשימה: פסיק."),
        ("סמיכות: בית + ספר", "בית ספר", ["בית של ספר תמיד רק", "הבית ספרים", "ספר בית"], "סמיכות: בית ספר."),
        ("אותיות שימוש בראשי מילה", "מש״ה וכל״ב", ["רק ת״ו", "רק ניקוד", "רק מספרים"], "משה וכלב, אותיות שימוש."),
        ("ה' הידיעה באה", "לפני שם מיודע", ["אחרי כל פועל", "רק בסוף משפט", "רק באנגלית"], "הַבית = מיודע."),
        ("ו' החיבור מחברת", "מילים או משפטים", ["רק מספרים", "רק ניקוד", "רק לועזית"], "דן ודנה."),
    ]
    rows = []
    for q, a, w, why in items:
        rows.append(_q(q, a, w, _why(why, "זה כלל לשון, לא ניחוש לפי צליל."), "Easy"))
    return rows


def _heb_syntax() -> list:
    return [
        _q("במשפט «התלמיד קרא ספר» הנשוא הוא", "קרא", ["התלמיד", "ספר", "ה"], _why("נשוא = מה נאמר על הנושא. כאן הפעולה קרא.", "נושא עושה, נשוא עושה/מתאר."), "Medium"),
        _q("במשפט «התלמיד קרא ספר» הנושא הוא", "התלמיד", ["קרא", "ספר", "ה"], _why("מי שביצע: התלמיד.", "שאלו מי."), "Medium"),
        _q("מושא ב«קרא ספר» הוא", "ספר", ["התלמיד", "קרא", "את"], _why("מושא = על מה הפעולה. קרא מה? ספר.", "לא הנושא."), "Medium"),
        _q("משפט שמני הוא משפט", "בלי פועל כנשוא מרכזי", ["עם פועל חובה תמיד", "רק שאלה", "רק ציווי"], _why("«דני תלמיד», נשוא שמני.", "אין חובה לפועל."), "Hard"),
        _q("לוואי מתאר", "שם עצם", ["רק פועל", "רק מילת יחס", "רק מספר"], _why("הבית הגדול, גדול לוואי של בית.", "צמוד לשם."), "Medium"),
        _q("תיאור זמן עונה על", "מתי", ["מי", "מה", "כמה כסף"], _why("«בבוקר» = מתי.", "לא נושא."), "Easy"),
        _q("תיאור מקום עונה על", "איפה", ["מתי", "למה", "מי"], _why("«בכיתה» = איפה.", "מקום."), "Easy"),
        _q("גוף ראשון יחיד", "אני", ["אתה", "הם", "אתן"], _why("אני = מדבר על עצמו.", "לא אתה."), "Easy"),
        _q("גוף שני רבים (זכר)", "אתם", ["אני", "הוא", "אנחנו"], _why("פונים לכמה גברים/מעורב.", "לא אני."), "Easy"),
        _q("התאם: הילדות ___ בחצר", "שיחקו", ["שיחק", "שיחקה", "שיחקן ליחיד"], _why("רבות → שיחקו.", "התאם מין ומספר."), "Medium"),
        _q("התאם: הילד ___ בחצר", "שיחק", ["שיחקו", "שיחקה", "שיחקן"], _why("יחיד זכר → שיחק.", "התאם."), "Easy"),
        _q("משפט איחוי מחבר שני משפטים ב", "ו' / אבל / או", ["רק ניקוד", "רק לועזית", "רק מספר"], _why("איחוי = חיבור.", "לא משפט מורכב עם אשר."), "Hard"),
        _q("משפט מורכב מכיל", "פסוקית", ["רק מילה אחת", "רק ניקוד", "רק כותרת"], _why("פסוקית משועבדת, למשל ש־...", "יש תלות."), "Hard"),
        _q("דוגמה לפסוקית ב«ש»", "הספר שהבאתי", ["רק ו' החיבור", "רק ה' הידיעה", "רק מספר"], _why("שהבאתי מגדיר איזה ספר.", "שעבוד."), "Hard"),
        _q("ציווי של שב (יחיד)", "שב", ["ישב", "יושב", "ישבו"], _why("ציווי: שב.", "לא עבר."), "Medium"),
        _q("שלילה בעבר עם פועל", "לא + עבר", ["אל + עבר", "אין + עבר", "בלתי + עבר"], _why("לא כתב. אל לציווי.", "לא ואל אינם זהים."), "Medium"),
        _q("«את» לפני מושא מיודע", "מופיעה לרוב", ["אסורה תמיד", "רק באנגלית", "רק במספרים"], _why("קרא את הספר.", "מושא מיודע."), "Medium"),
        _q("שם תואר ב«בית גדול»", "גדול", ["בית", "ה", "ב"], _why("גדול מתאר את הבית.", "תואר."), "Easy"),
        _q("קמץ ומלא: כתיב מלא של קול", "קול", ["קולל", "כול", "קואל"], _why("כללי האקדמיה, לא מכפילים לחינם.", "כתיב מלא אינו ניחוש."), "Hard"),
        _q("דגש חזק בא אחרי", "אותיות בג״ד כפ״ת במצבים מסוימים / הכפלה", ["רק בסוף מילה תמיד", "רק במספרים", "רק באנגלית"], _why("דגש משפיע על הגיה.", "לא בכל מילה."), "Hard"),
    ]


def _heb_packs() -> list:
    return [
        ("כתיב, שורשים וניגודים, בסיס", T("לשון בסיס", ["ניגודים ונרדפות.", "שורש ובניין.", "רבים ופיסוק."], "רחב↔צר; כתב→כתיבה."), _heb_spelling(), EASY),
        ("תחביר: נושא נשוא מושא", T("משפט", ["נושא = מי.", "נשוא = מה נאמר.", "מושא = על מה הפעולה."], "התלמיד קרא ספר."), _heb_syntax(), MID),
    ]


# ---------------------------------------------------------------------------
# אזרחות / היסטוריה / גאוגרפיה, עובדות ציבוריות, ניסוח מקורי
# ---------------------------------------------------------------------------
def _civics_rows() -> list:
    facts = [
        ("מספר חברי הכנסת", "120", ["70", "100", "61"], "120 ח״כים.", "Easy"),
        ("הרשות המחוקקת בישראל", "הכנסת", ["הממשלה", "בג״ץ", "המשטרה"], "הכנסת מחוקקת.", "Easy"),
        ("הרשות המבצעת", "הממשלה", ["הכנסת", "בג״ץ", "הנשיא כראש מבצעת יום־יום"], "הממשלה מיישמת.", "Easy"),
        ("הרשות השופטת", "בתי המשפט", ["הכנסת", "הממשלה", "העיריות"], "שפיטה נפרדת.", "Easy"),
        ("זכות הצבעה לכנסת מגיל", "18", ["21 תמיד", "16 תמיד", "30"], "בגיר.", "Easy"),
        ("בחירות לכנסת הן", "כלליות, חשאיות, ארציות, יחסיות", ["רק לראש עיר", "גלויות חובה", "רק למפלגה אחת"], "עקרונות בחירות.", "Medium"),
        ("אחוז חסימה נועד ל", "למנוע ריבוי מפלגות זעירות", ["לבטל אופוזיציה", "לבחור נשיא", "להעלות מס"], "סף כניסה.", "Hard"),
        ("אופוזיציה היא", "סיעות שאינן בקואליציה", ["הממשלה עצמה", "בג״ץ", "צה״ל"], "פיקוח פרלמנטרי.", "Medium"),
        ("נשיא המדינה נבחר על ידי", "הכנסת", ["העם בקלפי ישירה תמיד", "בג״ץ", "האו״ם"], "בחירה עקיפה.", "Medium"),
        ("חוק יסוד הוא", "נורמה עליונה יחסית לחוק רגיל", ["תקנון בית ספר", "צו עירוני", "החלטת שר בלבד"], "מעמד מיוחד.", "Hard"),
        ("בג״ץ דן בעיקר ב", "עתירות נגד רשויות", ["סכסוך שכנים על גדר", "משחק כדורגל", "מבחן בגרות"], "משפט מינהלי.", "Medium"),
        ("הפרדת רשויות נועדה ל", "הגבלת שלטון", ["חיזוק שלטון יחיד", "ביטול בחירות", "סגירת עיתונים"], "איזונים ובלמים.", "Medium"),
        ("חופש הביטוי", "זכות יסוד שאינה מוחלטת", ["מוחלט תמיד כולל אלימות", "לא קיים", "רק לשלטון"], "יש גבול בחוק.", "Hard"),
        ("הכרזת העצמאות נקראה ב", "14 במאי 1948 בתל אביב", ["1967 בירושלים", "1979 בקהיר", "1917 בלונדון"], "ה׳ באייר תש״ח.", "Easy"),
        ("זכות השבות נוגעת ל", "עליית יהודים לישראל", ["רק תיירות", "רק מס", "רק בחירות"], "חוק השבות.", "Medium"),
        ("שלטון החוק פירושו", "השלטון כפוף לחוק כמו האזרח", ["השלטון מעל החוק", "אין חוקים", "רק צבא מחוקק"], "גם השלטון מוגבל.", "Hard"),
        ("מועצה מקומית היא", "שלטון מקומי", ["הכנסת", "בג״ץ", "משרד הביטחון"], "עירייה/מועצה.", "Easy"),
        ("תקציב המדינה מאושר ב", "הכנסת", ["בג״ץ בלבד", "עירייה בלבד", "או״ם"], "חקיקת תקציב.", "Medium"),
        ("חסינות ח״כ", "מוגבלת ואינה מבטלת פלילים לגמרי", ["פוטרת מכל חוק תמיד", "לא קיימת", "שייכת לראש עיר בלבד"], "יש כללים.", "Hard"),
        ("משאל עם בישראל", "נדיר / כמעט לא בשימוש שוטף", ["חובה כל שנה", "מחליף את הכנסת תמיד", "בוחר שופטים"], "הדמוקרטיה בעיקרה ייצוגית.", "Hard"),
        ("מבקר המדינה", "בודק את הרשות המבצעת", ["מחוקק במקום הכנסת", "ממנה שרים", "פוקד על צה״ל בקרב"], "ביקורת.", "Medium"),
        ("יועמ״ש לממשלה", "יועץ משפטי בכיר לרשות המבצעת", ["ראש הכנסת", "נשיא בית משפט תמיד אותו אדם", "ראש מוסד"], "ייעוץ וייצוג משפטי.", "Hard"),
        ("קואליציה נבנית", "אחרי הבחירות כדי להשיג רוב", ["לפני הקלפי תמיד כחוק", "על ידי בג״ץ בלבד", "על ידי ראש עיר"], "הרכבת ממשלה.", "Medium"),
        ("זכות הקניין", "הגנה על רכוש במגבלות החוק", ["גניבה מותרת", "רק לשרים", "אין רכוש פרטי בחוק"], "זכות אדם.", "Medium"),
        ("שוויון בפני החוק", "אותו חוק חל על כולם", ["רק על מיעוטים", "רק על הרוב", "רק על תיירים"], "עקרון דמוקרטי.", "Easy"),
    ]
    return [_q(a, b, c, _why(d, "זה חומר אזרחות לבגרות/מימ״ד, לא סיסמה."), e) for a, b, c, d, e in facts]


def _history_rows() -> list:
    facts = [
        ("הצהרת בלפור היא משנת", "1917", ["1948", "1967", "1973"], "הצהרת בריטניה על בית לאומי.", "Medium"),
        ("החלטת כ״ט בנובמבר", "1947", ["1948", "1967", "1917"], "החלטת החלוקה באו״ם.", "Easy"),
        ("הקמת המדינה", "1948", ["1947", "1967", "1973"], "ה׳ באייר תש״ח.", "Easy"),
        ("מלחמת ששת הימים", "1967", ["1948", "1973", "1982"], "יוני 1967.", "Easy"),
        ("מלחמת יום הכיפורים", "1973", ["1967", "1948", "1956"], "תשל״ד.", "Easy"),
        ("מבצע קדש / סיני", "1956", ["1967", "1973", "1948"], "1956.", "Medium"),
        ("הסכם השלום עם מצרים", "1979", ["1967", "1948", "1993"], "קמפ דיוויד הוביל לשלום 1979.", "Medium"),
        ("הסכמי אוסלו", "שנות ה־90", ["1948", "1967", "1917"], "תהליך מדיני עם אש״ף.", "Medium"),
        ("השואה התרחשה בעיקר ב", "מלחמת העולם השנייה", ["מלחמת העצמאות", "ששת הימים", "לבנון השנייה"], "1939-1945 בהקשר האירופי.", "Easy"),
        ("אושוויץ הוא", "מחנה השמדה/ריכוז נאצי", ["קרב ב־1948", "עיר בנגב", "הסכם שלום"], "סמל השואה.", "Easy"),
        ("חוקי נירנברג", "חקיקה גזעית נאצית", ["חוקי הכנסת 1948", "הצהרת בלפור", "מגילת העצמאות"], "שלילת זכויות יהודים בגרמניה.", "Hard"),
        ("ועידת אוויאן", "דיון בינלאומי על פליטים יהודים לפני המלחמה, סגירת שערים", ["הקמת צה״ל", "הסכם עם מצרים", "כ״ט בנובמבר"], "1938.", "Hard"),
        ("המרד בגטאות קשור ל", "התנגדות יהודית בשואה", ["מלחמת לבנון", "אוסלו", "קדש"], "למשל גטו ורשה 1943.", "Medium"),
        ("הצהרת העצמאות נחתמה ב", "תל אביב", ["ירושלים המזרחית", "חיפה בלבד", "שכם"], "מוזיאון תל אביב.", "Medium"),
        ("דוד בן־גוריון", "ראש הממשלה הראשון", ["נשיא ארה״ב", "ראש אש״ף", "מלך ירדן"], "הכריז על המדינה.", "Easy"),
        ("חיים ויצמן", "נשיא ראשון של ישראל", ["רמטכ״ל 1967", "ראש הממשלה ב־1973", "נשיא מצרים"], "נשיא.", "Medium"),
        ("המנדט הבריטי בארץ ישראל", "שלטון בריטי בין מלחמות העולם עד 1948", ["שלטון עות׳מאני אחרי 1948", "שלטון צרפתי בנגב", "שלטון אמריקאי"], "אחרי מלחמת העולם הראשונה.", "Medium"),
        ("העלייה הראשונה", "סוף המאה ה־19", ["1967", "1973", "2000"], "ראשית הציונות המעשית.", "Hard"),
        ("קונגרס באזל", "1897, הרצל והקונגרס הציוני", ["1948", "1967", "1917 בלבד"], "מדינה יהודית כמטרה.", "Hard"),
        ("האו״ם נוסד ב", "1945", ["1917", "1948", "1967"], "אחרי מלחמת העולם השנייה.", "Medium"),
        ("מלחמת העולם הראשונה", "1914-1918", ["1939-1945", "1948", "1967"], "לא השנייה.", "Easy"),
        ("מלחמת העולם השנייה", "1939-1945", ["1914-1918", "1948", "1967"], "השואה בהקשרה.", "Easy"),
        ("הקו הירוק", "קווי 1949", ["גבול 1967 אחרי הסיפוח כקו ירוק", "חומת ברלין", "תעלת סואץ"], "שביתת נשק.", "Hard"),
        ("איחוד ירושלים במזרח העיר", "1967", ["1948 במלואה", "1979", "1917"], "אחרי ששת הימים.", "Medium"),
        ("רצח רבין", "1995", ["1948", "1967", "1973"], "ראש ממשלה שנרצח.", "Medium"),
    ]
    return [_q(a, b, c, _why(d, "לא מבלבלים בין מלחמות ותאריכים."), e) for a, b, c, d, e in facts]


def _geo_rows() -> list:
    capitals = [
        ("צרפת", "פריז", "אירופה"),
        ("גרמניה", "ברלין", "אירופה"),
        ("איטליה", "רומא", "אירופה"),
        ("ספרד", "מדריד", "אירופה"),
        ("יוון", "אתונה", "אירופה"),
        ("מצרים", "קהיר", "אפריקה"),
        ("ירדן", "עמאן", "אסיה"),
        ("לבנון", "ביירות", "אסיה"),
        ("סוריה", "דמשק", "אסיה"),
        ("טורקיה", "אנקרה", "אסיה"),
        ("סעודיה", "ריאד", "אסיה"),
        ("עיראק", "בגדאד", "אסיה"),
        ("איראן", "טהראן", "אסיה"),
        ("הודו", "ניו דלהי", "אסיה"),
        ("סין", "בייג׳ין", "אסיה"),
        ("יפן", "טוקיו", "אסיה"),
        ("ארה״ב", "וושינגטון", "אמריקה"),
        ("קנדה", "אוטווה", "אמריקה"),
        ("ברזיל", "ברזיליה", "אמריקה"),
        ("ארגנטינה", "בואנוס איירס", "אמריקה"),
        ("אוסטרליה", "קנברה", "אוקיאניה"),
        ("בריטניה", "לונדון", "אירופה"),
        ("רוסיה", "מוסקבה", "אירופה/אסיה"),
        ("פולין", "ורשה", "אירופה"),
        ("אוקראינה", "קייב", "אירופה"),
        ("אתיופיה", "אדיס אבבה", "אפריקה"),
        ("דרום אפריקה, אחת הבירות", "פרטוריה", "אפריקה"),
        ("מרוקו", "רבאט", "אפריקה"),
        ("קניה", "ניירובי", "אפריקה"),
        ("מקסיקו", "מקסיקו סיטי", "אמריקה"),
    ]
    rows = []
    for country, cap, cont in capitals:
        others = [c[1] for c in capitals if c[1] != cap][:3]
        rows.append(_q(
            f"בירת {country} היא",
            cap,
            others,
            _why(f"{cap} היא בירת {country} ({cont}).", "לא מבלבלים עם עיר גדולה שאינה בירה (למשל סידני, ניו יורק, ריו)."),
            "Easy",
        ))
        rows.append(_q(
            f"{country} נמצאת בעיקר ב",
            cont.split("/")[0],
            [x for x in ("אירופה", "אסיה", "אפריקה", "אמריקה") if x not in cont][:3],
            _why(f"{country} משויכת ליבשת {cont}.", "יבשת ≠ בירה."),
            "Easy",
        ))
    extra = [
        _q("הים המלח נמצא", "בין ישראל לירדן, הנקודה הנמוכה ביבשה", ["בהרי האלפים", "במרכז אפריקה", "בקוטב"], _why("בקע השבר הסורי־אפריקני.", "מליחות גבוהה."), "Medium"),
        _q("הכנרת היא", "אגם מתוק בצפון", ["ים מלח דרומי", "נהר באירופה", "הר בנגב"], _why("מקור מים עילי חשוב.", "לא ים המלח."), "Easy"),
        _q("הנגב הוא", "אזור מדברי בדרום ישראל", ["חוף הים התיכון בלבד", "הגולן", "עמק יזרעאל"], _why("מדבר ופיתוח דרום.", "לא צפון."), "Easy"),
        _q("השבר הסורי־אפריקני קשור ל", "רעידות אדמה ובקעת הירדן", ["הרי ההימלאיה בלבד", "האמזונס", "הקוטב הצפוני"], _why("גבול לוחות.", "סיכון סייסמי."), "Hard"),
        _q("אקלים ים־תיכוני בישראל אופייני ל", "קיץ חם יבש וחורף גשום במרכז ובחוף", ["שלג כל הקיץ", "גשם יומיומי בנגב", "קור קוטבי"], _why("ים תיכוני ≠ מדברי.", "הנגב יבש יותר."), "Medium"),
        _q("הירדן זורם בעיקר", "מצפון לדרום אל ים המלח", ["ממערב למזרח לים התיכון כולו כנחל יחיד", "מהנגב לחרמון", "מאילת לחיפה"], _why("בקעת הירדן.", "כיוון הזרימה."), "Medium"),
        _q("הים האדום נושק לישראל ב", "אילת", ["חיפה", "נתניה", "טבריה"], _why("מפרץ אילת.", "לא הים התיכון."), "Easy"),
        _q("הים התיכון נושק לישראל ב", "השרון והחוף", ["אילת בלבד", "ים המלח", "החרמון"], _why("חוף מערבי.", "לא אילת."), "Easy"),
        _q("החרמון הוא", "הר בצפון, שלג בחורף", ["הר געש באילת", "אי בכנרת", "חולות הנגב"], _why("גובה ושלג.", "לא מדבר."), "Easy"),
        _q("עיור פירושו", "גידול האוכלוסייה בערים", ["רק חקלאות", "רק יערות", "ביטול ערים"], _why("תהליך מרחבי.", "לא בהכרח תעשייה בלבד."), "Medium"),
        _q("חקלאות שלחין נשענת על", "השקיה מתוכננת", ["רק גשם מובטח כל יום", "שלג בקיץ", "מי ים בלי התפלה"], _why("בארץ יבשה, מים מתוכננים.", "בעיקר בערבה/נגב."), "Hard"),
        _q("קו המשווה הוא", "0 מעלות רוחב", ["90 מעלות", "קו אורך 180 בלבד", "קו גובה הר"], _why("רוחב גאוגרפי.", "לא אורך."), "Medium"),
        _q("קוטב צפוני", "90°N", ["0°", "קו המשווה", "180°E בלבד"], _why("קצה כדור הארץ צפון.", "קור קיצוני."), "Easy"),
        _q("מדבור הוא", "התרחבות תנאי מדבר", ["הצפה תמיד", "התקרחות תמיד", "בניית עיר"], _why("פגיעה בקרקע וצומח.", "סכנה סביבתית."), "Hard"),
    ]
    return rows + extra


def _chem_rows() -> list:
    rows = [
        _q("חלקיק חיובי בגרעין", "פרוטון", ["אלקטרון", "נויטרון בלבד כחיובי", "פוטון"], _why("פרוטון = +1. אלקטרון שלילי.", "מספר פרוטונים = מספר אטומי."), "Easy"),
        _q("חלקיק בלי מטען בגרעין", "נויטרון", ["פרוטון", "אלקטרון", "יון"], _why("נויטרון ניטרלי.", "משפיע על מסה ואיזוטופים."), "Easy"),
        _q("אלקטרון נמצא", "בענן סביב הגרעין", ["רק בגרעין כחיובי", "רק בגרעין כנייטרלי", "מחוץ לאטום תמיד"], _why("מעטפת אלקטרונים.", "לא בגרעין."), "Easy"),
        _q("מספר אטומי הוא", "מספר הפרוטונים", ["מספר הנויטרונים בלבד", "מסה בלבד", "מספר המולקולות"], _why("Z = פרוטונים.", "קובע את היסוד."), "Medium"),
        _q("איזוטופים נבדלים ב", "מספר נויטרונים", ["מספר פרוטונים", "מספר אלקטרונים ביסוד ניטרלי בהכרח שונה", "צבע החנקן"], _why("אותו Z, N שונה.", "מסה שונה."), "Hard"),
        _q("קשר יוני אופייני ל", "מתכת + אל־מתכת", ["שתי אל־מתכות זהות תמיד", "גז אציל + גז אציל", "רק מולקולת מימן"], _why("העברת אלקטרונים.", "NaCl לדוגמה."), "Medium"),
        _q("קשר קוולנטי אופייני ל", "שיתוף אלקטרונים בין אל־מתכות", ["מתכת טהורה תמיד", "גז אציל בלבד", "פלזמה בלבד"], _why("H2O, CO2, O2.", "שיתוף לא העברה."), "Medium"),
        _q("pH=7 הוא", "סביבה ניטרלית", ["חומצה חזקה", "בסיס חזק", "מלח בהכרח"], _why("מים טהורים ~7.", "מתחת ל־7 חומצי."), "Easy"),
        _q("pH=1 הוא", "חומצי מאוד", ["בסיסי מאוד", "ניטרלי", "חסר מים"], _why("נמוך = חומצי.", "לא בסיס."), "Easy"),
        _q("בסיס חזק לדוגמה", "NaOH", ["HCl", "H2SO4", "CO2 כחומצה יחידה"], _why("הידרוקסידים מתכתיים.", "HCl חומצה."), "Medium"),
        _q("חומצה חזקה לדוגמה", "HCl", ["NaOH", "NaCl", "O2"], _why("HCl מימן כלורי.", "NaOH בסיס."), "Medium"),
        _q("תגובת שריפה צורכת בדרך כלל", "חמצן", ["ארגון בלבד", "הליום בלבד", "חנקן אציל"], _why("בעירה + O2.", "תוצרים לרוב CO2 ומים."), "Easy"),
        _q("שימור מסה אומר", "המסה לא נעלמת בתגובה כימית רגילה", ["נעלמים אטומים", "נוצרים יסודות חדשים יש מאין", "המסה הופכת תמיד לאור בלבד"], _why("סופרים אטומים בשני הצדדים.", "מאזנים משוואה."), "Hard"),
        _q("מול הוא", "כמות חלקיקים (מספר אבוגדרו)", ["יחידת לחץ", "יחידת טמפרטורה", "יחידת זמן"], _why("~6.02×10²³.", "n=m/M."), "Hard"),
        _q("נוסחה של מים", "H2O", ["CO2", "NaCl", "O3"], _why("שני מימנים וחמצן.", "לא פחמן דו־חמצני."), "Easy"),
        _q("CO2 הוא", "פחמן דו־חמצני", ["מים", "חמצן מולקולרי", "חנקן"], _why("פחמן + שני חמצנים.", "גז חממה."), "Easy"),
        _q("O2 במעבדה הוא", "חמצן מולקולרי", ["אוזון O3", "מים", "מימן"], _why("דו־אטומי.", "דרוש לבעירה."), "Easy"),
        _q("טבלה מחזורית מסודרת לפי", "מספר אטומי / מבנה אלקטרוני", ["אבן־הב"], "אלפבית שמות בלבד", ["צבע טהור", "טמפרטורת חדר"], "Hard"),
    ]
    # I made a syntax error on last one. Fix below in cleaned list.
    return [r for r in rows if isinstance(r, tuple) and len(r) >= 5]


def _chem_rows_clean() -> list:
    facts = [
        ("חלקיק חיובי בגרעין", "פרוטון", ["אלקטרון", "נויטרון", "פוטון"], "פרוטון = +1.", "Easy"),
        ("חלקיק בלי מטען בגרעין", "נויטרון", ["פרוטון", "אלקטרון", "יון"], "נויטרון ניטרלי.", "Easy"),
        ("אלקטרון נמצא", "בענן סביב הגרעין", ["רק בגרעין", "רק מחוץ לאטום תמיד", "רק במולקולת מלח"], "מעטפת.", "Easy"),
        ("מספר אטומי הוא", "מספר הפרוטונים", ["מספר הנויטרונים בלבד", "מסה בלבד", "מספר המולקולות"], "Z קובע את היסוד.", "Medium"),
        ("איזוטופים נבדלים ב", "מספר נויטרונים", ["מספר פרוטונים", "שם היסוד", "צבע החנקן"], "אותו Z, N שונה.", "Hard"),
        ("קשר יוני אופייני ל", "מתכת + אל־מתכת", ["שתי אל־מתכות זהות תמיד", "גז אציל + גז אציל", "רק מולקולת מימן"], "העברת אלקטרונים.", "Medium"),
        ("קשר קוולנטי אופייני ל", "שיתוף אלקטרונים", ["מתכת טהורה תמיד", "גז אציל בלבד", "פלזמה בלבד"], "H2O, O2.", "Medium"),
        ("pH=7 הוא", "סביבה ניטרלית", ["חומצה חזקה", "בסיס חזק", "מלח בהכרח"], "מים ~7.", "Easy"),
        ("pH=1 הוא", "חומצי מאוד", ["בסיסי מאוד", "ניטרלי", "חסר מים"], "נמוך = חומצי.", "Easy"),
        ("בסיס חזק לדוגמה", "NaOH", ["HCl", "H2SO4", "CO2"], "הידרוקסיד.", "Medium"),
        ("חומצה חזקה לדוגמה", "HCl", ["NaOH", "NaCl", "O2"], "מימן כלורי.", "Medium"),
        ("תגובת שריפה צורכת בדרך כלל", "חמצן", ["ארגון", "הליום", "חנקן אציל"], "בעירה + O2.", "Easy"),
        ("שימור מסה אומר", "המסה לא נעלמת בתגובה כימית רגילה", ["נעלמים אטומים", "נוצרים יסודות יש מאין", "המסה הופכת תמיד לאור"], "מאזנים משוואה.", "Hard"),
        ("מול הוא", "כמות חלקיקים (מספר אבוגדרו)", ["יחידת לחץ", "יחידת טמפרטורה", "יחידת זמן"], "n=m/M.", "Hard"),
        ("נוסחה של מים", "H2O", ["CO2", "NaCl", "O3"], "שני מימנים וחמצן.", "Easy"),
        ("CO2 הוא", "פחמן דו־חמצני", ["מים", "חמצן מולקולרי", "חנקן"], "גז חממה.", "Easy"),
        ("O2 הוא", "חמצן מולקולרי", ["אוזון", "מים", "מימן"], "דו־אטומי.", "Easy"),
        ("הטבלה המחזורית מסודרת לפי", "מספר אטומי", ["אלפבית שמות בלבד", "צבע טהור", "טמפרטורת חדר"], "עמודות = משפחות.", "Hard"),
        ("גז אציל לדוגמה", "הליום / נאון / ארגון", ["חמצן", "מימן", "כלור"], "מעטפת מלאה."),
    ]
    # last has 4 fields if I forget diff - fix
    out = []
    for item in facts:
        if len(item) == 4:
            a, b, c, d = item
            e = "Medium"
        else:
            a, b, c, d, e = item
        # skip slash-correct
        if " / " in b:
            b = "נאון"
            c = ["חמצן", "מימן", "כלור"]
        out.append(_q(a, b, c, _why(d, "כימיה: קוראים את ההגדרה לא את המילה המוכרת."), e))
    # extra stoichiometry numeric
    for n in (2, 3, 4, 5, 6):
        out.append(_q(
            f"2H2 + O2 → 2H2O. אם יש {n} מול O2 (עודף מימן), כמה מול מים?",
            str(2 * n),
            [str(n), str(n + 2), str(2 * n + 1)],
            _why(f"כל מול O2 נותן 2 מול מים → {2 * n}.", "יחס מקדמים במשוואה מאוזנת."),
            "Hard",
        ))
    return out


def _phys_rows() -> list:
    rows = []
    for v, t in ((10, 3), (20, 2), (5, 6), (15, 4), (8, 5), (12, 3)):
        s = v * t
        rows.append(_q(
            f"מהירות קבועה {v} מ׳/ש׳ במשך {t} שניות. הדרך",
            f"{s} מ׳",
            [f"{v + t} מ׳", f"{t} מ׳", f"{v} מ׳"],
            _why(f"s=v·t = {v}×{t}={s}.", "יחידות מטר."),
            "Easy",
        ))
    for m, a in ((2, 3), (5, 2), (10, 1), (4, 4), (3, 5), (6, 2)):
        f = m * a
        rows.append(_q(
            f"F=ma. מסה {m} ק״ג ותאוצה {a} מ׳/ש׳². הכוח",
            f"{f} ניוטון",
            [f"{m + a} ניוטון", f"{a} ניוטון", f"{m} ניוטון"],
            _why(f"F={m}×{a}={f} N.", "ניוטון החוק השני."),
            "Medium",
        ))
    for m, v in ((2, 3), (4, 2), (1, 10), (5, 4), (3, 6)):
        e = m * v * v // 2 if (m * v * v) % 2 == 0 else None
        if e is None:
            continue
        rows.append(_q(
            f"אנרגיה קינטית של מסה {m} ומהירות {v} (במ׳, ק״ג)",
            f"{e} ג׳אול",
            [f"{m * v} ג׳אול", f"{v} ג׳אול", f"{m} ג׳אול"],
            _why(f"Ek=½mv² = {e}.", "מהירות בריבוע, לא ליניארית."),
            "Hard",
        ))
    extras = [
        _q("יחידת כוח", "ניוטון", ["ג׳אול", "ואט", "פאסקל"], _why("N = kg·m/s².", "ג׳אול לאנרגיה."), "Easy"),
        _q("יחידת אנרגיה", "ג׳אול", ["ניוטון", "אמפר", "קלווין"], _why("עבודה ואנרגיה בג׳אול.", "ואט הוא הספק."), "Easy"),
        _q("הספק הוא", "אנרגיה ליחידת זמן", ["מסה לזמן", "כוח למהירות בלי זמן תמיד", "טמפרטורה"], _why("P=W/t, ואט.", "לא כוח."), "Medium"),
        _q("זרם חשמלי נמדד ב", "אמפר", ["וולט", "אוהם", "ואט"], _why("I באמפר.", "V בוולט."), "Easy"),
        _q("מתח נמדד ב", "וולט", ["אמפר", "אוהם", "ניוטון"], _why("V בוולט.", "חוק אוהם V=IR."), "Easy"),
        _q("התנגדות נמדדת ב", "אוהם", ["וולט", "אמפר", "ג׳אול"], _why("R באוהם.", "נגד."), "Easy"),
        _q("חוק אוהם", "V=IR", ["F=ma", "E=mc²", "p=mv"], _why("מתח = זרם × התנגדות.", "מעגל חשמלי."), "Medium"),
        _q("תאוצת כובד על פני כדור הארץ היא בערך", "10 מ׳/ש׳²", ["0", "300000", "1 מ״מ/ש׳"], _why("g≈9.8≈10.", "לא מהירות האור."), "Medium"),
        _q("גל קול באוויר הוא בעיקר", "גל אורך", ["גל רוחב כמו אור בריק", "חלקיק מסה", "זרם ישר"], _why("דחיסות האוויר.", "אור הוא אלקטרומגנטי."), "Hard"),
        _q("אור בריק נע בערך", "300,000 ק״מ/ש׳", ["340 מ׳/ש׳", "10 מ׳/ש׳", "1 ק״מ/ש׳"], _why("c ≈ 3×10^8 מ׳/ש׳.", "340 מ׳/ש׳ זה קול."), "Hard"),
        _q("אנרגיה פוטנציאלית כובדית עולה כש", "מגביהים את הגוף", ["מורידים לקרקע בלי תנועה תמיד", "מכבים אור", "מקררים מים בלבד"], _why("Ep=mgh.", "h גובה."), "Medium"),
        _q("חיכוך בדרך כלל", "מתנגד לתנועה יחסית", ["מגדיל מהירות תמיד", "מבטל מסה", "יוצר אור בלי חום"], _why("כוח מגע.", "יכול גם להניע (הליכה)."), "Medium"),
        _q("מנוף מגדיל", "מומנט / יתרון מכני", ["מסה של כדור הארץ", "מהירות האור", "מטען אלקטרון"], _why("מומנט = כוח × זרוע.", "עבודה לא נוצרת יש מאין."), "Hard"),
        _q("מעגל חשמלי סגור מאפשר", "זרם", ["רק מתח בלי מסלול", "רק מסה", "רק אור בריק"], _why("צריך מסלול רציף.", "נתק = אין זרם."), "Easy"),
        _q("קצר חשמלי הוא", "התנגדות נמוכה מאוד → זרם גדול מסוכן", ["נתק מוחלט תמיד בטוח", "סוללה ריקה בלבד", "חום קור"], _why("זהירות.", "מנתק/נתיך מגנים."), "Hard"),
    ]
    return rows + extras


def _lesson(title, bullets, example, rows, cat):
    return (title, T(title, bullets, example), rows, cat)


PACKS: dict[str, list] = {
    "math": _math_packs(),
    "english": _eng_packs(),
    "hebrew": _heb_packs() + [
        _lesson("אוצר מילים והקשר", ["מילה נלמדת במשפט.", "ניגוד עוזר לזכור.", "לא בוחרים לפי צליל בלבד."], "שמח ≠ עצוב.", _heb_spelling(), ADV),
    ],
    "civics": [
        _lesson("מוסדות וזכויות, תרגול מודרג", ["שלוש רשויות.", "בחירות.", "זכויות עם גבול בחוק."], "120 ח״כים; הממשלה מבצעת.", _civics_rows(), MID),
    ],
    "history": [
        _lesson("ציר זמן ישראלי ומאה ה־20", ["לא מבלבלים 48/67/73.", "שואה בהקשר מלחמת העולם השנייה.", "מסמכים: בלפור, כ״ט בנובמבר, הכרזה."], "1948 הקמת המדינה; 1967 ששת הימים.", _history_rows(), MID),
    ],
    "geography": [
        _lesson("בירות ויבשות, תרגול", ["בירה ≠ העיר הגדולה תמיד.", "יבשת נפרדת ממשטר."], "אוסטרליה, קנברה, לא סידני.", _geo_rows(), EASY),
    ],
    "chemistry": [
        _lesson("אטום, קשרים ו־pH, תרגול", ["Z = פרוטונים.", "יוני מול קוולנטי.", "pH נמוך = חומצי."], "HCl חומצה; NaOH בסיס.", _chem_rows_clean(), MID),
    ],
    "physics": [
        _lesson("מכניקה וחשמל, תרגול חישובי", ["s=vt, F=ma, Ek=½mv².", "V=IR.", "יחידות חשובות כמו הנוסחה."], "2 ק״ג ו־3 מ׳/ש׳² → 6 ניוטון.", _phys_rows(), ADV),
    ],
}
