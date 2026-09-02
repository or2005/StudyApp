import datetime
import tkinter as tk

from core.config import ADHD_CONFIG, COLORS, FONT_STEPS, VERSION, rtl
from ui.fast import fast_label
from ui.widgets import GhostButton, ModernButton, font_size, make_card, page_header, rounded_field, Page


class SettingsScreen(Page):
    def __init__(self, master, storage, focus_on, on_focus, on_reset, on_theme, appearance="Light",
                 on_font=None, on_export=None, on_import=None, on_logs=None, on_exam_date=None,
                 on_tts=None, tts_on=False, on_clear_reports=None,
                 on_check_update=None, on_install_update=None, on_pick_update=None,
                 on_auto_update=None, update_status="", pending_update=None,
                 on_telemetry=None, telemetry_on=False,
                 profile_name="", profile_names=None,
                 on_switch_profile=None, on_add_profile=None, on_delete_profile=None,
                 on_parent_report=None, on_question_editor=None, on_open_data=None,
                 on_toggle_autostart=None, autostart_on=False,
                 on_toggle_reminder=None, reminder_on=False, reminder_time="17:00",
                 on_save_reminder_time=None,                  on_install_shortcuts=None, on_test_notify=None, on_secret=None):
        super().__init__(master)
        self.storage = storage
        self.on_exam_date = on_exam_date
        self._secret_taps = 0
        self.on_secret = on_secret
        self.on_switch_profile = on_switch_profile
        self.on_add_profile = on_add_profile
        self.on_delete_profile = on_delete_profile

        page_header(self, "הגדרות", "רק מה שמשפיע על הלמידה.")

        look = self._card("תצוגה", "בהיר או כהה, גודל טקסט, ומיקוד בלי רעש.")
        self._chips(look, (
            ("בהיר", appearance == "Light", lambda: on_theme("Light")),
            ("כהה", appearance == "Dark", lambda: on_theme("Dark")),
        ))
        current_font = storage.get_pref("font_label", "רגיל")
        self._chips(look, (
            (label, label == current_font, lambda lb=label: on_font(lb) if on_font else None)
            for label in FONT_STEPS
        ), width=88)
        self._toggle(look, "מיקוד: דולק" if focus_on else "מיקוד: כבוי", focus_on, on_focus)

        learn = self._card("למידה", "הקראה בקול, ותאריך מבחן ליעד היומי.")
        self._toggle(learn, "הקראה: דולקת" if tts_on else "הקראה: כבויה", tts_on, on_tts)
        target = storage.get_exam_date()
        days = storage.days_to_exam()
        if days is None:
            note = "לא חובה. אם ממלאים, היעד היומי מתאים לזמן שנשאר."
        else:
            note = f"{target.get('label') or 'מבחן'}  ·  {target.get('date')}  ·  בעוד {days} ימים"
        fast_label(learn, note, size=13, muted=True, bg=COLORS["card_bg"]).pack(fill="x", pady=(12, 0))
        row = tk.Frame(learn, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=(10, 0))
        self.date_var = tk.StringVar(value=target.get("date") or datetime.date.today().isoformat())
        self.label_var = tk.StringVar(value=target.get("label") or "מימ״ד")
        self._field(row, self.date_var, width=14, justify="center")
        self._field(row, self.label_var, width=16, justify="right")
        ModernButton(row, text=rtl("שמירה"), height=42, width=110, command=self._save_date).pack(
            side="right", padx=6,
        )
        self.date_err = fast_label(learn, "", size=12, muted=True, bg=COLORS["card_bg"])
        self.date_err.pack(anchor="e")

        data = self._card("נתונים", f"פרופיל פעיל: {profile_name or 'תלמיד'}. גיבוי לקובץ, בלי רשת.")
        row = tk.Frame(data, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=(10, 0))
        ModernButton(row, text=rtl("החלפת פרופיל"), height=42, width=150,
                     command=on_switch_profile).pack(side="right", padx=6)
        GhostButton(row, text=rtl("פרופיל חדש"), height=42, width=130,
                    command=on_add_profile).pack(side="right", padx=6)
        if len(profile_names or []) > 1:
            GhostButton(row, text=rtl("מחיקת פרופיל"), height=42, width=140,
                        command=on_delete_profile).pack(side="right", padx=6)
        row = tk.Frame(data, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=(10, 0))
        ModernButton(row, text=rtl("ייצוא גיבוי"), height=42, width=140,
                     command=on_export).pack(side="right", padx=6)
        GhostButton(row, text=rtl("טעינת גיבוי"), height=42, width=140,
                    command=on_import).pack(side="right", padx=6)

        danger = self._card("התחלה מחדש", "מוחק הרשמה, אבחון והתקדמות מהמחשב הזה.", danger=True)
        ModernButton(
            danger, text=rtl("מחיקת כל הנתונים"), height=46,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color=COLORS.get("danger_text") or "#FFFFFF",
            command=on_reset,
        ).pack(fill="x", pady=(10, 0))

        ver = fast_label(self, f"גרסה {VERSION}", size=12, muted=True)
        ver.pack(anchor="e", pady=12)
        if on_secret:
            ver.bind("<Button-1>", lambda _e: self._tap_secret())

    def _card(self, title, subtitle, danger=False):
        card, inner = make_card(
            self, padx=20, pady=18,
            accent=COLORS["danger"] if danger else None,
            gold_top=danger,
        )
        card.pack(fill="x", pady=(0, 14))
        tk.Label(
            inner, text=rtl(title), bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(18), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x")
        fast_label(inner, subtitle, size=13, muted=True, bg=COLORS["card_bg"], wrap=740).pack(
            fill="x", pady=(4, 0),
        )
        return inner

    def _chips(self, parent, items, width=110):
        row = tk.Frame(parent, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=(12, 0))
        for label, active, command in items:
            if active:
                ModernButton(
                    row, text=rtl(label), height=40, width=width, command=command,
                ).pack(side="right", padx=6)
            else:
                GhostButton(
                    row, text=rtl(label), height=40, width=width, command=command,
                ).pack(side="right", padx=6)

    def _toggle(self, parent, label, on, command):
        if on:
            ModernButton(parent, text=rtl(label), height=44, command=command).pack(fill="x", pady=(12, 0))
        else:
            GhostButton(parent, text=rtl(label), height=44, command=command).pack(fill="x", pady=(12, 0))

    def _field(self, parent, variable, **kwargs):
        rounded_field(parent, variable, **kwargs).pack(side="right", padx=6)

    def _tap_secret(self):
        self._secret_taps += 1
        if self._secret_taps >= 5 and self.on_secret:
            self._secret_taps = 0
            self.on_secret()

    def _save_date(self):
        raw = self.date_var.get().strip()
        try:
            datetime.date.fromisoformat(raw)
        except ValueError:
            self.date_err.configure(text=rtl("תאריך לא תקין. הפורמט: 2026-06-01"))
            return
        if self.on_exam_date:
            self.on_exam_date(raw, self.label_var.get().strip())
