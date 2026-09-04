"""מסך העוזר: שיחה פשוטה, התאמת תרגול, בלי זargon מיותר."""
from __future__ import annotations

import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, Page, font_size, make_card, page_header, themed_entry


class AIAssistantScreen(Page):
    def __init__(
        self,
        master,
        *,
        ai_engine,
        on_start_practice=None,
        on_back=None,
        initial_question=None,
        subject: str = "",
    ):
        super().__init__(master)
        self.ai = ai_engine
        self.on_start_practice = on_start_practice
        self.on_back = on_back
        self.subject = subject or ""
        self.question = initial_question
        self._busy = False
        self._history = list(ai_engine.chat_history())
        self._pending_action = None

        page_header(
            self,
            "העוזר שלי",
            "שאלה על החומר, בקשה לתרגול מותאם, או עזרה כשנתקעים. הכל נשאר על המחשב שלכם.",
        )

        status = self.ai.status()
        tip = tk.Frame(self, bg=COLORS["bg"])
        tip.pack(fill="x", pady=(0, 8))
        online = bool(status.get("online") and status.get("enabled"))
        if not status.get("enabled"):
            tip_txt = "העוזר כבוי בהגדרות. אפשר להדליק ולחזור לכאן."
        elif online:
            tip_txt = "מחובר. אפשר לכתוב חופשי או לבחור קיצור למטה."
        else:
            tip_txt = "בלי חיבור מקומי עדיין אפשר לבקש תרגול מותאם לפי האנליסט."
        fast_label(tip, tip_txt, size=13, muted=True, bg=COLORS["bg"], wrap=740).pack(anchor="e")
        mem_n = int(status.get("memory_items") or 0)
        if mem_n:
            fast_label(
                tip,
                f"זוכר {mem_n} דברים מהתרגולים הקודמים שלכם",
                size=12,
                muted=True,
                bg=COLORS["bg"],
            ).pack(anchor="e", pady=(2, 0))

        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(0, 10))
        ModernButton(
            actions,
            text=rtl("תתאים לי תרגול"),
            height=44,
            width=180,
            command=lambda: self._quick("תתאים לי תרגול לפי הרמה שלי"),
        ).pack(side="right", padx=4)
        GhostButton(
            actions,
            text=rtl("מה כדאי לחזק?"),
            height=44,
            width=150,
            command=lambda: self._quick("מה כדאי לי לחזק עכשיו?"),
        ).pack(side="right", padx=4)
        GhostButton(
            actions,
            text=rtl("בוא לאט יותר"),
            height=44,
            width=140,
            command=lambda: self._quick("אני עייף וממהר. תתאים לי קצב רגוע"),
        ).pack(side="right", padx=4)

        chat_card, chat_inner = make_card(self, pady=12, padx=12)
        chat_card.pack(fill="both", expand=True, pady=(0, 8))
        self.chat = tk.Text(
            chat_inner,
            wrap="word",
            height=15,
            font=(ADHD_CONFIG["font_family"], font_size(14)),
            bg=COLORS.get("option_bg") or COLORS["bg"],
            fg=COLORS["text_main"],
            relief="flat",
            padx=12,
            pady=10,
            insertbackground=COLORS["text_main"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure("rtl", justify="right")
        self.chat.tag_configure("user", foreground=COLORS["primary"])
        self.chat.tag_configure("bot", foreground=COLORS["text_main"])
        self.chat.configure(state="disabled")

        if self._history:
            for row in self._history[-16:]:
                who = "אתם" if row.get("role") == "user" else "העוזר"
                self._append(who, row.get("content") or "", user=(row.get("role") == "user"))
        else:
            welcome = (
                "היי. אפשר לשאול על נושא מהלימודים, לבקש שאתאים תרגול, "
                "או לכתוב מה לא ברור בשאלה. במבחן אמיתי העזרה נעולה; כאן אפשר בחופשי."
            )
            if self.question:
                welcome = (
                    "רואה שיש שאלה פתוחה. כתבו מה לא מובן, "
                    "ואעזור בשלבים קטנים בלי לחשוף את התשובה מיד."
                )
            self._append("העוזר", welcome, user=False)

        self.action_bar = tk.Frame(self, bg=COLORS["bg"])
        self.action_bar.pack(fill="x", pady=(0, 6))

        row = tk.Frame(self, bg=COLORS["bg"])
        row.pack(fill="x", pady=(0, 4))
        self.var = tk.StringVar()
        entry = themed_entry(row, self.var, justify="right")
        entry.pack(side="right", fill="x", expand=True, ipady=10)
        entry.bind("<Return>", lambda _e: self._send())
        ModernButton(row, text=rtl("שליחה"), width=110, height=44, command=self._send).pack(
            side="left", padx=(0, 6),
        )
        if on_back:
            GhostButton(row, text=rtl("חזרה"), width=90, height=44, command=on_back).pack(side="left")

        self.status_lbl = fast_label(self, "", size=11, muted=True, bg=COLORS["bg"])
        self.status_lbl.pack(anchor="e", pady=(0, 4))
        self.after(80, entry.focus_set)

    def _append(self, who: str, text: str, *, user: bool) -> None:
        self.chat.configure(state="normal")
        tag = "user" if user else "bot"
        self.chat.insert("end", rtl(f"{who}\n{text}") + "\n\n", ("rtl", tag))
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        try:
            self.status_lbl.configure(text=rtl(text))
        except tk.TclError:
            pass

    def _clear_action_bar(self) -> None:
        for child in self.action_bar.winfo_children():
            child.destroy()

    def _show_practice_action(self, result: dict) -> None:
        self._clear_action_bar()
        self._pending_action = result
        if not self.on_start_practice or result.get("action") != "start_practice":
            return
        ModernButton(
            self.action_bar,
            text=rtl("מתחילים את התרגול"),
            height=46,
            width=220,
            command=self._run_pending_practice,
        ).pack(side="right", padx=4)

    def _run_pending_practice(self) -> None:
        result = self._pending_action or {}
        if not self.on_start_practice:
            return
        self.on_start_practice(
            result.get("subject") or "",
            result.get("topics") or [],
            int(result.get("count") or 6),
        )

    def _quick(self, text: str) -> None:
        self.var.set(text)
        self._send()

    def _send(self) -> None:
        if self._busy:
            return
        text = str(self.var.get() or "").strip()
        if not text:
            return
        self.var.set("")
        self._append("אתם", text, user=True)
        self._history.append({"role": "user", "content": text})
        self._busy = True
        self._set_status("רגע…")
        self._clear_action_bar()

        history = list(self._history)
        question = self.question
        subject = self.subject
        ai = self.ai

        def work():
            return ai.assistant_chat(
                text,
                history=history[:-1],
                question=question,
                subject=subject,
                use_llm=True,
            )

        def done(result):
            def paint():
                self._busy = False
                self._set_status("")
                reply = (result or {}).get("reply") or "לא הצלחתי לענות עכשיו. נסו שוב או בקשו תרגול מותאם."
                self._append("העוזר", reply, user=False)
                self._history.append({"role": "assistant", "content": reply})
                try:
                    self.ai.save_chat_history(self._history)
                except Exception:
                    pass
                action = (result or {}).get("action")
                if action == "enable_calm" and self.ai.storage:
                    self.ai.storage.set_pref("ai_calm_mode", True)
                    self._append("העוזר", "הפעלתי מצב רגוע: סשנים קצרים יותר.", user=False)
                if action == "start_practice":
                    self._show_practice_action(result or {})

            try:
                self.after(0, paint)
            except Exception:
                self._busy = False

        def fail(err):
            def paint():
                self._busy = False
                self._set_status("")
                self._append("העוזר", "משהו נתקע. נסו שוב בעוד רגע.", user=False)

            try:
                self.after(0, paint)
            except Exception:
                self._busy = False

        from core import ai_tutor

        ai_tutor.run_async(work, on_done=done, on_error=fail)
