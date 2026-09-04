# -*- coding: utf-8 -*-
"""הרשמה: פרטים+תקנון → מקצועות → רמה → יעד → אבחון אופציונלי."""
from __future__ import annotations

import os
import tkinter as tk

from core.config import (
    ADHD_CONFIG, ALL_SUBJECTS, COLORS, ELECTIVE_SUBJECTS, HOME_SUBJECTS,
    SUBJECTS, rtl, subject_label,
)
from core.diagnostic import EXAM_LENGTH, build_diagnostic, compute_level
from core.i18n import LANGS, LANG_LABELS, get_lang, set_lang, ui as i18n_ui
from core.learner_prefs import (
    GOAL_KEYS, GOAL_LABELS_HE, LEVEL_KEYS, LEVEL_LABELS_HE,
    apply_preferred_levels, normalize_level, save_onboarding_choices,
)
from core.storage import UserStorage
from ui.fast import TkButton
from ui.widgets import (
    GhostButton, ModernButton, ProgressBar, QuietFrame, body, heading, kicker,
    themed_entry, Page,
)


def _terms_excerpt(limit: int = 900) -> str:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "docs", "TERMS.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read().strip().replace("# ", "").replace("## ", "")
    except OSError:
        text = "השימוש מקומי. הנתונים נשמרים במחשב שלכם."
    return text if len(text) <= limit else text[: limit - 1] + "…"


class _ChoiceVar:
    def __init__(self, owner):
        self._owner = owner

    def set(self, value):
        self._owner._pick(int(value))

    def get(self):
        return self._owner._choice


class OnboardingFrame(Page):
    def __init__(self, master, storage: UserStorage, on_done, adaptive_engine=None, **kwargs):
        kwargs.pop("fg_color", None)
        super().__init__(master, bg=COLORS["bg_dark"], **kwargs)
        self.storage = storage
        self.on_done = on_done
        self.adaptive_engine = adaptive_engine
        self.questions = []
        self.answers = []
        self.q_index = 0
        self._choice = -1
        self.selected = _ChoiceVar(self)
        self._opt_btns = []
        self._picked_subjects = set(HOME_SUBJECTS)
        self._level = "starter"
        self._goal = "practice_only"
        self._terms_ok = tk.BooleanVar(value=False)
        self._stage("welcome")

    def _clear(self):
        self._opt_btns = []
        for w in self.winfo_children():
            w.destroy()

    def _stage(self, stage: str):
        self._clear()
        {
            "welcome": self._build_welcome,
            "subjects": self._build_subjects,
            "level": self._build_level,
            "goal": self._build_goal,
            "diagnostic_gate": self._build_diagnostic_gate,
            "diagnostic": self._build_diagnostic,
        }[stage]()

    def _card_shell(self):
        holder = tk.Frame(self, bg=COLORS["bg_dark"])
        holder.pack(fill="both", expand=True, padx=28, pady=24)
        shell = tk.Frame(holder, bg=COLORS.get("gold") or COLORS["accent"])
        shell.pack(fill="x", padx=8)
        card = QuietFrame(shell)
        card.pack(fill="x", pady=(4, 0))
        return card

    def _style_toggle(self, btn, on: bool):
        try:
            btn.configure(
                fg_color=COLORS["primary"] if on else COLORS["option_bg"],
                text_color=COLORS["text_on_primary"] if on else COLORS["option_text"],
                border_color=COLORS["primary"] if on else (COLORS.get("option_border") or COLORS["card_border"]),
            )
        except tk.TclError:
            pass

    def _opt_btn(self, parent, text, command, height=46):
        return TkButton(
            parent, text=rtl(text), font=(ADHD_CONFIG["font_family"], 15, "bold"),
            fg_color=COLORS["option_bg"], hover_color=COLORS["option_hover"],
            text_color=COLORS["option_text"], border_width=1,
            border_color=COLORS.get("option_border") or COLORS["card_border"],
            anchor="e", height=height, command=command,
        )

    def _build_welcome(self):
        card = self._card_shell()
        kicker(card, "שלב 1 מתוך 4  ·  הרשמה", bg=COLORS["card_bg"]).pack(
            pady=(24, 0), padx=36, anchor="e"
        )
        heading(card, i18n_ui("onboard.lang"), 16).pack(anchor="e", padx=36, pady=(8, 4))
        lang_row = tk.Frame(card, bg=COLORS["card_bg"])
        lang_row.pack(fill="x", padx=36, pady=(0, 8))
        current = get_lang()
        for code in LANGS:
            maker = ModernButton if code == current else GhostButton
            maker(
                lang_row, text=rtl(LANG_LABELS[code]), height=36, width=110,
                command=lambda c=code: self._pick_lang(c),
            ).pack(side="right", padx=4)
        heading(card, i18n_ui("onboard.welcome"), 26).pack(anchor="e", padx=36, pady=(8, 4))
        body(card, i18n_ui("onboard.body"), muted=True, wrap=460).pack(pady=(0, 8), padx=36)
        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.err_label = tk.Label(
            card, text="", bg=COLORS["card_bg"], fg=COLORS["danger"],
            font=(ADHD_CONFIG["font_family"], 14), anchor="e", justify="right",
        )
        for title, var in (
            (i18n_ui("onboard.name"), self.name_var),
            (i18n_ui("onboard.age"), self.age_var),
            (i18n_ui("onboard.id"), self.id_var),
        ):
            tk.Label(
                card, text=rtl(title), bg=COLORS["card_bg"], fg=COLORS["text_main"],
                font=(ADHD_CONFIG["font_family"], 14, "bold"), anchor="e",
            ).pack(fill="x", padx=40)
            themed_entry(card, var, justify="right", font=(ADHD_CONFIG["font_family"], 16)).pack(
                fill="x", padx=40, pady=(4, 10), ipady=10
            )
        terms_box = tk.Frame(card, bg=COLORS["card_bg"])
        terms_box.pack(fill="x", padx=40, pady=(0, 6))
        body(terms_box, "תקנון (תמצית)", size=13).pack(anchor="e")
        t = tk.Text(
            terms_box, height=4, wrap="word", font=(ADHD_CONFIG["font_family"], 11),
            bg=COLORS["card_bg"], fg=COLORS["text_muted"], relief="flat", bd=0,
        )
        t.pack(fill="x", pady=4)
        t.insert("1.0", _terms_excerpt())
        t.configure(state="disabled")
        tk.Checkbutton(
            card, text=rtl("קראתי ואני מסכים/ה לתקנון"), variable=self._terms_ok,
            bg=COLORS["card_bg"], fg=COLORS["text_main"], selectcolor=COLORS["card_bg"],
            activebackground=COLORS["card_bg"], font=(ADHD_CONFIG["font_family"], 14),
            anchor="e", justify="right",
        ).pack(anchor="e", padx=40)
        self.err_label.pack()
        ModernButton(
            card, text=rtl("המשך לבחירת מקצועות"), fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], command=self._submit_details,
        ).pack(fill="x", padx=40, pady=(8, 28))

    def _submit_details(self):
        name = self.name_var.get().strip()
        age = self.age_var.get().strip()
        idn = self.id_var.get().strip()
        if not name or not age:
            self.err_label.configure(text=rtl(i18n_ui("onboard.need_name")))
            return
        if not age.isdigit() or not 5 <= int(age) <= 120:
            self.err_label.configure(text=rtl("הגיל צריך להיות מספר בין 5 ל-120"))
            return
        if idn and not (idn.isdigit() and 5 <= len(idn) <= 9):
            self.err_label.configure(text=rtl("אם ממלאים תז: רק ספרות, 5 עד 9"))
            return
        if not self._terms_ok.get():
            self.err_label.configure(text=rtl("חייבים לאשר את התקנון כדי להמשיך"))
            return
        self.storage.save_student(name, int(age), idn)
        self.storage.set_pref("helper_lang", get_lang())
        self._stage("subjects")

    def _pick_lang(self, code: str):
        set_lang(code)
        self.storage.set_pref("helper_lang", code)
        name = self.name_var.get() if hasattr(self, "name_var") else ""
        age = self.age_var.get() if hasattr(self, "age_var") else ""
        idn = self.id_var.get() if hasattr(self, "id_var") else ""
        terms = bool(self._terms_ok.get())
        self._stage("welcome")
        if hasattr(self, "name_var"):
            self.name_var.set(name)
            self.age_var.set(age)
            self.id_var.set(idn)
            self._terms_ok.set(terms)

    def _build_subjects(self):
        card = self._card_shell()
        kicker(card, "שלב 2 מתוך 4  ·  מקצועות", bg=COLORS["card_bg"]).pack(
            pady=(20, 0), padx=28, anchor="e"
        )
        heading(card, "מה לומדים?", 24).pack(anchor="e", padx=28, pady=(8, 4))
        body(card, "סמנו מקצועות או בחרו הכול.", muted=True, wrap=520).pack(anchor="e", padx=28)
        actions = tk.Frame(card, bg=COLORS["card_bg"])
        actions.pack(fill="x", padx=28, pady=8)
        GhostButton(actions, text=rtl("בחר הכול"), width=120, command=self._select_all_subjects).pack(side="right", padx=4)
        GhostButton(actions, text=rtl("נקה"), width=90, command=self._clear_subjects).pack(side="right", padx=4)
        grid = tk.Frame(card, bg=COLORS["card_bg"])
        grid.pack(fill="x", padx=20, pady=8)
        self._subject_btns = {}
        for i, key in enumerate(ALL_SUBJECTS):
            if key not in SUBJECTS:
                continue
            tag = "בחירה" if key in ELECTIVE_SUBJECTS else "ליבה"
            btn = self._opt_btn(grid, f"{subject_label(key)}  ·  {tag}", lambda k=key: self._toggle_subject(k), 42)
            row, col = divmod(i, 2)
            btn.grid(row=row, column=1 - col, sticky="ew", padx=6, pady=4)
            self._subject_btns[key] = btn
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        self._refresh_subject_btns()
        self.subj_err = tk.Label(card, text="", bg=COLORS["card_bg"], fg=COLORS["danger"],
                                 font=(ADHD_CONFIG["font_family"], 13), anchor="e")
        self.subj_err.pack(fill="x", padx=28)
        ModernButton(card, text=rtl("המשך לרמת לימוד"), fg_color=COLORS["primary"],
                     hover_color=COLORS["primary_hover"], command=self._submit_subjects).pack(
            fill="x", padx=28, pady=(8, 24)
        )

    def _toggle_subject(self, key: str):
        if key in self._picked_subjects:
            self._picked_subjects.discard(key)
        else:
            self._picked_subjects.add(key)
        self._refresh_subject_btns()

    def _select_all_subjects(self):
        self._picked_subjects = set(ALL_SUBJECTS)
        self._refresh_subject_btns()

    def _clear_subjects(self):
        self._picked_subjects.clear()
        self._refresh_subject_btns()

    def _refresh_subject_btns(self):
        for key, btn in getattr(self, "_subject_btns", {}).items():
            self._style_toggle(btn, key in self._picked_subjects)

    def _submit_subjects(self):
        if not self._picked_subjects:
            self.subj_err.configure(text=rtl("בחרו לפחות מקצוע אחד"))
            return
        self._stage("level")

    def _build_level(self):
        card = self._card_shell()
        kicker(card, "שלב 3 מתוך 4  ·  רמת לימוד", bg=COLORS["card_bg"]).pack(
            pady=(20, 0), padx=28, anchor="e"
        )
        heading(card, "באיזו רמה מתחילים?", 24).pack(anchor="e", padx=28, pady=(8, 4))
        body(card, "האנליסט יתאים שאלות ושיעורים, ויעלה או יוריד לפי ביצועים.", muted=True, wrap=520).pack(
            anchor="e", padx=28, pady=(0, 10)
        )
        hints = {
            "starter": "בסיס רגוע",
            "easy": "קצת יותר אתגר",
            "intermediate": "תערובת מאוזנת",
            "advanced": "חומר רציני / מימ״ד",
            "elite": "בגרות מלאה ומבחנים ארוכים",
        }
        self._level_btns = {}
        for key in LEVEL_KEYS:
            btn = self._opt_btn(
                card, f"{LEVEL_LABELS_HE[key]}  —  {hints[key]}",
                lambda k=key: self._pick_level(k),
            )
            btn.pack(fill="x", padx=28, pady=4)
            self._level_btns[key] = btn
        self._refresh_level_btns()
        ModernButton(card, text=rtl("המשך ליעד למידה"), fg_color=COLORS["primary"],
                     hover_color=COLORS["primary_hover"],
                     command=lambda: self._stage("goal")).pack(fill="x", padx=28, pady=(12, 24))

    def _pick_level(self, key: str):
        self._level = normalize_level(key)
        self._refresh_level_btns()

    def _refresh_level_btns(self):
        for key, btn in getattr(self, "_level_btns", {}).items():
            self._style_toggle(btn, key == self._level)

    def _build_goal(self):
        card = self._card_shell()
        kicker(card, "יעד למידה", bg=COLORS["card_bg"]).pack(pady=(20, 0), padx=28, anchor="e")
        heading(card, "מה חשוב לכם עכשיו?", 22).pack(anchor="e", padx=28, pady=(8, 4))
        body(card, "הדשבורד יתאים את ההמלצה היומית.", muted=True, wrap=520).pack(anchor="e", padx=28, pady=(0, 10))
        self._goal_btns = {}
        for key in GOAL_KEYS:
            btn = self._opt_btn(card, GOAL_LABELS_HE[key], lambda k=key: self._pick_goal(k))
            btn.pack(fill="x", padx=28, pady=4)
            self._goal_btns[key] = btn
        self._refresh_goal_btns()
        ModernButton(card, text=rtl("המשך לאבחון (אופציונלי)"), fg_color=COLORS["primary"],
                     hover_color=COLORS["primary_hover"],
                     command=self._persist_choices_then_gate).pack(fill="x", padx=28, pady=(12, 24))

    def _pick_goal(self, key: str):
        if key in GOAL_KEYS:
            self._goal = key
        self._refresh_goal_btns()

    def _refresh_goal_btns(self):
        for key, btn in getattr(self, "_goal_btns", {}).items():
            self._style_toggle(btn, key == self._goal)

    def _persist_choices_then_gate(self):
        subjects = [k for k in ALL_SUBJECTS if k in self._picked_subjects] or list(HOME_SUBJECTS)
        save_onboarding_choices(
            self.storage, subjects=subjects, level=self._level,
            goal=self._goal, terms_accepted=True,
        )
        if self.adaptive_engine is not None:
            apply_preferred_levels(self.storage, self.adaptive_engine)
        self._stage("diagnostic_gate")

    def _build_diagnostic_gate(self):
        card = self._card_shell()
        kicker(card, "שלב 4 מתוך 4  ·  אבחון", bg=COLORS["card_bg"]).pack(
            pady=(24, 0), padx=36, anchor="e"
        )
        heading(card, "מבחן אבחון קצר?", 24).pack(anchor="e", padx=36, pady=(8, 6))
        body(
            card,
            f"{EXAM_LENGTH} שאלות קצרות עוזרות לכוון. אפשר לדלג ולהתחיל מהרמה שבחרתם.",
            muted=True, wrap=520,
        ).pack(anchor="e", padx=36, pady=(0, 16))
        ModernButton(
            card, text=rtl("להתחיל אבחון"), fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=lambda: self._stage("diagnostic"),
        ).pack(fill="x", padx=36, pady=(0, 8))
        GhostButton(card, text=rtl("דלג והמשך לדשבורד"), command=self._skip_diagnostic).pack(
            fill="x", padx=36, pady=(0, 28)
        )

    def _skip_diagnostic(self):
        self.storage.set_pref("diagnostic_skipped", True)
        self.on_done()

    def advance_setup_for_tests(self):
        if not self.storage.has_profile():
            return False
        if not self._picked_subjects:
            self._picked_subjects = set(HOME_SUBJECTS)
        self._persist_choices_then_gate()
        return True

    def _build_diagnostic(self):
        self.questions = build_diagnostic()
        self.answers = []
        self.q_index = 0
        ink = COLORS["bg_dark"]
        ink_fg = COLORS.get("banner_text") or COLORS["text_on_primary"]
        ink_muted = COLORS.get("sidebar_muted") or "#9DC4BC"
        top = tk.Frame(self, bg=ink)
        top.pack(fill="x", padx=32, pady=(24, 8))
        heading(top, "מבחן אבחון", 24, fg=ink_fg).pack(anchor="e")
        body(top, f"{EXAM_LENGTH} שאלות קצרות.", fg=ink_muted).pack(anchor="e", pady=(0, 6))
        self.counter_lbl = body(top, "", fg=ink_muted)
        self.counter_lbl.pack(anchor="e")
        self.progress = ProgressBar(
            self, pct=0, height=8, color=COLORS["primary"],
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
                card, text=rtl(f"{i + 1}.  {opt}"),
                font=(ADHD_CONFIG["font_family"], 16, "bold"),
                fg_color=COLORS["option_bg"], hover_color=COLORS["option_hover"],
                text_color=COLORS["option_text"], border_width=1,
                border_color=COLORS.get("option_border") or COLORS["card_border"],
                anchor="e", height=ADHD_CONFIG["option_height"],
                command=lambda idx=i: self._pick(idx),
            )
            btn.pack(fill="x", padx=24, pady=4)
            self._opt_btns.append(btn)
        self.pick_hint = body(card, "בחרו תשובה ואז המשיכו.", muted=True, size=13)
        self.pick_hint.pack(anchor="e", padx=24, pady=(8, 0))
        last = n == EXAM_LENGTH
        ModernButton(
            card, text=rtl("סיום אבחון") if last else rtl("הבא"),
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
                    fg_color=COLORS["primary"], text_color=COLORS["text_on_primary"],
                    border_color=COLORS["primary"],
                )
            else:
                btn.configure(
                    fg_color=COLORS["option_bg"], text_color=COLORS["option_text"],
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
        if self._choice < 0:
            self.pick_hint.configure(text=rtl("בחרו תשובה כדי להמשיך."), fg=COLORS["danger"])
            return
        q = self.questions[self.q_index]
        self.answers.append({
            "subject": q["subject"], "topic": q["topic"],
            "correct": self._choice == q["answer"], "difficulty": q["difficulty"],
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
        mapped = normalize_level(result["level"])
        self.storage.set_pref("preferred_level", mapped)
        if self.adaptive_engine is not None:
            apply_preferred_levels(self.storage, self.adaptive_engine)
        self._show_summary(result, correct)

    def _show_summary(self, result, correct):
        self._clear()
        card = self._card_shell()
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

