import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, SUBJECT_MODES, SUBJECTS, rtl
from core.theme import subject_accent
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, ProgressBar, SUBJECT_ICONS, body, font_size, heading, make_card, Page


class SubjectHubScreen(Page):
    def __init__(self, master, subject_key, on_mode_select, on_back, stats=None, storage=None,
                 level_info=None, specs=None, topics=None):
        super().__init__(master)
        self.subject_key = subject_key
        self.on_mode_select = on_mode_select
        self.on_back = on_back
        self.stats = stats or {}
        self.storage = storage
        self.level_info = level_info or {}
        self.specs = specs or {}
        self.topics = topics or []
        self._setup_ui()

    def _mode_desc(self, mode_key: str, fallback: str) -> str:
        """הטקסט חייב לשקף את מה שבאמת יקרה, הכמות והשעון משתנים לפי הרמה."""
        spec = self.specs.get(mode_key)
        if not spec:
            return fallback
        count = spec.get("count")
        seconds = spec.get("seconds")
        total = spec.get("total_limit_sec")
        if mode_key == "practice":
            return f"{count} שאלות מותאמות לרמה שלך, עם רמז והסבר אחרי כל תשובה."
        if mode_key == "compose":
            return (
                f"{count} שאלות כתיבה אמיתיות. כל שאלה אומרת מה לרשום "
                "(מילה, מספר או שנה), בלי ארבע אפשרויות."
            )
        if mode_key == "mock":
            clock = f"עם {seconds} שניות לשאלה" if seconds else "בלי שעון"
            return f"{count} שאלות, {clock}. הציון בסוף, בלי השפעה על הפרופיל."
        if mode_key == "final":
            minutes = round((total or 0) / 60) if total else None
            when = f", {minutes} דקות סה\"כ" if minutes else ""
            return f"{count} שאלות בזמן{when}. התוצאה נשמרת."
        return fallback

    def _setup_ui(self):
        info = SUBJECTS.get(self.subject_key, {})
        icon = SUBJECT_ICONS.get(self.subject_key, "📚")

        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(0, 2))
        GhostButton(bar, text=rtl("‹  חזרה לבית"), width=160, command=self.on_back).pack(side="right")

        heading(self, f"{icon}  {info.get('name', self.subject_key)}", 26).pack(anchor="e", pady=(6, 0))
        from ui.widgets import gold_tick
        gold_tick(self).pack(anchor="e", pady=(0, 6))
        body(self, info.get("desc", ""), muted=True).pack(anchor="e")

        snap = self.level_info
        accent = subject_accent(self.subject_key)
        if snap:
            banner, inner = make_card(self, accent=accent, pady=12)
            banner.pack(fill="x", pady=(10, 8))
            tk.Label(
                inner, text=rtl(snap.get("headline", "רמת המקצוע")),
                bg=COLORS["card_bg"], fg=COLORS["text_main"],
                font=(ADHD_CONFIG["font_family"], font_size(16), "bold"),
                anchor="e", justify="right",
            ).pack(fill="x")
            fast_label(inner, snap.get("blurb", ""), size=13, muted=True,
                       bg=COLORS["card_bg"], wrap=720).pack(fill="x", pady=(2, 0))
            ProgressBar(
                inner, pct=max(0.04, min(1.0, float(snap.get("progress") or 0))), height=8,
                color=accent,
            ).pack(fill="x", pady=(8, 4))

        line = f"{self.stats.get('lessons', 0)} שיעורים  ·  {self.stats.get('questions', 0)} שאלות"
        mistakes = int(self.stats.get("mistakes", 0) or 0)
        if mistakes:
            line += f"  ·  {mistakes} טעויות פתוחות"
        fast_label(self, line, size=13, muted=True, bg=COLORS["bg"]).pack(anchor="e", pady=(2, 10))

        can_final = True
        if self.storage:
            can_final = self.storage.can_take_final(self.subject_key)

        grid = tk.Frame(self, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1, uniform="mode")
        grid.columnconfigure(1, weight=1, uniform="mode")

        for i, (mode_key, mode) in enumerate(SUBJECT_MODES.items()):
            locked = mode_key == "final" and not can_final
            card, inner = make_card(grid, pady=16)
            card.grid(row=i // 2, column=1 - (i % 2), sticky="nsew", padx=10, pady=10)

            tk.Label(inner, text=rtl(mode["name"]), bg=COLORS["card_bg"], fg=COLORS["text_main"],
                     font=(ADHD_CONFIG["font_family"], font_size(17), "bold"),
                     anchor="e", justify="right").pack(fill="x")
            if locked:
                desc = "נעול. תרגלו 20 שאלות עם דיוק 50%+."
            else:
                desc = self._mode_desc(mode_key, mode["desc"])
            fast_label(inner, desc, size=13, muted=True, bg=COLORS["card_bg"], wrap=380).pack(fill="x", pady=(6, 12))

            if locked:
                GhostButton(inner, text=rtl("נעול"), height=44, state="disabled").pack(fill="x")
            else:
                ModernButton(
                    inner, text=rtl("התחלה"), height=44,
                    command=lambda k=mode_key: self.on_mode_select(self.subject_key, k),
                ).pack(fill="x")

        if mistakes:
            ModernButton(
                self, text=rtl(f"תרגול {mistakes} הטעויות במקצוע הזה"), fg_color=COLORS["accent"],
                command=lambda: self.on_mode_select(self.subject_key, "mistakes"),
            ).pack(fill="x", pady=(10, 4))

        self._pack_topics()

    def _pack_topics(self):
        rows = [row for row in self.topics if row.get("name") and (row.get("practice") or row.get("compose"))]
        if not rows:
            return
        heading(self, "תרגול לפי נושא", 18).pack(anchor="e", pady=(18, 2))
        fast_label(
            self, "רק הנושא הזה, בלי לערבב את שאר המקצוע.",
            size=13, muted=True, bg=COLORS["bg"],
        ).pack(anchor="e", pady=(0, 8))
        grid = tk.Frame(self, bg=COLORS["bg"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="topic")
        grid.columnconfigure(1, weight=1, uniform="topic")
        for i, row in enumerate(rows):
            card, inner = make_card(grid, pady=12)
            card.grid(row=i // 2, column=1 - (i % 2), sticky="nsew", padx=8, pady=6)
            tk.Label(
                inner, text=rtl(row["name"]),
                bg=COLORS["card_bg"], fg=COLORS["text_main"],
                font=(ADHD_CONFIG["font_family"], font_size(15), "bold"),
                anchor="e", justify="right",
            ).pack(fill="x")
            bits = []
            if row.get("practice"):
                bits.append(f"{row['practice']} לתרגול")
            if row.get("compose"):
                bits.append(f"{row['compose']} ליצור")
            fast_label(inner, "  ·  ".join(bits), size=12, muted=True, bg=COLORS["card_bg"]).pack(fill="x", pady=(2, 8))
            btns = tk.Frame(inner, bg=COLORS["card_bg"])
            btns.pack(fill="x")
            name = row["name"]
            if row.get("practice"):
                ModernButton(
                    btns, text=rtl("תרגול"), height=40,
                    command=lambda topic=name: self.on_mode_select(
                        self.subject_key, "practice", topic, True
                    ),
                ).pack(side="right", fill="x", expand=True, padx=(4, 0))
            if row.get("compose"):
                GhostButton(
                    btns, text=rtl("יצור"), height=40,
                    command=lambda topic=name: self.on_mode_select(
                        self.subject_key, "compose", topic, True
                    ),
                ).pack(side="right", fill="x", expand=True, padx=(0, 4))
