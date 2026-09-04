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
        self._topics_open = False
        self._topics_host = None
        self._setup_ui()

    def _mode_desc(self, mode_key: str, fallback: str) -> str:
        if mode_key == "read":
            return "לקרוא ולהבין, בלי שעון"
        spec = self.specs.get(mode_key)
        if not spec:
            return fallback
        count = spec.get("count")
        seconds = spec.get("seconds")
        total = spec.get("total_limit_sec")
        if mode_key == "practice":
            return f"{count} שאלות עם הסבר"
        if mode_key == "compose":
            return f"{count} שאלות. כותבים לבד"
        if mode_key == "mock":
            clock = f"{seconds} שנ׳ לשאלה" if seconds else "בלי שעון"
            return f"{count} שאלות · {clock} · לא נשמר לפרופיל"
        if mode_key == "final":
            minutes = round((total or 0) / 60) if total else None
            when = f", כ־{minutes} דק׳" if minutes else ""
            return f"{count} שאלות{when} · התוצאה נשמרת"
        return fallback

    def _mode_row(self, parent, mode_key: str, can_final: bool) -> None:
        mode = SUBJECT_MODES.get(mode_key) or {}
        locked = mode_key == "final" and not can_final
        row = tk.Frame(parent, bg=COLORS["bg"])
        row.pack(fill="x", pady=3)
        left = tk.Frame(row, bg=COLORS["bg"])
        left.pack(side="right", fill="x", expand=True)
        tk.Label(
            left, text=rtl(mode.get("name", mode_key)),
            bg=COLORS["bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x")
        if locked:
            desc = "נעול עד שתתרגלו קצת (20 שאלות, 50%+)"
        else:
            desc = self._mode_desc(mode_key, mode.get("desc") or "")
        fast_label(left, desc, size=12, muted=True, bg=COLORS["bg"]).pack(fill="x")
        if locked:
            GhostButton(row, text=rtl("נעול"), width=96, height=38, state="disabled").pack(
                side="left", padx=(0, 6)
            )
        else:
            GhostButton(
                row, text=rtl("פתיחה"), width=96, height=38,
                command=lambda k=mode_key: self.on_mode_select(self.subject_key, k),
            ).pack(side="left", padx=(0, 6))

    def _setup_ui(self):
        info = SUBJECTS.get(self.subject_key, {})
        icon = SUBJECT_ICONS.get(self.subject_key, "")

        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x", pady=(0, 2))
        GhostButton(bar, text=rtl("‹  חזרה"), width=120, command=self.on_back).pack(side="right")

        title = info.get("name", self.subject_key)
        if icon:
            title = f"{icon}  {title}"
        heading(self, title, 26).pack(anchor="e", pady=(6, 0))
        from ui.widgets import gold_tick
        gold_tick(self).pack(anchor="e", pady=(0, 4))
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

        mistakes = int(self.stats.get("mistakes", 0) or 0)
        bits = [
            f"{self.stats.get('lessons', 0)} שיעורים",
            f"{self.stats.get('questions', 0)} שאלות במאגר",
        ]
        if mistakes:
            bits.append(f"{mistakes} לתיקון")
        fast_label(self, "  ·  ".join(bits), size=12, muted=True, bg=COLORS["bg"]).pack(
            anchor="e", pady=(2, 8)
        )

        can_final = True
        if self.storage:
            can_final = self.storage.can_take_final(self.subject_key)

        progress = float((self.level_info or {}).get("progress") or 0)
        primary_label = "המשך תרגול" if progress > 0.02 else "בואו נתרגל"
        ModernButton(
            self, text=rtl(primary_label), height=52,
            command=lambda: self.on_mode_select(self.subject_key, "practice"),
        ).pack(fill="x", pady=(2, 8))

        if mistakes:
            GhostButton(
                self, text=rtl(f"לתקן {mistakes} טעויות"), height=38,
                command=lambda: self.on_mode_select(self.subject_key, "mistakes"),
            ).pack(fill="x", pady=(0, 10))

        fast_label(self, "עוד דרכים ללמוד", size=12, muted=True, bg=COLORS["bg"]).pack(
            anchor="e", pady=(4, 2)
        )
        learn = tk.Frame(self, bg=COLORS["bg"])
        learn.pack(fill="x")
        for key in ("read", "compose"):
            if key in SUBJECT_MODES:
                self._mode_row(learn, key, can_final)

        fast_label(self, "מבחן במקצוע", size=12, muted=True, bg=COLORS["bg"]).pack(
            anchor="e", pady=(14, 2)
        )
        exams = tk.Frame(self, bg=COLORS["bg"])
        exams.pack(fill="x")
        for key in ("mock", "final"):
            if key in SUBJECT_MODES:
                self._mode_row(exams, key, can_final)

        self._topics_host = tk.Frame(self, bg=COLORS["bg"])
        self._topics_host.pack(fill="x", pady=(14, 0))
        self._render_topics()

    def _toggle_topics(self):
        self._topics_open = not self._topics_open
        self._render_topics()

    def _render_topics(self):
        for child in self._topics_host.winfo_children():
            child.destroy()
        rows = [row for row in self.topics if row.get("name") and (row.get("practice") or row.get("compose"))]
        if not rows:
            return
        label = "להסתיר נושאים" if self._topics_open else "לפי נושא מסוים"
        GhostButton(
            self._topics_host, text=rtl(label), height=38,
            command=self._toggle_topics,
        ).pack(fill="x")
        if not self._topics_open:
            return
        grid = tk.Frame(self._topics_host, bg=COLORS["bg"])
        grid.pack(fill="x", pady=(8, 0))
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
            fast_label(inner, "  ·  ".join(bits), size=12, muted=True, bg=COLORS["card_bg"]).pack(
                fill="x", pady=(2, 8)
            )
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
