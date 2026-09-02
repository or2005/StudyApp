"""התראות קצרות בתוך החלון, בלי דיאלוג של Windows."""
from __future__ import annotations

import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl
from ui.widgets import font_size


class ToastHost:
    def __init__(self, master: tk.Misc):
        self.master = master
        self._frame: tk.Frame | None = None
        self._job = None

    def show(self, title: str, detail: str = "", kind: str = "info", ms: int = 3200) -> None:
        self.dismiss()
        try:
            if not self.master.winfo_exists():
                return
        except tk.TclError:
            return
        accent = {
            "success": COLORS["success"],
            "warn": COLORS.get("hint") or COLORS["accent"],
            "danger": COLORS["danger"],
        }.get(kind, COLORS["primary"])
        frame = tk.Frame(
            self.master,
            bg=COLORS["card_bg"],
            highlightthickness=1,
            highlightbackground=accent,
        )
        tk.Frame(frame, bg=accent, height=3).pack(fill="x")
        inner = tk.Frame(frame, bg=COLORS["card_bg"])
        inner.pack(fill="x", padx=16, pady=12)
        tk.Label(
            inner, text=rtl(title), bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
            anchor="e", justify="right",
        ).pack(anchor="e")
        if detail:
            tk.Label(
                inner, text=rtl(detail), bg=COLORS["card_bg"], fg=COLORS["text_muted"],
                font=(ADHD_CONFIG["font_family"], font_size(12)),
                anchor="e", justify="right", wraplength=360,
            ).pack(anchor="e", pady=(2, 0))
        frame.place(relx=0.5, rely=1.0, x=0, y=-28, anchor="s")
        frame.lift()
        self._frame = frame
        try:
            self._job = self.master.after(max(1200, int(ms)), self.dismiss)
        except tk.TclError:
            self._job = None

    def dismiss(self) -> None:
        job = self._job
        self._job = None
        if job is not None:
            try:
                self.master.after_cancel(job)
            except Exception:
                pass
        frame = self._frame
        self._frame = None
        if frame is None:
            return
        try:
            frame.place_forget()
            frame.destroy()
        except tk.TclError:
            pass
