import tkinter as tk

from core.config import ADHD_CONFIG, ALL_SUBJECTS, COLORS, rtl, subject_label
from core import custom_questions
from ui.fast import FastButton, fast_label
from ui.widgets import font_size, page_header, themed_entry, Page


class QuestionEditorScreen(Page):
    def __init__(self, master, on_back, **kwargs):
        super().__init__(master)
        self.on_back = on_back
        self.subject = ALL_SUBJECTS[0]
        self.correct = 0
        self.difficulty = "Easy"
        self.q_var = tk.StringVar()
        self.topic_var = tk.StringVar(value="שאלות שהוספתי")
        self.opt_vars = [tk.StringVar() for _ in range(4)]
        self.exp_var = tk.StringVar()
        self._status = None
        self._list_host = None
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x")
        FastButton(bar, "חזרה", command=self.on_back).pack(anchor="e")

        page_header(
            self,
            "עורך שאלות",
            "מוסיפים שאלה בעברית. היא נשמרת במחשב ונכנסת לתרגול של המקצוע.",
        )

        card = self._card("מקצוע", "השאלה תופיע רק במקצוע שבחרתם.")
        self._subject_btns = []
        keys = list(ALL_SUBJECTS)
        for chunk_start in (0, 4, 8):
            row = tk.Frame(card, bg=COLORS["card_bg"])
            row.pack(fill="x", pady=(8, 0) if chunk_start == 0 else (4, 0))
            for key in keys[chunk_start:chunk_start + 4]:
                btn = FastButton(
                    row,
                    subject_label(key),
                    command=lambda k=key: self._set_subject(k),
                    primary=(key == self.subject),
                    width=8,
                )
                btn.pack(side="right", padx=3, pady=2)
                self._subject_btns.append((key, btn))

        card = self._card("השאלה", "נושא קצר, ואז ניסוח ברור.")
        themed_entry(card, self.topic_var, justify="right").pack(fill="x", pady=(8, 4), ipady=7)
        themed_entry(card, self.q_var, justify="right").pack(fill="x", pady=(0, 0), ipady=7)

        card = self._card("ארבע תשובות", "סמנו איזו תשובה נכונה. כל אפשרות חייבת להיות שונה.")
        self._correct_btns = []
        for idx in range(4):
            line = tk.Frame(card, bg=COLORS["card_bg"])
            line.pack(fill="x", pady=3)
            themed_entry(line, self.opt_vars[idx], justify="right").pack(
                side="right", fill="x", expand=True, ipady=6, padx=(8, 0)
            )
            btn = FastButton(
                line,
                f"{idx + 1}",
                command=lambda i=idx: self._set_correct(i),
                primary=(idx == self.correct),
                width=4,
            )
            btn.pack(side="right")
            self._correct_btns.append(btn)

        card = self._card("הסבר", "לפחות 20 תווים. התלמיד רואה אותו אחרי התשובה.")
        themed_entry(card, self.exp_var, justify="right").pack(fill="x", pady=(8, 0), ipady=7)
        row = tk.Frame(card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=(8, 0))
        self._diff_btns = []
        for label, value in (("קל", "Easy"), ("בינוני", "Medium"), ("קשה", "Hard")):
            btn = FastButton(
                row,
                label,
                command=lambda v=value: self._set_diff(v),
                primary=(value == self.difficulty),
                width=8,
            )
            btn.pack(side="right", padx=4)
            self._diff_btns.append((value, btn))
        FastButton(row, "שמירת השאלה", command=self._save, primary=True).pack(side="left")

        self._status = fast_label(self, "", size=13, muted=True, bg=COLORS["bg"])
        self._status.pack(anchor="e", pady=(4, 8))

        heading_card = self._card("שאלות שהוספתם", "אפשר למחוק שאלה בלי לגעת במאגר המובנה.")
        self._list_host = tk.Frame(heading_card, bg=COLORS["card_bg"])
        self._list_host.pack(fill="x", pady=(8, 0))
        self._refresh_list()

    def _card(self, title, subtitle):
        frame = tk.Frame(
            self,
            bg=COLORS["card_bg"],
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
        )
        frame.pack(fill="x", pady=6)
        inner = tk.Frame(frame, bg=COLORS["card_bg"])
        inner.pack(fill="x", padx=16, pady=14)
        tk.Label(
            inner,
            text=rtl(title),
            bg=COLORS["card_bg"],
            fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(17), "bold"),
            anchor="e",
            justify="right",
        ).pack(fill="x")
        fast_label(inner, subtitle, size=13, muted=True, bg=COLORS["card_bg"], wrap=740).pack(fill="x")
        return inner

    def _set_subject(self, key):
        self.subject = key
        for item_key, btn in self._subject_btns:
            btn._bg = COLORS["primary"] if item_key == key else COLORS["card_bg"]
            btn._hover = COLORS["primary_hover"] if item_key == key else COLORS["card_hover"]
            btn.configure(
                bg=btn._bg,
                fg=COLORS["text_on_primary"] if item_key == key else COLORS["text_main"],
            )
        self._refresh_list()

    def _set_correct(self, index):
        self.correct = index
        for idx, btn in enumerate(self._correct_btns):
            btn._bg = COLORS["primary"] if idx == index else COLORS["card_bg"]
            btn._hover = COLORS["primary_hover"] if idx == index else COLORS["card_hover"]
            btn.configure(
                bg=btn._bg,
                fg=COLORS["text_on_primary"] if idx == index else COLORS["text_main"],
            )

    def _set_diff(self, value):
        self.difficulty = value
        for item, btn in self._diff_btns:
            btn._bg = COLORS["primary"] if item == value else COLORS["card_bg"]
            btn._hover = COLORS["primary_hover"] if item == value else COLORS["card_hover"]
            btn.configure(
                bg=btn._bg,
                fg=COLORS["text_on_primary"] if item == value else COLORS["text_main"],
            )

    def _save(self):
        from core import dialogs

        error = custom_questions.validate_draft(
            self.subject,
            self.q_var.get(),
            [var.get() for var in self.opt_vars],
            self.correct,
            self.exp_var.get(),
            self.topic_var.get(),
        )
        if error:
            self._status.configure(text=rtl(error))
            return
        try:
            custom_questions.add_question(
                self.subject,
                self.q_var.get(),
                [var.get() for var in self.opt_vars],
                self.correct,
                self.exp_var.get(),
                self.topic_var.get(),
                self.difficulty,
            )
        except ValueError as exc:
            self._status.configure(text=rtl(str(exc)))
            return
        self.q_var.set("")
        self.exp_var.set("")
        for var in self.opt_vars:
            var.set("")
        self._status.configure(text=rtl("השאלה נשמרה ונכנסה לתרגול."))
        self._refresh_list()
        dialogs.info("עורך שאלות", "השאלה נשמרה במחשב.")

    def _refresh_list(self):
        for child in self._list_host.winfo_children():
            child.destroy()
        rows = custom_questions.load_for_subject(self.subject)
        if not rows:
            fast_label(
                self._list_host,
                "עדיין אין שאלות שהוספתם למקצוע הזה.",
                size=13,
                muted=True,
                bg=COLORS["card_bg"],
            ).pack(anchor="e")
            return
        for row in reversed(rows[-12:]):
            line = tk.Frame(self._list_host, bg=COLORS["card_bg"])
            line.pack(fill="x", pady=3)
            FastButton(
                line,
                "מחיקה",
                command=lambda qid=row.get("id"): self._delete(qid),
                danger=True,
                width=8,
            ).pack(side="left")
            text = str(row.get("question") or "")
            if len(text) > 70:
                text = text[:70] + "…"
            fast_label(line, text, size=13, bg=COLORS["card_bg"], wrap=620).pack(
                side="right", fill="x", expand=True
            )

    def _delete(self, qid):
        from core import dialogs

        if not dialogs.confirm("מחיקה", "למחוק את השאלה הזאת מהמאגר האישי?"):
            return
        custom_questions.delete_question(qid)
        self._refresh_list()
