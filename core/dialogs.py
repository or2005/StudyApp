from tkinter import messagebox

from core.config import rtl
from core.i18n import ui as i18n_ui


def info(title: str, text: str) -> None:
    messagebox.showinfo(rtl(title), rtl(text))


def error(title: str, text: str) -> None:
    messagebox.showerror(rtl(title), rtl(text))


def confirm(title: str, text: str) -> bool:
    return bool(messagebox.askyesno(rtl(title), rtl(text)))


def cancel_label() -> str:
    return i18n_ui("btn.cancel")


def choose(title: str, text: str, options: list[str], parent=None) -> str | None:
    """בחירה מרשימה קצרה. מחזיר את הטקסט שנבחר, או None אם בוטל."""
    import tkinter as tk

    from core.config import ADHD_CONFIG, COLORS
    from ui.fast import TkButton

    root = parent or tk._get_default_root()
    win = tk.Toplevel(root)
    win.title(title)
    win.configure(bg=COLORS["card_bg"])
    win.resizable(False, False)
    win.transient(root)

    result: dict[str, str | None] = {"value": None}

    tk.Label(
        win, text=rtl(text), bg=COLORS["card_bg"], fg=COLORS["text_main"],
        font=(ADHD_CONFIG["font_family"], 15, "bold"), anchor="e", justify="right", wraplength=440,
    ).pack(fill="x", padx=20, pady=(18, 12))

    def pick(value: str | None):
        result["value"] = value
        win.destroy()

    for option in options:
        TkButton(
            win, text=rtl(option), command=lambda o=option: pick(o),
            fg_color=COLORS["option_bg"], hover_color=COLORS["option_hover"],
            text_color=COLORS["option_text"],
            border_width=1, border_color=COLORS.get("option_border") or COLORS["card_border"],
            anchor="e", height=46,
            font=(ADHD_CONFIG["font_family"], 13, "bold"),
        ).pack(fill="x", padx=20, pady=3)

    TkButton(
        win, text=rtl(cancel_label()), command=lambda: pick(None),
        fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"],
        text_color=COLORS["text_muted"],
        border_width=1, border_color=COLORS["card_border"],
        height=42, font=(ADHD_CONFIG["font_family"], 12),
    ).pack(fill="x", padx=20, pady=(10, 18))

    win.update_idletasks()
    try:
        x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_rooty() + 120
        win.geometry(f"+{max(0, x)}+{max(0, y)}")
    except Exception:
        pass
    try:
        win.grab_set()
        win.wait_window()
    except Exception:
        pass
    return result["value"]


def ask_text(title: str, text: str, initial: str = "", parent=None) -> str | None:
    """שדה טקסט קצר. מחזיר את המחרוזת, או None אם בוטל."""
    import tkinter as tk

    from core.config import ADHD_CONFIG, COLORS
    from ui.fast import TkButton
    from ui.widgets import themed_entry

    root = parent or tk._get_default_root()
    win = tk.Toplevel(root)
    win.title(title)
    win.configure(bg=COLORS["card_bg"])
    win.resizable(False, False)
    win.transient(root)

    result: dict[str, str | None] = {"value": None}
    var = tk.StringVar(value=initial or "")

    tk.Label(
        win, text=rtl(text), bg=COLORS["card_bg"], fg=COLORS["text_main"],
        font=(ADHD_CONFIG["font_family"], 15, "bold"), anchor="e", justify="right", wraplength=440,
    ).pack(fill="x", padx=20, pady=(18, 12))

    entry = themed_entry(win, var, width=36, justify="right")
    entry.pack(fill="x", padx=20, ipady=7)
    entry.focus_set()
    try:
        entry.icursor("end")
    except Exception:
        pass

    def submit(_event=None):
        result["value"] = var.get().strip()
        win.destroy()

    def cancel():
        result["value"] = None
        win.destroy()

    row = tk.Frame(win, bg=COLORS["card_bg"])
    row.pack(fill="x", padx=20, pady=(12, 18))
    TkButton(
        row, text=rtl("אישור"), command=submit,
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color=COLORS["text_on_primary"],
        height=42, font=(ADHD_CONFIG["font_family"], 13, "bold"),
    ).pack(side="right", padx=4)
    TkButton(
        row, text=rtl("ביטול"), command=cancel,
        fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"],
        text_color=COLORS["text_muted"],
        border_width=1, border_color=COLORS["card_border"],
        height=42, font=(ADHD_CONFIG["font_family"], 12),
    ).pack(side="right", padx=4)
    win.bind("<Return>", submit)
    win.bind("<Escape>", lambda _e: cancel())

    win.update_idletasks()
    try:
        x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_rooty() + 120
        win.geometry(f"+{max(0, x)}+{max(0, y)}")
    except Exception:
        pass
    try:
        win.grab_set()
        win.wait_window()
    except Exception:
        pass
    return result["value"]
