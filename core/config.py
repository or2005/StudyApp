# StudyApp, זהות, צבעים ומקצועות
from __future__ import annotations

import os
import sys
from typing import Final, TypedDict


def _base_dir() -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return str(sys._MEIPASS)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


WINDOW_SIZE: Final[str] = "1280x820"
BASE_DIR: Final[str] = _base_dir()
QUESTIONS_DIR: Final[str] = os.path.join(BASE_DIR, "data", "questions")
ASSETS_DIR: Final[str] = os.path.join(BASE_DIR, "assets")
ICON_PATH: Final[str] = os.path.join(ASSETS_DIR, "icon.ico")
ICON_PNG_PATH: Final[str] = os.path.join(ASSETS_DIR, "icon.png")
APP_TITLE: Final[str] = "StudyApp"
APP_NAME: Final[str] = "StudyApp"
VERSION: Final[str] = "4.5.3"
FONT_FAMILY: Final[str] = "Segoe UI"

DEVELOPER_NAME: Final[str] = "אור דדשב"
DEVELOPER_NAME_EN: Final[str] = "Or Dadshaev"
CONTACT_EMAIL: Final[str] = "dadshaev@gmail.com"
COPYRIGHT_YEAR: Final[str] = "2026"

# ערוץ עדכונים. כשמפרסמים ב-GitHub Releases, ממלאים את שם המאגר.
GITHUB_REPO: Final[str] = "or2005/StudyApp"
UPDATE_MANIFEST_URLS: Final[tuple[str, ...]] = (
    "https://raw.githubusercontent.com/or2005/StudyApp/main/docs/latest.json",
    "https://raw.githubusercontent.com/or2005/StudyApp/master/docs/latest.json",
)
# פינג אנונימי בהסכמה בלבד. אין שם / גיל / ת״ז.
TELEMETRY_URL: Final[str] = "https://formsubmit.co/ajax/dadshaev@gmail.com"


def copyright_he() -> str:
    return f"© {COPYRIGHT_YEAR} {DEVELOPER_NAME}. כל הזכויות שמורות."

DAILY_GOAL_TARGET: Final[int] = 15
FONT_STEPS: Final[dict[str, int]] = {"קטן": -2, "רגיל": 0, "גדול": 3, "ענק": 6}
FINAL_EXAM_MIN_QUESTIONS: Final[int] = 20
FINAL_EXAM_MIN_ACCURACY: Final[int] = 50
MOCK_SIZE: Final[int] = 15
FINAL_SIZE: Final[int] = 30
PRACTICE_SIZE: Final[int] = 16
GUIDED_SIZE: Final[int] = 6
TIMED_SECONDS_PER_QUESTION: Final[int] = 75
GENERAL_EXAM_SIZE: Final[int] = 50
GENERAL_EXAM_MINUTES: Final[int] = 50
GENERAL_EXAM_COVERAGE: Final[float] = 0.50


def rtl(text: str) -> str:
    from core.rtltext import apply

    return apply(text)


# ערכת הצבעים הפעילה. core/theme.py מחליף את התוכן במקום בעת מעבר בהיר/כהה.
COLORS: dict[str, str] = {
    "bg": "#F0F9F6",
    "bg_dark": "#264A45",
    "card_bg": "#FFFFFF",
    "card_hover": "#E8F6F1",
    "card_border": "#DCEAE4",
    "shadow": "#C5D6D0",
    "primary": "#0D9488",
    "primary_hover": "#0F766E",
    "accent": "#EA7A3A",
    "success": "#16A34A",
    "success_hover": "#15803D",
    "success_text": "#FFFFFF",
    "danger": "#E11D48",
    "danger_hover": "#BE123C",
    "danger_text": "#FFFFFF",
    "streak": "#EA7A3A",
    "hint": "#EA7A3A",
    "text_main": "#143D38",
    "text_muted": "#4F746E",
    "text_on_primary": "#FFFFFF",
    "focus_bg": "#E8F6F1",
    "banner": "#0F766E",
    "banner_text": "#F0FDFA",
    "banner_track": "#B7E4D8",
    "banner_fill": "#0D9488",
    "option_bg": "#F3FBFA",
    "option_hover": "#D9F3EC",
    "option_text": "#134E4A",
    "option_border": "#C5E4DC",
    "progress_track": "#D7EDE7",
    "progress_fill": "#0D9488",
    "scrollbar": "#E8F6F1",
    "scrollbar_thumb": "#7AADA3",
    "input_bg": "#FFFFFF",
    "input_fg": "#143D38",
    "input_border": "#C5E4DC",
    "sidebar_rule": "#D2E8E1",
    "sidebar_bg": "#FFFFFF",
    "sidebar_fg": "#143D38",
    "sidebar_muted": "#4F746E",
    "sidebar_hover": "#E8F6F1",
    "sidebar_active": "#0D9488",
    "gold": "#EA7A3A",
    "gold_text": "#FFFFFF",
    "hero_bg": "#CFF5EA",
    "hero_fg": "#143D38",
    "hero_muted": "#0F766E",
    "hairline": "#D2E8E1",
}


class ADHDConfig(TypedDict):
    font_family: str
    header_size: int
    title_size: int
    body_size: int
    button_radius: int
    animation_speed: int
    high_contrast: bool
    option_height: int
    font_delta: int


ADHD_CONFIG: Final[ADHDConfig] = {
    "font_family": "Segoe UI",
    "header_size": 28,
    "title_size": 22,
    "body_size": 17,
    "button_radius": 16,
    "animation_speed": 180,
    "high_contrast": True,
    "option_height": 66,
    "font_delta": 0,
}


class ModeInfo(TypedDict):
    name: str
    desc: str
    color: str


SUBJECT_MODES: Final[dict[str, ModeInfo]] = {
    "read": {
        "name": "שיעור עיוני",
        "desc": "מאגר שיעורים מלא לכל נושא במקצוע: תיאוריה, דוגמאות וסיכום.",
        "color": "#0F9A8A",
    },
    "practice": {
        "name": "תרגול",
        "desc": "תרגול מותאם לרמה, עם רמז והסבר אחרי כל תשובה. גם כשעונים נכון.",
        "color": "#0D9488",
    },
    "compose": {
        "name": "יצור",
        "desc": "כותבים מילה, מספר או משפט קצר. כל שאלה אומרת בדיוק מה לרשום.",
        "color": "#C45A2A",
    },
    "mock": {
        "name": "מבחן דמה",
        "desc": "הציון בסוף, בלי השפעה על הפרופיל. מספר השאלות והשעון לפי הרמה.",
        "color": "#0EA5E9",
    },
    "final": {
        "name": "מבחן אמיתי",
        "desc": "נפתח אחרי 20 שאלות תרגול בדיוק 50%+. אורך וזמן לפי הרמה. אין חזרה אחורה.",
        "color": "#7C3AED",
    },
}


class SubjectInfo(TypedDict):
    name: str
    desc: str
    icon: str
    color: str


SUBJECTS: Final[dict[str, SubjectInfo]] = {
    "hebrew": {
        "name": "לשון",
        "desc": "חלקי דיבר, תחביר, כתיב, פיסוק ושורשים.",
        "icon": "book",
        "color": "#7C6BC4",
    },
    "english": {
        "name": "אנגלית",
        "desc": "אוצר מילים, דקדוק והבנת הנקרא.",
        "icon": "translate",
        "color": "#3B6FBF",
    },
    "geography": {
        "name": "גאוגרפיה",
        "desc": "מדינות, ערים, יבשות ותופעות טבע.",
        "icon": "globe",
        "color": "#3D8B5A",
    },
    "history": {
        "name": "היסטוריה",
        "desc": "אירועים, תקופות ודמויות לאורך הזמן.",
        "icon": "scroll",
        "color": "#C45A2A",
    },
    "civics": {
        "name": "אזרחות",
        "desc": "דמוקרטיה, זכויות, מוסדות וחוק.",
        "icon": "landmark",
        "color": "#2E7A9A",
    },
    "physics": {
        "name": "פיזיקה",
        "desc": "תנועה, כוחות, אנרגיה, חשמל וגלים.",
        "icon": "atom",
        "color": "#2A8A96",
    },
    "chemistry": {
        "name": "כימיה",
        "desc": "אטום, טבלה מחזורית, קשרים ותגובות.",
        "icon": "beaker",
        "color": "#C45A88",
    },
    "math": {
        "name": "מתמטיקה",
        "desc": "סדרות, אחוזים, יחס, היגיון ואנלוגיות.",
        "icon": "calculator",
        "color": "#C4841A",
    },
    "arabic": {
        "name": "ערבית",
        "desc": "ערבית בסיסית לדוברי עברית: ברכות, יום־יום ובית ספר.",
        "icon": "chat",
        "color": "#2E8B6A",
    },
    "first_aid": {
        "name": "עזרה ראשונה",
        "desc": "החייאה, דימום, כוויות, שבץ ועוד. חומר לימודי רחב.",
        "icon": "plus",
        "color": "#C0364A",
    },
}


# מקצועות הליבה למבחן הכללי ולאבחון. שלושת הראשונים הם גם פרקי מימ״ד.
HOME_SUBJECTS: Final[list[str]] = [
    "hebrew",
    "english",
    "math",
    "history",
    "geography",
    "civics",
    "chemistry",
    "physics",
]

# מקצועות בחירה: מופיעים במסך המקצועות, לא במבחן הכללי ולא במימ״ד.
ELECTIVE_SUBJECTS: Final[list[str]] = ["arabic", "first_aid"]
ALL_SUBJECTS: Final[list[str]] = [*HOME_SUBJECTS, *ELECTIVE_SUBJECTS]
# עדיין מוצגים בבית, אבל מעומעמים ולא נפתחים.
COMING_SOON_SUBJECTS: Final[frozenset[str]] = frozenset({"arabic", "first_aid"})

# פרקי מבחן מימ״ד (מאל"ו): עברית, אנגלית וחשבון.
MEIMAD_SUBJECTS: Final[list[str]] = ["hebrew", "english", "math"]


def subject_label(key: str) -> str:
    info = SUBJECTS.get(subject_key(key), {})
    return str(info.get("name") or key)


def is_coming_soon(key: str) -> bool:
    return subject_key(key) in COMING_SOON_SUBJECTS


def subject_key(value: str) -> str:
    raw = (value or "").strip()
    aliases = {
        "meimad": "math",
        "מימד": "math",
        "מתמטיקה": "math",
        "חשבון": "math",
        "לשון": "hebrew",
        "עברית": "hebrew",
        "ערבית": "arabic",
        "עזרה ראשונה": "first_aid",
        "עזרהראשונה": "first_aid",
    }
    if raw in aliases:
        return aliases[raw]
    if raw in SUBJECTS:
        return raw
    from core.rtltext import strip_marks

    cleaned = strip_marks(raw).strip()
    for key, info in SUBJECTS.items():
        if info["name"] in cleaned or cleaned.startswith(info["name"]):
            return key
        if key in cleaned:
            return key
    return raw


MODE_COUNTS: Final[dict[str, int]] = {
    "guided": GUIDED_SIZE,
    "practice": PRACTICE_SIZE,
    "mock": MOCK_SIZE,
    "timed": MOCK_SIZE,
    "final": FINAL_SIZE,
}
