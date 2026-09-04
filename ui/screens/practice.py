import time
import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl, rtl_paragraph
from core.theme import subject_accent
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, OptionTile, ProgressBar, body, font_size, heading, kicker, make_card, number_pill, themed_entry, Page


class PracticeScreen(Page):
    def __init__(self, master, session, on_back, on_finished, on_persist,
                 show_feedback=True, exam_mode=False, speaker=None, level_he=None,
                 on_report=None, subject_key=None, on_review_grade=None):
        super().__init__(master)
        self.session = session
        self.on_back = on_back
        self.on_finished = on_finished
        self.on_persist = on_persist
        self.on_report = on_report
        self.on_review_grade = on_review_grade
        self.show_feedback = show_feedback
        self.exam_mode = exam_mode
        self.speaker = speaker
        self.level_he = level_he
        self.subject_key = subject_key
        self._timer_job = None
        self._advance_job = None
        self._locked = False
        self._buttons = []
        self._typed = None
        self._answer_box = None
        self._compose_err = None
        self._render()

    def destroy(self):
        self._cancel_timer()
        self._cancel_advance()
        super().destroy()

    def _cancel_timer(self):
        if self._timer_job is not None:
            try:
                self.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None

    def _cancel_advance(self):
        if self._advance_job is not None:
            try:
                self.after_cancel(self._advance_job)
            except Exception:
                pass
            self._advance_job = None

    # ---------- מקלדת ----------
    def on_key(self, event):
        key = (event.keysym or "").lower()
        letters = {"a": 0, "b": 1, "c": 2, "d": 3}
        compose = self._is_compose()
        if compose:
            if key in {"return"} and not self._locked:
                self._submit_text()
            elif key in {"return", "space"} and self._locked:
                self._render()
            elif key == "s" and self.session.mode not in {"final", "general"}:
                self._skip()
            return
        if key in {"1", "2", "3", "4"} and not self._locked:
            index = int(key) - 1
            if index < len(self._buttons):
                self._choose(index)
        elif key in letters and not self._locked:
            index = letters[key]
            if index < len(self._buttons):
                self._choose(index)
        elif key in {"return", "space"}:
            if self._locked:
                self._render()
        elif key == "s" and self.session.mode not in {"final", "general"}:
            self._skip()

    # ---------- ציור ----------
    def _render(self):
        self._cancel_timer()
        self._cancel_advance()
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        for widget in self.winfo_children():
            widget.destroy()
        self._buttons = []
        self._typed = None
        self._answer_box = None
        self._compose_err = None

        if self.session.out_of_time():
            self.on_finished()
            return
        q = self.session.get_current_question()
        if not q:
            self.on_finished()
            return

        self.session.mark_question_start()
        self._locked = False
        self.start_time = time.time()

        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x")
        general = self.session.mode == "general"
        meimad = self.session.mode == "meimad"
        if not self.exam_mode:
            GhostButton(bar, text=rtl("‹  חזרה"), width=100, command=self.on_back).pack(side="right")
        elif meimad:
            chapter = self.session.current_chapter() or {}
            idx = self.session.chapter_index()
            total_ch = max(1, len(self.session.chapters))
            fast_label(
                bar,
                f"מימד · פרק {idx}/{total_ch}",
                size=13, bold=True, bg=COLORS["bg"],
            ).pack(side="right", padx=6)
        elif general:
            fast_label(bar, "מבחן כללי", size=13, bold=True, bg=COLORS["bg"]).pack(side="right", padx=6)
        elif self.session.mode == "final":
            fast_label(bar, "מבחן אמיתי", size=13, bold=True, bg=COLORS["bg"]).pack(side="right", padx=6)
        else:
            fast_label(bar, "מבחן דמה", size=13, bold=True, bg=COLORS["bg"]).pack(side="right", padx=6)

        if self.session.can_skip() and self.session.mode not in {"final", "general"}:
            GhostButton(bar, text=rtl("דלג (S)"), width=90, command=self._skip).pack(side="left", padx=4)
        if self.speaker is not None and self.speaker.enabled:
            from core.teach import clarify_stem as _say_stem

            GhostButton(bar, text=rtl("🔊"), width=56,
                        command=lambda item=q: self.speaker.say(_say_stem(item))).pack(side="left", padx=2)
        from core.i18n import get_lang, ui as i18n_ui

        if get_lang() != "he":
            GhostButton(
                bar, text=rtl(i18n_ui("btn.explain")), width=140,
                command=self._explain_helper,
            ).pack(side="left", padx=4)

        total = self.session.get_total()
        current = self.session.current_index + 1
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", pady=(6, 0))
        number_pill(top, f"שאלה {current} / {total}").pack(side="right")
        if not self.exam_mode:
            fast_label(
                top, f"{self.session.score} נכונות",
                size=12, muted=True, bg=COLORS["bg"],
            ).pack(side="left", padx=(0, 4))

        self._progress = ProgressBar(self, pct=(current / total) if total else 0, height=7)
        self._progress.pack(fill="x", pady=(6, 6))

        if not self.exam_mode:
            diff = {"Easy": "קל", "Medium": "בינוני", "Hard": "קשה"}.get(
                str(q.get("difficulty") or ""), str(q.get("difficulty") or "")
            )
            from core.teach import topic_label

            meta = topic_label(q.get("topic") or "תרגול", q.get("subject") or self.subject_key or "")
            if self.level_he:
                meta = f"{meta}  ·  {self.level_he}"
            if diff:
                meta = f"{meta}  ·  {diff}"
            fast_label(self, meta, size=11, muted=True, bg=COLORS["bg"]).pack(anchor="e", pady=(0, 4))

        self.timer_lbl = None
        if self.session.time_limit_sec or self.session.total_limit_sec:
            self.timer_lbl = fast_label(self, "", size=13, muted=True, bg=COLORS["bg"])
            self.timer_lbl.pack(anchor="e", pady=(0, 4))
            self._tick()

        passage = (q.get("passage") or "").strip()
        if passage:
            box = tk.Frame(self, bg=COLORS["card_bg"], highlightthickness=1,
                           highlightbackground=COLORS["card_border"])
            box.pack(fill="x", pady=(0, 10))
            fast_label(box, "קטע קריאה. קראו קודם, אחר כך ענו", size=12, muted=True,
                       bg=COLORS["card_bg"]).pack(anchor="e", padx=14, pady=(10, 0))
            text = tk.Text(
                box, wrap="word", height=max(6, min(14, 3 + passage.count("\n") + max(1, len(passage) // 78))),
                font=(ADHD_CONFIG["font_family"], font_size(14)),
                bg=COLORS["card_bg"], fg=COLORS["text_main"],
                relief="flat", highlightthickness=0, padx=10, pady=8,
                insertbackground=COLORS["text_main"],
                selectbackground=COLORS["primary"],
                selectforeground=COLORS["text_on_primary"],
            )
            text.pack(fill="x", padx=10, pady=(2, 12))
            text.insert("1.0", rtl_paragraph(passage))
            text.tag_configure("rtl", justify="right")
            text.tag_add("rtl", "1.0", "end")
            text.configure(state="disabled")

        compose = self._is_compose(q)
        qbox, qinner = make_card(self, pady=16)
        qbox.pack(fill="x", pady=(0, 14))
        from core.teach import clarify_stem, task_prompt

        if not self.exam_mode:
            try:
                from core.illustrations.schema import get_visual
                from ui.visual_panel import VisualPanel

                if get_visual(q):
                    VisualPanel(qinner, q, mode="question", bg=COLORS["card_bg"], max_width=700).pack(
                        fill="x", pady=(0, 10),
                    )
            except Exception:
                pass
        stem = clarify_stem(q)
        if compose:
            fast_label(
                qinner, "מצב יצור: כותבים את התשובה, לא בוחרים מתוך רשימה.",
                size=13, muted=True, bg=COLORS["card_bg"],
            ).pack(anchor="e", pady=(0, 8))
        if not self.exam_mode:
            from core.learn_format import exhibit_label, exhibit_text, kicker_for

            kick = kicker_for(q)
            if kick:
                kicker(qinner, kick, bg=COLORS["card_bg"]).pack(anchor="e", pady=(0, 4))
            extra = exhibit_text(q)
            if extra and extra != passage:
                label = exhibit_label(q)
                if label:
                    fast_label(
                        qinner, label, size=12, muted=True, bg=COLORS["card_bg"],
                    ).pack(anchor="e")
                body(qinner, extra, size=15, wrap=720).pack(anchor="e", pady=(0, 8))
            task = task_prompt(q)
            if task:
                tk.Label(
                    qinner,
                    text=rtl(f"מה השאלה מבקשת: {task}"),
                    bg=COLORS["card_bg"],
                    fg=COLORS["primary"],
                    font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
                    anchor="e",
                    justify="right",
                    wraplength=720,
                ).pack(fill="x", pady=(0, 8))
        heading(qinner, stem, 21).pack(anchor="e")
        if self.speaker is not None and self.speaker.enabled:
            spoken = stem
            if not self.exam_mode:
                spoken = f"{task_prompt(q)} {stem}".strip()
            self.speaker.say(spoken)

        self.opts = tk.Frame(self, bg=COLORS["bg"])
        self.opts.pack(fill="x")
        latin = self.session.mode == "general" or bool(q.get("letter_options")) or (
            str(q.get("subject") or self.subject_key or "") == "english"
        )
        if compose:
            self._pack_compose_box(q)
        else:
            letters = "ABCD" if latin else "אבגד"
            accent = subject_accent(q.get("subject") or self.subject_key or "")
            for idx, opt in enumerate(q.get("options") or []):
                mark = letters[idx] if idx < len(letters) else str(idx + 1)
                tile = OptionTile(
                    self.opts,
                    letter=mark,
                    text=str(opt),
                    command=lambda i=idx: self._choose(i),
                    accent=accent,
                )
                tile.pack(fill="x", pady=5)
                self._buttons.append(tile)

        hints = tk.Frame(self, bg=COLORS["bg"])
        hints.pack(fill="x", pady=(4, 0))
        if not self.exam_mode:
            if compose:
                hint_line = "Enter לבדיקה"
            elif latin:
                hint_line = "A–D או 1–4"
            else:
                hint_line = "1–4 לבחירה"
            fast_label(
                hints, hint_line,
                size=11, muted=True, bg=COLORS["bg"],
            ).pack(side="right")
            from core.teach import live_hint

            GhostButton(
                hints, text=rtl("רמז"), width=72, height=32,
                command=lambda item=q: self._show_hint(live_hint(item, self.subject_key or "")),
            ).pack(side="left")
            if self.on_report:
                GhostButton(
                    hints, text=rtl("דיווח"), width=72, height=32,
                    command=lambda item=q: self._report(item),
                ).pack(side="left", padx=4)

        self.feedback = tk.Frame(self, bg=COLORS["bg"])
        self.feedback.pack(fill="x", pady=(10, 0))

    def _is_compose(self, question=None) -> bool:
        q = question if question is not None else self.session.get_current_question()
        if self.session.mode == "compose":
            return True
        return bool(q and (q.get("compose") or q.get("kind") == "compose"))

    def _pack_compose_box(self, question):
        from core.compose import infer_write_guide

        box, inner = make_card(self.opts, pady=14)
        box.pack(fill="x", pady=(0, 8))
        guide = infer_write_guide(question)
        fast_label(
            inner, "מה לרשום",
            size=12, muted=True, bg=COLORS["card_bg"],
        ).pack(anchor="e")
        tk.Label(
            inner, text=rtl(guide),
            bg=COLORS["card_bg"], fg=COLORS["primary"],
            font=(ADHD_CONFIG["font_family"], font_size(16), "bold"),
            anchor="e", justify="right", wraplength=720,
        ).pack(fill="x", pady=(2, 10))
        expected = str(question.get("correct_answer") or "")
        long_form = len(expected) > 24 or any(
            token in str(question.get("question") or "") for token in ("חברו", "משפט", "השלימו")
        )
        if long_form:
            self._answer_box = tk.Text(
                inner, height=3, wrap="word",
                font=(ADHD_CONFIG["font_family"], font_size(16)),
                bg=COLORS.get("input_bg") or COLORS["card_bg"], fg=COLORS["text_main"],
                relief="flat", highlightthickness=1,
                highlightbackground=COLORS["card_border"],
                highlightcolor=COLORS["primary"],
                insertbackground=COLORS["text_main"], padx=10, pady=8,
            )
            self._answer_box.pack(fill="x")
            self._answer_box.tag_configure("rtl", justify="right")
            self._answer_box.bind("<Control-Return>", lambda _e: self._submit_text())
            self.after(80, self._answer_box.focus_set)
        else:
            self._typed = tk.StringVar()
            entry = themed_entry(
                inner, self._typed, justify="right",
                font=(ADHD_CONFIG["font_family"], font_size(18)),
            )
            entry.pack(fill="x", ipady=10)
            entry.bind("<Return>", lambda _e: self._submit_text())
            self._answer_box = entry
            self.after(80, entry.focus_set)
        self._compose_err = fast_label(
            inner, "", size=13, muted=True, bg=COLORS["card_bg"],
        )
        self._compose_err.pack(anchor="e", pady=(8, 0))
        ModernButton(
            inner, text=rtl("בדיקה"), height=46,
            command=self._submit_text,
        ).pack(fill="x", pady=(12, 0))

    def _typed_text(self) -> str:
        box = self._answer_box
        if box is None:
            return ""
        try:
            if isinstance(box, tk.Text):
                return box.get("1.0", "end").strip()
            if self._typed is not None:
                return str(self._typed.get() or "").strip()
            return str(box.get() or "").strip()
        except tk.TclError:
            return ""

    def _submit_text(self, _event=None):
        if self._locked:
            return
        typed = self._typed_text()
        if not typed:
            label = getattr(self, "_compose_err", None)
            if label is not None:
                try:
                    label.configure(text=rtl("קודם כותבים תשובה בתיבה, אחר כך לוחצים בדיקה."))
                except tk.TclError:
                    pass
            return
        self._choose(-1, typed=typed)

    def _show_hint(self, text):
        from core.dialogs import info

        info("רמז", text)

    def _report(self, question):
        if self.on_report:
            self.on_report(question)

    def _explain_helper(self):
        from core import dialogs
        from core.i18n import block, ui as i18n_ui

        dialogs.info(i18n_ui("explain.title"), block("explain.body"))

    def _skip(self):
        if self._locked or self.session.mode in {"final", "general"}:
            return
        if self.session.skip_current():
            self._render()

    def _tick(self):
        if not self.timer_lbl:
            return
        try:
            parts = []
            left_q = self.session.remaining_for_question()
            if left_q is not None:
                parts.append(f"לשאלה: {left_q} שניות")
            left_ch = self.session.chapter_remaining() if self.session.chapters else None
            if left_ch is not None:
                parts.append(f"לפרק: {left_ch // 60}:{left_ch % 60:02d}")
            left_total = self.session.remaining_total()
            if left_total is not None:
                parts.append(f"סה\"כ: {left_total // 60}:{left_total % 60:02d} דקות")
            self.timer_lbl.configure(text=rtl("   ·   ".join(parts)))
            urgent = (
                (left_q is not None and left_q <= 15)
                or (left_ch is not None and left_ch <= 30)
                or (left_total is not None and left_total <= 60)
            )
            self.timer_lbl.configure(fg=COLORS["danger"] if urgent else COLORS["text_muted"])
            if left_total is not None and left_total <= 0:
                self.on_finished()
                return
            if left_ch is not None and left_ch <= 0:
                if self.session.close_chapter():
                    self._render()
                else:
                    self.on_finished()
                return
            if left_q is not None and left_q <= 0 and not self._locked:
                self._choose(-1)
                return
        except tk.TclError:
            return
        self._timer_job = self.after(400, self._tick)

    def _choose(self, selected_index, typed: str | None = None):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if self._locked:
            return
        q = self.session.get_current_question()
        if not q:
            self.on_finished()
            return
        self._locked = True
        self._cancel_timer()
        if self._is_compose(q) and typed is None:
            typed = self._typed_text()
        try:
            if self._answer_box is not None and self._answer_box.winfo_exists():
                self._answer_box.configure(state="disabled")
        except tk.TclError:
            pass

        elapsed = time.time() - getattr(self, "start_time", time.time())
        is_correct = self.session.submit_answer(selected_index, elapsed, typed=typed)
        if self.on_persist:
            self.on_persist(q, is_correct, elapsed, selected_index)

        if not self.show_feedback:
            # במבחן אסור לחשוף ירוק/אדום לפני הדוח בסוף.
            for idx, btn in enumerate(self._buttons):
                try:
                    if not btn.winfo_exists():
                        continue
                    if idx == selected_index:
                        btn.configure(
                            fg_color=COLORS["primary"],
                            text_color=COLORS["text_on_primary"],
                            border_color=COLORS["primary"],
                        )
                    btn.configure(state="disabled")
                except tk.TclError:
                    continue
            self._advance_job = self.after(220, self._render)
            return

        for idx, btn in enumerate(self._buttons):
            try:
                if not btn.winfo_exists():
                    continue
                if idx == q.get("answer"):
                    btn.configure(
                        fg_color=COLORS["success"],
                        text_color=COLORS.get("success_text") or "#FFFFFF",
                        border_color=COLORS["success"],
                    )
                elif idx == selected_index and not is_correct:
                    btn.configure(
                        fg_color=COLORS["danger"],
                        text_color=COLORS.get("danger_text") or "#FFFFFF",
                        border_color=COLORS["danger"],
                    )
                btn.configure(state="disabled")
            except tk.TclError:
                continue

        msg = "נכון. כל הכבוד." if is_correct else "לא נורא. קוראים את ההסבר וממשיכים."
        color = COLORS["success"] if is_correct else COLORS["danger"]
        for child in self.feedback.winfo_children():
            child.destroy()
        card, inner = make_card(self.feedback, accent=color, thick=2, pady=12, gold_top=True)
        card.pack(fill="x")
        tk.Label(
            inner, text=rtl(msg), bg=COLORS["card_bg"], fg=color,
            font=(ADHD_CONFIG["font_family"], font_size(17), "bold"), anchor="e",
        ).pack(anchor="e")
        if self._is_compose(q) and typed:
            fast_label(
                inner, f"כתבת: {typed}", size=13, muted=True, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(4, 0))
        from core.teach import display_explanation, feedback_note

        opts = q.get("options") or []
        idx = q.get("answer")
        correct = q.get("correct_answer") or ""
        if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
            correct = opts[idx]
        if self._is_compose(q) and correct and not is_correct:
            fast_label(
                inner, f"צריך היה לכתוב: {correct}", size=15, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(6, 0))
        explanation = display_explanation(q, self.subject_key or "")
        fast_label(
            inner, f"הסבר: {explanation}", size=14, bg=COLORS["card_bg"], wrap=720,
        ).pack(anchor="e", pady=(6, 4))
        if not self.exam_mode:
            try:
                from core.illustrations.schema import get_visual
                from ui.visual_panel import VisualPanel

                if get_visual(q):
                    VisualPanel(inner, q, mode="explain", bg=COLORS["card_bg"], max_width=680).pack(
                        fill="x", pady=(4, 8),
                    )
            except Exception:
                pass
        note = feedback_note(q, correct=bool(is_correct), subject=self.subject_key or "")
        if note and note[:40] not in explanation:
            label = "כלל קצר" if is_correct else "שימו לב"
            fast_label(
                inner, f"{label}: {note}", size=13, muted=True, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(0, 8))
        if self.speaker is not None and self.speaker.enabled:
            self.speaker.say(explanation)
        ModernButton(
            inner, text=rtl("לשאלה הבאה  (Enter)"), width=220, command=self._render,
        ).pack(anchor="e")
        self.after(40, self._scroll_feedback)

    def _scroll_feedback(self):
        widget = self.master
        while widget is not None:
            if hasattr(widget, "to_bottom"):
                try:
                    widget.to_bottom()
                except Exception:
                    pass
                return
            widget = getattr(widget, "master", None)
