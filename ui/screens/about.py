import webbrowser
from urllib.parse import quote

import tkinter as tk

from core import applog, dialogs
from core.config import (
    ADHD_CONFIG,
    APP_NAME,
    COLORS,
    CONTACT_EMAIL,
    DEVELOPER_NAME,
    DEVELOPER_NAME_EN,
    ELECTIVE_SUBJECTS,
    HOME_SUBJECTS,
    SUBJECTS,
    VERSION,
    copyright_he,
    rtl,
)
from core.storage import DATA_DIR
from ui.fast import FastText, fast_label
from ui.widgets import GhostButton, ModernButton, RoundedCard, font_size, make_card, page_header, Page


class AboutScreen(Page):
    def __init__(self, master, on_secret=None):
        super().__init__(master)
        self.on_secret = on_secret
        self._secret_taps = 0
        self._hero()
        self._chips()
        self._developer()
        self._what()
        self._howto()
        self._keys()
        self._privacy()
        self._disclaimer()
        self._terms()
        self._footer()

    def _hero(self):
        page_header(self, "אודות", "מי עומד מאחורי התוכנה, ואיך היא עובדת אצלכם במחשב.")
        card = RoundedCard(self, fill=COLORS["card_bg"], radius=14, padx=20, pady=18)
        card.pack(fill="x", pady=(0, 12))
        inner = card.inner
        ink = COLORS["card_bg"]
        tk.Label(
            inner, text=rtl("לימוד למבחן, בעברית"), bg=ink,
            fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(12)),
            anchor="e", justify="right",
        ).pack(fill="x")
        title_row = tk.Frame(inner, bg=ink)
        title_row.pack(fill="x", pady=(2, 4))
        from ui import skin

        logo = skin.logo_photo(self, 40)
        if logo is not None:
            tk.Label(title_row, image=logo, bg=ink, bd=0).pack(side="right", padx=(8, 0))
            self._logo_photo = logo
        tk.Label(
            title_row, text=rtl(APP_NAME), bg=ink, fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(28), "bold"),
            anchor="e", justify="right",
        ).pack(side="right", fill="x", expand=True)
        tk.Label(
            inner,
            text=rtl("שיעורים, תרגול ומבחנים על המחשב. בלי חשבון ובלי שרת."),
            bg=ink, fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(14)),
            anchor="e", justify="right", wraplength=760,
        ).pack(fill="x")
        ver = tk.Label(
            inner,
            text=rtl(f"גרסה {VERSION} · ההתקדמות נשמרת אצלכם"),
            bg=ink, fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(13)),
            anchor="e", justify="right",
        )
        ver.pack(fill="x", pady=(8, 0))
        if self.on_secret:
            ver.bind("<Button-1>", lambda _e: self._tap_secret())

    def _chips(self):
        row = tk.Frame(self, bg=COLORS["bg"])
        row.pack(fill="x", pady=(0, 10))
        for label, value in (
            ("גרסה", VERSION),
            ("מערכת", "Windows"),
            ("שפה", "עברית"),
            ("נתונים", "רק במחשב"),
        ):
            chip, inner = make_card(row, padx=14, pady=10, radius=18)
            chip.pack(side="right", padx=5)
            tk.Label(
                inner, text=rtl(label), bg=COLORS["card_bg"], fg=COLORS["text_muted"],
                font=(ADHD_CONFIG["font_family"], font_size(11)), anchor="e",
            ).pack(anchor="e")
            tk.Label(
                inner, text=rtl(value), bg=COLORS["card_bg"], fg=COLORS["text_main"],
                font=(ADHD_CONFIG["font_family"], font_size(15), "bold"), anchor="e",
            ).pack(anchor="e", pady=(2, 0))

    def _developer(self):
        inner = self._card("מפתח התוכנה", accent=True)
        tk.Label(
            inner, text=rtl(DEVELOPER_NAME), bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(22), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x", pady=(6, 0))
        fast_label(
            inner,
            "פיתוח, עיצוב ומאגר הלמידה",
            size=14, muted=True, bg=COLORS["card_bg"],
        ).pack(fill="x", pady=(2, 0))
        tk.Label(
            inner, text=DEVELOPER_NAME_EN, bg=COLORS["card_bg"], fg=COLORS["text_muted"],
            font=(ADHD_CONFIG["font_family"], font_size(13)),
            anchor="e", justify="right",
        ).pack(fill="x", pady=(0, 8))
        fast_label(
            inner,
            "לפניות, דיווח על תקלה, שאלה שגויה או הצעה לשיפור, אפשר לכתוב ישירות:",
            size=14, muted=True, bg=COLORS["card_bg"], wrap=760,
        ).pack(fill="x")
        tk.Label(
            inner, text="\u200e" + CONTACT_EMAIL + "\u200e", bg=COLORS["card_bg"], fg=COLORS["primary"],
            font=(ADHD_CONFIG["font_family"], font_size(16), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x", pady=(4, 8))

        row = tk.Frame(inner, bg=COLORS["card_bg"])
        row.pack(fill="x")
        ModernButton(row, text=rtl("שליחת מייל"), height=42, width=140,
                     command=self._open_email).pack(side="right", padx=6)
        GhostButton(row, text=rtl("העתקת המייל"), height=42, width=150,
                    command=self._copy_email).pack(side="right", padx=6)
        self._mail_status = fast_label(inner, "", size=12, muted=True, bg=COLORS["card_bg"])
        self._mail_status.pack(fill="x", pady=(6, 0))

    def _what(self):
        names = ", ".join(SUBJECTS[key]["name"] for key in HOME_SUBJECTS)
        electives = ", ".join(SUBJECTS[key]["name"] for key in ELECTIVE_SUBJECTS)
        inner = self._card("מה יש כאן")
        for line in (
            "StudyApp היא תוכנת למידה למחשב, בעברית, בלי צורך באינטרנט אחרי ההתקנה.",
            f"שמונה מקצועות ליבה: {names}.",
            f"מקצועות בחירה: {electives}. לא נכנסים למבחן הכללי ולא למימ״ד.",
            "בכל מקצוע: שיעור עיוני, תרגול עם הסבר, מבחן דמה ומבחן אמיתי לפי הרמה.",
            "יש גם מבחן מימ״ד (עברית, אנגלית וחשבון) ומבחן כללי משולב.",
            "בהגדרות אפשר להפעיל מצב מיקוד, להגדיל טקסט ולהקריא שאלות בקול.",
        ):
            fast_label(inner, line, size=14, muted=True, bg=COLORS["card_bg"], wrap=760).pack(fill="x", pady=1)

    def _howto(self):
        inner = self._card("איך מתחילים")
        for line in (
            "1. נרשמים בשם וגיל, בלי סיסמה ובלי חשבון רשת.",
            "2. עוברים אבחון קצר שמציב רמה לכל מקצוע.",
            "3. במסך הבית בוחרים מקצוע ונכנסים לשיעור או לתרגול.",
            "4. בכל מקצוע: קודם שיעור, אחר כך תרגול לפי הרמה.",
            "5. מבחן דמה: הציון בסוף. מספר השאלות והשעון לפי הרמה.",
            "6. מבחן אמיתי: נפתח אחרי 20 שאלות תרגול בדיוק 50%+.",
        ):
            fast_label(inner, line, size=14, muted=True, bg=COLORS["card_bg"], wrap=760).pack(fill="x", pady=1)

    def _keys(self):
        inner = self._card("קיצורי מקלדת")
        for line in (
            "1 עד 4: בחירת תשובה.",
            "Enter: לשאלה הבאה.",
            "S: דילוג על שאלה בתרגול.",
            "Esc: חזרה לבית (לא באמצע מבחן מדורג).",
        ):
            fast_label(inner, line, size=14, muted=True, bg=COLORS["card_bg"], wrap=760).pack(fill="x", pady=1)

    def _privacy(self):
        inner = self._card("פרטיות ונתונים")
        for line in (
            "התוכנה לא שולחת את הלמידה שלך לשרת. אין התחברות לענן ואין פרסומות.",
            "נשמרים במחשב: שם, גיל, תוצאות אבחון, התקדמות, טעויות והעדפות תצוגה.",
            "שם, גיל ותעודת זהות לא נשלחים לעולם. פינג אנונימי (גרסה ומערכת בלבד) כבוי כברירת מחדל ואפשר להדליק בהגדרות.",
            "אפשר לייצא גיבוי או למחוק הכל בהגדרות.",
            f"תיקיית הנתונים: {DATA_DIR}",
            f"יומן תקלות: {applog.LOG_PATH}",
        ):
            fast_label(inner, line, size=14, muted=True, bg=COLORS["card_bg"], wrap=760).pack(fill="x", pady=1)

    def _disclaimer(self):
        inner = self._card("חשוב לדעת")
        for line in (
            "זה כלי עזר ללמידה ותרגול, לא מבחן רשמי ולא תעודה.",
            "התוכנה אינה קשורה למשרד החינוך, לראמ״ה או למאל״ו.",
            "היא אינה תחליף למורה, לבית ספר, לייעוץ מקצועי או לאבחון רפואי.",
            "תאוריית הנהיגה כאן היא תרגול הכנה. בדקו מול המאגר הרשמי לפני המבחן בלשכה.",
            "הציון באפליקציה משקף את התרגול כאן, לא את הציון בבחינה האמיתית.",
        ):
            fast_label(inner, line, size=14, muted=True, bg=COLORS["card_bg"], wrap=760).pack(fill="x", pady=1)

    def _terms(self):
        inner = self._card("תקנון שימוש קצר")
        blob = "\n\n".join(f"{title}\n{text}" for title, text in TERMS)
        blob += "\n\nמסמך זה הוא תקנון תפעולי קצר בלבד, ואינו ייעוץ משפטי."
        box = FastText(inner, height=14)
        box.pack(fill="x", pady=(8, 0))
        box.set_text(blob, rtl_lines=True)

    def _footer(self):
        inner = self._card("זכויות יוצרים")
        tk.Label(
            inner, text=rtl(copyright_he()), bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(15), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x")
        for line in (
            f"הקוד, הממשק ומאגר הלמידה שייכים ל{DEVELOPER_NAME}.",
            "אין להעתיק, להפיץ או למכור את התוכנה כאילו היא רשמית או של גוף אחר.",
            "התוכנה מסופקת כפי שהיא, ברישיון MIT, בלי אחריות לציון, לתוכן או לתוצאה.",
        ):
            fast_label(inner, line, size=13, muted=True, bg=COLORS["card_bg"], wrap=760).pack(fill="x", pady=1)

    def _card(self, title: str, accent: bool = False):
        card, inner = make_card(
            self, padx=20, pady=16,
            gold_top=accent, accent=COLORS["primary"] if accent else None,
        )
        card.pack(fill="x", pady=(0, 12))
        tk.Label(
            inner, text=rtl(title), bg=COLORS["card_bg"], fg=COLORS["text_main"],
            font=(ADHD_CONFIG["font_family"], font_size(17), "bold"),
            anchor="e", justify="right",
        ).pack(fill="x")
        return inner

    def _copy_email(self):
        try:
            root = self.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(CONTACT_EMAIL)
            root.update_idletasks()
            self._mail_status.configure(text=rtl("המייל הועתק ללוח."))
        except Exception:
            dialogs.error("העתקה", f"לא הצלחתי להעתיק. אפשר להעתיק ידנית:\n{CONTACT_EMAIL}")

    def _open_email(self):
        subject = quote("פנייה מ-StudyApp")
        try:
            webbrowser.open(f"mailto:{CONTACT_EMAIL}?subject={subject}")
            self._mail_status.configure(text=rtl("נפתחה תוכנת הדואר במחשב."))
        except Exception:
            dialogs.info("מייל", f"אפשר לכתוב ידנית אל:\n{CONTACT_EMAIL}")

    def _tap_secret(self):
        self._secret_taps += 1
        if self._secret_taps >= 5 and self.on_secret:
            self._secret_taps = 0
            self.on_secret()


TERMS = (
    (
        "1. מטרת השימוש",
        "התוכנה מיועדת ללמידה, לתרגול ולמעקב התקדמות אישי. השימוש בה הוא באחריות המשתמש.",
    ),
    (
        "2. גיל וסביבה",
        "התוכנה מתאימה לתלמידים ולהורים שעוזרים להם. מומלץ להשתמש במחשב אישי, לא במחשב ציבורי בלי יציאה מהחשבון.",
    ),
    (
        "3. תוכן הלמידה",
        "השאלות והשיעורים הם חומר עזר מקורי לתרגול. הם לא שאלון רשמי ולא מבטיחים ציון בבגרות, במימ״ד או בכל מבחן אחר.",
    ),
    (
        "4. נתונים",
        "הנתונים נשמרים מקומית במחשב. שם, גיל, תעודת זהות ונתוני למידה לא נשלחים. פינג אנונימי (גרסה ומערכת) הוא אופציונלי וכבוי כברירת מחדל. מי ששולח מייל בוחר מה לכתוב שם.",
    ),
    (
        "5. שימוש הולם",
        "אסור להשתמש בתוכנה בניגוד לחוק, לפרוץ אליה, להעתיק את המאגר בלי רשות, או להציג אותה כשירות רשמי של מוסד לימודים.",
    ),
    (
        "6. אחריות",
        "התוכנה מסופקת «כפי שהיא». אין אחריות שממליצה, ציון או מדד יהיו מדויקים בכל מצב, ושלא תקרה תקלה טכנית.",
    ),
    (
        "7. סיום השימוש",
        "אפשר להפסיק להשתמש בכל רגע ולמחוק את הנתונים בהגדרות, או למחוק את תיקיית הנתונים מהמחשב.",
    ),
    (
        "8. פניות",
        f"פניות לתמיכה ולזכויות: {DEVELOPER_NAME} · {CONTACT_EMAIL}",
    ),
)
