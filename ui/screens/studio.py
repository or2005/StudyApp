"""חדר מפתח: מסך שחור-ירוק, בעברית, עם מידע וכלים."""
from __future__ import annotations

import tkinter as tk

from core import studio_brief, studio_gate
from core.config import ALL_SUBJECTS, VERSION, subject_label

BG = "#000000"
PANEL = "#020802"
GREEN = "#39FF14"
DIM = "#1C7A28"
GLOW = "#A8FF8A"
AMBER = "#FFB000"
RED = "#FF5555"
FONT = ("Segoe UI", 12)
FONT_SM = ("Segoe UI", 11)
FONT_LG = ("Segoe UI", 16, "bold")


class StudioScreen(tk.Frame):
    def __init__(self, master, unlocked=False, on_auth=None, on_exit=None, actions=None):
        super().__init__(master, bg=BG, highlightthickness=0)
        self.on_auth = on_auth
        self.on_exit = on_exit
        self.actions = actions or {}
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.info_box = None
        self.out = None
        if unlocked:
            self._desk()
        else:
            self._gate()

    def _font(self, size=12, bold=False):
        return ("Segoe UI", size, "bold" if bold else "normal")

    def _line(self, parent, text, color=GREEN, size=12, bold=False, anchor="e"):
        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg") or BG,
            fg=color,
            font=self._font(size, bold),
            anchor=anchor,
            justify="right",
        )

    def _btn(self, parent, text, command, color=GREEN):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=BG,
            fg=color,
            activebackground=PANEL,
            activeforeground=GLOW,
            font=FONT_SM,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=DIM,
            highlightcolor=GREEN,
            anchor="e",
            padx=10,
            pady=4,
            cursor="hand2",
        )
        btn.pack(fill="x", pady=2)
        return btn

    def _banner(self, parent, title):
        self._line(parent, "חדר מפתח  ·  StudyApp", GLOW, 16, True).pack(anchor="e")
        self._line(parent, f"גרסה {VERSION}", DIM, 11).pack(anchor="e", pady=(0, 8))
        self._line(parent, title, AMBER, 13, True).pack(anchor="e")
        self._line(parent, "─" * 42, DIM, 11).pack(anchor="e", pady=(0, 10))

    def _gate(self):
        box = tk.Frame(self, bg=BG)
        box.pack(fill="both", expand=True, padx=28, pady=24)
        self._banner(box, "כניסה למפתח מורשה בלבד")
        self._line(box, "שם משתמש", DIM).pack(anchor="e", pady=(8, 2))
        self._field(box, self.user_var)
        self._line(box, "סיסמה", DIM).pack(anchor="e", pady=(8, 2))
        self._field(box, self.pass_var, secret=True)
        self._status = self._line(box, "ממתינים לכניסה", DIM, 11)
        self._status.pack(anchor="e", pady=(14, 8))
        self._btn(box, "כניסה", self._try_login, GLOW)
        self._btn(box, "חזרה לתוכנה", self._leave, DIM)
        self.user_var.set("ordadshev")

    def _field(self, parent, variable, secret=False):
        row = tk.Frame(parent, bg=BG)
        row.pack(anchor="e", pady=2)
        entry = tk.Entry(
            row,
            textvariable=variable,
            bg=PANEL,
            fg=GREEN,
            insertbackground=GREEN,
            font=FONT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=DIM,
            highlightcolor=GREEN,
            width=28,
            justify="right",
            show="*" if secret else "",
        )
        entry.pack(anchor="e")
        if secret:
            entry.bind("<Return>", lambda _e: self._try_login())

    def _try_login(self):
        if studio_gate.check(self.user_var.get(), self.pass_var.get()):
            if self.on_auth:
                self.on_auth(True)
            for child in self.winfo_children():
                child.destroy()
            self._desk()
            return
        self._status.configure(text="הסיסמה לא נכונה", fg=RED)
        self.pass_var.set("")

    def _desk(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=16, pady=12)
        self._banner(wrap, "כלים, גיבויים ומידע על התוכנה")

        body = tk.Frame(wrap, bg=BG)
        body.pack(fill="both", expand=True)

        info = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=DIM, width=280)
        info.pack(side="right", fill="y", padx=(10, 0))
        info.pack_propagate(False)
        self._line(info, "עמודת מידע", AMBER, 12, True).pack(anchor="e", padx=10, pady=(8, 4))
        self.info_box = tk.Text(
            info,
            bg=PANEL,
            fg=GREEN,
            insertbackground=GREEN,
            font=FONT_SM,
            relief="flat",
            wrap="word",
            highlightthickness=0,
            padx=8,
            pady=6,
            width=28,
        )
        self.info_box.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.info_box.tag_configure("rtl", justify="right")
        self._btn(info, "רענון המידע", self._refresh_info, DIM)

        menu = tk.Frame(body, bg=BG, width=300)
        menu.pack(side="right", fill="y")
        menu.pack_propagate(False)
        self._fill_menu(menu)

        right = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=DIM)
        right.pack(side="left", fill="both", expand=True)
        self._line(right, "מה קרה עכשיו", AMBER, 12, True).pack(anchor="e", padx=8, pady=(6, 0))
        self.out = tk.Text(
            right,
            bg=PANEL,
            fg=GREEN,
            insertbackground=GREEN,
            font=FONT_SM,
            relief="flat",
            wrap="word",
            highlightthickness=0,
            padx=10,
            pady=8,
        )
        self.out.pack(fill="both", expand=True, padx=4, pady=4)
        self.out.tag_configure("rtl", justify="right")
        self._write(
            "כאן מופיע פלט של הפעולות.\n\n"
            "שמירת קבצי תוכנה (StudyApp Files) = כל קוד המקור.\n"
            "אם הכל נמחק: מורידים, מחלצים את התיקייה, ופותחים אותה ב-VS Code.\n"
            "אחר כך: python -m venv .venv , pip install -r requirements.txt , python main.py\n\n"
            "חבילת דיסק און קי = התקנה לתלמיד. זה לא הקוד לעריכה."
        )
        self._refresh_info()

    def _fill_menu(self, menu):
        canvas = tk.Canvas(menu, bg=BG, highlightthickness=0, width=300)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        window = canvas.create_window((0, 0), window=inner, anchor="nw", width=300)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        canvas.pack(fill="both", expand=True)

        def _wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(widget):
            widget.bind("<MouseWheel>", _wheel)
            for child in widget.winfo_children():
                _bind_wheel(child)

        self._line(inner, "גיבוי התוכנה", AMBER, 12, True).pack(anchor="e", pady=(0, 4))
        self._btn(inner, "שמירת קבצי תוכנה (לקוד ול-VS Code)", lambda: self._run("pack_files"), GLOW)
        self._btn(inner, "חבילת דיסק און קי (לתלמיד)", lambda: self._run("pack_usb"), GLOW)
        self._btn(inner, "פתיחת תיקיית הקוד", lambda: self._run("project"), GREEN)
        self._btn(inner, "פתיחה ב-VS Code", lambda: self._run("vscode"), GREEN)

        self._line(inner, "מאגר ועריכה", AMBER, 12, True).pack(anchor="e", pady=(12, 4))
        self._btn(inner, "עורך שאלות", lambda: self._run("editor"), GREEN)
        self._btn(inner, "תיקיית קבצי השאלות", lambda: self._run("json"), GREEN)
        self._btn(inner, "סיכום מאגר לפי מקצוע", self._census, GREEN)
        self._btn(inner, "רענון מאגר (ניקוי מטמון)", lambda: self._run("cache"), DIM)

        self._line(inner, "נתוני תלמיד", AMBER, 12, True).pack(anchor="e", pady=(12, 4))
        self._btn(inner, "תיקיית הנתונים במחשב", lambda: self._run("data"), GREEN)
        self._btn(inner, "גיבוי נתוני תלמיד", lambda: self._run("backup"), GREEN)
        self._btn(inner, "טעינת גיבוי תלמיד", lambda: self._run("restore"), GREEN)
        self._btn(inner, "דוח להורה", lambda: self._run("report"), GREEN)

        self._line(inner, "בדיקות מפתח", AMBER, 12, True).pack(anchor="e", pady=(12, 4))
        self._btn(inner, "העתק סיכום למפתח (להדבקה ב-AI)", self._brief, GLOW)
        self._btn(inner, "דלג על אבחון", lambda: self._run("skip_diag"), AMBER)
        self._btn(inner, "פתח מבחנים בפרופיל הזה", lambda: self._run("unlock"), AMBER)
        self._btn(inner, "בדיקת עדכון", lambda: self._run("update"), GREEN)
        self._btn(inner, "יומן אחרון", self._log, GREEN)
        self._btn(inner, "תיקיית יומן", lambda: self._run("logs"), GREEN)
        self._btn(inner, "בניית התקנה לחלונות", lambda: self._run("build"), DIM)

        self._line(inner, "מעבר למקצוע", AMBER, 12, True).pack(anchor="e", pady=(12, 4))
        for key in ALL_SUBJECTS:
            self._btn(
                inner,
                subject_label(key),
                lambda k=key: self._run("jump", k),
                DIM,
            )
        self._btn(inner, "חזרה לתוכנה", self._leave, RED)
        _bind_wheel(canvas)
        _bind_wheel(inner)

    def _write(self, text: str):
        if self.out is None:
            return
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text, "rtl")
        self.out.configure(state="disabled")

    def _refresh_info(self):
        fn = self.actions.get("info")
        text = fn() if fn else studio_brief.info_text()
        if self.info_box is None:
            return
        self.info_box.configure(state="normal")
        self.info_box.delete("1.0", "end")
        self.info_box.insert("1.0", text, "rtl")
        self.info_box.configure(state="disabled")

    def _brief(self):
        text = ""
        fn = self.actions.get("brief")
        if fn:
            text = fn() or ""
        shown = text or "אין סיכום."
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._write(shown + "\n\nהועתק ללוח. אפשר להדביק בצ׳אט.")
        except tk.TclError:
            self._write(shown)

    def _census(self):
        self._write(studio_brief.census_text())
        self._refresh_info()

    def _log(self):
        fn = self.actions.get("tail")
        self._write(fn() if fn else "אין יומן.")

    def _run(self, name: str, *args):
        fn = self.actions.get(name)
        if not fn:
            self._write(f"הפעולה {name} לא מחוברת.")
            return
        result = fn(*args) if args else fn()
        if result:
            self._write(str(result))
        self._refresh_info()

    def _leave(self):
        if self.on_exit:
            self.on_exit()
