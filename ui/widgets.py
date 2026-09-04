import datetime
import tkinter as tk

import customtkinter as ctk

from core.config import ADHD_CONFIG, COLORS, DEVELOPER_NAME, SUBJECTS, rtl
from core.theme import subject_accent, subject_wash
from ui.fast import TkButton
from ui import skin

SUBJECT_ICONS = {
    "hebrew": "📖",
    "english": "🌐",
    "history": "📜",
    "geography": "🌍",
    "civics": "🏛",
    "chemistry": "🧪",
    "physics": "⚛",
    "math": "🔢",
    "arabic": "💬",
    "first_aid": "✚",
}

PAD = 20
GAP = 14
PAGE_WIDTH = 800
RAIL_WIDTH = 260
SIDEBAR_WIDTH = 224
RAIL_BREAKPOINT = 1240
SHADOW_PAD = (0, 4)
SHADOW_PAD_Y = (0, 5)
CARD_RADIUS = 24


def font_size(base: int) -> int:
    return max(10, base + int(ADHD_CONFIG.get("font_delta", 0) or 0))


def _c(key: str, fallback: str) -> str:
    return COLORS.get(key) or fallback


def elevate(master, *, face_bg: str | None = None, border: str | None = None, **kwargs):
    card = RoundedCard(master, fill=face_bg, **kwargs)
    return card, card.inner


class RoundedCard(tk.Frame):
    """כרטיס מעוגל עם צל, כמו במקאפ. התמונה סטטית ולכן לא נמרחת בגלילה."""

    def __init__(self, master, fill: str | None = None, radius: int = CARD_RADIUS,
                 shadow: bool = True, padx: int = 18, pady: int = 16, **kwargs):
        page = kwargs.pop("page", None) or COLORS["bg"]
        super().__init__(master, bg=page, highlightthickness=0, **kwargs)
        self._fill = fill or COLORS["card_bg"]
        self._radius = radius
        self._shadow = shadow
        self._page = page
        self._art = tk.Label(self, bg=page, bd=0, highlightthickness=0)
        self._art.place(x=0, y=0, relwidth=1, relheight=1)
        self.inner = tk.Frame(self, bg=self._fill)
        self.inner.pack(fill="both", expand=True, padx=padx, pady=(pady, pady + 4 if shadow else pady))
        self._size = (0, 0)
        self._paint_job = None
        self.bind("<Configure>", self._request_paint)

    def _request_paint(self, _event=None):
        if self._paint_job is not None:
            return
        try:
            self._paint_job = self.after_idle(self._paint)
        except tk.TclError:
            self._paint_job = None

    def _paint(self, _event=None):
        self._paint_job = None
        try:
            w, h = int(self.winfo_width()), int(self.winfo_height())
        except tk.TclError:
            return
        if w < 24 or h < 24:
            return
        prev_w, prev_h = self._size
        if abs(w - prev_w) < 2 and abs(h - prev_h) < 2:
            return
        self._size = (w, h)
        photo = skin.card_photo(self, w, h, self._fill, self._radius, self._shadow)
        if photo is not None:
            try:
                self._art.configure(image=photo)
            except tk.TclError:
                pass


class RoundBar(tk.Label):
    def __init__(self, master, pct: float = 0, color: str | None = None,
                 track: str | None = None, height: int = 12, **kwargs):
        super().__init__(master, bg=bg_of(master), bd=0, highlightthickness=0, **kwargs)
        self._pct = max(0.0, min(1.0, float(pct or 0)))
        self._color = color or COLORS["primary"]
        self._track = track or _c("progress_track", COLORS["card_hover"])
        self._bar_h = height
        self._size = 0
        self.bind("<Configure>", self._paint)

    def _paint(self, _event=None):
        w = self.winfo_width()
        if w < 40 or w == self._size:
            return
        self._size = w
        photo = skin.bar_photo(self, w, self._bar_h, self._pct, self._color, self._track)
        if photo is not None:
            self.configure(image=photo)


class ModernButton(tk.Frame):
    """כפתור גלולה מעוגל, כמו במקאפ."""

    def __init__(self, master, **kwargs):
        text = kwargs.pop("text", "")
        command = kwargs.pop("command", None)
        width = kwargs.pop("width", None)
        height = int(kwargs.pop("height", 48) or 48)
        fg = kwargs.pop("fg_color", None) or COLORS["primary"]
        hover = kwargs.pop("hover_color", None) or COLORS["primary_hover"]
        font = kwargs.pop("font", None) or (ADHD_CONFIG["font_family"], font_size(16), "bold")
        light_bg = str(fg).upper() in {
            str(COLORS["card_bg"]).upper(),
            str(COLORS["card_hover"]).upper(),
            "TRANSPARENT",
        }
        text_color = kwargs.pop("text_color", None) or (
            COLORS["text_main"] if light_bg else COLORS["text_on_primary"]
        )
        outline = kwargs.pop("outline", None)
        if outline is None:
            outline = kwargs.pop("border_color", "") or ""
        else:
            kwargs.pop("border_color", None)
        kwargs.pop("border_width", None)
        kwargs.pop("corner_radius", None)
        kwargs.pop("anchor", None)
        state = kwargs.pop("state", "normal")
        page = bg_of(master)
        super().__init__(master, bg=page, highlightthickness=0, **kwargs)
        self._fg = fg
        self._hover = hover
        self._text_color = text_color
        self._command = command
        self._state = state
        self._height = height
        self._width = int(width) if width else 0
        self._fill = fg
        self._outline = str(outline or "")
        self._label = tk.Label(
            self, text=text, bg=page, fg=text_color, font=font,
            bd=0, highlightthickness=0, cursor="hand2",
            compound="center", padx=8, pady=0,
        )
        self._label.pack(fill="both", expand=True)
        if self._width:
            self.configure(width=self._width)
        self.configure(height=height)
        self.pack_propagate(False)
        self._size = (0, 0)
        self.bind("<Configure>", self._paint)
        for widget in (self, self._label):
            widget.bind("<ButtonPress-1>", self._press)
            widget.bind("<ButtonRelease-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)
        self._apply_state()

    def _paint(self, _event=None):
        w = max(self._width, self.winfo_width(), 80)
        h = max(self._height, 36)
        if (w, h, self._fill, self._outline) == getattr(self, "_drawn", None):
            return
        self._drawn = (w, h, self._fill, self._outline)
        photo = skin.pill_photo(self, w, h, self._fill, outline=self._outline)
        if photo is not None:
            self._label.configure(image=photo, compound="center")

    def _apply_state(self):
        disabled = self._state == "disabled"
        cursor = "arrow" if disabled else "hand2"
        self.configure(cursor=cursor)
        self._label.configure(
            fg=COLORS["text_muted"] if disabled else self._text_color,
            cursor=cursor,
        )

    def _press(self, _event=None):
        if self._state == "disabled":
            return
        self._fill = self._hover
        self._drawn = None
        self._paint()

    def _click(self, _event=None):
        if self._state == "disabled":
            return
        self._fill = self._hover
        self._drawn = None
        self._paint()
        if self._command:
            self._command()

    def _enter(self, _event=None):
        from ui.fast import is_scrolling
        if self._state == "disabled" or is_scrolling():
            return
        self._fill = self._hover
        self._drawn = None
        self._paint()

    def _leave(self, _event=None):
        self._fill = self._fg
        self._drawn = None
        self._paint()

    def invoke(self):
        self._click()

    def configure(self, **kwargs):  # type: ignore[override]
        if "text" in kwargs:
            self._label.configure(text=kwargs.pop("text"))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "fg_color" in kwargs:
            self._fg = kwargs.pop("fg_color")
            self._fill = self._fg
            self._drawn = None
            self._paint()
        if "hover_color" in kwargs:
            self._hover = kwargs.pop("hover_color")
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            self._label.configure(fg=self._text_color)
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._apply_state()
        for key in ("corner_radius", "border_width", "border_color", "font", "anchor"):
            kwargs.pop(key, None)
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def cget(self, key):
        if key == "text":
            return self._label.cget("text")
        if key == "command":
            return self._command or (lambda: None)
        if key == "state":
            return self._state
        if key == "fg_color":
            return self._fg
        return super().cget(key)


class GhostButton(ModernButton):
    """כפתור משני, רקע בהיר עם טקסט כהה וקו מתאר. תמיד קריא."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["card_bg"])
        kwargs.setdefault("hover_color", COLORS["card_hover"])
        kwargs.setdefault("text_color", COLORS["text_main"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["card_border"])
        kwargs.setdefault("height", 48)
        super().__init__(master, **kwargs)


class OptionTile(tk.Frame):
    """תשובה כמו בטופס בחינה: אות בריבוע, טקסט לכל הרוחב."""

    def __init__(self, master, letter: str, text: str, command=None, accent: str | None = None):
        self._fg = COLORS.get("option_bg") or COLORS["card_bg"]
        self._hover = COLORS.get("option_hover") or COLORS["card_hover"]
        self._text_color = COLORS.get("option_text") or COLORS["text_main"]
        self._border = COLORS.get("option_border") or COLORS["card_border"]
        self._accent = accent or COLORS["primary"]
        self._command = command
        self._state = "normal"
        height = int(ADHD_CONFIG.get("option_height") or 66)
        super().__init__(
            master, bg=self._fg, cursor="hand2",
            highlightthickness=1, highlightbackground=self._border,
            highlightcolor=self._accent,
        )
        self.badge = tk.Label(
            self, text=rtl(letter), width=3,
            bg=self._accent, fg=COLORS["text_on_primary"],
            font=(ADHD_CONFIG["font_family"], font_size(18), "bold"),
        )
        self.badge.pack(side="right", fill="y")
        self.label = tk.Label(
            self, text=rtl(text), bg=self._fg, fg=self._text_color,
            font=(ADHD_CONFIG["font_family"], font_size(17), "bold"),
            anchor="e", justify="right", padx=14, pady=10, wraplength=680,
        )
        self.label.pack(side="right", fill="both", expand=True)
        self.update_idletasks()
        try:
            need = max(height, int(self.label.winfo_reqheight()) + 8)
            self.configure(height=need)
            self.pack_propagate(False)
        except tk.TclError:
            self.configure(height=height)
            self.pack_propagate(False)
        for widget in (self, self.badge, self.label):
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _click(self, _event=None):
        if self._state != "disabled" and self._command:
            self._command()

    def invoke(self):
        self._click()

    def _enter(self, _event=None):
        from ui.fast import is_scrolling, widget_alive
        if self._state == "disabled" or is_scrolling() or not widget_alive(self):
            return
        try:
            self.configure(bg=self._hover, highlightbackground=self._accent)
            if widget_alive(self.label):
                self.label.configure(bg=self._hover)
        except tk.TclError:
            pass

    def _leave(self, _event=None):
        from ui.fast import widget_alive
        if not widget_alive(self):
            return
        try:
            super().configure(bg=self._fg, highlightbackground=self._border)
            if widget_alive(self.label):
                self.label.configure(bg=self._fg)
            if widget_alive(self.badge):
                self.badge.configure(bg=self._fg if self._state == "disabled" else self._accent)
        except tk.TclError:
            pass

    def configure(self, **kwargs):  # type: ignore[override]
        if "fg_color" in kwargs:
            self._fg = kwargs.pop("fg_color")
            super().configure(bg=self._fg)
            self.label.configure(bg=self._fg)
            self.badge.configure(bg=self._fg)
        if "hover_color" in kwargs:
            self._hover = kwargs.pop("hover_color")
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            self.label.configure(fg=self._text_color)
            self.badge.configure(fg=self._text_color)
        if "border_color" in kwargs:
            self._border = kwargs.pop("border_color")
            super().configure(highlightbackground=self._border)
        if "accent" in kwargs:
            self._accent = kwargs.pop("accent")
            self.badge.configure(bg=self._accent)
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            disabled = self._state == "disabled"
            cursor = "arrow" if disabled else "hand2"
            super().configure(cursor=cursor)
            self.label.configure(cursor=cursor)
            self.badge.configure(cursor=cursor)
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def cget(self, key):
        if key == "fg_color":
            return self._fg
        if key == "state":
            return self._state
        if key == "text":
            return self.label.cget("text")
        if key == "command":
            return self._command or (lambda: None)
        return super().cget(key)


class Sidebar(tk.Frame):
    """ניווט קצר: למידה יומית למעלה, מבחנים והגדרות מתחת."""

    # פריטים ראשיים בלבד. מבחני מימ״ד/כללי נכנסים דרך «מבחנים».
    NAV_KEYS = (
        ("dashboard", "nav.home"),
        ("mistakes", "nav.mistakes"),
        ("exams", "nav.exams"),
        ("settings", "nav.settings"),
    )

    def __init__(self, master, on_nav, **kwargs):
        page = COLORS["bg"]
        super().__init__(master, bg=page, width=SIDEBAR_WIDTH, highlightthickness=0, **kwargs)
        self.on_nav = on_nav
        self.buttons: dict[str, TkButton] = {}
        self._bars: dict[str, tk.Frame] = {}
        self._rows: dict[str, tk.Frame] = {}
        self.pack_propagate(False)
        card = RoundedCard(self, fill=_c("sidebar_bg", COLORS["card_bg"]), radius=22, padx=14, pady=16)
        card.pack(fill="both", expand=True)
        ink = _c("sidebar_bg", COLORS["card_bg"])
        host = card.inner

        brand = tk.Frame(host, bg=ink)
        brand.pack(fill="x", pady=(4, 6))
        mark = tk.Label(brand, bg=ink, bd=0, highlightthickness=0)
        from core.display import dip

        logo = skin.logo_photo(self, dip(36))
        if logo is not None:
            mark.configure(image=logo)
            self._logo_photo = logo
        mark.pack(side="right", padx=(8, 0))
        tk.Label(
            brand, text=rtl("StudyApp"), bg=ink, fg=COLORS["primary"],
            font=(ADHD_CONFIG["font_family"], font_size(20), "bold"),
            anchor="e",
        ).pack(side="right", fill="x", expand=True)

        self.user_lbl = tk.Label(
            host, text="", bg=ink, fg=_c("sidebar_muted", COLORS["text_muted"]),
            font=(ADHD_CONFIG["font_family"], font_size(12)),
            anchor="e",
        )
        self.user_lbl.pack(pady=(0, 12), fill="x")

        from core.i18n import ui as i18n_ui

        for key, msg in self.NAV_KEYS:
            self._add_nav_row(host, ink, key, i18n_ui(msg))

        foot = tk.Frame(host, bg=ink)
        foot.pack(side="bottom", fill="x", pady=(8, 2))
        about = tk.Label(
            foot, text=rtl(i18n_ui("nav.about")), bg=ink,
            fg=_c("sidebar_muted", COLORS["text_muted"]),
            font=(ADHD_CONFIG["font_family"], font_size(11)),
            anchor="e", cursor="hand2",
        )
        about.pack(fill="x")
        about.bind("<Button-1>", lambda _e: self.on_nav("about"))
        credit = tk.Label(
            foot, text=rtl(f"פיתוח: {DEVELOPER_NAME}"), bg=ink,
            fg=_c("sidebar_muted", COLORS["text_muted"]),
            font=(ADHD_CONFIG["font_family"], font_size(10)),
            anchor="e",
        )
        credit.pack(fill="x", pady=(4, 0))
        self.stats_lbl = tk.Label(
            foot, text="", bg=ink, fg=_c("sidebar_muted", COLORS["text_muted"]),
            font=(ADHD_CONFIG["font_family"], font_size(12)), justify="right", anchor="e",
        )
        self.stats_lbl.pack(fill="x", pady=(2, 0))

    def _add_nav_row(self, host, ink: str, key: str, label: str) -> None:
        row = tk.Frame(host, bg=ink)
        row.pack(fill="x", pady=2)
        bar = tk.Frame(row, width=4, bg=ink)
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)
        btn = TkButton(
            row,
            text=rtl(label),
            font=(ADHD_CONFIG["font_family"], font_size(14)),
            height=44,
            fg_color=ink,
            hover_color=_c("sidebar_hover", COLORS["card_hover"]),
            text_color=_c("sidebar_fg", COLORS["text_main"]),
            anchor="e",
            command=lambda k=key: self.on_nav(k),
        )
        btn.pack(side="right", fill="x", expand=True, padx=(0, 2))
        self.buttons[key] = btn
        self._bars[key] = bar
        self._rows[key] = row

    def set_active(self, key: str) -> None:
        # מימ״ד / כללי מדגישים את «מבחנים»; אודות בלי סימון.
        active = key
        if key in {"meimad", "general_exam", "exams"}:
            active = "exams"
        if key == "about":
            active = ""
        idle = _c("sidebar_bg", COLORS["card_bg"])
        hover = _c("sidebar_hover", COLORS["card_hover"])
        fg = _c("sidebar_fg", COLORS["text_main"])
        gold = _c("sidebar_active", COLORS["primary"])
        for name, btn in self.buttons.items():
            on = name == active
            bg = hover if on else idle
            try:
                if btn.winfo_exists():
                    btn.configure(
                        fg_color=bg, hover_color=hover,
                        text_color=gold if on else fg,
                    )
                row = self._rows.get(name)
                bar = self._bars.get(name)
                if row is not None and row.winfo_exists():
                    tk.Frame.configure(row, bg=bg)
                if bar is not None and bar.winfo_exists():
                    tk.Frame.configure(bar, bg=gold if on else idle)
            except tk.TclError:
                continue

    def set_user(self, name: str, level_he: str, streak: int, level: int) -> None:
        try:
            if self.user_lbl.winfo_exists():
                self.user_lbl.configure(text=rtl(f"{name}  ·  {level_he}"))
            if self.stats_lbl.winfo_exists():
                self.stats_lbl.configure(text=rtl(f"רצף {streak} ימים"))
        except tk.TclError:
            pass


class ContextRail(tk.Frame):
    """וידג'טים מימין: ביצועים, יעד, והתראות. מעוגל כמו במקאפ."""

    def __init__(self, master, on_weak=None, **kwargs):
        super().__init__(master, bg=COLORS["bg"], width=RAIL_WIDTH, highlightthickness=0, **kwargs)
        self.on_weak = on_weak
        self.pack_propagate(False)
        card = RoundedCard(self, fill=COLORS["card_bg"], radius=20, padx=14, pady=12)
        card.pack(fill="both", expand=True)
        self._inner = card.inner

    def set_data(self, data: dict | None = None) -> None:
        data = data or {}
        for widget in self._inner.winfo_children():
            widget.destroy()
        bg = COLORS["card_bg"]
        tk.Label(
            self._inner, text=rtl("מצב עכשיו"), bg=bg, fg=COLORS["primary"],
            font=(ADHD_CONFIG["font_family"], font_size(12), "bold"), anchor="e",
        ).pack(anchor="e", pady=(0, 6))

        daily = data.get("daily") or {}
        done = int(daily.get("completed", 0) or 0)
        target = int(daily.get("target", 15) or 15)
        self._metric("יעד היום", f"{done} / {target}", first=True)
        ProgressBar(
            self._inner,
            pct=max(0, min(100, int(daily.get("completion", 0) or 0))) / 100,
            height=8,
        ).pack(fill="x", pady=(8, 4))

        streak = int(data.get("streak", 0) or 0)
        self._metric("רצף", f"{streak} ימים")
        self._metric("דיוק", f"{int(data.get('accuracy', 0) or 0)}%")

        exam_when = (data.get("exam_when") or "").strip()
        if exam_when:
            exam_label = (data.get("exam_label") or "מבחן יעד").strip()
            self._metric(exam_label, exam_when)

        weak_label = (data.get("weak_label") or "").strip()
        weak_key = data.get("weak_key")
        if weak_label:
            self._metric("לחיזוק", weak_label)
            if self.on_weak and weak_key:
                TkButton(
                    self._inner,
                    text=rtl("פתח מקצוע"),
                    font=(ADHD_CONFIG["font_family"], font_size(12)),
                    height=32,
                    fg_color=COLORS["card_bg"],
                    hover_color=COLORS["card_hover"],
                    text_color=COLORS["text_main"],
                    border_width=1,
                    border_color=COLORS["card_border"],
                    command=lambda k=weak_key: self.on_weak(k),
                ).pack(anchor="e", fill="x", pady=(6, 0))

        due = int(data.get("due", 0) or 0)
        if due:
            self._metric("לחזרה", str(due))

        self._metric("הטעויות שלי", str(int(data.get("mistakes", 0) or 0)))

        tk.Label(
            self._inner, text=rtl("דוח ביצועים שבועי"), bg=bg, fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(13), "bold"), anchor="e",
        ).pack(anchor="e", pady=(14, 8))
        week = data.get("week") or [35, 58, 22, 74, 46]
        palette = ["#7C6BC4", "#3B6FBF", "#C45A2A", "#C4841A", "#0D9488"]
        chart = tk.Frame(self._inner, bg=bg, height=64, width=110)
        chart.pack(anchor="e", pady=(0, 8))
        chart.pack_propagate(False)
        row = tk.Frame(chart, bg=bg)
        row.pack(side="right", fill="y")
        for i, value in enumerate(list(week)[:5]):
            col = tk.Frame(row, bg=bg, width=16)
            col.pack(side="right", fill="y", padx=3)
            col.pack_propagate(False)
            bar_h = max(6, int(52 * max(0, min(100, int(value))) / 100))
            tk.Frame(col, bg=palette[i % len(palette)], height=bar_h, width=12).pack(side="bottom")
            tk.Frame(col, bg=bg).pack(side="bottom", fill="both", expand=True)

        alerts = [item for item in (data.get("alerts") or []) if item]
        if alerts:
            tk.Label(
                self._inner, text=rtl("עדכונים והתראות"), bg=bg, fg=COLORS["text_main"],
                font=(ADHD_CONFIG["font_family"], font_size(13), "bold"), anchor="e",
            ).pack(anchor="e", pady=(18, 6))
            for line in alerts[:3]:
                tk.Label(
                    self._inner, text=rtl(line), bg=bg, fg=COLORS["text_muted"],
                    font=(ADHD_CONFIG["font_family"], font_size(12)),
                    anchor="e", justify="right",                     wraplength=RAIL_WIDTH - 48,
                ).pack(anchor="e", pady=2)

    def _metric(self, label: str, value: str, first: bool = False) -> None:
        tk.Label(
            self._inner, text=rtl(label), bg=COLORS["card_bg"], fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(11)), anchor="e",
        ).pack(anchor="e", pady=(2 if first else 10, 0))
        tk.Label(
            self._inner, text=rtl(value), bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(16), "bold"), anchor="e",
        ).pack(anchor="e")


class QuietFrame(tk.Frame):
    """כרטיס tk. CTkFrame הוא Canvas שנצבע מחדש בכל פיקסל גלילה."""

    def __init__(self, master, **kwargs):
        bg = kwargs.pop("fg_color", None) or COLORS["card_bg"]
        kwargs.pop("corner_radius", None)
        border = int(kwargs.pop("border_width", 1) or 0)
        bcolor = kwargs.pop("border_color", None) or COLORS["card_border"]
        super().__init__(
            master, bg=bg, highlightthickness=max(1, border),
            highlightbackground=bcolor, bd=0, **kwargs,
        )


class Page(tk.Frame):
    """עמוד בתוך אזור הגלילה. בלי Canvas של CustomTkinter."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("bg", COLORS["bg"])
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(master, **kwargs)


class ProgressBar(tk.Frame):
    """פס התקדמות אחיד לכל המסכים."""

    def __init__(self, master, pct: float = 0, color: str | None = None,
                 track: str | None = None, height: int = 8, **kwargs):
        track = track or _c("progress_track", COLORS["card_hover"])
        super().__init__(master, bg=track, height=height, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self._fill_color = color or _c("progress_fill", COLORS["primary"])
        self._fill = tk.Frame(self, bg=self._fill_color, height=height)
        self.set_pct(pct)

    def set_pct(self, pct: float) -> None:
        width = max(0.0, min(1.0, float(pct or 0)))
        self._fill.place(relx=0, rely=0, relheight=1, relwidth=width)

    def set_color(self, color: str) -> None:
        self._fill_color = color
        self._fill.configure(bg=color)


def greeting_he(now=None) -> str:
    hour = (now or datetime.datetime.now()).hour
    if 5 <= hour < 12:
        return "בוקר טוב"
    if 12 <= hour < 17:
        return "צהריים טובים"
    if 17 <= hour < 22:
        return "ערב טוב"
    return "לילה טוב"


class StudioHero(RoundedCard):
    """כרטיס ברכה רחב: שלום + התקדמות כוללת, כמו במקאפ."""

    def __init__(self, master, name: str, level_he: str, daily: dict | None = None,
                 exam_line: str = "", streak: int = 0, **kwargs):
        super().__init__(master, fill=COLORS["card_bg"], radius=20, padx=18, pady=14, **kwargs)
        bg = COLORS["card_bg"]
        muted = _c("hero_muted", COLORS["text_muted"])
        inner = self.inner
        who = (name or "").strip() or "תלמיד"

        head = tk.Frame(inner, bg=bg)
        head.pack(fill="x")
        if streak:
            tk.Label(
                head, text=rtl(f"רצף  {int(streak)}"),
                bg=COLORS["card_hover"], fg=_c("gold", COLORS["accent"]),
                font=(ADHD_CONFIG["font_family"], font_size(11), "bold"),
                padx=10, pady=4,
            ).pack(side="left", padx=(6, 0), anchor="n")
        tk.Label(
            head, text=rtl(f"{greeting_he()}, {who}"),
            bg=bg, fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(19), "bold"),
            anchor="e", justify="right",
        ).pack(side="right", fill="x", expand=True)
        tk.Label(
            inner, text=rtl(level_he), bg=bg, fg=muted,
            font=(ADHD_CONFIG["font_family"], font_size(12)),
            anchor="e", justify="right",
        ).pack(fill="x", pady=(2, 0))
        if exam_line:
            tk.Label(
                inner, text=rtl(exam_line), bg=bg, fg=muted,
                font=(ADHD_CONFIG["font_family"], font_size(11)),
                anchor="e", justify="right",
            ).pack(fill="x", pady=(2, 0))
        pct = 0
        if daily:
            pct = max(0, min(100, int(daily.get("completion", 0) or 0)))
        tk.Label(
            inner, text=rtl(f"היום  {pct}%"), bg=bg, fg=muted,
            font=(ADHD_CONFIG["font_family"], font_size(11)),
            anchor="e", justify="right",
        ).pack(fill="x", pady=(10, 4))
        RoundBar(inner, pct=pct / 100, height=10).pack(fill="x")


class CompactSubjectTile(RoundedCard):
    """כרטיס מקצוע נמוך: שם, סטטוס; לחיצה על האריח נכנסת למקצוע."""

    def __init__(self, master, subject_key: str, level_he: str, accuracy: float, total: int, on_open,
                 coming_soon: bool = False, **kwargs):
        wash = COLORS["card_hover"] if coming_soon else subject_wash(subject_key)
        super().__init__(master, fill=wash, radius=14, padx=10, pady=6, shadow=False, **kwargs)
        self._on_open = None if coming_soon else on_open
        self._coming_soon = coming_soon
        accent_color = COLORS["text_muted"] if coming_soon else subject_accent(subject_key)
        self.configure(cursor="arrow" if coming_soon else "hand2")
        inner = self.inner
        name = SUBJECTS.get(subject_key, {}).get("name") or subject_key
        letter = (name[:1] or "?").replace("\u200f", "")
        icon = SUBJECT_ICONS.get(subject_key, letter)
        pct = 0.0 if coming_soon else float(accuracy or 0)
        ink = COLORS["text_muted"] if coming_soon else COLORS["text_main"]

        top = tk.Frame(inner, bg=wash)
        top.pack(fill="x")
        badge = tk.Label(
            top, text=rtl(icon), bg=accent_color, fg=COLORS["text_on_primary"],
            font=(ADHD_CONFIG["font_family"], font_size(11)),
            padx=6, pady=4,
        )
        photo = skin.circle_photo(badge, 26, accent_color)
        if photo is not None:
            badge.configure(image=photo, compound="center", bg=wash)
        badge.pack(side="right")
        col = tk.Frame(top, bg=wash)
        col.pack(side="right", fill="x", expand=True, padx=(0, 8))
        if coming_soon:
            status = "בהכנה"
        elif total:
            status = f"{level_he}  ·  {accuracy:g}%"
        else:
            status = f"{level_he}  ·  טרם תורגל"
        title = tk.Label(
            col, text=rtl(name), bg=wash, fg=ink,
            font=(ADHD_CONFIG["font_family"], font_size(14), "bold"),
            anchor="e", justify="right",
        )
        title.pack(fill="x")
        meta = tk.Label(
            col, text=rtl(status), bg=wash, fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(10)),
            anchor="e", justify="right",
        )
        meta.pack(fill="x")

        bar = RoundBar(inner, pct=pct / 100, color=accent_color, height=5)
        bar.pack(fill="x", pady=(5, 4))

        if coming_soon:
            GhostButton(
                inner, text=rtl("בהכנה"), height=26,
                font=(ADHD_CONFIG["font_family"], font_size(12), "bold"),
                state="disabled",
            ).pack(fill="x")
        else:
            for widget in (self, inner, top, col, title, meta, badge, bar):
                widget.bind("<Button-1>", self._click)

    def _click(self, _event=None):
        if self._on_open:
            self._on_open()

    def _enter(self, _event=None):
        return

    def _leave(self, _event=None):
        return


class DailyBanner(tk.Frame):
    def __init__(self, master, daily: dict, level_he: str, **kwargs):
        bg = _c("hero_bg", COLORS["banner"])
        fg = _c("hero_fg", COLORS["banner_text"])
        super().__init__(master, bg=bg, highlightthickness=0, **kwargs)
        tk.Frame(self, bg=COLORS["primary"], height=4).pack(fill="x")
        inner = tk.Frame(self, bg=bg)
        inner.pack(fill="x", padx=18, pady=14)
        tk.Label(
            inner,
            text=rtl(f"היום  {daily.get('completed', 0)}/{daily.get('target', 15)} שאלות  ·  רמה {level_he}"),
            font=(ADHD_CONFIG["font_family"], font_size(15), "bold"),
            bg=bg, fg=fg,
            anchor="e", justify="right",
        ).pack(fill="x")
        ProgressBar(
            inner,
            pct=max(0, min(100, int(daily.get("completion", 0) or 0))) / 100,
            color=_c("progress_fill", COLORS["primary"]),
            track=_c("progress_track", COLORS["card_hover"]),
            height=7,
        ).pack(fill="x", pady=(10, 0))


class StatChip(tk.Frame):
    def __init__(self, master, label: str, value: str, **kwargs):
        super().__init__(master, bg=COLORS["card_bg"], highlightthickness=1,
                         highlightbackground=COLORS["card_border"], **kwargs)
        tk.Frame(self, bg=COLORS["primary"], height=3).pack(fill="x")
        tk.Label(self, text=rtl(label), font=(ADHD_CONFIG["font_family"], font_size(12)),
                 bg=COLORS["card_bg"], fg=COLORS["text_muted"], anchor="e").pack(anchor="e", padx=14, pady=(10, 0))
        tk.Label(self, text=rtl(value), font=(ADHD_CONFIG["font_family"], font_size(22), "bold"),
                 bg=COLORS["card_bg"], fg=COLORS["text_main"], anchor="e").pack(anchor="e", padx=14, pady=(0, 12))


class SubjectCard(RoundedCard):
    """כרטיס מקצוע במסך הרשימה, אותו סגנון כמו בדשבורד."""

    def __init__(self, master, subject_key: str, status: str, accuracy: int | None, on_open,
                 coming_soon: bool = False, **kwargs):
        info = SUBJECTS.get(subject_key, {})
        wash = COLORS["card_hover"] if coming_soon else subject_wash(subject_key)
        super().__init__(master, fill=wash, radius=22, padx=18, pady=16, **kwargs)
        self._on_open = None if coming_soon else on_open
        self._coming_soon = coming_soon
        accent_color = COLORS["text_muted"] if coming_soon else subject_accent(subject_key)
        self.configure(cursor="arrow" if coming_soon else "hand2")
        inner = self.inner
        name = info.get("name", subject_key)
        icon = SUBJECT_ICONS.get(subject_key, (name[:1] or "?"))
        pct = 0.0 if coming_soon else float(accuracy or 0)
        ink = COLORS["text_muted"] if coming_soon else COLORS["text_main"]

        top = tk.Frame(inner, bg=wash)
        top.pack(fill="x")
        badge = tk.Label(
            top, text=rtl(icon), bg=accent_color, fg=COLORS["text_on_primary"],
            font=(ADHD_CONFIG["font_family"], font_size(16)), padx=10, pady=8,
        )
        photo = skin.circle_photo(badge, 44, accent_color)
        if photo is not None:
            badge.configure(image=photo, compound="center", bg=wash)
        badge.pack(side="right")
        col = tk.Frame(top, bg=wash)
        col.pack(side="right", fill="x", expand=True, padx=(0, 10))
        tk.Label(
            col, text=rtl(name), bg=wash, fg=ink,
            font=(ADHD_CONFIG["font_family"], font_size(18), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x")
        tk.Label(
            col, text=rtl("בהכנה" if coming_soon else status), bg=wash, fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(13)),
            anchor="e", justify="right",
        ).pack(fill="x", pady=(4, 0))
        RoundBar(inner, pct=pct / 100, color=accent_color, height=10).pack(fill="x", pady=(12, 10))
        if coming_soon:
            GhostButton(inner, text=rtl("בהכנה"), height=40, state="disabled").pack(fill="x")
        else:
            ModernButton(
                inner, text=rtl("המשך לתרגל"), height=40,
                fg_color=accent_color, hover_color=accent_color,
                text_color=COLORS["text_on_primary"],
                command=self._click,
            ).pack(fill="x")
            for widget in (self, inner, top, badge):
                widget.bind("<Button-1>", self._click)

    def _click(self, _event=None):
        if self._on_open:
            self._on_open()

    def _enter(self, _event=None):
        return

    def _leave(self, _event=None):
        return


class StartLessonCard(RoundedCard):
    """הצעד הבא: כרטיס לבן מעוגל עם כפתור גלולה."""

    def __init__(self, master, kicker_text: str, title: str, detail: str, button: str, command, **kwargs):
        super().__init__(master, fill=COLORS["card_bg"], radius=18, padx=16, pady=12, **kwargs)
        bg = COLORS["card_bg"]
        inner = self.inner
        tk.Label(
            inner, text=rtl(kicker_text), bg=bg, fg=_c("gold", COLORS["accent"]),
            font=(ADHD_CONFIG["font_family"], font_size(11), "bold"),
            anchor="e",
        ).pack(fill="x")
        tk.Label(
            inner, text=rtl(title), bg=bg, fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(18), "bold"),
            anchor="e", justify="right", wraplength=PAGE_WIDTH - 80,
        ).pack(fill="x", pady=(4, 4))
        if detail:
            tk.Label(
                inner, text=rtl(detail), bg=bg, fg=COLORS["text_muted"],
                font=(ADHD_CONFIG["font_family"], font_size(12)),
                anchor="e", justify="right", wraplength=PAGE_WIDTH - 80,
            ).pack(fill="x", pady=(0, 10))
        ModernButton(
            inner, text=rtl(button), height=38,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color=COLORS["text_on_primary"],
            command=command,
        ).pack(fill="x")


def empty_state(parent, title: str, detail: str):
    """מצב ריק מעוצב, לא שורה אפורה באמצע המסך."""
    box, inner = make_card(parent, pady=22, gold_top=True)
    tk.Label(
        inner, text=rtl(title), bg=COLORS["card_bg"], fg=COLORS["text_main"],
        font=(ADHD_CONFIG["font_family"], font_size(18), "bold"),
        anchor="e", justify="right",
    ).pack(anchor="e")
    tk.Label(
        inner, text=rtl(detail), bg=COLORS["card_bg"], fg=COLORS["text_muted"],
        font=(ADHD_CONFIG["font_family"], font_size(14)),
        anchor="e", justify="right", wraplength=PAGE_WIDTH - 80,
    ).pack(anchor="e", pady=(6, 0))
    return box


def make_card(parent, *, accent: str | None = None, padx: int = 20, pady: int = 16, thick: int = 1,
              gold_top: bool = False, fill: str | None = None, shadow: bool = True,
              radius: int = CARD_RADIUS):
    """כרטיס מעוגל אחיד, מחזיר (מעטפת, פנים)."""
    card = RoundedCard(
        parent, fill=fill or COLORS["card_bg"], radius=radius, shadow=shadow, padx=padx, pady=pady,
    )
    if gold_top:
        tk.Frame(card.inner, bg=accent or COLORS["primary"], height=3).pack(fill="x", pady=(0, 8))
    return card, card.inner


def gold_tick(parent, width: int = 56):
    wrap = tk.Frame(parent, bg=bg_of(parent))
    bar = tk.Label(wrap, bg=bg_of(parent), bd=0, highlightthickness=0)
    photo = skin.bar_photo(bar, width, 5, 1.0, COLORS["primary"], COLORS["primary"])
    if photo is not None:
        bar.configure(image=photo)
        wrap._tick_photo = photo
        bar.pack(side="right")
    else:
        tk.Frame(wrap, bg=COLORS["primary"], height=3, width=width).pack(side="right")
    return wrap


def kicker(parent, text: str, bg: str | None = None):
    return tk.Label(
        parent,
        text=rtl(text),
        font=(ADHD_CONFIG["font_family"], font_size(12), "bold"),
        fg=COLORS["primary"],
        bg=bg or bg_of(parent),
        justify="right",
        anchor="e",
    )


def number_pill(parent, text: str):
    bg = _c("hero_bg", COLORS["banner"])
    fg = _c("hero_fg", COLORS["banner_text"])
    wrap = tk.Frame(parent, bg=bg)
    tk.Label(
        wrap, text=rtl(text), bg=bg, fg=fg,
        font=(ADHD_CONFIG["font_family"], font_size(13), "bold"),
        padx=12, pady=5,
    ).pack()
    return wrap


def section_label(parent, text: str):
    wrap = tk.Frame(parent, bg=bg_of(parent))
    wrap.pack(anchor="e", fill="x", pady=(16, 8))
    tk.Frame(wrap, bg=COLORS["primary"], height=2, width=36).pack(
        side="right", pady=(7, 0), padx=(8, 0),
    )
    tk.Label(
        wrap, text=rtl(text), bg=bg_of(parent), fg=COLORS["text_muted"],
        font=(ADHD_CONFIG["font_family"], font_size(13), "bold"),
        anchor="e",
    ).pack(side="right")
    return wrap


def page_header(parent, title: str, subtitle: str | None = None, size: int = 26):
    heading(parent, title, size).pack(anchor="e", pady=(4, 4))
    gold_tick(parent).pack(anchor="e", pady=(0, 8 if subtitle else 20))
    if subtitle:
        body(parent, subtitle, muted=True, wrap=PAGE_WIDTH - 40).pack(anchor="e", pady=(0, 22))


def themed_entry(master, textvariable, **kwargs):
    kwargs.setdefault("relief", "flat")
    kwargs.setdefault("borderwidth", 0)
    kwargs.setdefault("highlightthickness", 1)
    kwargs.setdefault("highlightbackground", _c("input_border", COLORS["card_border"]))
    kwargs.setdefault("highlightcolor", COLORS["primary"])
    kwargs.setdefault("bg", _c("input_bg", COLORS["card_bg"]))
    kwargs.setdefault("fg", _c("input_fg", COLORS["text_main"]))
    kwargs.setdefault("insertbackground", _c("input_fg", COLORS["text_main"]))
    kwargs.setdefault("font", (ADHD_CONFIG["font_family"], font_size(14)))
    return tk.Entry(master, textvariable=textvariable, **kwargs)


def rounded_field(parent, variable, **kwargs):
    """שדה טקסט בתוך גלולה מעוגלת, בלי תיבה מרובעת."""
    well = _c("option_bg", COLORS["card_hover"])
    page = bg_of(parent)
    wrap = tk.Frame(parent, bg=page, highlightthickness=0, height=48)
    art = tk.Label(wrap, bg=page, bd=0, highlightthickness=0)
    art.place(x=0, y=0, relwidth=1, relheight=1)
    kwargs.setdefault("bg", well)
    kwargs.setdefault("highlightthickness", 0)
    kwargs.setdefault("highlightbackground", well)
    entry = themed_entry(wrap, variable, **kwargs)
    entry.pack(fill="both", expand=True, padx=16, pady=12)

    def paint(_event=None):
        w, h = int(wrap.winfo_width()), int(wrap.winfo_height())
        if w < 36 or h < 24:
            return
        if getattr(wrap, "_drawn", None) == (w, h):
            return
        wrap._drawn = (w, h)
        photo = skin.pill_photo(
            wrap, w, h, well, outline=_c("input_border", COLORS["card_border"]),
        )
        if photo is not None:
            art.configure(image=photo)

    wrap.bind("<Configure>", paint)
    return wrap


def bg_of(master) -> str:
    """צבע הרקע של ההורה, כדי שאפשר יהיה לשים tk.Label גם בתוך ווידג'ט CTk."""
    for attr in ("fg_color", "bg"):
        try:
            value = master.cget(attr)
        except Exception:
            continue
        if isinstance(value, (list, tuple)) and value:
            value = value[1] if ctk.get_appearance_mode() == "Dark" else value[0]
        if isinstance(value, str) and value.startswith("#"):
            return value
    return COLORS["bg"]


# כותרות וטקסט הם רק תוויות סטטיות. CTkLabel בונה Canvas לכל אחת ומייקר
# כל מסך בעשרות מילישניות, tk.Label נראה זהה כאן ועולה כמעט כלום.
def heading(parent, text, size=None, fg=None):
    return tk.Label(
        parent,
        text=rtl(text),
        font=(ADHD_CONFIG["font_family"], font_size(size or ADHD_CONFIG["header_size"]), "bold"),
        fg=fg or COLORS["text_main"],
        bg=bg_of(parent),
        justify="right",
        anchor="e",
        wraplength=PAGE_WIDTH - 40,
    )


def body(parent, text, muted=False, size=None, wrap=None, fg=None):
    color = fg if fg is not None else (COLORS["text_muted"] if muted else COLORS["text_main"])
    return tk.Label(
        parent,
        text=rtl(text),
        font=(ADHD_CONFIG["font_family"], font_size(size or ADHD_CONFIG["body_size"])),
        fg=color,
        bg=bg_of(parent),
        justify="right",
        anchor="e",
        wraplength=wrap if wrap is not None else PAGE_WIDTH - 40,
    )
