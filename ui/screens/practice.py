import time
import tkinter as tk
import os
import re

from core.config import ADHD_CONFIG, COLORS, rtl, rtl_paragraph
from core.theme import subject_accent
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, OptionTile, ProgressBar, body, content_wrap, font_size, heading, kicker, make_card, number_pill, themed_entry, Page


class PracticeScreen(Page):
    def __init__(self, master, session, on_back, on_finished, on_persist,
                 show_feedback=True, exam_mode=False, speaker=None, level_he=None,
                 on_report=None, subject_key=None, on_review_grade=None, storage=None,
                 on_similar_topic=None, ai_engine=None, coach_tip: str = ""):
        super().__init__(master)
        self.session = session
        self.on_back = on_back
        self.on_finished = on_finished
        self.on_persist = on_persist
        self.on_report = on_report
        self.on_review_grade = on_review_grade
        self.on_similar_topic = on_similar_topic
        self.ai_engine = ai_engine
        self.coach_tip = str(coach_tip or "").strip()
        self.show_feedback = show_feedback
        self.exam_mode = exam_mode
        self.speaker = speaker
        self.level_he = level_he
        self.subject_key = subject_key
        self.storage = storage
        self._timer_job = None
        self._advance_job = None
        self._locked = False
        self._buttons = []
        self._typed = None
        self._answer_box = None
        self._compose_err = None
        self._plain_box = None
        self._tutor_history = []
        self._hint_level = 0
        self._coach_shown = False
        self._render()

    def destroy(self):
        self._cancel_timer()
        self._cancel_advance()
        super().destroy()


    def _ai_status_line(self) -> str:
        """שורה קצרה בלי בדיקת רשת (לא חוסמת UI)."""
        if self.storage is None:
            return ""
        try:
            from core import ollama_client

            if ollama_client.enabled(self.storage):
                return "עזרה מקומית זמינה"
            return ""
        except Exception:
            return ""

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
        self._hint_level = 0
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

        # סידור מלמעלה למטה - בלי רווח ריק שדוחף תשובות לקצה המסך
        self.pack_propagate(True)

        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x")
        general = self.session.mode == "general"
        meimad = self.session.mode == "meimad"
        if not self.exam_mode:
            GhostButton(bar, text=rtl("‹  חזרה"), width=100, command=self.on_back).pack(side="right")
        elif meimad:
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
        top.pack(fill="x", pady=(2, 0))
        number_pill(top, f"שאלה {current} / {total}").pack(side="right")
        if not self.exam_mode:
            fast_label(
                top, f"{self.session.score} נכונות",
                size=12, muted=True, bg=COLORS["bg"],
            ).pack(side="left", padx=(0, 4))

        self._progress = ProgressBar(self, pct=(current / total) if total else 0, height=5)
        self._progress.pack(fill="x", pady=(3, 3))

        if (not self.exam_mode) and self.coach_tip and int(getattr(self.session, "current_index", 0) or 0) == 0:
            fast_label(
                self, self.coach_tip, size=12, muted=True, bg=COLORS["bg"], wrap=720,
            ).pack(anchor="e", pady=(0, 4))

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
            fast_label(self, meta, size=11, muted=True, bg=COLORS["bg"]).pack(anchor="e", pady=(0, 2))

        self.timer_lbl = None
        if self.session.time_limit_sec or self.session.total_limit_sec:
            self.timer_lbl = fast_label(self, "", size=12, muted=True, bg=COLORS["bg"])
            self.timer_lbl.pack(anchor="e", pady=(0, 2))
            self._tick()

        passage = (q.get("passage") or "").strip()
        if passage:
            box = tk.Frame(self, bg=COLORS["card_bg"], highlightthickness=1,
                           highlightbackground=COLORS["card_border"])
            box.pack(fill="x", pady=(0, 4))
            fast_label(box, "קטע קריאה", size=11, muted=True,
                       bg=COLORS["card_bg"]).pack(anchor="e", padx=10, pady=(4, 0))
            text = tk.Text(
                box, wrap="word", height=max(2, min(4, 1 + passage.count("\n") + max(1, len(passage) // 140))),
                font=(ADHD_CONFIG["font_family"], font_size(13)),
                bg=COLORS["card_bg"], fg=COLORS["text_main"],
                relief="flat", highlightthickness=0, padx=8, pady=4,
                insertbackground=COLORS["text_main"],
                selectbackground=COLORS["primary"],
                selectforeground=COLORS["text_on_primary"],
            )
            text.pack(fill="x", padx=8, pady=(2, 6))
            text.insert("1.0", rtl_paragraph(passage))
            text.tag_configure("rtl", justify="right")
            text.tag_add("rtl", "1.0", "end")
            text.configure(state="disabled")

        compose = self._is_compose(q)
        qbox, qinner = make_card(self, pady=8, padx=12)
        qbox.pack(fill="x", pady=(0, 6))
        from core.teach import clarify_stem

        stem = clarify_stem(q)
        if compose:
            fast_label(
                qinner, "מצב יצור: כותבים את התשובה.",
                size=12, muted=True, bg=COLORS["card_bg"],
            ).pack(anchor="e", pady=(0, 4))
        if not self.exam_mode:
            from core.learn_format import exhibit_label, exhibit_text, kicker_for
            from core.teach import needs_task_prompt, task_prompt

            kick = kicker_for(q)
            if kick:
                kicker(qinner, kick, bg=COLORS["card_bg"]).pack(anchor="e", pady=(0, 2))
            extra = exhibit_text(q)
            if extra and extra != passage and len(extra) < 160:
                label = exhibit_label(q)
                if label:
                    fast_label(qinner, label, size=11, muted=True, bg=COLORS["card_bg"]).pack(anchor="e")
                body(qinner, extra, size=13, wrap=content_wrap(self)).pack(anchor="e", pady=(0, 2))
            if needs_task_prompt(q):
                task = task_prompt(q)
                if task:
                    tk.Label(
                        qinner,
                        text=rtl(task),
                        bg=COLORS["card_bg"],
                        fg=COLORS["primary"],
                        font=(ADHD_CONFIG["font_family"], font_size(12)),
                        anchor="e",
                        justify="right",
                        wraplength=content_wrap(self),
                    ).pack(fill="x", pady=(0, 2))
        heading(qinner, stem, 17).pack(anchor="e")
        image_url = str(q.get("image") or "").strip()
        if image_url.startswith("http"):
            self._pack_question_image(qinner, image_url)
        if self.speaker is not None and self.speaker.enabled:
            self.speaker.say(stem)

        # תשובות ישר מתחת לשאלה - עמודה אחת כמו בבחינה, בלי רווח ריק באמצע
        self.opts = tk.Frame(self, bg=COLORS["bg"])
        self.opts.pack(fill="x", pady=(0, 2))
        latin = self.session.mode == "general" or bool(q.get("letter_options")) or (
            str(q.get("subject") or self.subject_key or "") == "english"
        )
        if compose:
            self._pack_compose_box(q)
        else:
            letters = "ABCD" if latin else "אבגד"
            accent = subject_accent(q.get("subject") or self.subject_key or "")
            options = list(q.get("options") or [])
            wrap = max(280, content_wrap(self) - 48)
            for idx, opt in enumerate(options[:4]):
                mark = letters[idx] if idx < len(letters) else str(idx + 1)
                tile = OptionTile(
                    self.opts,
                    letter=mark,
                    text=str(opt),
                    command=lambda i=idx: self._choose(i),
                    accent=accent,
                    compact=True,
                    wrap=wrap,
                )
                tile.pack(fill="x", pady=2)
                self._buttons.append(tile)

        hints = tk.Frame(self, bg=COLORS["bg"])
        hints.pack(fill="x", pady=(2, 0))
        if not self.exam_mode:
            hint_line = "Enter לבדיקה" if compose else ("A-D / 1-4" if latin else "1-4 לבחירה")
            right = tk.Frame(hints, bg=COLORS["bg"])
            right.pack(side="right")
            ai_line = self._ai_status_line()
            if ai_line:
                fast_label(right, ai_line, size=10, muted=True, bg=COLORS["bg"]).pack(side="right", padx=(0, 8))
            fast_label(right, hint_line, size=11, muted=True, bg=COLORS["bg"]).pack(side="right")

            GhostButton(
                hints, text=rtl("רמז"), width=72, height=32,
                command=lambda item=q: self._show_ladder_hint(item),
            ).pack(side="left")
            GhostButton(
                hints, text=rtl("בשפה פשוטה"), width=118, height=32,
                command=lambda item=q: self._paraphrase_question(item),
            ).pack(side="left", padx=(4, 0))
            GhostButton(
                hints, text=rtl("מורה שלב־שלב"), width=130, height=32,
                command=lambda item=q: self._open_tutor(item, reveal=False),
            ).pack(side="left", padx=(4, 0))
            if self.on_report:
                GhostButton(
                    hints, text=rtl("דיווח"), width=72, height=32,
                    command=lambda item=q: self.on_report(item),
                ).pack(side="left", padx=(8, 0))

        self._plain_box = tk.Frame(self, bg=COLORS["bg"])
        self._plain_box.pack(fill="x", pady=(2, 0))

        self.feedback = tk.Frame(self, bg=COLORS["bg"])
        self.feedback.pack(fill="x", pady=(4, 0))

        self.after(40, self._refit_scroll)

    def _on_self_configure(self, _event=None):
        return

    def _fit_to_parent(self) -> None:
        return

    def _refit_scroll(self) -> None:
        try:
            root = self.winfo_toplevel()
            scroll = getattr(root, "scroll", None)
            if scroll is not None and hasattr(scroll, "pin_viewport"):
                scroll.pin_viewport(True)
                scroll.to_top()
        except Exception:
            pass

    def _pack_question_image(self, parent, url: str) -> None:
        """מציג תמונת תמרור/שאלה מקישור רשמי - קומפקטי כדי לא לדחוף גלילה."""
        try:
            import io
            import urllib.request
            from PIL import Image, ImageTk

            cache_dir = os.path.join(
                os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
                "StudyApp", "image_cache",
            )
            os.makedirs(cache_dir, exist_ok=True)
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("/")[-1])[:80] or "qimg.jpg"
            path = os.path.join(cache_dir, name)
            if not os.path.isfile(path) or os.path.getsize(path) < 50:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 StudyApp"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    path_bytes = resp.read()
                with open(path, "wb") as handle:
                    handle.write(path_bytes)
            img = Image.open(path)
            img.thumbnail((320, 140))
            photo = ImageTk.PhotoImage(img)
            holder = tk.Label(parent, image=photo, bg=COLORS["card_bg"])
            holder.image = photo  # noqa: keep ref
            holder.pack(anchor="e", pady=(6, 2))
        except Exception:
            fast_label(
                parent, "לתמונה בשאלה: בדקו חיבור לרשת או תרגלו לפי הטקסט.",
                size=11, muted=True, bg=COLORS["card_bg"],
            ).pack(anchor="e", pady=(4, 0))

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
            anchor="e", justify="right", wraplength=content_wrap(self),
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

    def _show_ladder_hint(self, question):
        """סולם רמזים 1→2→3 דרך מנוע ה־AI (או live_hint כנפילה)."""
        self._hint_level = min(3, int(getattr(self, "_hint_level", 0) or 0) + 1)
        engine = self.ai_engine
        if engine is not None:
            text = engine.hint_ladder(
                question, level=self._hint_level, subject=self.subject_key or "",
            )
        else:
            from core.teach import live_hint

            text = live_hint(question, self.subject_key or "")
        titles = {1: "רמז · כיוון", 2: "רמז · צעד", 3: "רמז · מלכודת"}
        from core.dialogs import info

        info(titles.get(self._hint_level, "רמז"), text)

    def _paraphrase_question(self, question):
        """כפתור «תרגם לי את השאלה» - שפת יום־יום דרך Ollama."""
        box = getattr(self, "_plain_box", None)
        if box is None:
            return
        for child in box.winfo_children():
            child.destroy()
        card, inner = make_card(box, pady=10, padx=12)
        card.pack(fill="x")
        wait = fast_label(
            inner, "מנסח מחדש בשפה פשוטה…", size=13, muted=True, bg=COLORS["card_bg"],
        )
        wait.pack(anchor="e")

        def done(result):
            if not box.winfo_exists():
                return
            for child in box.winfo_children():
                child.destroy()
            card2, inner2 = make_card(box, pady=10, padx=12, accent=COLORS["primary"])
            card2.pack(fill="x")
            fast_label(inner2, "בשפה פשוטה", size=12, muted=True, bg=COLORS["card_bg"]).pack(anchor="e")
            body(inner2, result.get("plain") or "לא הצלחתי לנסח מחדש.", size=15).pack(anchor="e", pady=(2, 4))
            if result.get("given"):
                fast_label(
                    inner2, f"נתון: {result['given']}", size=13, bg=COLORS["card_bg"], wrap=720,
                ).pack(anchor="e", pady=(2, 0))
            if result.get("find"):
                fast_label(
                    inner2, f"צריך למצוא: {result['find']}", size=13, bg=COLORS["card_bg"], wrap=720,
                ).pack(anchor="e", pady=(2, 0))
            if result.get("steps"):
                fast_label(
                    inner2, f"שלבים: {result['steps']}", size=12, muted=True, bg=COLORS["card_bg"], wrap=720,
                ).pack(anchor="e", pady=(2, 0))
            src = result.get("source") or ""
            if src == "fallback":
                err = (result.get("error") or "").strip()
                tip = "אין חיבור מקומי. מציגים ניסוח בסיסי. בדקו בהגדרות."
                if err:
                    tip = f"מצב מקומי: {err}"
                fast_label(
                    inner2,
                    tip,
                    size=11, muted=True, bg=COLORS["card_bg"], wrap=720,
                ).pack(anchor="e", pady=(4, 0))
            try:
                self.after(40, self._refit_scroll)
            except Exception:
                pass

        def fail(msg):
            if not box.winfo_exists():
                return
            for child in box.winfo_children():
                child.destroy()
            from core.dialogs import info
            info("תרגום שאלה", f"לא הצלחתי: {msg}")

        from core import ai_tutor

        storage = self.storage
        ai_tutor.run_async(
            lambda: ai_tutor.paraphrase_question(question, storage=storage),
            on_done=done,
            on_error=fail,
            ui=self,
        )

    def _gentle_explain(self, question):
        from core import ai_tutor, dialogs

        def done(text):
            if not self.winfo_exists():
                return
            try:
                dialogs.info("הסבר פשוט", text or "אין הסבר.")
            except Exception:
                pass

        def fail(msg):
            if not self.winfo_exists():
                return
            try:
                dialogs.info("הסבר פשוט", str(msg))
            except Exception:
                pass

        storage = self.storage
        ai_tutor.run_async(
            lambda: ai_tutor.gentle_explain(question, storage=storage),
            on_done=done,
            on_error=fail,
            ui=self,
        )

    def _open_tutor(self, question, reveal=False):
        """חלון מורה פרטי סוקרטי."""
        import tkinter as tk

        from core import ai_tutor, ollama_client
        from core.config import ADHD_CONFIG
        from ui.widgets import font_size

        root = self.winfo_toplevel()
        win = tk.Toplevel(root)
        win.title("מורה שלב־שלב")
        win.configure(bg=COLORS["card_bg"])
        win.geometry("520x480")
        win.transient(root)
        history: list[dict[str, str]] = []
        state = {"busy": False, "cancel": None, "started": 0.0}

        tk.Label(
            win, text=rtl("עזרה שלב־שלב"),
            bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(15), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x", padx=14, pady=(12, 4))

        chat = tk.Text(
            win, wrap="word", height=16,
            font=(ADHD_CONFIG["font_family"], font_size(13)),
            bg=COLORS["bg"], fg=COLORS["text_main"],
            relief="flat", padx=10, pady=8,
        )
        chat.pack(fill="both", expand=True, padx=14, pady=6)
        chat.tag_configure("rtl", justify="right")
        chat.insert("end", rtl("רגע, המורה מתחיל…") + "\n", "rtl")
        chat.configure(state="disabled")

        entry_var = tk.StringVar()
        row = tk.Frame(win, bg=COLORS["card_bg"])
        row.pack(fill="x", padx=14, pady=(0, 12))
        entry = themed_entry(row, entry_var, justify="right")
        entry.pack(side="right", fill="x", expand=True, ipady=6)

        status = fast_label(win, "", size=11, muted=True, bg=COLORS["card_bg"])
        status.pack(anchor="e", padx=14, pady=(0, 8))

        send_btn = ModernButton(row, text=rtl("שליחה"), width=100, height=36)
        send_btn.pack(side="left", padx=(0, 6))
        reveal_btn = GhostButton(row, text=rtl("גלה תשובה"), width=110, height=36)
        reveal_btn.pack(side="left")

        def append(who: str, text: str):
            try:
                if not win.winfo_exists():
                    return
                chat.configure(state="normal")
                chat.insert("end", rtl(f"{who}: {text}") + "\n\n", "rtl")
                chat.see("end")
                chat.configure(state="disabled")
            except tk.TclError:
                pass

        def set_busy(flag: bool, note: str = ""):
            state["busy"] = flag
            try:
                if not win.winfo_exists():
                    return
                send_btn.configure(state=("disabled" if flag else "normal"))
                reveal_btn.configure(state=("disabled" if flag else "normal"))
                status.configure(text=rtl(note))
            except tk.TclError:
                pass

        def ask(msg: str = "", do_reveal: bool = False):
            if state["busy"]:
                try:
                    status.configure(text=rtl("עדיין חושב על ההודעה הקודמת…"))
                except tk.TclError:
                    pass
                return
            try:
                if not win.winfo_exists():
                    return
            except tk.TclError:
                return
            set_busy(True, "חושב… (עד כ־40 שניות)")
            storage = self.storage
            import time as _time
            state["started"] = _time.time()

            def work():
                return ai_tutor.socratic_turn(
                    question,
                    history=list(history),
                    student_message=msg,
                    reveal_answer=do_reveal,
                    storage=storage,
                )

            def done(result):
                try:
                    if not win.winfo_exists():
                        return
                    set_busy(False, "")
                    say = result.get("say") or ""
                    ask_q = result.get("ask") or ""
                    term = result.get("term") or ""
                    blob = say
                    if term:
                        blob += f"\n({term})"
                    if ask_q:
                        blob += f"\n→ {ask_q}"
                    append("מורה", blob)
                    history.append({"role": "assistant", "content": blob})
                    if result.get("source") == "fallback":
                        err = result.get("error") or ollama_client.last_error()
                        note = "בלי חיבור: מצב מקומי."
                        if err:
                            note = f"מצב מקומי · {err}"
                        status.configure(text=rtl(note))
                except tk.TclError:
                    pass

            def fail(err):
                try:
                    if win.winfo_exists():
                        set_busy(False, str(err) or "שגיאה")
                        append("מורה", "לא הצלחתי לענות עכשיו. נסו שוב בעוד רגע.")
                except tk.TclError:
                    pass

            cancel = ai_tutor.run_async(work, on_done=done, on_error=fail, ui=win)
            state["cancel"] = cancel

            def tick_wait():
                try:
                    if not win.winfo_exists() or not state["busy"]:
                        return
                    elapsed = int(_time.time() - float(state["started"] or _time.time()))
                    status.configure(text=rtl(f"חושב… {elapsed} שנ׳"))
                    win.after(500, tick_wait)
                except tk.TclError:
                    pass

            try:
                win.after(500, tick_wait)
            except tk.TclError:
                pass

        def send(_event=None):
            if state["busy"]:
                return
            text = str(entry_var.get() or "").strip()
            if not text:
                return
            entry_var.set("")
            append("אתם", text)
            history.append({"role": "user", "content": text})
            want_reveal = any(tok in text for tok in ("תן תשובה", "גלה", "תשובה מלאה"))
            ask(text, do_reveal=want_reveal)

        def on_close():
            cancel = state.get("cancel")
            if cancel is not None:
                try:
                    cancel.set()
                except Exception:
                    pass
            try:
                win.destroy()
            except tk.TclError:
                pass

        send_btn.configure(command=send)
        reveal_btn.configure(command=lambda: ask("תן תשובה בבקשה", do_reveal=True))
        entry.bind("<Return>", send)
        win.protocol("WM_DELETE_WINDOW", on_close)
        ask("", do_reveal=bool(reveal))
        try:
            entry.focus_set()
        except tk.TclError:
            pass

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
        from core.teach import teach_after_answer

        blocks = teach_after_answer(q, is_correct=bool(is_correct), subject=self.subject_key or "")
        msg = blocks.get("status") or msg
        tk.Label(
            inner, text=rtl(msg), bg=COLORS["card_bg"], fg=color,
            font=(ADHD_CONFIG["font_family"], font_size(17), "bold"), anchor="e",
        ).pack(anchor="e")
        if self._is_compose(q) and typed:
            fast_label(
                inner, f"כתבת: {typed}", size=13, muted=True, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(4, 0))
        opts = q.get("options") or []
        idx = q.get("answer")
        correct = q.get("correct_answer") or ""
        if not correct and isinstance(idx, int) and 0 <= idx < len(opts):
            correct = opts[idx]
        if self._is_compose(q) and correct and not is_correct:
            fast_label(
                inner, f"צריך היה לכתוב: {correct}", size=15, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(6, 0))
        if blocks.get("why"):
            fast_label(
                inner, f"מה נכון: {blocks['why']}", size=14, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(6, 2))
        if blocks.get("how"):
            fast_label(
                inner, f"איך: {blocks['how']}", size=13, muted=True, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(0, 2))
        if blocks.get("watch") and not is_correct:
            fast_label(
                inner, f"שימו לב: {blocks['watch']}", size=13, muted=True, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(0, 2))
        # המחשה רק אחרי תשובה - לא תופסת מקום לפני הבחירה
        if not self.exam_mode:
            try:
                from core.illustrations.schema import get_visual
                from ui.visual_panel import VisualPanel

                if get_visual(q):
                    VisualPanel(inner, q, mode="explain", bg=COLORS["card_bg"], max_width=640).pack(
                        fill="x", pady=(4, 2),
                    )
            except Exception:
                pass
        if blocks.get("next_hint") and not is_correct:
            fast_label(
                inner, blocks["next_hint"], size=13, muted=True, bg=COLORS["card_bg"], wrap=720,
            ).pack(anchor="e", pady=(0, 2))
        if not self.exam_mode and not is_correct:
            tutor_row = tk.Frame(inner, bg=COLORS["card_bg"])
            tutor_row.pack(fill="x", pady=(6, 2))
            GhostButton(
                tutor_row, text=rtl("מורה שלב־שלב"), width=150, height=34,
                command=lambda item=q: self._open_tutor(item, reveal=False),
            ).pack(side="right", padx=4)
            GhostButton(
                tutor_row, text=rtl("הסבר קצר"), width=110, height=34,
                command=lambda item=q: self._gentle_explain(item),
            ).pack(side="right", padx=4)
        spoken = " ".join(
            p for p in (blocks.get("why"), blocks.get("how"), blocks.get("watch")) if p
        )
        if self.speaker is not None and self.speaker.enabled and spoken:
            self.speaker.say(spoken)
        row = tk.Frame(inner, bg=COLORS["card_bg"])
        row.pack(anchor="e", fill="x", pady=(6, 0))
        ModernButton(
            row, text=rtl("לשאלה הבאה  (Enter)"), width=220, command=self._render,
        ).pack(side="right", padx=(6, 0))
        if (
            not is_correct
            and callable(getattr(self, "on_similar_topic", None))
            and not self.exam_mode
            and (q.get("topic") or blocks.get("cta"))
        ):
            GhostButton(
                row,
                text=rtl(blocks.get("cta") or "עוד על הנושא"),
                width=160,
                command=lambda: self.on_similar_topic(str(q.get("topic") or "")),
            ).pack(side="right")
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
