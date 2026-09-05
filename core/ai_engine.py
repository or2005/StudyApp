"""מנוע AI מערכתי — מתחבר לאנליסט, תרגול, זיכרון תלמיד, ADHD ושומר בחינה.

שכבה מעל הסטטיסטיקה המקומית: לא מחליפה את AdaptiveEngine, אלא מכוונת
ומנסחת. כש־Ollama כבוי — כל הנתיבים נופלים ללוגיקה מקומית מהירה.
"""
from __future__ import annotations

import re
import time
from typing import Any

from core import ai_tutor, ollama_client
from core.config import ALL_SUBJECTS, HOME_SUBJECTS, subject_key, subject_label

EXAM_MODES = frozenset({"mock", "final", "timed", "exam", "general", "meimad"})
MEMORY_KEY = "ai_student_memory"
MEMORY_MAX = 220
NOTE_MAX_CHARS = 600

_HEB = re.compile(r"[\u0590-\u05FF]")


def _scrub_ai_dashes(text: str) -> str:
    """מסיר מקפי AI ארוכים מטקסט שמוצג לתלמיד."""
    raw = str(text or "")
    raw = raw.replace("\u2014", ": ").replace("\u2013", ", ")
    raw = re.sub(r" {2,}", " ", raw)
    return raw.strip()


def _hebrew_ok(text: str) -> bool:
    """דוחה תשובות הזיות/לא עבריות מהמודל הקטן."""
    blob = str(text or "").strip()
    if len(blob) < 8:
        return False
    heb = len(_HEB.findall(blob))
    if heb < max(6, int(len(blob) * 0.22)):
        return False
    # סימנים לתשובה שבורת הקשר
    bad = ("כיסא", "מזון שכולל", "lorem", "as an ai", "as a language")
    low = blob.lower()
    if any(tok in blob or tok in low for tok in bad):
        return False
    return True


class AIEngine:
    """ממשק אחד לכל יכולות ה־AI במערכת."""

    def __init__(self, storage: Any, adaptive_engine: Any = None):
        self.storage = storage
        self.adaptive = adaptive_engine

    # ---------- סטטוס מערכת ----------
    def status(self) -> dict[str, Any]:
        health = ollama_client.health(storage=self.storage)
        online = bool(health.get("ok"))
        model = health.get("model") or ollama_client.configured_model(self.storage)
        if not ollama_client.enabled(self.storage):
            line = "העוזר המקומי כבוי בהגדרות."
        elif not online:
            line = f"אין חיבור לכתובת {health.get('url') or ollama_client.configured_url(self.storage)}."
        elif health.get("models") and not health.get("has_model"):
            line = f"מחובר, אבל המודל «{model}» חסר."
        else:
            line = f"מחובר · {model}"
        return {
            "enabled": ollama_client.enabled(self.storage),
            "online": online,
            "model": model,
            "url": health.get("url") or ollama_client.configured_url(self.storage),
            "line": line,
            "memory_items": len(self.memory_list()),
        }

    def available(self) -> bool:
        return ai_tutor.available(self.storage)

    # ---------- שומר בחינה ----------
    def is_exam_mode(self, mode: str | None) -> bool:
        return str(mode or "") in EXAM_MODES

    def features_for_mode(self, mode: str | None) -> dict[str, bool]:
        """מה מותר במצב הנוכחי — במבחן בלי עזרת AI."""
        exam = self.is_exam_mode(mode)
        on = ollama_client.enabled(self.storage)
        return {
            "paraphrase": on and not exam,
            "tutor": on and not exam,
            "assistant": on and not exam,
            "hints_ai": on and not exam,
            "debrief": True,  # אחרי מבחן תמיד מותר
            "exam_locked": exam,
        }

    # ---------- זיכרון תלמיד מקומי ----------
    def _memory_blob(self) -> dict[str, Any]:
        raw = self.storage.get_pref(MEMORY_KEY, None) if self.storage else None
        if isinstance(raw, dict):
            return dict(raw)
        return {"notes": [], "styles": {}, "updated": 0}

    def _save_memory(self, blob: dict[str, Any]) -> None:
        if not self.storage:
            return
        blob["updated"] = time.time()
        self.storage.set_pref(MEMORY_KEY, blob)

    def memory_list(self) -> list[dict[str, Any]]:
        return list(self._memory_blob().get("notes") or [])

    def remember(
        self,
        *,
        subject: str = "",
        topic: str = "",
        kind: str = "note",
        text: str,
        meta: dict | None = None,
    ) -> None:
        text = " ".join(str(text or "").split())
        if not text:
            return
        blob = self._memory_blob()
        notes = list(blob.get("notes") or [])
        entry = {
            "ts": time.time(),
            "subject": subject_key(subject) if subject else "",
            "topic": str(topic or ""),
            "kind": kind,
            "text": text[:NOTE_MAX_CHARS],
            "meta": meta or {},
        }
        notes.insert(0, entry)
        blob["notes"] = notes[:MEMORY_MAX]
        self._save_memory(blob)

    def recall(self, subject: str = "", topic: str = "", limit: int = 5) -> list[dict[str, Any]]:
        subj = subject_key(subject) if subject else ""
        topic = str(topic or "")
        scored: list[tuple[int, dict]] = []
        for row in self.memory_list():
            score = 0
            if subj and row.get("subject") == subj:
                score += 2
            if topic and topic in str(row.get("topic") or ""):
                score += 3
            if score:
                scored.append((score, row))
        scored.sort(key=lambda item: (-item[0], -float(item[1].get("ts") or 0)))
        return [row for _, row in scored[:limit]]

    def memory_context_line(self, subject: str = "", topic: str = "") -> str:
        rows = self.recall(subject, topic, limit=4)
        if not rows:
            return ""
        parts = [str(r.get("text") or "") for r in rows if r.get("text")]
        return " · ".join(parts[:4])

    # ---------- ADHD / קצב ----------
    def pacing(self, subject: str | None = None) -> dict[str, Any]:
        """המלצת קצב לפי דפוסי חיפזון/רצף טעויות של האנליסט."""
        subj = subject_key(subject or "") if subject else ""
        rush = False
        streak = False
        struggle = False
        patterns: list[dict] = []
        if self.adaptive and subj:
            try:
                patterns = list(self.adaptive.mistake_patterns(subj) or [])
                struggle = bool(self.adaptive.struggling(subj))
            except Exception:
                patterns = []
        kinds = {str(p.get("kind") or "") for p in patterns}
        rush = "rush" in kinds
        streak = "streak" in kinds
        focus_on = bool(self.storage.get_pref("ai_calm_mode", False)) if self.storage else False
        needs_break = False
        if self.storage and hasattr(self.storage, "get_focus_summary"):
            try:
                needs_break = (self.storage.get_focus_summary() or {}).get("status") == "needs_break"
            except Exception:
                needs_break = False

        shorten = rush or streak or struggle or focus_on or needs_break
        count_cap = 6 if (rush and streak) or needs_break else (8 if shorten else None)
        break_sec = 60 if needs_break else (45 if rush else (30 if streak else 0))
        message = ""
        if needs_break:
            message = "המערכת מזהה ניווט מהיר מדי. הפסקה קצרה, ואז סשן קצר וממוקד."
        elif rush and streak:
            message = "רואים חיפזון ורצף טעויות. סשן קצר, קוראים עד הסוף, ואז הפסקה קצרה."
        elif rush:
            message = "הרבה תשובות מהירות מדי. עדיף לאט יותר, גם אם הסשן יהיה קצר יותר."
        elif streak:
            message = "רצף טעויות. נעצור על סשן קצר עם הסבר אחרי כל שאלה."
        elif struggle:
            message = "יש קושי במקצוע. נתמקד בחיזוק בסיס, בלי לקפוץ קדימה."
        elif focus_on:
            message = "מצב רגוע דולק: סשנים קצרים וממוקדים."
        return {
            "shorten": bool(shorten),
            "count_cap": count_cap,
            "break_sec": break_sec,
            "rush": rush,
            "streak": streak,
            "struggle": struggle,
            "calm": focus_on,
            "needs_break": needs_break,
            "message": message,
            "prefer_easy": rush or streak or needs_break,
        }

    def adjust_count(self, subject: str, mode: str, count: int) -> int:
        if mode not in {"practice", "smart_practice", "guided", "compose"}:
            return count
        advice = self.pacing(subject)
        cap = advice.get("count_cap")
        if cap is None:
            return count
        return max(4, min(int(count), int(cap)))

    # ---------- מיון טעויות + סולם רמזים ----------
    def classify_error(
        self,
        question: dict | None,
        *,
        time_sec: float | None = None,
        is_correct: bool = False,
    ) -> str:
        if is_correct:
            return "ok"
        if time_sec is not None and float(time_sec) < 2.8:
            return "rush"
        stem = str((question or {}).get("question") or "")
        if len(stem) > 140 or any(tok in stem for tok in ("נתון", "מצאו", "הוכיחו", "בקטע")):
            return "reading"
        topic = str((question or {}).get("topic") or "")
        if any(tok in topic for tok in ("שבר", "אלגבר", "משווא", "אגף")):
            return "concept"
        return "compute"

    def hint_ladder(self, question: dict | None, level: int = 1, subject: str = "") -> str:
        """רמה 1 כיוון, 2 צעד, 3 מלכודת — בלי לחשוף תשובה."""
        level = max(1, min(3, int(level or 1)))
        q = question or {}
        topic = str(q.get("topic") or "")
        mem = self.memory_context_line(subject or q.get("subject") or "", topic)
        from core.teach import live_hint

        base = live_hint(q, subject or q.get("subject") or "")
        if level == 1:
            tip = f"כיוון: סמנו מה נתון ומה מבוקש בנושא «{topic or 'השאלה'}»."
            return tip + (f" (נזכרים: {mem})" if mem else "")
        if level == 2:
            return f"צעד: {base}" if base else "צעד: פסלו אפשרות אחת שלא מתאימה לנתון."
        # level 3
        kind = self.classify_error(q)
        traps = {
            "rush": "מלכודת: לא בוחרים לפני שקוראים את כל השאלה.",
            "reading": "מלכודת: הניסוח מבלבל. מחפשים את הפועל המרכזי (מצאו/חשבו/בחרו).",
            "concept": "מלכודת: לפעמים מתבלבלים בין הכלל הבסיסי לנושא המתקדם.",
            "compute": "מלכודת: בדקו יחידות וסימן לפני שבוחרים.",
        }
        return traps.get(kind, "מלכודת: בדקו שוב מה בדיוק נשאל.")

    # ---------- חיבור לאנליסט: תוכנית חיזוק ----------
    def remediation(self, subject: str, *, use_llm: bool = False) -> dict[str, Any]:
        subj = subject_key(subject)
        plan: dict[str, Any] = {"steps": [], "subject": subj}
        if self.adaptive:
            try:
                plan = dict(self.adaptive.action_plan(subj) or plan)
            except Exception:
                pass
        enriched = ai_tutor.enrichment_for_action_plan(
            subj, plan, engine=self.adaptive, storage=self.storage, use_llm=use_llm,
        )
        gap = enriched.get("silent_gap") or {}
        focus = list(gap.get("focus_topics") or enriched.get("readiness", {}).get("weak_topics") or [])
        if not focus and self.adaptive:
            try:
                focus = list(self.adaptive.weak_topics(subj, limit=3) or [])
            except Exception:
                focus = []
        prereq = str(gap.get("prerequisite") or (focus[-1] if focus else ""))
        # זיכרון: אם כבר חיזקנו את הבסיס — מזכירים
        mem = self.memory_context_line(subj, prereq or (focus[0] if focus else ""))
        pace = self.pacing(subj)
        count = int(gap.get("drill_size") or 6)
        count = self.adjust_count(subj, "practice", count)
        return {
            "subject": subj,
            "focus_topics": focus[:4],
            "prerequisite": prereq,
            "root_gap": gap.get("root_gap") or "",
            "message": gap.get("message") or enriched.get("ai_message") or pace.get("message") or "",
            "title": gap.get("coach_title") or "חיזוק ממוקד",
            "drill_size": count,
            "steps": list(enriched.get("steps") or [])[:5],
            "memory": mem,
            "pacing": pace,
            "source": gap.get("source") or "local",
        }

    def pick_practice_target(self) -> dict[str, Any]:
        """בוחר מקצוע+נושאים לתרגול מותאם רמה — לפי האנליסט."""
        best = None
        if self.adaptive:
            for key in list(ALL_SUBJECTS):
                try:
                    struggle = self.adaptive.struggling(key)
                    weak = self.adaptive.weak_topics(key, limit=3) or []
                    snap = self.adaptive.snapshot(key)
                    total = int(snap.get("recent_total") or 0)
                    acc = float(snap.get("recent_accuracy") or 100)
                except Exception:
                    continue
                if total < 3 and not weak:
                    continue
                score = 0.0
                if struggle:
                    score += 40
                score += max(0.0, 70 - acc)
                score += 8 * len(weak)
                row = {"subject": key, "weak": weak, "score": score, "accuracy": acc}
                if best is None or score > best["score"]:
                    best = row
        if not best:
            key = HOME_SUBJECTS[0] if HOME_SUBJECTS else "math"
            return self.remediation(key)
        rem = self.remediation(best["subject"])
        if not rem.get("focus_topics"):
            rem["focus_topics"] = best.get("weak") or []
        return rem

    # ---------- טיפים קצרים לאנליסט (בלי צ'אט) ----------
    def coach_nudge(self, subject: str = "", topic: str = "") -> str:
        """משפט קצר לתצוגה בשיעור/תרגול — מקומי ומהיר."""
        subj = subject_key(subject or "")
        if not subj:
            try:
                rem = self.pick_practice_target()
            except Exception:
                return ""
            subj = subject_key(rem.get("subject") or "")
            topic = topic or (rem.get("focus_topics") or [""])[0]
        else:
            rem = self.remediation(subj)
        name = subject_label(subj)
        focus = [str(t) for t in (rem.get("focus_topics") or []) if t]
        if topic and topic not in focus:
            focus = [topic] + focus
        gap = str(rem.get("root_gap") or rem.get("message") or "").strip()
        mem = self.memory_context_line(subj, topic or (focus[0] if focus else ""))
        bits: list[str] = []
        if focus:
            bits.append("כדאי לחזק ב" + name + ": " + " · ".join(focus[:2]) + ".")
        elif gap:
            bits.append("ב" + name + ": " + gap)
        if mem:
            bits.append("נזכרים: " + mem)
        pace = rem.get("pacing") or self.pacing(subj)
        if isinstance(pace, dict) and pace.get("shorten") and pace.get("message"):
            bits.append(str(pace["message"]))
        out = " ".join(bits).strip()
        return out[:220]

    # ---------- Hooks לאירועי מערכת ----------
    def on_answer(
        self,
        question: dict | None,
        *,
        is_correct: bool,
        time_sec: float | None = None,
        subject: str = "",
        mode: str = "practice",
    ) -> dict[str, Any]:
        """אחרי תשובה: זיכרון, מיון טעות, אות קצב."""
        if self.is_exam_mode(mode) and mode in {"mock", "general", "meimad"}:
            return {"skipped": True}
        q = question or {}
        subj = subject_key(subject or q.get("subject") or "")
        topic = str(q.get("topic") or "")
        kind = self.classify_error(q, time_sec=time_sec, is_correct=is_correct)
        if not is_correct and kind != "ok":
            labels = {
                "rush": "טעות מחיפזון",
                "reading": "קושי בניסוח/קריאה",
                "concept": "פער מושגי",
                "compute": "טעות חישוב",
            }
            self.remember(
                subject=subj,
                topic=topic,
                kind="error",
                text=f"{labels.get(kind, kind)} ב«{topic or 'תרגול'}»",
                meta={"error_kind": kind},
            )
        elif is_correct and topic:
            # לא מציפים זיכרון — רק אם היה קושי קודם באותו נושא
            prev = self.recall(subj, topic, limit=1)
            if prev and prev[0].get("kind") == "error":
                self.remember(
                    subject=subj,
                    topic=topic,
                    kind="win",
                    text=f"הצלחה אחרי קושי ב«{topic}»: להמשיך כך",
                )
        return {"error_kind": kind, "pacing": self.pacing(subj)}

    def remember_explanation(self, subject: str, topic: str, text: str) -> None:
        self.remember(subject=subject, topic=topic, kind="teach", text=text)

    def session_debrief(
        self,
        *,
        subject: str,
        answers: list[dict] | None = None,
        mode: str = "practice",
    ) -> dict[str, Any]:
        subj = subject_key(subject)
        rem = self.remediation(subj)
        answers = answers or []
        total = len(answers)
        correct = sum(1 for a in answers if (a.get("correct") if isinstance(a, dict) else False))
        pace = self.pacing(subj)
        lines = [
            f"סיימתם {total} שאלות ב{subject_label(subj)} · {correct}/{total} נכונות."
            if total
            else f"סשן ב{subject_label(subj)} הסתיים."
        ]
        if rem.get("root_gap"):
            lines.append(f"פער שקט: {rem['root_gap']}")
        if rem.get("prerequisite"):
            lines.append(f"לחיזוק הבא: {rem['prerequisite']} ({rem.get('drill_size', 6)} שאלות).")
        if pace.get("message"):
            lines.append(pace["message"])
        if rem.get("memory"):
            lines.append(f"נזכרים: {rem['memory']}")
        text = "\n".join(lines)
        self.remember(subject=subj, topic="", kind="debrief", text=lines[0] if lines else text)
        return {
            "title": "סיכום AI",
            "message": text,
            "remediation": rem,
            "pacing": pace,
            "features": self.features_for_mode(mode),
        }

    def micro_lesson(self, subject: str, topic: str = "", *, use_llm: bool = False) -> str:
        """מיקרו־שיעור קצר. ברירת מחדל מקומית (בלי לחכות ל־Ollama)."""
        rem = self.remediation(subject)
        topic = topic or rem.get("prerequisite") or (rem.get("focus_topics") or [""])[0]
        mem = self.memory_context_line(subject, topic)
        if use_llm and self.available():
            raw = ollama_client.chat(
                [{
                    "role": "user",
                    "content": (
                        f"מקצוע {subject_label(subject)}, נושא {topic}. "
                        f"פער: {rem.get('root_gap')}. זיכרון: {mem or 'אין'}. "
                        "כתוב מיקרו־שיעור בעברית: 4 משפטים פשוטים לתלמיד תיכון, בלי תרגיל ובלי תשובות."
                    ),
                }],
                system="מורה סבלני. עברית פשוטה.",
                storage=self.storage,
                temperature=0.3,
                timeout=28.0,
                num_predict=180,
            )
            if raw:
                text_out = ai_tutor._clean(raw, 500)
                self.remember_explanation(subject, topic, text_out[:200])
                return text_out
        base = rem.get("message") or f"נחזור ליסודות של «{topic or 'הנושא'}» לפני שממשיכים."
        if mem:
            base += f" כבר דיברנו על זה: {mem}"
        return base

