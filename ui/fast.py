"""ווידג'טים מהירים מבוססי tkinter טהור.

CustomTkinter בונה לכל כפתור Canvas + Label + ציור פינות מעוגלות. כשיש 20 פריטים
ברשימה זה נהיה איטי ומרגיש "נמרח". כאן משתמשים ב-tk רגיל לפריטים חוזרים,
ושומרים את CustomTkinter רק לכפתורי הפעולה הגדולים.
"""
from __future__ import annotations

import time
import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, rtl

# בזמן גלגלת, ווידג'טים זזים מתחת לעכבר ומייצרים Enter/Leave על כל שורה.
# זה הצביעה מחדש של עשרות Labels בכל טיק, וזה מה שנראה כמו "נמרח".
_SCROLL_UNTIL = 0.0


def widget_alive(widget) -> bool:
    try:
        return bool(widget) and bool(widget.winfo_exists())
    except tk.TclError:
        return False


class SafeWidget:
    """CTk מחזיר פוקוס עם after(1, widget.focus) אחרי שינוי שורת הכותרת.

    אם הווידג'ט כבר נהרס (החלפת ערכת נושא / ניווט), זה TclError ביומן.
    Canvas.focus() בלי ארגומנטים הוא בכלל פוקוס לפריט קנבס, לא לחלון.
    """

    def focus_set(self, *args, **kwargs):
        try:
            if widget_alive(self):
                return super().focus_set(*args, **kwargs)
        except tk.TclError:
            return None
        return None

    def focus(self, *args, **kwargs):
        try:
            if not widget_alive(self):
                return ""
            if not args and not kwargs:
                super().focus_set()
                return ""
            return super().focus(*args, **kwargs)
        except tk.TclError:
            return ""


def is_scrolling() -> bool:
    return time.monotonic() < _SCROLL_UNTIL


def mark_scrolling(ms: int = 160) -> None:
    global _SCROLL_UNTIL
    _SCROLL_UNTIL = time.monotonic() + ms / 1000.0


def _family() -> str:
    return str(ADHD_CONFIG.get("font_family") or "Segoe UI")


def _font(base: int) -> int:
    return max(10, int(base) + int(ADHD_CONFIG.get("font_delta", 0) or 0))


def _color(key: str, fallback: str) -> str:
    return COLORS.get(key) or fallback


class ThinScrollbar(SafeWidget, tk.Canvas):
    """סרגל גלילה דק בצבעי הערכת נושא, במקום הסרגל המקורי של Windows."""

    WIDTH = 11

    def __init__(self, master, command, bg: str | None = None, thumb: str | None = None):
        self._track = bg or _color("scrollbar", COLORS["card_hover"])
        super().__init__(master, width=self.WIDTH, bg=self._track, highlightthickness=0, bd=0)
        self._command = command
        self._thumb = thumb or _color("scrollbar_thumb", COLORS["primary"])
        self._lo = 0.0
        self._hi = 1.0
        self._thumb_id = None
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Button-1>", self._scrub)
        self.bind("<B1-Motion>", self._scrub)

    def set(self, first, last):
        if not widget_alive(self):
            return
        try:
            lo, hi = float(first), float(last)
        except (TypeError, ValueError):
            return
        if abs(lo - self._lo) < 0.0008 and abs(hi - self._hi) < 0.0008:
            return
        self._lo, self._hi = lo, hi
        self._draw()

    def set_colors(self, bg: str, thumb: str):
        if not widget_alive(self):
            return
        self._track, self._thumb = bg, thumb
        try:
            self.configure(bg=bg)
            self._draw()
        except tk.TclError:
            pass

    def _draw(self):
        if not widget_alive(self):
            return
        try:
            h = max(1, int(self.winfo_height() or 1))
            y1 = max(0, int(self._lo * h))
            y2 = min(h, int(self._hi * h))
            if y2 - y1 < 32:
                y2 = min(h, y1 + 32)
            coords = (3, y1 + 3, self.WIDTH - 2, max(y1 + 4, y2 - 3))
            if self._thumb_id is None:
                self._thumb_id = self.create_rectangle(
                    *coords, fill=self._thumb, outline="", tags="thumb",
                )
            else:
                self.coords(self._thumb_id, *coords)
                self.itemconfigure(self._thumb_id, fill=self._thumb)
        except tk.TclError:
            return

    def _scrub(self, event):
        if not widget_alive(self):
            return
        try:
            h = max(1, int(self.winfo_height() or 1))
        except tk.TclError:
            return
        span = max(0.06, self._hi - self._lo)
        frac = (event.y / h) - span / 2
        frac = max(0.0, min(1.0, frac))
        if callable(self._command):
            self._command("moveto", frac)


class FastScroll(SafeWidget, tk.Frame):
    """אזור גלילה קל. מחליף CTkScrollableFrame שהוא יקר מאוד."""

    def __init__(self, master, bg: str | None = None, padx: int = 0, max_width: int = 0):
        bg = bg or COLORS["bg"]
        super().__init__(master, bg=bg, highlightthickness=0, bd=0)
        self._bg = bg
        self._max_width = int(max_width or 0)
        self.canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, bd=0, takefocus=0,
            yscrollincrement=36,
        )
        self.vbar = ThinScrollbar(
            self, command=self.canvas.yview,
            bg=_color("scrollbar", COLORS["card_hover"]),
            thumb=_color("scrollbar_thumb", COLORS["primary"]),
        )
        self.body = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_yview)
        # הסרגל תמיד במקום. pack/forget משנה את רוחב הקנבס ומריץ wrap מחדש לכל התוויות.
        self.vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=padx)
        self._bar_visible = True
        self._wheel_acc = 0
        self._wheel_bound = False
        self._sync_job = None
        self.body.bind("<Configure>", self._request_sync)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<Enter>", lambda _e: self._bind_wheel())
        self.bind("<Leave>", lambda _e: self._unbind_wheel())

    def _request_sync(self, _event=None):
        """כל ווידג'ט שנוסף מפעיל Configure. בלי דחייה ל-idle זה יוצא ריבועי
        ומרגיש כמו תקיעה כשבונים מסך עם הרבה שורות."""
        if not widget_alive(self):
            return
        if self._sync_job is None:
            try:
                self._sync_job = self.after_idle(self._sync_now)
            except tk.TclError:
                self._sync_job = None

    def _cancel_sync(self):
        if self._sync_job is not None:
            try:
                self.after_cancel(self._sync_job)
            except tk.TclError:
                pass
            self._sync_job = None

    def _sync_now(self):
        self._sync_job = None
        if not widget_alive(self) or not widget_alive(self.canvas):
            return
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self._update_bar()
        except tk.TclError:
            pass

    def _on_canvas_configure(self, event):
        if not widget_alive(self) or not widget_alive(self.canvas):
            return
        try:
            avail = max(1, int(event.width or 1))
            if self._max_width and avail > self._max_width:
                page_w = self._max_width
                x = (avail - page_w) // 2
            else:
                page_w = avail
                x = 0
            self.canvas.coords(self._window, x, 0)
            self.canvas.itemconfigure(self._window, width=page_w)
            self._request_sync()
        except tk.TclError:
            return

    def _update_bar(self):
        try:
            need = self.body.winfo_reqheight() > self.canvas.winfo_height() + 2
        except tk.TclError:
            return
        self._bar_visible = bool(need)

    def _on_yview(self, first, last):
        if widget_alive(getattr(self, "vbar", None)):
            self.vbar.set(first, last)

    def _bind_wheel(self):
        if self._wheel_bound:
            return
        self._wheel_bound = True
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", self._wheel)
        self.canvas.bind_all("<Button-5>", self._wheel)

    def _unbind_wheel(self):
        if not self._wheel_bound:
            return
        self._wheel_bound = False
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.canvas.unbind_all(seq)
            except Exception:
                pass

    def _wheel(self, event):
        mark_scrolling()
        steps = 0
        if getattr(event, "num", None) == 4:
            steps = -1
        elif getattr(event, "num", None) == 5:
            steps = 1
        elif getattr(event, "delta", 0):
            self._wheel_acc += int(event.delta)
            while self._wheel_acc >= 120:
                self._wheel_acc -= 120
                steps -= 1
            while self._wheel_acc <= -120:
                self._wheel_acc += 120
                steps += 1
        if steps:
            self.canvas.yview_scroll(steps, "units")
        return "break"

    def to_top(self):
        if not widget_alive(self) or not widget_alive(getattr(self, "canvas", None)):
            return
        try:
            self.canvas.yview_moveto(0)
        except tk.TclError:
            pass

    def to_bottom(self):
        if not widget_alive(self) or not widget_alive(getattr(self, "canvas", None)):
            return
        try:
            self._sync_now()
            self.canvas.yview_moveto(1)
        except tk.TclError:
            pass

    def set_bg(self, color: str):
        if not widget_alive(self):
            return
        self._cancel_sync()
        self._bg = color
        # CustomTkinter עוטף Frame.configure של האב כשילד CTk נארז לתוכו.
        # אחרי שמוחקים מסך, העטיפה עדיין מצביעה על ווידג'ט מת, לכן קוראים
        # ל-configure של המחלקה, לא למופע.
        try:
            tk.Frame.configure(self, bg=color)
            if widget_alive(self.canvas):
                self.canvas.configure(bg=color)
            if widget_alive(self.body):
                tk.Frame.configure(self.body, bg=color)
            if widget_alive(self.vbar):
                self.vbar.set_colors(
                    _color("scrollbar", COLORS["card_hover"]),
                    _color("scrollbar_thumb", COLORS["primary"]),
                )
        except tk.TclError:
            pass

    def destroy(self):
        self._cancel_sync()
        self._unbind_wheel()
        super().destroy()


class FastRow(SafeWidget, tk.Frame):
    """שורת רשימה לחיצה, זולה מאוד לעומת CTkButton."""

    def __init__(self, master, text: str, on_click, subtitle: str = "", bg: str | None = None,
                 font_size: int | None = None, done: bool = False):
        bg = bg or COLORS["card_bg"]
        super().__init__(master, bg=bg, highlightthickness=1,
                         highlightbackground=COLORS["card_border"], cursor="hand2")
        self._bg = bg
        self._hover = COLORS["card_hover"]
        self._on_click = on_click

        pad = tk.Frame(self, bg=bg)
        pad.pack(fill="x", padx=14, pady=10)
        self._pad = pad

        chevron = tk.Label(
            pad, text="‹", bg=bg, fg=COLORS["primary"],
            font=(_family(), _font(18), "bold"), cursor="hand2",
        )
        chevron.pack(side="left", padx=(0, 8))

        col = tk.Frame(pad, bg=bg)
        col.pack(side="right", fill="x", expand=True)

        mark = "✓  " if done else ""
        self.label = tk.Label(
            col, text=rtl(mark + text), bg=bg, fg=COLORS["text_main"],
            font=(_family(), _font(font_size or 16), "bold"), anchor="e", justify="right",
        )
        self.label.pack(fill="x")
        self._kids = [pad, chevron, col, self.label]

        if subtitle:
            self.sub = tk.Label(
                col, text=rtl(subtitle), bg=bg, fg=COLORS["text_muted"],
                font=(_family(), _font(12)), anchor="e", justify="right",
            )
            self.sub.pack(fill="x")
            self._kids.append(self.sub)

        for widget in [self] + self._kids:
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _click(self, _event=None):
        if self._on_click:
            self._on_click()

    def _enter(self, _event=None):
        if is_scrolling() or not widget_alive(self):
            return
        try:
            for widget in [self] + self._kids:
                if widget_alive(widget):
                    widget.configure(bg=self._hover)
            self.configure(highlightbackground=COLORS["primary"])
        except tk.TclError:
            pass

    def _leave(self, _event=None):
        if is_scrolling() or not widget_alive(self):
            return
        try:
            for widget in [self] + self._kids:
                if widget_alive(widget):
                    widget.configure(bg=self._bg)
            self.configure(highlightbackground=COLORS["card_border"])
        except tk.TclError:
            pass


class FastCard(SafeWidget, tk.Frame):
    """כרטיס תוכן פשוט (בלי פינות מעוגלות יקרות)."""

    def __init__(self, master, bg: str | None = None, pad: int = 16):
        bg = bg or COLORS["card_bg"]
        super().__init__(master, bg=bg, highlightthickness=1,
                         highlightbackground=COLORS["card_border"])
        self.inner = tk.Frame(self, bg=bg)
        self.inner.pack(fill="both", expand=True, padx=pad, pady=pad)
        self._bg = bg

    def title(self, text: str, size: int = 18, color: str | None = None):
        lbl = tk.Label(self.inner, text=rtl(text), bg=self._bg,
                       fg=color or COLORS["text_main"], font=(_family(), _font(size), "bold"),
                       anchor="e", justify="right")
        lbl.pack(fill="x")
        return lbl

    def line(self, text: str, muted: bool = True, size: int = 14, wrap: int = 760):
        lbl = tk.Label(self.inner, text=rtl(text), bg=self._bg,
                       fg=COLORS["text_muted"] if muted else COLORS["text_main"],
                       font=(_family(), _font(size)), anchor="e", justify="right", wraplength=wrap)
        lbl.pack(fill="x", pady=(2, 0))
        return lbl


class FastText(tk.Text):
    """תיבת קריאה זולה. CTkTextbox הוא Canvas עם שעון 200ms, ובתוך גלילה זה נמרח."""

    def __init__(self, master, *, height: int = 12, font=None, **_ignored):
        super().__init__(
            master,
            wrap="word",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=_color("card_border", COLORS["card_border"]),
            highlightcolor=COLORS["primary"],
            bg=_color("card_bg", COLORS["card_bg"]),
            fg=_color("text_main", COLORS["text_main"]),
            insertbackground=_color("text_main", COLORS["text_main"]),
            font=font or (_family(), _font(15)),
            padx=12,
            pady=10,
            height=height,
            takefocus=0,
        )
        self.tag_configure("rtl", justify="right")

    def set_text(self, text: str, rtl_lines: bool = False):
        self.configure(state="normal")
        self.delete("1.0", "end")
        if rtl_lines:
            text = "\n".join(rtl(line) if line.strip() else line for line in str(text).split("\n"))
        self.insert("1.0", text)
        self.tag_add("rtl", "1.0", "end")
        self.configure(state="disabled")


class TkButton(SafeWidget, tk.Frame):
    """כפתור מבוסס tk עם אותו API של CTkButton.

    CTkButton בונה Canvas ומצייר פינות מעוגלות לכל כפתור. במסך עם עשרה כפתורים
    זה עשרות עד מאות מילישניות, וזאת הסיבה העיקרית שהתוכנה הרגישה נמרחת.
    כאן מוותרים על הפינות המעוגלות ומקבלים מסכים שנפתחים מיידית.
    """

    def __init__(self, master, text="", command=None, width=None, height=46,
                 fg_color=None, hover_color=None, text_color=None,
                 border_width=0, border_color=None, corner_radius=None,
                 anchor="center", state="normal", font=None, **_ignored):
        self._fg = fg_color or COLORS["primary"]
        self._hover = hover_color or COLORS["primary_hover"]
        self._text_color = text_color or COLORS["text_on_primary"]
        self._border_color = border_color or COLORS["card_border"]
        border_w = max(0, int(border_width or 0))
        super().__init__(
            master, bg=self._fg,
            highlightthickness=border_w,
            highlightbackground=self._border_color,
            highlightcolor=COLORS["primary"],
            bd=0,
        )
        self._command = command
        self._state = state
        self.label = tk.Label(
            self, text=text, bg=self._fg, fg=self._text_color,
            font=font or (_family(), _font(16), "bold"), anchor=anchor, justify="right",
            padx=14, pady=0,
        )
        self.label.pack(fill="both", expand=True)
        if width:
            self.configure(width=int(width))
        if height:
            self.configure(height=int(height))
        if width or height:
            self.pack_propagate(False)
            self.grid_propagate(False)
        self._apply_state()
        for widget in (self, self.label):
            widget.bind("<ButtonPress-1>", self._press)
            widget.bind("<ButtonRelease-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _apply_state(self):
        disabled = self._state == "disabled"
        self.label.configure(
            fg=COLORS["text_muted"] if disabled else self._text_color,
            cursor="arrow" if disabled else "hand2",
        )
        self.configure(cursor="arrow" if disabled else "hand2")

    def _press_color(self) -> str:
        raw = (self._hover or self._fg or "#000000").lstrip("#")
        if len(raw) != 6:
            return self._hover
        try:
            r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
        except ValueError:
            return self._hover
        return f"#{max(0, int(r * 0.82)):02x}{max(0, int(g * 0.82)):02x}{max(0, int(b * 0.82)):02x}"

    def _press(self, _event=None):
        if self._state == "disabled" or is_scrolling() or not widget_alive(self):
            return
        try:
            pressed = self._press_color()
            self.configure(bg=pressed, highlightbackground=COLORS["primary"])
            if widget_alive(self.label):
                self.label.configure(bg=pressed)
        except tk.TclError:
            pass

    def _click(self, _event=None):
        if self._state == "disabled":
            return
        if widget_alive(self):
            try:
                self.configure(bg=self._hover, highlightbackground=COLORS["primary"])
                if widget_alive(self.label):
                    self.label.configure(bg=self._hover)
            except tk.TclError:
                pass
        if self._command:
            self._command()

    def _enter(self, _event=None):
        if self._state == "disabled" or is_scrolling() or not widget_alive(self):
            return
        try:
            self.configure(bg=self._hover, highlightbackground=COLORS["primary"])
            if widget_alive(self.label):
                self.label.configure(bg=self._hover)
        except tk.TclError:
            pass

    def _leave(self, _event=None):
        if not widget_alive(self):
            return
        try:
            self.configure(bg=self._fg, highlightbackground=self._border_color)
            if widget_alive(self.label):
                self.label.configure(bg=self._fg)
        except tk.TclError:
            pass

    def invoke(self):
        self._click()

    def configure(self, **kwargs):  # type: ignore[override]
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if "text" in kwargs:
            self.label.configure(text=kwargs.pop("text"))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "fg_color" in kwargs:
            self._fg = kwargs.pop("fg_color")
            super().configure(bg=self._fg)
            self.label.configure(bg=self._fg)
        if "hover_color" in kwargs:
            self._hover = kwargs.pop("hover_color")
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            self.label.configure(fg=self._text_color)
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            super().configure(highlightbackground=self._border_color)
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._apply_state()
        for key in ("corner_radius", "border_width", "font", "anchor"):
            kwargs.pop(key, None)
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def cget(self, key):
        if key == "text":
            return self.label.cget("text")
        if key == "command":
            return self._command or (lambda: None)
        if key == "state":
            return self._state
        if key == "fg_color":
            return self._fg
        return super().cget(key)


class FastButton(SafeWidget, tk.Label):
    """כפתור tk. נראה כמעט כמו CTkButton אבל נבנה פי כמה יותר מהר,
    ולכן משמש בכל מקום שיש הרבה כפתורים על אותו מסך."""

    def __init__(self, master, text: str, command=None, primary: bool = False,
                 width: int = 0, size: int = 15, danger: bool = False, disabled: bool = False):
        if danger:
            bg = COLORS["danger"]
            fg = _color("danger_text", "#FFFFFF")
            hover = _color("danger_hover", "#BE123C")
        elif primary:
            bg, fg, hover = COLORS["primary"], COLORS["text_on_primary"], COLORS["primary_hover"]
        else:
            bg, fg, hover = COLORS["card_bg"], COLORS["text_main"], COLORS["card_hover"]
        if disabled:
            fg = COLORS["text_muted"]
        super().__init__(
            master, text=rtl(text), bg=bg, fg=fg,
            font=(_family(), _font(size), "bold"), padx=16, pady=9,
            cursor="arrow" if disabled else "hand2",
            highlightthickness=1,
            highlightbackground=COLORS["danger"] if danger else COLORS["card_border"],
        )
        if width:
            self.configure(width=width)
        self._bg, self._hover = bg, hover
        self._border = COLORS["danger"] if danger else COLORS["card_border"]
        self._command = None if disabled else command
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

    def _enter(self, _event=None):
        if self._command is None or is_scrolling() or not widget_alive(self):
            return
        try:
            self.configure(bg=self._hover, highlightbackground=COLORS["primary"])
        except tk.TclError:
            pass

    def _leave(self, _event=None):
        if not widget_alive(self):
            return
        try:
            self.configure(bg=self._bg, highlightbackground=self._border)
        except tk.TclError:
            pass

    def _click(self, _event=None):
        if self._command and widget_alive(self):
            self._command()

    def invoke(self):
        self._click()

    def cget(self, key):
        if key == "command":
            return self._command or (lambda: None)
        return super().cget(key)


def _bg_of(master) -> str:
    for attr in ("fg_color", "bg"):
        try:
            value = master.cget(attr)
        except Exception:
            continue
        if isinstance(value, (list, tuple)) and value:
            value = value[-1]
        if isinstance(value, str) and value.startswith("#"):
            return value
    return COLORS["bg"]


def fast_label(master, text: str, size: int = 15, muted: bool = False, bold: bool = False,
               bg: str | None = None, wrap: int = 900):
    return tk.Label(
        master, text=rtl(text), bg=bg or _bg_of(master),
        fg=COLORS["text_muted"] if muted else COLORS["text_main"],
        font=(_family(), _font(size), "bold" if bold else "normal"),
        anchor="e", justify="right", wraplength=wrap,
    )
