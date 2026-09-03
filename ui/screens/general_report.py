"""דוח מקיף אחרי המבחן הכללי האמריקאי."""
import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, ProgressBar, font_size, heading, make_card, Page


class GeneralExamReportScreen(Page):
    def __init__(self, master, report, on_home, on_retry=None, session=None):
        super().__init__(master)
        self.report = report or {}
        self.session = session
        percent = float(self.report.get("percent") or 0)
        grade = self.report.get("grade") or "-"
        scaled = self.report.get("scaled") or 200
        level_he = self.report.get("level_he") or "מתחיל"
        score = self.report.get("score") or 0
        total = self.report.get("total") or 50
        if percent >= 85:
            color = COLORS["success"]
        elif percent >= 55:
            color = COLORS["accent"]
        else:
            color = COLORS["danger"]

        hero, hero_inner = make_card(self, accent=color, thick=2, pady=16)
        hero.pack(fill="x", pady=(4, 10))
        heading(hero_inner, "דוח מבחן כללי, American MCQ", 24).pack(anchor="e")
        fast_label(hero_inner, self.report.get("headline") or "", size=14, muted=True,
                   bg=COLORS["card_bg"], wrap=820).pack(anchor="e", pady=(4, 8))
        tk.Label(
            hero_inner,
            text=rtl(f"{score}/{total}   ·   {percent}%   ·   Grade {grade}   ·   Scaled {scaled}"),
            font=(ADHD_CONFIG["font_family"], font_size(26), "bold"),
            bg=COLORS["card_bg"], fg=COLORS["text_main"], anchor="e",
        ).pack(anchor="e")
        ProgressBar(hero_inner, pct=percent / 100, color=color, height=8).pack(fill="x", pady=(8, 8))
        tk.Label(
            hero_inner, text=rtl(f"רמת התלמיד לפי המבחן: {level_he}"),
            font=(ADHD_CONFIG["font_family"], font_size(16), "bold"),
            bg=COLORS["card_bg"], fg=color, anchor="e",
        ).pack(anchor="e")
        date = self.report.get("date") or ""
        extra = f"זמן ממוצע לשאלה: {self.report.get('avg_time_sec', 0)} שנ׳"
        if date:
            extra = f"{date}  ·  {extra}"
        fast_label(hero_inner, extra, size=13, muted=True, bg=COLORS["card_bg"]).pack(
            anchor="e", pady=(4, 0)
        )

        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(0, 10))
        ModernButton(actions, text=rtl("חזרה לדשבורד"), width=200, command=on_home).pack(side="right", padx=5)
        if on_retry:
            GhostButton(actions, text=rtl("למסך המבחן הכללי"), width=200, command=on_retry).pack(side="right", padx=5)

        heading(self, "איפה להשתפר לפי מקצוע", 18).pack(anchor="e", pady=(6, 6))
        for row in self.report.get("subjects") or []:
            if not row.get("total"):
                continue
            card, inner = make_card(self, pady=10)
            card.pack(fill="x", pady=4)
            pct = float(row.get("percent") or 0)
            fill = max(0.04, min(1.0, pct / 100))
            heading(
                inner,
                f"{row.get('name')}  ·  {row.get('correct')}/{row.get('total')}  ({pct}%)  ·  {row.get('grade')}  ·  {row.get('level_he')}",
                16,
            ).pack(anchor="e")
            bar_color = COLORS["success"] if pct >= 80 else (COLORS["accent"] if pct >= 55 else COLORS["danger"])
            ProgressBar(inner, pct=fill, color=bar_color, height=8).pack(fill="x", pady=(8, 6))
            fast_label(inner, row.get("advice") or "", size=13, muted=True,
                       bg=COLORS["card_bg"], wrap=800).pack(anchor="e")

        plan = self.report.get("plan") or []
        if plan:
            box, plan_inner = make_card(self, accent=COLORS["primary"], pady=12)
            box.pack(fill="x", pady=(10, 8))
            heading(plan_inner, "תוכנית לימוד קרובה", 18).pack(anchor="e")
            for step in plan:
                fast_label(plan_inner, f"• {step}", size=14, bg=COLORS["card_bg"], wrap=800).pack(
                    anchor="e", pady=1
                )

        recs = self.report.get("recommendations") or []
        if recs:
            rec_box, rec_inner = make_card(self, pady=10)
            rec_box.pack(fill="x", pady=(0, 8))
            heading(rec_inner, "המלצות המערכת", 17).pack(anchor="e")
            for rec in recs:
                fast_label(rec_inner, f"• {rec}", size=13, muted=True,
                           bg=COLORS["card_bg"], wrap=800).pack(anchor="e", pady=1)

        weak_topics = self.report.get("weak_topics") or []
        if weak_topics:
            heading(self, "נושאים שירדו במבחן", 17).pack(anchor="e", pady=(6, 4))
            for item in weak_topics:
                fast_label(
                    self,
                    f"{item.get('subject_name')}: {item.get('topic')}, "
                    f"{item.get('correct')}/{item.get('total')} ({item.get('percent')}%)",
                    size=13, muted=True,
                ).pack(anchor="e")

        narrative = self.report.get("narrative") or ""
        if narrative:
            info, info_inner = make_card(self, pady=10)
            info.pack(fill="both", expand=True, pady=(12, 6))
            heading(info_inner, "דוח לימודי מלא", 17).pack(anchor="e")
            fast_label(
                info_inner, narrative, size=14, muted=True,
                bg=COLORS["card_bg"], wrap=780,
            ).pack(fill="x", padx=4, pady=8)

        wrong = []
        if self.session is not None and hasattr(self.session, "wrong_answers"):
            wrong = self.session.wrong_answers()
        if wrong:
            heading(self, f"סקירת שגיאות ({len(wrong)})", 19).pack(anchor="e", pady=(10, 6))
            for ans in wrong:
                self._review_card(ans)

    def _review_card(self, ans):
        card, inner = make_card(self, pady=10)
        card.pack(fill="x", pady=4)
        from core.config import subject_label

        subj = subject_label(ans.get("subject") or "")
        fast_label(inner, f"{subj}  ·  {ans.get('topic', '')}", size=12, muted=True,
                   bg=COLORS["card_bg"]).pack(fill="x")
        fast_label(inner, ans.get("question", ""), size=15, bold=True,
                   bg=COLORS["card_bg"], wrap=780).pack(fill="x", pady=(2, 5))
        options = ans.get("options") or []
        chosen = ans.get("selected")
        letters = "ABCD"
        if isinstance(chosen, int) and 0 <= chosen < len(options):
            letter = letters[chosen] if chosen < 4 else str(chosen + 1)
            picked = f"{letter}. {options[chosen]}"
        else:
            picked = "לא נענתה בזמן"
        tk.Label(inner, text=rtl(f"בחרת: {picked}"), bg=COLORS["card_bg"], fg=COLORS["danger"],
                 font=(ADHD_CONFIG["font_family"], font_size(13)), anchor="e",
                 justify="right", wraplength=780).pack(fill="x")
        correct = ans.get("correct_answer", "")
        ans_idx = ans.get("answer")
        if isinstance(ans_idx, int) and 0 <= ans_idx < 4:
            correct = f"{letters[ans_idx]}. {correct}"
        tk.Label(inner, text=rtl(f"נכון: {correct}"), bg=COLORS["card_bg"],
                 fg=COLORS["success"], font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
                 anchor="e", justify="right", wraplength=780).pack(fill="x")
        from core.teach import display_explanation

        expl = display_explanation(ans, ans.get("subject") or "")
        if expl:
            fast_label(inner, expl, size=13, muted=True, bg=COLORS["card_bg"], wrap=780).pack(
                fill="x", pady=(3, 0)
            )
