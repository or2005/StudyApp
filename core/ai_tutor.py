"""מורה AI מקומי (Ollama): פערים שקטים, פרפראזה, שיעור סוקרטי, משגיח אנליסט."""
from __future__ import annotations

import json
import re
import threading
from typing import Any, Callable

from core.config import subject_key, subject_label
from core import ollama_client

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")
_cache_lock = threading.Lock()
_para_cache: dict[str, dict[str, str]] = {}
_gap_cache: dict[str, dict[str, Any]] = {}


def available(storage=None) -> bool:
    if not ollama_client.enabled(storage):
        return False
    return bool(ollama_client.health(storage=storage).get("ok"))


def _clean(text: str, limit: int = 900) -> str:
    blob = " ".join(str(text or "").split())
    blob = blob.replace("\u2014", ": ").replace("\u2013", ", ")
    if len(blob) > limit:
        return blob[: limit - 1].rstrip() + "…"
    return blob


def _parse_json(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        match = _JSON_BLOCK.search(text)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}


def _stem_of(question: dict[str, Any] | None) -> str:
    q = question or {}
    try:
        from core.teach import clarify_stem

        return clarify_stem(q) or str(q.get("question") or "")
    except Exception:
        return str(q.get("question") or "")


def _correct_of(question: dict[str, Any] | None) -> str:
    q = question or {}
    opts = q.get("options") or []
    idx = q.get("answer")
    correct = str(q.get("correct_answer") or "").strip()
    if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
        correct = str(opts[idx])
    return correct


# ---------- פרפראזה / תרגום לשפת יום־יום ----------

_PARA_SYSTEM = """אתה מורה לתלמידי תיכון בישראל.
תפקידך לנסח מחדש שאלות בגרות בשפה פשוטה ויומיומית.
כללים:
- ענה רק בעברית תקנית.
- אל תחשוף את התשובה הנכונה ואל תרמוז עליה.
- אל תשנה מספרים, יחידות או עובדות.
- בלי מקפים ארוכים ובלי אימוג'י.
- החזר JSON בלבד:
{"plain":"סיפור קצר וברור של השאלה","given":"מה נתון","find":"מה צריך למצוא","steps":["שלב קטן 1","שלב קטן 2"]}
"""


def paraphrase_question(
    question: dict[str, Any] | None,
    *,
    storage=None,
    force: bool = False,
) -> dict[str, str]:
    """ממיר שאלת בגרות לשפת יום־יום + נתון/מבוקש."""
    q = question or {}
    qid = str(q.get("id") or "") or _clean(_stem_of(q), 80)
    with _cache_lock:
        if not force and qid in _para_cache:
            return dict(_para_cache[qid])

    stem = _stem_of(q)
    if not stem:
        return {}
    subject = subject_label(q.get("subject") or "")
    topic = str(q.get("topic") or "")
    opts = [str(o) for o in (q.get("options") or [])[:4]]
    user = (
        f"מקצוע: {subject}\nנושא: {topic}\n"
        f"שאלה רשמית:\n{stem}\n"
        f"אפשרויות (אל תגלה מה נכון): {opts}\n"
        "נסח מחדש בשפה פשוטה."
    )
    raw = ollama_client.chat(
        [{"role": "user", "content": user}],
        system=_PARA_SYSTEM,
        storage=storage,
        temperature=0.2,
        format_json=True,
        timeout=30.0,
        num_predict=220,
    )
    data = _parse_json(raw)
    plain = _clean(str(data.get("plain") or raw or ""), 500)
    if not plain:
        # נפילה מקומית בלי AI
        err = ollama_client.last_error()
        plain = f"במילים פשוטות: {stem}"
        result = {
            "plain": plain,
            "given": "קראו מה כתוב בשאלה.",
            "find": "מה בדיוק מבקשים למצוא או לבחור.",
            "steps": "1) סמנו נתון  2) סמנו מבוקש  3) בחרו",
            "source": "fallback",
            "error": err,
        }
        return result

    steps = data.get("steps") or []
    if isinstance(steps, list):
        steps_txt = " · ".join(_clean(str(s), 80) for s in steps[:4] if str(s).strip())
    else:
        steps_txt = _clean(str(steps), 200)
    result = {
        "plain": plain,
        "given": _clean(str(data.get("given") or "מה שכתוב בשאלה"), 220),
        "find": _clean(str(data.get("find") or "מה שמבקשים למצוא"), 220),
        "steps": steps_txt,
        "source": "ollama",
    }
    with _cache_lock:
        _para_cache[qid] = dict(result)
    return result


# ---------- פערים שקטים + תוכנית חיזוק ----------

_GAP_SYSTEM = """אתה אנליסט למידה לתלמידי תיכון בישראל.
מנתחים טעויות ומוצאים את החולשה האמיתית (פער שקט), לא רק את נושא השאלה האחרונה.
דוגמה: נכשל בטריגונומטריה כי נתקע בהעברת אגפים / שברים.
החזר JSON בלבד:
{
  "root_gap": "תיאור קצר של הפער האמיתי",
  "surface_topic": "הנושא שנראה על פני השטח",
  "prerequisite": "נושא בסיס לחיזוק",
  "focus_topics": ["נושא1","נושא2"],
  "drill_size": 6,
  "message": "הודעה קצרה לתלמיד בגובה העיניים",
  "coach_title": "כותרת קצרה"
}
כל השדות בעברית. בלי תשובות לשאלות.
"""


def analyze_silent_gaps(
    subject: str,
    *,
    weak_topics: list[str] | None = None,
    recent_mistakes: list[dict[str, Any]] | None = None,
    topic_scores: list[dict[str, Any]] | None = None,
    patterns: list[dict[str, Any]] | None = None,
    storage=None,
    force: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    """מזהה פער שורש ובונה תוכנית חיזוק קצרה."""
    key = subject_key(subject)
    weak = [str(t) for t in (weak_topics or []) if t][:5]
    cache_key = f"{key}|{','.join(weak)}|{'llm' if use_llm else 'local'}"
    with _cache_lock:
        if not force and cache_key in _gap_cache:
            return dict(_gap_cache[cache_key])

    mistakes = recent_mistakes or []
    miss_lines = []
    for row in mistakes[-8:]:
        stem = _clean(str(row.get("question") or row.get("stem") or ""), 120)
        topic = str(row.get("topic") or "")
        if stem or topic:
            miss_lines.append(f"- נושא={topic} | {stem}")
    score_lines = []
    for row in (topic_scores or [])[:8]:
        score_lines.append(
            f"- {row.get('topic')}: חוזק={row.get('strength')} חלש={row.get('weak')}"
        )
    pat_lines = [
        str(p.get("message") or p.get("title") or p.get("kind") or "")
        for p in (patterns or [])[:4]
    ]

    fallback = {
        "root_gap": (
            f"קושי ב{' · '.join(weak[:2])}" if weak else "עדיין אין מספיק טעויות לזיהוי פער"
        ),
        "surface_topic": weak[0] if weak else "",
        "prerequisite": weak[-1] if len(weak) > 1 else (weak[0] if weak else "יסודות"),
        "focus_topics": weak[:3] or ["יסודות"],
        "drill_size": 6 if weak else 4,
        "message": (
            f"נחזק קודם את הבסיס ב«{(weak[-1] if len(weak) > 1 else (weak[0] if weak else 'יסודות'))}», "
            "ואז נחזור לנושא הקשה."
            if weak
            else "עוד כמה תרגולים ואפשר יהיה לראות איפה נתקעים באמת."
        ),
        "coach_title": "חיזוק ממוקד",
        "source": "local",
        "subject": key,
    }
    if not use_llm or not available(storage):
        with _cache_lock:
            _gap_cache[cache_key] = dict(fallback)
        return fallback

    user = (
        f"מקצוע: {subject_label(key)}\n"
        f"נושאים חלשים מהסטטיסטיקה: {weak}\n"
        f"דפוסי טעות: {pat_lines}\n"
        f"ציוני נושאים:\n" + ("\n".join(score_lines) or "(אין)") + "\n"
        f"טעויות אחרונות:\n" + ("\n".join(miss_lines) or "(אין)") + "\n"
        "מה הפער השקט האמיתי ומה לחזק לפני שממשיכים?"
    )
    raw = ollama_client.chat(
        [{"role": "user", "content": user}],
        system=_GAP_SYSTEM,
        storage=storage,
        temperature=0.2,
        format_json=True,
        timeout=35.0,
        num_predict=240,
    )
    data = _parse_json(raw)
    if not data:
        return fallback

    focus = data.get("focus_topics") or weak[:3]
    if isinstance(focus, str):
        focus = [focus]
    focus = [str(t).strip() for t in focus if str(t).strip()][:4] or weak[:3] or ["יסודות"]
    try:
        drill = int(data.get("drill_size") or 6)
    except (TypeError, ValueError):
        drill = 6
    drill = max(4, min(10, drill))
    result = {
        "root_gap": _clean(str(data.get("root_gap") or fallback["root_gap"]), 180),
        "surface_topic": _clean(str(data.get("surface_topic") or (weak[0] if weak else "")), 80),
        "prerequisite": _clean(str(data.get("prerequisite") or focus[-1]), 80),
        "focus_topics": focus,
        "drill_size": drill,
        "message": _clean(str(data.get("message") or fallback["message"]), 280),
        "coach_title": _clean(str(data.get("coach_title") or "חיזוק ממוקד"), 60),
        "source": "ollama",
        "subject": key,
    }
    with _cache_lock:
        _gap_cache[cache_key] = dict(result)
    return result


def enrichment_for_action_plan(
    subject: str,
    plan: dict[str, Any],
    *,
    engine=None,
    storage=None,
    use_llm: bool = False,
) -> dict[str, Any]:
    """משלב ניתוח פערים שקטים לתוך תוכנית האנליסט.

    use_llm=False — מהיר ל־UI. True — מעשיר עם Ollama (סטודיו/כפתור).
    """
    out = dict(plan or {})
    steps = list(out.get("steps") or [])
    weak: list[str] = []
    patterns: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    mistakes: list[dict[str, Any]] = []
    if engine is not None:
        try:
            weak = list(engine.weak_topics(subject, limit=4) or [])
            patterns = list(engine.mistake_patterns(subject) or [])
            scores = list(engine.topic_scores(subject) or [])[:8]
            rec = engine.record_for(subject)
            for row in list(rec.get("recent") or [])[-12:]:
                if not row.get("correct"):
                    mistakes.append({
                        "topic": row.get("topic"),
                        "question": row.get("question") or row.get("stem") or "",
                    })
        except Exception:
            pass
    if storage is not None and not mistakes:
        try:
            book = storage.get("mistakes") or {}
            for entry in list(book.values())[-10:]:
                if subject_key(entry.get("subject") or "") == subject_key(subject):
                    mistakes.append(entry)
        except Exception:
            pass

    gap = analyze_silent_gaps(
        subject,
        weak_topics=weak or list((out.get("readiness") or {}).get("weak_topics") or []),
        recent_mistakes=mistakes,
        topic_scores=scores,
        patterns=patterns,
        storage=storage,
        use_llm=bool(use_llm),
    )
    out["silent_gap"] = gap
    if gap.get("focus_topics"):
        tip = (
            f"פער שקט: {gap.get('root_gap')} → חיזוק {gap.get('prerequisite')} "
            f"({gap.get('drill_size')} תרגילים) לפני {gap.get('surface_topic') or 'הנושא הקשה'}."
        )
        if tip not in steps:
            steps.insert(0, tip)
    if gap.get("message"):
        out["ai_message"] = gap["message"]
    out["steps"] = steps[:5]
    return out


# ---------- מורה פרטי סוקרטי ----------

_TUTOR_SYSTEM = """אתה מורה פרטי סבלני לתלמידי תיכון בישראל.
מדברים בגובה העיניים, בלי זרגון מיותר.
שיטה: שאלות קצרות, שלבים קטנים.
כללים:
- עברית תקנית ופשוטה בלבד.
- אל תמסור את התשובה הסופית אלא אם התלמיד מבקש במפורש «תן תשובה» או «גלה».
- שאלה אחת בכל תור, קצרה.
- אם יש מונח קשה: הסבר במשפט יומיומי אחד.
- אחרי טעות: עודדו, פרקו לשלב קטן יותר.
- בלי מקפים ארוכים ובלי אימוג'י.
החזר JSON:
{"say":"מה אומרים לתלמיד","ask":"שאלת הכוונה הקטנה הבאה","term":"הסבר מונח אם צריך, אחרת ריק","done":false}
"""


def socratic_turn(
    question: dict[str, Any] | None,
    *,
    history: list[dict[str, str]] | None = None,
    student_message: str = "",
    reveal_answer: bool = False,
    storage=None,
) -> dict[str, str]:
    """צעד אחד של מורה פרטי סוקרטי."""
    q = question or {}
    stem = _stem_of(q)
    correct = _correct_of(q)
    topic = str(q.get("topic") or "")
    subject = subject_label(q.get("subject") or "")
    opts = [str(o) for o in (q.get("options") or [])[:4]]
    explanation = _clean(str(q.get("explanation") or ""), 280)

    fallback_ask = "מה הנתון הראשון שאתם רואים בשאלה?"
    fallback = {
        "say": "בסדר, נלך לאט. קודם מבינים מה כתוב, ורק אחר כך בוחרים.",
        "ask": fallback_ask,
        "term": "",
        "done": "false",
        "source": "fallback",
    }
    if not available(storage):
        err = ollama_client.last_error()
        if err:
            fallback["say"] = (
                "כרגע אין עוזר מקומי זמין. אפשר להמשיך לבד עם רמז מהשאלה, "
                "או לבדוק בהגדרות ש־Ollama רץ."
            )
            fallback["error"] = err
        return fallback

    ctx = (
        f"מקצוע: {subject}\nנושא: {topic}\nשאלה: {stem}\n"
        f"אפשרויות: {opts}\n"
        f"הסבר קיים (לשימוש פנימי בלבד): {explanation}\n"
        f"תשובה נכונה (לשימוש פנימי בלבד, אל תחשוף אלא אם מבקשים): {correct}\n"
    )
    if reveal_answer:
        ctx += "התלמיד ביקש לגלות את התשובה. אפשר לגלות בעדינות עם הסבר קצר.\n"

    messages: list[dict[str, str]] = [{"role": "user", "content": ctx + "התחל הכוונה קצרה."}]
    for row in (history or [])[-6:]:
        role = "assistant" if row.get("role") == "assistant" else "user"
        content = str(row.get("content") or "").strip()
        if content:
            messages.append({"role": role, "content": content[:500]})
    if student_message.strip():
        messages.append({"role": "user", "content": student_message.strip()[:400]})

    raw = ollama_client.chat(
        messages,
        system=_TUTOR_SYSTEM,
        storage=storage,
        temperature=0.35,
        format_json=True,
        timeout=35.0,
        num_predict=200,
    )
    data = _parse_json(raw)
    if not data:
        if raw:
            return {"say": _clean(raw, 400), "ask": "", "term": "", "done": "false", "source": "ollama"}
        err = ollama_client.last_error()
        if err:
            fallback["say"] = "לא קיבלתי תשובה בזמן. נסו שוב, או כבו את העוזר בהגדרות אם זה חוזר."
            fallback["error"] = err
        return fallback
    return {
        "say": _clean(str(data.get("say") or fallback["say"]), 400),
        "ask": _clean(str(data.get("ask") or ""), 200),
        "term": _clean(str(data.get("term") or ""), 200),
        "done": "true" if data.get("done") in (True, "true", "yes", 1) else "false",
        "source": "ollama",
    }


def gentle_explain(
    question: dict[str, Any] | None,
    *,
    storage=None,
) -> str:
    """מפרק פתרון יבש להסבר יומיומי קצר."""
    q = question or {}
    stem = _stem_of(q)
    correct = _correct_of(q)
    body = _clean(str(q.get("explanation") or ""), 400)
    if not available(storage):
        return body or f"התשובה היא «{correct}»." if correct else ""
    raw = ollama_client.chat(
        [{
            "role": "user",
            "content": (
                f"שאלה: {stem}\nתשובה נכונה: {correct}\nהסבר יבש: {body}\n"
                "הסבירו ב־3 משפטים פשוטים, בגובה העיניים, בלי זרגון מיותר."
            ),
        }],
        system="אתה מורה סבלני. עברית פשוטה. בלי אימוג'י.",
        storage=storage,
        temperature=0.25,
        timeout=28.0,
        num_predict=180,
    )
    return _clean(raw or body, 500)


# ---------- משגיח / אנליסט מקביל ----------

_SUPER_SYSTEM = """אתה משגיח־אנליסט מקביל במערכת לימוד עברית.
כותבים דוח קצר למפתח/מורה: מה קורה לתלמיד, איפה הפערים השקטים, ומה לעשות הלאה.
עברית ברורה, בלי זargon מיותר, 8–14 שורות."""


def supervisor_report(
    snapshots: list[dict[str, Any]] | None = None,
    *,
    deep_report: str = "",
    storage=None,
) -> str:
    """דוח נרטיבי שמקביל לאנליסט ההיוריסטי."""
    lines = []
    for snap in snapshots or []:
        name = subject_label(snap.get("subject") or "")
        weak = " · ".join(snap.get("weak_topics") or [])
        lines.append(
            f"{name}: רמה={snap.get('level_he')} דיוק={snap.get('recent_accuracy')}% "
            f"חלש={weak or '—'}"
        )
    blob = "\n".join(lines) or "אין עדיין נתונים."
    if deep_report:
        blob += "\n\nדוח אנליסט קיים:\n" + _clean(deep_report, 1200)
    if not available(storage):
        return (
            "משגיח AI לא זמין (Ollama כבוי או לא רץ).\n"
            "להלן סיכום מקומי:\n" + blob
        )
    raw = ollama_client.chat(
        [{"role": "user", "content": "סכם ופרש:\n" + blob}],
        system=_SUPER_SYSTEM,
        storage=storage,
        temperature=0.25,
        timeout=40.0,
        num_predict=320,
    )
    return _clean(raw, 2000) or ("דוח מקומי:\n" + blob)


def run_async(
    fn: Callable,
    on_done: Callable[[Any], None],
    on_error: Callable[[str], None] | None = None,
    *,
    ui=None,
) -> threading.Event:
    """מריץ קריאת AI ברקע כדי לא לחסום את ה־UI.

    מחזיר Event לביטול: set() אומר להתעלם מהתוצאה (חלון נסגר).
    אם מועבר ui (ווידג'ט Tk), התוצאה חוזרת דרך after() ורק אם הווידג'ט עדיין חי.
    """
    cancel = threading.Event()

    def _alive(widget) -> bool:
        if cancel.is_set():
            return False
        if widget is None:
            return True
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def worker():
        try:
            result = fn()
        except Exception as exc:
            err = str(exc)

            def fail():
                if not _alive(ui):
                    return
                if on_error:
                    try:
                        on_error(err)
                    except Exception:
                        pass

            if ui is not None:
                try:
                    ui.after(0, fail)
                except Exception:
                    pass
            elif on_error and not cancel.is_set():
                try:
                    on_error(err)
                except Exception:
                    pass
            return

        def succeed():
            if not _alive(ui):
                return
            try:
                on_done(result)
            except Exception:
                pass

        if ui is not None:
            try:
                ui.after(0, succeed)
            except Exception:
                pass
        elif not cancel.is_set():
            try:
                on_done(result)
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()
    return cancel
