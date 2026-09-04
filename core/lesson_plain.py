# -*- coding: utf-8 -*-
"""סידור שיעור עיוני לקריאה ברורה: קטע → דוגמה → הסבר. בלי מלל מטא."""
from __future__ import annotations

import re
from typing import Any

from core.config import subject_key

# כותרות מטא שרק מבלבלות — מוחקים את הסעיף כולו
_DROP_SECTIONS = (
    "למה זה חשוב",
    "איך ללמוד את זה",
    "איך ללמוד",
    "טעויות נפוצות",
    "סיכום לפני תרגול",
    "סיכום",
)
_KEEP_AS_EXPLAIN = ("הרחבה", "הסבר", "רקע", "סיפור")
_EXAMPLE_HEAD = re.compile(r"^דוגמה\s*:?\s*(.*)$", re.I)
_BOILER = re.compile(
    r"^(?:קריאה בקצב שלכם|בקצב שלכם|השיעור מיושר|אחרי הקריאה|אחרי הדוגמה|אם משהו לא ברור)",
    re.I,
)
_SECTION_HEAD = re.compile(r"^[\u0590-\u05FFA-Za-z][\u0590-\u05FFA-Za-z \"״׳']{1,40}$")


_SECTION_INLINE = re.compile(
    r"(?<!\n)[ \t]+(?=(?:דוגמה|הסבר|הרחבה|רקע|סיפור)(?:\s|:|$))"
)
_NUM_INLINE = re.compile(r"(?<!\n)[ \t]+(?=\d+[\.\)]\s+)")


def restore_section_breaks(text: str) -> str:
    """משחזר מעברי שורה לשיעור שנמעך לשורה אחת (באג ניקוי סבב ישן)."""
    raw = str(text or "").replace("\r\n", "\n").strip()
    if not raw:
        return raw
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    standalone = sum(1 for ln in lines if ln in {"דוגמה", "הסבר", "הרחבה", "רקע", "סיפור"})
    if standalone >= 2 and raw.count("\n") >= 5:
        return raw
    raw = _SECTION_INLINE.sub("\n\n", raw)
    raw = _NUM_INLINE.sub("\n", raw)
    # כותרת סעיף לבד בשורה
    raw = re.sub(
        r"\n(דוגמה|הסבר|הרחבה|רקע|סיפור)[ \t]+",
        r"\n\1\n",
        raw,
    )
    raw = re.sub(r"^(דוגמה|הסבר|הרחבה|רקע|סיפור)[ \t]+", r"\1\n", raw)
    # כפילות «הסבר … הסבר …» בסוף — משאירים בלוק הסבר אחד
    chunks = re.split(r"(?=\nהסבר\n|^הסבר\n)", raw)
    if len(chunks) > 2:
        raw = "".join(chunks[:2]).strip()
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def organize_lesson(content: str, *, subject: str = "", topic: str = "") -> dict[str, str]:
    """מפרק תוכן גולמי לקריאה / דוגמה / הסבר מפורט — בלי לקצר את החומר עצמו."""
    from core.stem_fix import clean_topic_label, strip_round_noise

    raw = strip_round_noise(str(content or "").replace("\r\n", "\n").strip())
    raw = restore_section_breaks(raw)
    lines = [ln.rstrip() for ln in raw.split("\n")]
    # שורת כותרת «היסטוריה ־ סבב…» בראש השיעור — מוחקים
    if lines:
        head = clean_topic_label(lines[0].strip())
        if "סבב" in lines[0] or head != lines[0].strip():
            if len(head) < 8 or head == "תרגול":
                lines = lines[1:]
            else:
                lines[0] = head

    reading: list[str] = []
    example_lines: list[str] = []
    explain_lines: list[str] = []
    mode = "reading"  # reading | example | explain | drop

    i = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        if not stripped:
            if mode == "reading" and reading and reading[-1] != "":
                reading.append("")
            elif mode == "explain" and explain_lines and explain_lines[-1] != "":
                explain_lines.append("")
            i += 1
            continue

        if stripped in _DROP_SECTIONS or any(stripped.startswith(h + " ") for h in _DROP_SECTIONS):
            mode = "drop"
            i += 1
            continue
        if stripped in _KEEP_AS_EXPLAIN or any(stripped == h for h in _KEEP_AS_EXPLAIN):
            mode = "explain"
            i += 1
            continue

        ex = _EXAMPLE_HEAD.match(stripped)
        if ex:
            mode = "example"
            bit = ex.group(1).strip()
            if bit:
                example_lines.append(bit)
            i += 1
            continue

        if _BOILER.match(stripped):
            i += 1
            continue
        if stripped.startswith("אחרי ") and "תרגול" in stripped:
            i += 1
            continue

        # כותרת קצרה באמצע (כמו «כתיב») — נשארת בקריאה ככותרת משנה
        if mode == "drop":
            # יציאה מ־drop רק בכותרת סעיף חדשה מוכרת
            if stripped in _KEEP_AS_EXPLAIN:
                mode = "explain"
            elif _EXAMPLE_HEAD.match(stripped):
                mode = "example"
            i += 1
            continue

        if mode == "example":
            if stripped in _DROP_SECTIONS or stripped in _KEEP_AS_EXPLAIN:
                if stripped in _KEEP_AS_EXPLAIN:
                    mode = "explain"
                else:
                    mode = "drop"
                i += 1
                continue
            example_lines.append(stripped)
        elif mode == "explain":
            if stripped in _DROP_SECTIONS:
                mode = "drop"
                i += 1
                continue
            if stripped in _KEEP_AS_EXPLAIN:
                i += 1
                continue
            explain_lines.append(stripped)
        else:
            reading.append(stripped)
        i += 1

    reading_text = _strip_lesson_junk(_join_paras(reading))
    example = _strip_lesson_junk(_clarify_example(_join_paras(example_lines), topic or subject))
    explain = _strip_lesson_junk(_join_paras(explain_lines))

    # אם אין הסבר מופרד — מנסים מאמר עומק מהספרייה (תוכן אמיתי, לא מטא)
    if not explain and (subject or topic):
        from core.teach import match_depth

        depth = match_depth(subject_key(subject), f"{topic} {reading_text[:400]}")
        if depth and depth not in reading_text:
            explain = " ".join(str(depth).split())

    if not reading_text and explain:
        reading_text, explain = explain, ""

    return {
        "reading": reading_text,
        "example": example,
        "explain": explain,
    }


def _strip_lesson_junk(text: str) -> str:
    """מסיר זנבות מטא שנמעכו לתוך דוגמה/קריאה."""
    raw = str(text or "").strip()
    if not raw:
        return ""
    raw = re.sub(
        r"(?:לפני התרגול|ואז פתרו שתי שאלות|תוך סימון המילה או המספר שמכריעים).*$",
        "",
        raw,
        flags=re.S,
    )
    raw = re.sub(r"חדשה מהכיתה,?\s*", "", raw)
    return raw.strip(" ,.;")


def _clarify_example(example: str, topic: str = "") -> str:
    """הופך רשימת שנים/פריטים גולמית למשפט ברור לתלמיד."""
    ex = str(example or "").strip()
    if not ex:
        return ""
    topic_bit = clean_topic_safe(topic)
    # רשימה מופרדת בנקודה־פסיק בלי משפט מלא
    if ";" in ex and not re.search(r"[.!?]$", ex) and len(ex) <= 120:
        label = f" בנושא «{topic_bit}»" if topic_bit and topic_bit != "תרגול" else ""
        return (
            f"נקודות ציון לזכור{label}: {ex}. "
            "כל פריט הוא שנה או מסמך נפרד — לא אותו אירוע."
        )
    if len(ex) <= 90 and not re.search(r"(למשל|דוגמה|לדוגמה)", ex) and not ex.endswith((".", "!", "?")):
        return f"למשל: {ex}."
    return ex


def clean_topic_safe(topic: str) -> str:
    try:
        from core.stem_fix import clean_topic_label

        return clean_topic_label(topic)
    except Exception:
        return str(topic or "").strip()


def organize_to_text(content: str, *, subject: str = "", topic: str = "") -> str:
    parts = organize_lesson(content, subject=subject, topic=topic)
    blocks: list[str] = []
    if parts["reading"]:
        blocks.append(parts["reading"])
    if parts["example"]:
        blocks.extend(["", "דוגמה", parts["example"]])
    if parts["explain"]:
        blocks.extend(["", "הסבר", parts["explain"]])
    text = "\n".join(blocks).strip()
    return text or str(content or "").strip()


# תאימות לשם הישן
def distill_lesson(content: str, *, subject: str = "", topic: str = "") -> dict[str, str]:
    parts = organize_lesson(content, subject=subject, topic=topic)
    return {
        "rules": parts["reading"],
        "example": parts["example"],
        "tip": parts["explain"],
        "reading": parts["reading"],
        "explain": parts["explain"],
    }


def distill_to_text(content: str, *, subject: str = "", topic: str = "") -> str:
    return organize_to_text(content, subject=subject, topic=topic)


def distill_to_text_for_lesson(lesson: dict[str, Any] | None, subject: str = "") -> str:
    lesson = lesson or {}
    subj = subject_key(subject or lesson.get("subject") or "")
    return organize_to_text(
        str(lesson.get("content") or ""),
        subject=subj,
        topic=str(lesson.get("topic") or lesson.get("title") or ""),
    )


def _join_paras(lines: list[str]) -> str:
    out: list[str] = []
    buf: list[str] = []
    for ln in lines:
        if not ln.strip():
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        # שורות ממוספרות נשארות בשורות נפרדות
        if re.match(r"^\d+[\.\)]\s+", ln.strip()):
            if buf:
                out.append(" ".join(buf))
                buf = []
            out.append(ln.strip())
        else:
            buf.append(ln.strip())
    if buf:
        out.append(" ".join(buf))
    # מנקים כפילות ריקות
    text = "\n\n".join(p for p in out if p)
    return text.strip()
