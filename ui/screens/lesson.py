import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl
from core.lesson_plain import organize_lesson
from ui.fast import FastText, fast_label
from ui.widgets import GhostButton, ModernButton, font_size, heading, Page


class LessonScreen(Page):
    """שיעור עיוני: קריאה מסודרת → דוגמה → הסבר מפורט → תרגול."""

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

        from core.stem_fix import clean_topic_label

        title = clean_topic_label(str(lesson.get("title") or "שיעור"))
        heading(self, title, 24).pack(anchor="e", pady=(12, 2))
        category = lesson.get("category") or "שיעור עיוני"
        fast_label(
            self, f"שיעור {index + 1} מתוך {total}  ·  {category}",
            size=13, muted=True, bg=COLORS["bg"],
        ).pack(anchor="e", pady=(0, 8))

        card = tk.Frame(
            self, bg=COLORS["card_bg"],
            highlightthickness=1, highlightbackground=COLORS["card_border"],
        )
        card.pack(fill="x", pady=(0, 12))
        tk.Frame(card, bg=COLORS.get("gold") or COLORS["accent"], height=3).pack(fill="x")

        try:
            from core.illustrations.schema import get_visual
            from ui.visual_panel import VisualPanel

            if get_visual(lesson):
                VisualPanel(card, lesson, mode="lesson", bg=COLORS["card_bg"], max_width=720).pack(
                    fill="x", padx=10, pady=(10, 4),
                )
        except Exception:
            pass

        parts = organize_lesson(
            lesson.get("content") or "",
            subject=str(lesson.get("subject") or ""),
            topic=str(lesson.get("topic") or lesson.get("title") or ""),
        )
        inner = tk.Frame(card, bg=COLORS["card_bg"])
        inner.pack(fill="x", padx=14, pady=12)

        spoken: list[str] = []
        if parts.get("reading"):
            self._heading(inner, "קריאה")
            self._reader(inner, parts["reading"])
            spoken.append(parts["reading"])
        if parts.get("example"):
            self._heading(inner, "דוגמה")
            self._paras(inner, parts["example"], size=15)
            spoken.append(parts["example"])
        if parts.get("explain"):
            self._heading(inner, "הסבר")
            self._reader(inner, parts["explain"], height_hint=10)
            spoken.append(parts["explain"])
        if not spoken:
            fallback = (lesson.get("content") or "אין תוכן לשיעור.").strip()
            self._heading(inner, "קריאה")
            self._reader(inner, fallback)
            spoken.append(fallback)

        if speaker is not None and speaker.enabled:
            GhostButton(
                bar, text=rtl("🔊 הקראה"), width=120,
                command=lambda: speaker.say("\n".join(spoken)),
            ).pack(side="left", padx=4)

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
            self, text=rtl("תרגול קצר על השיעור"), fg_color=COLORS["success"],
            hover_color=COLORS.get("success_hover") or COLORS["primary_hover"],
            text_color=COLORS.get("success_text") or "#FFFFFF",
            command=on_practice,
        ).pack(fill="x", pady=(4, 8))

    def _heading(self, parent, title: str):
        tk.Label(
            parent,
            text=rtl(title),
            bg=COLORS["card_bg"],
            fg=COLORS["primary"],
            font=(ADHD_CONFIG["font_family"], font_size(16), "bold"),
            anchor="e",
        ).pack(anchor="e", pady=(10, 4))

    def _paras(self, parent, text: str, *, size: int = 15):
        for block in str(text or "").split("\n\n"):
            block = block.strip()
            if not block:
                continue
            for line in block.split("\n"):
                line = line.strip()
                if not line:
                    continue
                fast_label(parent, line, size=size, bg=COLORS["card_bg"], wrap=700).pack(
                    anchor="e", pady=1,
                )

    def _reader(self, parent, text: str, *, height_hint: int = 14):
        body = str(text or "").strip()
        lines = max(8, min(28, height_hint + body.count("\n") // 2 + len(body) // 120))
        reader = FastText(parent, height=lines)
        reader.pack(fill="x", pady=(0, 4))
        reader.set_text(body, rtl_lines=True)

    def on_key(self, event):
        key = (event.keysym or "").lower()
        if key == "left" and self._on_next:
            self._on_next()
        elif key == "right" and self._on_prev:
            self._on_prev()
