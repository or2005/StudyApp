import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl
from core.diagnostic import EXAM_LENGTH, build_diagnostic, compute_level
from core.storage import UserStorage
from ui.fast import TkButton
from ui.widgets import ModernButton, ProgressBar, QuietFrame, body, heading, kicker, themed_entry, Page


class _ChoiceVar:
    """תואם ל-IntVar הישן, סקריפטי QA קוראים selected.set(0)."""

    def __init__(self, owner):
        self._owner = owner

    def set(self, value):
        self._owner._pick(int(value))

    def get(self):
        return self._owner._choice


class OnboardingFrame(Page):
    def __init__(self, master, storage: UserStorage, on_done, **kwargs):
        kwargs.pop("fg_color", None)
        ink = COLORS["bg_dark"]
        super().__init__(master, bg=ink, **kwargs)
        self.storage = storage
        self.on_done = on_done
        self.questions = []
        self.answers = []
        self.q_index = 0
        self._choice = -1
        self.selected = _ChoiceVar(self)
        self._opt_btns: list = []
        self._stage("welcome")

    def _clear(self):
        self._opt_btns = []
        for widget in self.winfo_children():
            widget.destroy()

    def _stage(self, stage: str):
        self._clear()
        if stage == "welcome":
            self._build_welcome()
        elif stage == "diagnostic":
            self._build_diagnostic()

    def _build_welcome(self):
        ink = COLORS["bg_dark"]
        holder = tk.Frame(self, bg=ink)
        holder.pack(fill="both", expand=True, padx=28, pady=28)

        shell = tk.Frame(holder, bg=COLORS.get("gold") or COLORS["accent"])
        shell.pack(fill="x", pady=(12, 12), padx=8)
        card = QuietFrame(shell)
        card.pack(fill="x", pady=(4, 0))

        kicker(card, "שלב 1 מתוך 2  ·  הרשמה", bg=COLORS["card_bg"]).pack(pady=(24, 0), padx=36, anchor="e")
        welcome = tk.Frame(card, bg=COLORS["card_bg"])
        welcome.pack(fill="x", padx=36, pady=(8, 6))
        from ui import skin

        logo = skin.logo_photo(self, 40)
        if logo is not None:
            tk.Label(welcome, image=logo, bg=COLORS["card_bg"], bd=0).pack(side="right", padx=(10, 0))
            self._logo_photo = logo
        heading(welcome, "ברוכים הבאים ל-StudyApp", 26).pack(side="right", fill="x", expand=True)
        body(card, "רק שם וגיל. אחר כך מבחן קצר לקביעת הרמה.", muted=True, wrap=460).pack(
            pady=(0, 10), padx=36
        )
        for line in (
            "שיעורים ותרגול לפי הרמה שלכם",
            "הכל נשמר במחשב, בלי חשבון ובלי שרת",
            "20 שאלות קצרות קובעות איפה מתחילים",
        ):
            body(card, f"·  {line}", muted=True, wrap=460, size=14).pack(anchor="e", padx=36, pady=1)
        tk.Frame(card, bg=COLORS["card_bg"], height=10).pack()

        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.err_label = tk.Label(
            card, text="", bg=COLORS["card_bg"], fg=COLORS["danger"],
            font=(ADHD_CONFIG["font_family"], 14), anchor="e", justify="right",
        )

        rows = [
            ("שם", self.name_var, "למשל: נועה"),
            ("גיל", self.age_var, "למשל: 16"),
            ("תעודת זהות (לא חובה)", self.id_var, "אפשר להשאיר ריק"),
        ]
        for title, var, _ph in rows:
            tk.Label(
                card, text=rtl(title), bg=COLORS["card_bg"], fg=COLORS["text_main"],
                font=(ADHD_CONFIG["font_family"], 14, "bold"), anchor="e", justify="right",
            ).pack(fill="x", padx=40)
            themed_entry(
                card, var, justify="right",
                font=(ADHD_CONFIG["font_family"], 16),
            ).pack(fill="x", padx=40, pady=(4, 12), ipady=10)

        self.err_label.pack()
        ModernButton(
            card, text=rtl("המשך למבחן אבחון"),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._submit_details,
        ).pack(fill="x", padx=40, pady=(8, 28))

    def _submit_details(self):
        name = self.name_var.get().strip()
        age = self.age_var.get().strip()
        idn = self.id_var.get().strip()
        if not name or not age:
            self.err_label.configure(text=rtl("נא למלא שם וגיל"))
            return
        if not age.isdigit() or not 5 <= int(age) <= 120:
            self.err_label.configure(text=rtl("הגיל צריך להיות מספר בין 5 ל-120"))
            return
        if idn and not (idn.isdigit() and 5 <= len(idn) <= 9):
            self.err_label.configure(text=rtl("אם ממלאים ת\"ז: רק ספרות, 5 עד 9"))
            return
        self.storage.save_student(name, int(age), idn)
        self._stage("diagnostic")

    def _build_diagnostic(self):
        self.questions = build_diagnostic()
        self.answers = []
        self.q_index = 0
        ink = COLORS["bg_dark"]
        ink_fg = COLORS.get("banner_text") or COLORS["text_on_primary"]
        ink_muted = COLORS.get("sidebar_muted") or "#9DC4BC"
        top = tk.Frame(self, bg=ink)
        top.pack(fill="x", padx=32, pady=(24, 8))
        heading(top, "שלב 2 מתוך 2  ·  מבחן אבחון", 24, fg=ink_fg).pack(anchor="e")
        body(top, "20 שאלות קצרות. בסוף נקבעת הרמה שלך.", fg=ink_muted).pack(anchor="e", pady=(0, 6))
        self.counter_lbl = body(top, "", fg=ink_muted)
        self.counter_lbl.pack(anchor="e")
        self.progress = ProgressBar(
            self, pct=0, height=8,
            color=COLORS["primary"],
            track=COLORS.get("banner_track") or COLORS["card_hover"],
        )
        self.progress.pack(fill="x", padx=32, pady=(4, 0))
        self.body = tk.Frame(self, bg=ink)
        self.body.pack(fill="both", expand=True, padx=24, pady=12)
        self._show_question()

    def _show_question(self):
        for widget in self.body.winfo_children():
            widget.destroy()
        q = self.questions[self.q_index]
        n = self.q_index + 1
        self._choice = -1
        self.counter_lbl.configure(text=rtl(f"שאלה {n} מתוך {EXAM_LENGTH}"))
        self.progress.set_pct(n / EXAM_LENGTH)

        card = QuietFrame(self.body)
        card.pack(fill="both", expand=True)
        body(card, f"{q['topic']}", muted=True).pack(anchor="e", padx=24, pady=(20, 4))
        heading(card, q["question"], 20).pack(anchor="e", padx=24, pady=(0, 16))

        self._opt_btns = []
        for i, opt in enumerate(q["options"]):
            btn = TkButton(
                card,
                text=rtl(f"{i + 1}.  {opt}"),
                font=(ADHD_CONFIG["font_family"], 16, "bold"),
                fg_color=COLORS["option_bg"],
                hover_color=COLORS["option_hover"],
                text_color=COLORS["option_text"],
                border_width=1,
                border_color=COLORS.get("option_border") or COLORS["card_border"],
                anchor="e",
                height=ADHD_CONFIG["option_height"],
                command=lambda idx=i: self._pick(idx),
            )
            btn.pack(fill="x", padx=24, pady=4)
            self._opt_btns.append(btn)

        self.pick_hint = body(card, "בחרו תשובה ואז המשיכו.", muted=True, size=13)
        self.pick_hint.pack(anchor="e", padx=24, pady=(8, 0))

        last = n == EXAM_LENGTH
        ModernButton(
            card,
            text=rtl("סיום אבחון") if last else rtl("הבא"),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._next_question,
        ).pack(fill="x", padx=24, pady=(12, 24))

    def _pick(self, index: int):
        self._choice = index
        alive = []
        for i, btn in enumerate(getattr(self, "_opt_btns", []) or []):
            try:
                if not btn.winfo_exists():
                    continue
            except tk.TclError:
                continue
            alive.append(btn)
            if i == index:
                btn.configure(
                    fg_color=COLORS["primary"],
                    text_color=COLORS["text_on_primary"],
                    border_color=COLORS["primary"],
                )
            else:
                btn.configure(
                    fg_color=COLORS["option_bg"],
                    text_color=COLORS["option_text"],
                    border_color=COLORS.get("option_border") or COLORS["card_border"],
                )
        self._opt_btns = alive
        hint = getattr(self, "pick_hint", None)
        if hint is not None:
            try:
                if hint.winfo_exists():
                    hint.configure(text=rtl("אפשר להמשיך."), fg=COLORS["text_muted"])
            except tk.TclError:
                pass

    def _next_question(self):
        sel = self._choice
        if sel < 0:
            self.pick_hint.configure(text=rtl("בחרו תשובה כדי להמשיך."), fg=COLORS["danger"])
            return
        q = self.questions[self.q_index]
        self.answers.append({
            "subject": q["subject"],
            "topic": q["topic"],
            "correct": sel == q["answer"],
            "difficulty": q["difficulty"],
        })
        self.q_index += 1
        if self.q_index < EXAM_LENGTH:
            self._show_question()
        else:
            self._finish_diagnostic()

    def _finish_diagnostic(self):
        self._clear()
        correct = sum(1 for a in self.answers if a["correct"])
        result = compute_level(correct, answers=self.answers)
        self.storage.save_diagnostic(
            correct, EXAM_LENGTH, result["level"], self.answers,
            recommendations=result["recommendations"], weak_topics=result["weak_topics"],
        )
        self._show_summary(result, correct)

    def _show_summary(self, result, correct):
        self._clear()
        ink = COLORS["bg_dark"]
        holder = tk.Frame(self, bg=ink)
        holder.pack(fill="both", expand=True, padx=28, pady=28)
        shell = tk.Frame(holder, bg=COLORS.get("gold") or COLORS["accent"])
        shell.pack(fill="x", padx=8, pady=12)
        card = QuietFrame(shell)
        card.pack(fill="x", pady=(4, 0))
        kicker(card, "אבחון", bg=COLORS["card_bg"]).pack(pady=(24, 0), padx=36, anchor="e")
        heading(card, "סיימנו את האבחון").pack(pady=(8, 8), padx=36)
        body(card, f"נכון: {correct} מתוך {EXAM_LENGTH}  ({result['pct']}%)").pack(pady=4, padx=36)
        heading(card, f"רמה: {result['level_title']}", 20).pack(pady=(4, 12), padx=36)
        ProgressBar(card, pct=(result.get("pct") or 0) / 100, height=8).pack(fill="x", padx=36, pady=(0, 12))
        body(card, "מה כדאי עכשיו:", muted=True).pack(anchor="e", padx=36)
        for rec in result["recommendations"][:3]:
            body(card, f"• {rec}", muted=True, wrap=640).pack(anchor="e", padx=36, pady=3)
        ModernButton(
            card, text=rtl("המשך לדשבורד"), fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], command=self.on_done,
        ).pack(fill="x", padx=36, pady=(18, 24))
