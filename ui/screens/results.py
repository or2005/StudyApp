import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, SUBJECTS, rtl, subject_key
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, ProgressBar, font_size, heading, kicker, make_card, Page


def _picked_text(ans: dict) -> str:
    text = str(ans.get("selected_text") or "").strip()
    if text:
        return text
    chosen = ans.get("selected")
    if isinstance(chosen, str) and chosen.strip():
        return chosen.strip()
    options = ans.get("options") or []
    if isinstance(chosen, int) and 0 <= chosen < len(options):
        return str(options[chosen])
    return "לא נענתה"


class ResultsScreen(Page):
    def __init__(self, master, session, summary, on_home, mode="practice", subject=None,
                 on_retry_wrong=None, on_fix_questions=None, level_event=None, level_info=None,
                 insight=None, xp_info=None, streak=None, weak_report=None, on_practice_weak=None):
        super().__init__(master)
        total = max(1, len(session.questions))
        score = session.score
        percent = round((score / total) * 100) if total else 0
        minutes = round(session.get_total_time() / 60, 1)
        exam = mode in {"mock", "final", "timed", "meimad"}
        wrong = session.wrong_answers()

        if percent >= 90:
            msg, color = "מצוין. ממש חזק.", COLORS["success"]
        elif percent >= 70:
            msg, color = "טוב. עוד קצת תרגול והחומר יושב.", COLORS["accent"]
        elif percent >= 60:
            msg, color = "עברת. כל הכבוד.", COLORS["success"]
        else:
            msg, color = "התחלה טובה. חוזרים לשיעור ואז עוד 5 שאלות.", COLORS["danger"]

        card, inner = make_card(self, accent=color, thick=2, pady=16, gold_top=True)
        card.pack(fill="x", pady=(4, 10))
        kicker(inner, "תוצאה", bg=COLORS["card_bg"]).pack(anchor="e")
        heading(inner, "סיימת את ישיבת מימ״ד" if mode == "meimad" else ("סיימת את המבחן" if exam else "סיימת את הסשן"), 24).pack(anchor="e")
        tk.Label(
            inner,
            text=rtl(f"{score} מתוך {len(session.questions)}   ({percent}%)"),
            font=(ADHD_CONFIG["font_family"], font_size(32), "bold"),
            bg=COLORS["card_bg"], fg=COLORS["text_main"], anchor="e",
        ).pack(anchor="e", pady=(6, 2))
        ProgressBar(inner, pct=percent / 100, color=color, height=8).pack(fill="x", pady=(4, 8))
        tk.Label(inner, text=rtl(msg), font=(ADHD_CONFIG["font_family"], font_size(17)),
                 bg=COLORS["card_bg"], fg=color, anchor="e").pack(anchor="e")
        bits = [f"זמן: {minutes} דקות"]
        if isinstance(xp_info, dict) and xp_info.get("gained"):
            bits.append(f"+{xp_info['gained']} נקודות")
            if xp_info.get("level"):
                bits.append(f"רמה {xp_info['level']}")
        if streak:
            bits.append(f"רצף {streak} ימים")
        fast_label(inner, "  ·  ".join(bits), size=13, muted=True,
                   bg=COLORS["card_bg"]).pack(anchor="e", pady=(4, 0))

        self._pack_insight(insight)
        self._pack_weak_report(weak_report, on_practice_weak)

        if level_event:
            kind = level_event.get("kind")
            border = COLORS["success"] if kind == "promote" else COLORS["accent"]
            ev, ev_inner = make_card(self, accent=border, thick=2)
            ev.pack(fill="x", pady=(0, 10))
            heading(ev_inner, level_event.get("title", "עדכון רמה"), 19).pack(anchor="e")
            fast_label(ev_inner, level_event.get("message", ""), size=14, muted=True,
                       bg=COLORS["card_bg"], wrap=820).pack(anchor="e", pady=(4, 0))
        elif level_info:
            fast_label(
                inner,
                f"{level_info.get('headline', '')}  ·  {level_info.get('progress_caption', '')}",
                size=13, muted=True, bg=COLORS["card_bg"], wrap=820,
            ).pack(anchor="e", pady=(8, 0))

        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(0, 10))
        ModernButton(actions, text=rtl("חזרה למסך הראשי"), width=200, command=on_home).pack(side="right", padx=5)
        if wrong and on_retry_wrong:
            GhostButton(
                actions, text=rtl(f"תרגול כל {len(wrong)} השגויות"), width=220,
                command=lambda: on_retry_wrong(subject_key(subject) if subject else None),
            ).pack(side="right", padx=5)

        top_wrong = wrong[:3]
        if top_wrong:
            heading(self, "תקן עכשיו" if len(top_wrong) == 1 else f"תקן עכשיו ({len(top_wrong)} שאלות)", 18).pack(
                anchor="e", pady=(4, 6)
            )
            if on_fix_questions and len(top_wrong) > 1:
                ModernButton(
                    self, text=rtl("תקן את השלוש"), width=180,
                    command=lambda items=top_wrong: on_fix_questions(items),
                ).pack(anchor="e", pady=(0, 8))
            for ans in top_wrong:
                self._fix_card(ans, on_fix_questions)
            leftover = len(wrong) - len(top_wrong)
            if leftover > 0:
                fast_label(
                    self, f"עוד {leftover} שגויות בפירוט למטה, או בתרגול כל השגויות.",
                    size=13, muted=True, bg=COLORS["bg"],
                ).pack(anchor="e", pady=(2, 8))

        chapters = session.chapter_breakdown() if getattr(session, "chapters", None) else []
        if chapters:
            breakdown, bd_inner = make_card(self, accent=COLORS["primary"], pady=10)
            breakdown.pack(fill="x", pady=(0, 10))
            heading(bd_inner, "ציון לפי פרק", 17).pack(anchor="e")
            for row in chapters:
                fast_label(
                    bd_inner,
                    f"{row.get('name')}: {row.get('correct')}/{row.get('total')}  ({row.get('percent')}%)",
                    size=14, bg=COLORS["card_bg"],
                ).pack(anchor="e", pady=1)

        if mode == "final" and percent >= 60 and subject:
            subj_name = SUBJECTS.get(subject_key(subject), {}).get("name", subject)
            cert, cert_inner = make_card(self, accent=COLORS["success"], pady=12)
            cert.pack(fill="x", pady=(0, 10))
            heading(cert_inner, f"תעודת סיום: {subj_name}", 19).pack(anchor="e")
            fast_label(cert_inner, f"עברת את המבחן האמיתי ב-{percent}%. התוצאה נשמרה.",
                       size=13, muted=True, bg=COLORS["card_bg"]).pack(anchor="e", pady=(4, 0))

        if len(wrong) > 3:
            heading(self, f"שאר השגויות ({len(wrong) - 3})", 16).pack(anchor="e", pady=(8, 6))
            for ans in wrong[3:]:
                self._review_card(ans)

    def _pack_insight(self, insight):
        if not isinstance(insight, dict) or not insight.get("has_data"):
            return
        rec = str(insight.get("recommendation") or "").strip()
        weak = [str(item) for item in (insight.get("weak_topics") or []) if item]
        trend = str(insight.get("trend_label") or "").strip()
        if not rec and not weak and not trend:
            return
        card, inner = make_card(self, accent=COLORS["primary"], pady=12)
        card.pack(fill="x", pady=(0, 10))
        heading(inner, "מה האנליסט רואה", 18).pack(anchor="e")
        if trend:
            fast_label(inner, trend, size=13, muted=True, bg=COLORS["card_bg"]).pack(anchor="e", pady=(4, 0))
        if weak:
            fast_label(
                inner, "לחיזוק: " + " · ".join(weak),
                size=14, bg=COLORS["card_bg"], wrap=820,
            ).pack(anchor="e", pady=(4, 0))
        if rec:
            fast_label(inner, rec, size=14, muted=True, bg=COLORS["card_bg"], wrap=820).pack(
                anchor="e", pady=(6, 0)
            )

    def _pack_weak_report(self, weak_report, on_practice_weak):
        rows = [row for row in (weak_report or []) if row.get("topic") and row.get("missed")]
        if not rows:
            return
        card, inner = make_card(self, accent=COLORS["accent"], pady=12)
        card.pack(fill="x", pady=(0, 10))
        title = "נושא אחד לשיפור" if len(rows) == 1 else f"{len(rows)} נושאים לשיפור"
        heading(inner, title, 18).pack(anchor="e")
        fast_label(
            inner, "מהסשן הזה, לא מכל ההיסטוריה. כדאי לחזור רק עליהם.",
            size=13, muted=True, bg=COLORS["card_bg"], wrap=820,
        ).pack(anchor="e", pady=(2, 6))
        for row in rows:
            line = (
                f"{row['topic']}  ·  {row.get('correct', 0)}/{row.get('total', 0)} נכונות"
                f"  ·  {row.get('accuracy', 0)}%"
            )
            fast_label(inner, line, size=14, bg=COLORS["card_bg"], wrap=820).pack(anchor="e", pady=1)
        if on_practice_weak:
            ModernButton(
                inner,
                text=rtl("תרגל אותם עכשיו"),
                width=220,
                command=lambda items=rows: on_practice_weak([item["topic"] for item in items]),
            ).pack(anchor="e", pady=(10, 0))

    def _fix_card(self, ans, on_fix_questions):
        card, inner = make_card(self, accent=COLORS["danger"], pady=12)
        card.pack(fill="x", pady=5)
        fast_label(inner, ans.get("topic", ""), size=12, muted=True, bg=COLORS["card_bg"]).pack(fill="x")
        fast_label(inner, ans.get("question", ""), size=16, bold=True,
                   bg=COLORS["card_bg"], wrap=780).pack(fill="x", pady=(2, 6))
        picked = _picked_text(ans)
        verb = "כתבת" if ans.get("selected_text") else "בחרת"
        tk.Label(inner, text=rtl(f"{verb}: {picked}"), bg=COLORS["card_bg"], fg=COLORS["danger"],
                 font=(ADHD_CONFIG["font_family"], font_size(13)), anchor="e",
                 justify="right", wraplength=780).pack(fill="x")
        tk.Label(inner, text=rtl(f"נכון: {ans.get('correct_answer', '')}"), bg=COLORS["card_bg"],
                 fg=COLORS["success"], font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
                 anchor="e", justify="right", wraplength=780).pack(fill="x")
        from core.teach import display_explanation

        expl = display_explanation(ans, ans.get("subject") or "")
        if expl:
            fast_label(inner, expl, size=13, muted=True, bg=COLORS["card_bg"], wrap=780).pack(
                fill="x", pady=(4, 0)
            )
        if on_fix_questions:
            ModernButton(
                inner, text=rtl("תקן עכשיו"), width=150,
                command=lambda item=ans: on_fix_questions([item]),
            ).pack(anchor="e", pady=(10, 0))

    def _review_card(self, ans):
        card, inner = make_card(self, pady=10)
        card.pack(fill="x", pady=4)

        fast_label(inner, ans.get("topic", ""), size=12, muted=True, bg=COLORS["card_bg"]).pack(fill="x")
        fast_label(inner, ans.get("question", ""), size=15, bold=True,
                   bg=COLORS["card_bg"], wrap=780).pack(fill="x", pady=(2, 5))

        picked = _picked_text(ans)
        verb = "כתבת" if ans.get("selected_text") else "בחרת"
        tk.Label(inner, text=rtl(f"{verb}: {picked}"), bg=COLORS["card_bg"], fg=COLORS["danger"],
                 font=(ADHD_CONFIG["font_family"], font_size(13)), anchor="e",
                 justify="right", wraplength=780).pack(fill="x")
        tk.Label(inner, text=rtl(f"נכון: {ans.get('correct_answer', '')}"), bg=COLORS["card_bg"],
                 fg=COLORS["success"], font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
                 anchor="e", justify="right", wraplength=780).pack(fill="x")
        from core.teach import display_explanation

        expl = display_explanation(ans, ans.get("subject") or "")
        if expl:
            fast_label(inner, expl, size=13, muted=True, bg=COLORS["card_bg"], wrap=780).pack(
                fill="x", pady=(3, 0)
            )
