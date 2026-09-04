"""פאנל המחשה חכם: שיעור / שאלה / הסבר, עם הגדלה וכיתוב."""
from __future__ import annotations

import tkinter as tk

from core.config import COLORS, rtl
from core.illustrations.schema import get_visual
from ui.fast import fast_label
from ui.widgets import GhostButton, font_size


class VisualPanel(tk.Frame):
    """
    mode:
      lesson   — רחב, מעל הטקסט
      question — קומפקטי וניטרלי (לפני תשובה)
      explain  — עם הדגשת reveal אחרי תשובה
    """

    def __init__(
        self,
        master,
        item: dict | None,
        *,
        mode: str = "lesson",
        bg: str | None = None,
        max_width: int = 720,
    ):
        page = bg or COLORS.get("card_bg") or COLORS["bg"]
        super().__init__(master, bg=page, highlightthickness=0)
        self._item = item or {}
        self._mode = mode
        self._max_width = max_width
        self._expanded = False
        self._visual = get_visual(self._item)
        self._img_label = None
        self._caption = None
        if not self._visual:
            self.pack_forget()
            return
        self._build()

    def _sizes(self) -> tuple[int, int]:
        if self._expanded:
            return min(900, self._max_width + 80), 300 if self._mode != "question" else 220
        if self._mode == "lesson":
            return min(720, self._max_width), 210
        if self._mode == "explain":
            return min(680, self._max_width), 190
        return min(640, self._max_width), 140

    def _build(self):
        head = tk.Frame(self, bg=self["bg"])
        head.pack(fill="x", pady=(0, 4))
        title = str(self._visual.get("title") or "המחשה")
        fast_label(head, title, size=13, muted=False, bg=self["bg"]).pack(side="right")
        GhostButton(
            head,
            text=rtl("הקטן" if self._expanded else "הגדל"),
            width=90,
            command=self._toggle,
        ).pack(side="left")

        self._img_label = tk.Label(self, bg=self["bg"], bd=0, highlightthickness=0, cursor="hand2")
        self._img_label.pack(fill="x")
        self._img_label.bind("<Button-1>", lambda _e: self._toggle())
        self._paint_image()

        caption = str(self._visual.get("caption") or "")
        if self._mode == "explain":
            caption = str(self._visual.get("reveal_note") or caption)
        if caption:
            self._caption = fast_label(
                self, caption, size=13, muted=True, bg=self["bg"], wrap=self._max_width,
            )
            self._caption.pack(anchor="e", pady=(6, 2))

        alt = str(self._visual.get("alt") or "")
        if alt:
            fast_label(
                self, alt, size=11, muted=True, bg=self["bg"], wrap=self._max_width,
            ).pack(anchor="e", pady=(0, 4))

        if self._mode == "question":
            fast_label(
                self, "ההמחשה עוזרת להבין. עדיין קוראים את השאלה.",
                size=11, muted=True, bg=self["bg"], wrap=self._max_width,
            ).pack(anchor="e")

    def _paint_image(self):
        if not self._img_label or not self._visual:
            return
        try:
            from core.illustrations.render import photo_for

            w, h = self._sizes()
            photo = photo_for(self, self._visual, width=w, height=h, mode=self._mode)
            self._img_label.configure(image=photo)
            self._img_label.image = photo
        except Exception:
            self._img_label.configure(
                text=rtl(str(self._visual.get("title") or "המחשה")),
                fg=COLORS.get("muted") or "#666",
                font=(COLORS and "Segoe UI", font_size(14)),
            )

    def _toggle(self):
        self._expanded = not self._expanded
        for child in self.winfo_children():
            child.destroy()
        self._build()
