import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl, subject_label
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, empty_state, font_size, heading, make_card, page_header, Page


class MistakesScreen(Page):
    """כל שאלה שנענתה לא נכון, עם התשובה הנכונה וההסבר."""

    def __init__(self, master, mistakes, on_drill, on_clear):
        super().__init__(master)
        page_header(
            self,
            "הטעויות שלי",
            "כאן נשמרת כל שאלה שטעית בה. תשובה נכונה מסירה אותה מהרשימה.",
        )

        if not mistakes:
            empty_state(
                self,
                "אין טעויות פתוחות. יפה מאוד.",
                "כל תשובה שגויה תופיע כאן, עם ההסבר, עד שתענו עליה נכון.",
            ).pack(fill="x")
            return

        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(0, 12))
        ModernButton(
            actions, text=rtl(f"תרגול הטעויות ({min(15, len(mistakes))} שאלות)"), width=240,
            command=lambda: on_drill(None),
        ).pack(side="right", padx=5)
        GhostButton(actions, text=rtl("ניקוי הרשימה"), width=150, command=on_clear).pack(side="right", padx=5)

        by_subject: dict[str, list] = {}
        for item in mistakes:
            by_subject.setdefault(item.get("subject") or "כללי", []).append(item)

        for subject, items in by_subject.items():
            heading(self, f"{subject_label(subject)}  ({len(items)})", 18).pack(anchor="e", pady=(12, 6))
            for item in items:
                self._card(item)

    def _card(self, item):
        card, inner = make_card(self, pady=12)
        card.pack(fill="x", pady=4)

        times = int(item.get("times_wrong", 1))
        meta = f"{item.get('topic', '')}  ·  טעית {times} פעמים"
        fast_label(inner, meta, size=12, muted=True, bg=COLORS["card_bg"]).pack(fill="x")
        fast_label(inner, item.get("question", ""), size=15, bold=True,
                   bg=COLORS["card_bg"], wrap=780).pack(fill="x", pady=(2, 6))

        options = item.get("options") or []
        chosen = item.get("selected")
        if isinstance(chosen, int) and 0 <= chosen < len(options):
            tk.Label(
                inner, text=rtl(f"בחרת: {options[chosen]}"), bg=COLORS["card_bg"],
                fg=COLORS["danger"], font=(ADHD_CONFIG["font_family"], font_size(13)),
                anchor="e", justify="right", wraplength=780,
            ).pack(fill="x")
        tk.Label(
            inner, text=rtl(f"נכון: {item.get('correct_answer', '')}"), bg=COLORS["card_bg"],
            fg=COLORS["success"], font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
            anchor="e", justify="right", wraplength=780,
        ).pack(fill="x")
        from core.teach import display_explanation

        expl = display_explanation(item, item.get("subject") or "")
        if expl:
            fast_label(inner, expl, size=13, muted=True, bg=COLORS["card_bg"], wrap=780).pack(
                fill="x", pady=(4, 0)
            )
