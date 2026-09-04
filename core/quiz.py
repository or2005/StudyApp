from __future__ import annotations

import random
import re
from typing import Any

_NUM_LEAD = re.compile(r"^([+-]?(?:\d+\.\d+|\d+))(.*)$")
_YEAR = re.compile(r"^(1[0-9]{3}|20[0-2][0-9])$")

# מסיחים כלליים שונים זה מזה, רק כשאין מסיחים אמיתיים מהשאלה.
_GENERIC_DISTRACTORS = (
    "מסקנה שלא נובעת מהנתונים",
    "הגדרה של מושג אחר לגמרי",
    "פרט משני שאינו העיקר כאן",
    "סיבה ותוצאה הפוכות",
    "תאריך או מספר שלא מתאים לשאלה",
    "דוגמה נכונה לשאלה אחרת",
    "פירוש מילולי בלי קשר להקשר",
    "תשובה חלקית שמפספסת את העיקר",
    "הכללה רחבה מדי שלא מדויקת",
    "נתון שלא מופיע בשאלה",
)


def _leading_number(text: str):
    match = _NUM_LEAD.match(str(text).strip())
    if not match:
        return None
    raw, suffix = match.group(1), match.group(2)
    number = float(raw) if "." in raw else int(raw)
    return number, suffix


def _norm(text: str) -> str:
    return " ".join(str(text or "").split()).casefold()


def _too_similar(a: str, b: str) -> bool:
    """דוחים מסיחים כמעט זהים לתשובה או זה לזה."""
    left, right = _norm(a), _norm(b)
    if not left or not right:
        return True
    if left == right:
        return True
    if left in right or right in left:
        shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
        if len(shorter) >= 4 and len(longer) - len(shorter) <= 2:
            return True
    if abs(len(left) - len(right)) <= 1 and len(left) >= 5:
        diff = sum(1 for x, y in zip(left, right) if x != y) + abs(len(left) - len(right))
        if diff <= 1:
            return True
    return False


def _junk_option(correct: str, text: str, prompt: str = "", siblings: list[str] | None = None) -> bool:
    """מסיח שבור: אות בודדת, סיומת מזויפת, או מילוי גנרי ממוספר."""
    got = str(text or "").strip()
    want = str(correct or "").strip()
    blob = str(prompt or "")
    if not got:
        return True
    if got == want:
        return False
    low = got.lower()
    if low.startswith("לא נכון (") or "only wrong" in low or got == "גרסה שגויה":
        return True
    if got.startswith("אין מספיק מידע ("):
        return True
    if len(got) == 1 and not got.isdigit():
        if got.lower() in {"a", "i"}:
            return False
        return True
    if got.endswith("ון") and len(got) > 3:
        base = got[:-2]
        sibling_norms = {_norm(x) for x in (siblings or [])}
        if base == want or (base and base in blob) or _norm(base) in sibling_norms:
            return True
    if want and len(want) >= 2 and got == want + want[-1] and " " not in want:
        return True
    if _too_similar(want, got):
        return True
    return False


def _option_seed(question: dict) -> str:
    return str(
        question.get("id")
        or question.get("question")
        or question.get("correct_answer")
        or "studyapp"
    )


def scrub_question(question: dict) -> dict:
    """מתקן מסיחים שבורים, דואג ל־4 אפשרויות שונות, ומערבב כדי שהנכון לא יישאר תמיד ב־א׳."""
    item = dict(question)
    opts = [str(x) for x in (item.get("options") or [])]
    idx = item.get("answer")
    correct = str(item.get("correct_answer") or "").strip()
    if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
        correct = opts[idx]
    prompt = str(item.get("question") or "")
    if correct:
        wrongs = [x for x in opts if str(x).strip() and str(x).strip() != correct]
        fresh = unique_options(correct, wrongs, prompt=prompt)
        # חיזוק מסיחים: בלי אבסורד ובלי מספרים מטורפים
        try:
            from core.mcq_quality import harden_options

            answer = fresh.index(correct) if correct in fresh else 0
            fresh, answer = harden_options(
                fresh,
                answer,
                topic=str(item.get("topic") or ""),
                prompt=prompt,
            )
            if correct not in fresh:
                fresh = [correct] + [x for x in fresh if x != correct]
                answer = 0
            else:
                answer = fresh.index(correct)
            roller = random.Random(_option_seed(item))
            order = list(range(len(fresh[:4])))
            roller.shuffle(order)
            shuffled = [fresh[i] for i in order]
            item["options"] = shuffled
            item["answer"] = shuffled.index(correct)
            item["correct_answer"] = correct
        except Exception:
            roller = random.Random(_option_seed(item))
            roller.shuffle(fresh)
            item["options"] = fresh
            item["answer"] = fresh.index(correct)
            item["correct_answer"] = correct
    from core.teach import clarify_stem
    from core.stem_fix import clean_topic_label

    item["question"] = clarify_stem(item)
    if item.get("topic"):
        item["topic"] = clean_topic_label(str(item.get("topic") or ""))
    return item


def suggest_distractors(correct: str, prompt: str = "") -> list[str]:
    """מסיחים מגוונים: מספרים קרובים, שנים סבירות, או ניסוחים שונים זה מזה."""
    from core.mcq_quality import distractors_for, is_absurd_option

    parsed = _leading_number(correct)
    out: list[str] = []
    if parsed is not None:
        number, suffix = parsed
        if isinstance(number, int):
            pool = [
                number + 1,
                number - 1,
                number + 2,
                number - 2,
                number * 2,
                number // 2 if abs(number) > 1 else number + 3,
                number + 10,
                abs(number - 10),
                number + max(1, abs(number) // 10),
                number - max(1, abs(number) // 5) if abs(number) > 5 else number + 5,
            ]
            if _YEAR.match(str(number)):
                pool.extend([number + 1, number - 1, number + 10, number - 10, number + 19, number - 30])
            for item in pool:
                text = f"{item}{suffix}"
                if text != str(correct):
                    out.append(text)
        else:
            for item in (number + 1, number - 1, number * 2, number / 2, round(number + 0.5, 2), 0.0):
                text = f"{item:g}{suffix}"
                if text != str(correct):
                    out.append(text)
    else:
        out.extend(distractors_for("", prompt, correct, need=8))
        words = [w for w in re.split(r"\s+", str(correct).strip()) if w]
        if len(words) >= 2:
            out.append(" ".join(words[1:] + words[:1]))
            out.append(words[0])
            if len(words) > 2:
                out.append(" ".join(words[:-1]))
        out.extend(_GENERIC_DISTRACTORS)
        blob = f"{correct} {prompt}"
        if any(ch in blob for ch in "אבגדהוזחטיכלמנסעפצקרשת"):
            out.extend(
                [
                    "מילה נרדפת שלא מתאימה להקשר",
                    "ניגוד במקום התשובה המבוקשת",
                    "שורש או משפחה של מילה אחרת",
                ]
            )
        if re.search(r"[A-Za-z]", str(correct)):
            out.extend(
                [
                    "a similar word with the wrong meaning",
                    "the opposite idea in this sentence",
                    "a grammar form that does not fit",
                ]
            )
    seen = {_norm(correct)}
    clean = []
    for item in out:
        text = str(item).strip()
        key = _norm(text)
        if not text or key in seen:
            continue
        if is_absurd_option(text):
            continue
        if _too_similar(correct, text):
            continue
        clean.append(text)
        seen.add(key)
    return clean


def unique_options(correct: str, wrongs: list[str], prompt: str = "") -> list[str]:
    """ארבע אפשרויות שונות באמת: התשובה + שלושה מסיחים מובחנים."""
    from core.mcq_quality import distractors_for, is_absurd_option

    want = str(correct).strip()
    opts = [want]
    seen = {_norm(want)}
    pool = [str(x).strip() for x in list(wrongs) if str(x).strip()]
    pool.extend(distractors_for("", prompt, want, need=8))

    def try_add(raw: str) -> bool:
        text = str(raw or "").strip()
        key = _norm(text)
        if not text or key in seen:
            return False
        if is_absurd_option(text):
            return False
        if _junk_option(want, text, prompt, siblings=pool + opts):
            return False
        if any(_too_similar(text, existing) for existing in opts):
            return False
        opts.append(text)
        seen.add(key)
        return True

    for item in pool:
        try_add(item)
        if len(opts) >= 4:
            break
    if len(opts) < 4:
        for item in suggest_distractors(want, prompt=prompt):
            try_add(item)
            if len(opts) >= 4:
                break
    # מילוי אחרון רק באפשרויות שונות במפורש
    fallback = list(_GENERIC_DISTRACTORS) + [
        "תשובה שאינה מתאימה לשאלה הזו",
        "פירוש שגוי של המושג המרכזי",
        "בחירה שמבלבלת בין שני נושאים קרובים",
    ]
    for item in fallback:
        if len(opts) >= 4:
            break
        try_add(item)
    n = 1
    while len(opts) < 4:
        text = f"אפשרות שאינה נכונה כאן ({n})"
        if try_add(text):
            n += 1
        else:
            n += 1
            if n > 20:
                break
    return opts[:4]


def polish_explanation(correct: str, explanation: str, topic: str = "", subject: str = "") -> str:
    """משלים הסבר קצר בהוראה מהנושא, לא במלל גנרי."""
    from core.teach import enrich_explanation

    return enrich_explanation(correct, explanation, topic, subject)


def _default_hint(subject: str, topic: str, question: str = "") -> str:
    from core.teach import live_hint

    return live_hint({"topic": topic, "hint": "", "question": question, "subject": subject}, subject)


def make_question(
    subject: str,
    topic: str,
    qid: str,
    question: str,
    correct: str,
    wrongs: list[str],
    explanation: str,
    difficulty: str = "Easy",
    hint: str = "",
    rng: random.Random | None = None,
    kind: str = "normal",
    passage: str = "",
    passage_id: str = "",
) -> dict[str, Any]:
    roller = rng or random.Random(qid)
    options = unique_options(correct, wrongs, prompt=question)
    roller.shuffle(options)
    answer = options.index(str(correct))
    item = {
        "id": qid,
        "subject": subject,
        "topic": topic,
        "question": question,
        "options": options,
        "answer": answer,
        "correct_answer": str(correct),
        "explanation": polish_explanation(correct, explanation, topic, subject),
        "difficulty": difficulty,
        "kind": "trick" if "trick" in qid else kind,
        "tags": [subject, topic, difficulty],
        "hint": hint or _default_hint(subject, topic, question),
    }
    if passage:
        item["kind"] = "passage"
        item["passage"] = passage
        item["passage_id"] = passage_id or qid
    from core.teach import clarify_stem
    from core.stem_fix import clean_topic_label

    item["question"] = clarify_stem(item)
    if item.get("topic"):
        item["topic"] = clean_topic_label(str(item.get("topic") or ""))
    return item


def wrap_subject(key: str, title: str, topics: list[dict[str, Any]]) -> dict[str, Any]:
    questions: list[dict[str, Any]] = []
    lessons: list[dict[str, Any]] = []
    for idx, topic in enumerate(topics, start=1):
        topic_name = topic["topic"]
        theory = topic.get("theory_content") or topic.get("theory") or ""
        block = []
        for q in topic.get("questions") or []:
            q = dict(q)
            q.setdefault("subject", key)
            q.setdefault("topic", topic_name)
            block.append(q)
            questions.append(q)
        topic["questions"] = block
        topic["theory_content"] = theory
        lessons.append(
            {
                "id": f"{key}_lesson_{idx}",
                "title": f"{idx}. {topic_name}",
                "category": "שיעור עיוני",
                "content": theory,
                "topic": topic_name,
            }
        )
    return {
        "subject": key,
        "title": title,
        "study_path": [
            {"step": "read", "title": "שיעור עיוני", "summary": "קוראים בקצב שלכם. משפטים קצרים ודוגמה אחת."},
            {"step": "guided", "title": "שיעור ותרגול", "summary": "אחרי הקריאה: תרגול קצר רק על אותו נושא."},
            {"step": "practice", "title": "תרגול", "summary": "שאלות עם הסבר אחרי כל תשובה."},
            {"step": "mock", "title": "מבחן דמה", "summary": "הציון בסוף, בלי משוב אחרי כל שאלה."},
            {"step": "timed", "title": "מבחן בזמן", "summary": "אותו מבחן, עם שעון לפי הרמה."},
        ],
        "topics": topics,
        "lessons": lessons,
        "questions": questions,
    }
