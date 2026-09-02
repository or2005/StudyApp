import tkinter as tk

from core.config import COLORS, rtl
from ui.fast import FastText, fast_label
from ui.widgets import GhostButton, ModernButton, heading, Page


class LessonScreen(Page):
    def __init__(self, master, lesson, index, total, on_back, on_prev, on_next, on_practice,
                 speaker=None):
        super().__init__(master)
        self.speaker = speaker
        self.lesson = lesson
        self._on_prev = on_prev
        self._on_next = on_next

        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x")
        GhostButton(bar, text=rtl("‹  חזרה"), width=110, command=on_back).pack(side="right")
        if speaker is not None and speaker.enabled:
            GhostButton(bar, text=rtl("🔊 הקראת השיעור"), width=180,
                        command=lambda: speaker.say(lesson.get("content", ""))).pack(side="left", padx=4)

        heading(self, lesson.get("title", "שיעור"), 24).pack(anchor="e", pady=(12, 2))
        category = lesson.get("category") or "שיעור עיוני"
        fast_label(self, f"שיעור {index + 1} מתוך {total}  ·  {category}", size=13, muted=True,
                   bg=COLORS["bg"]).pack(anchor="e", pady=(0, 8))

        card = tk.Frame(
            self, bg=COLORS["card_bg"],
            highlightthickness=1, highlightbackground=COLORS["card_border"],
        )
        card.pack(fill="x", pady=(0, 12))
        tk.Frame(card, bg=COLORS.get("gold") or COLORS["accent"], height=3).pack(fill="x")
        content = lesson.get("content", "") or ""
        reader = FastText(card, height=min(36, 12 + content.count("\n") // 2))
        reader.pack(fill="x", padx=4, pady=4)
        reader.set_text(content, rtl_lines=True)
        fast_label(
            self, "חצים: שיעור קודם / הבא", size=12, muted=True, bg=COLORS["bg"],
        ).pack(anchor="e", pady=(0, 6))

        nav = tk.Frame(self, bg=COLORS["bg"])
        nav.pack(fill="x", pady=(0, 6))
        if on_prev:
            GhostButton(nav, text=rtl("‹  שיעור קודם"), width=160, command=on_prev).pack(side="right", padx=5)
        if on_next:
            ModernButton(nav, text=rtl("שיעור הבא  ›"), width=160, height=48,
                         command=on_next).pack(side="right", padx=5)

        ModernButton(
            self, text=rtl("תרגול על השיעור הזה"), fg_color=COLORS["success"],
            hover_color=COLORS.get("success_hover") or COLORS["primary_hover"],
            text_color=COLORS.get("success_text") or "#FFFFFF",
            command=on_practice,
        ).pack(fill="x", pady=(4, 8))

    def on_key(self, event):
        key = (event.keysym or "").lower()
        if key == "left" and self._on_next:
            self._on_next()
        elif key == "right" and self._on_prev:
            self._on_prev()
