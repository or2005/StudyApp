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
VERSION: Final[str] = "5.0.2"
FONT_FAMILY: Final[str] = "Segoe UI"

DEVELOPER_NAME: Final[str] = "אור דדשב"
DEVELOPER_NAME_EN: Final[str] = "Or Dadshaev"
CONTACT_EMAIL: Final[str] = "dadshaev@gmail.com"
COPYRIGHT_YEAR: Final[str] = "2026"

# ערוץ עדכונים. כשמפרסמים ב-GitHub Releases, ממלאים את שם המאגר.
GITHUB_REPO: Final[str] = "or2005/StudyApp"
UPDATE_MANIFEST_URLS: Final[tuple[str, ...]] = (
    # jsDelivr for JSON (cache-friendly); raw with cache-buster as backup.
    "https://cdn.jsdelivr.net/gh/or2005/StudyApp@main/docs/latest.json",
    "https://raw.githubusercontent.com/or2005/StudyApp/main/docs/latest.json?v=20260905c",
    "https://raw.githubusercontent.com/or2005/StudyApp/master/docs/latest.json?v=20260905c",
)
# פינג אנונימי בהסכמה בלבד. אין שם / גיל / ת״ז.
TELEMETRY_URL: Final[str] = "https://formsubmit.co/ajax/dadshaev@gmail.com"

# מורה AI מקומי דרך Ollama (בלי מפתח API). אפשר לדרוס עם משתני סביבה:
# STUDYAPP_OLLAMA_URL / STUDYAPP_OLLAMA_MODEL / STUDYAPP_OLLAMA_ENABLED / STUDYAPP_OLLAMA_TIMEOUT
OLLAMA_BASE_URL: Final[str] = os.environ.get("STUDYAPP_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL: Final[str] = os.environ.get("STUDYAPP_OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SEC: Final[float] = float(os.environ.get("STUDYAPP_OLLAMA_TIMEOUT", "40") or 40)
OLLAMA_ENABLED_DEFAULT: Final[bool] = (
    str(os.environ.get("STUDYAPP_OLLAMA_ENABLED", "1")).strip().lower()
    not in {"0", "false", "off", "no"}
)


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


def rtl_paragraph(text: str) -> str:
    from core.rtltext import apply_paragraph

    return apply_paragraph(text)


# ערכת הצבעים הפעילה. core/theme.py מחליף את התוכן במקום בעת מעבר בהיר/כהה.
COLORS: dict[str, str] = {
    "bg": "#F2F3F0",
    "bg_dark": "#2A3834",
    "card_bg": "#FFFFFF",
    "card_hover": "#EBECE8",
    "card_border": "#D8DBD4",
    "shadow": "#C8CBC3",
    "primary": "#3A6B5E",
    "primary_hover": "#2F564C",
    "accent": "#B86B45",
    "success": "#3D8B5F",
    "success_hover": "#327350",
    "success_text": "#FFFFFF",
    "danger": "#C24B5A",
    "danger_hover": "#A33D4A",
    "danger_text": "#FFFFFF",
    "streak": "#B86B45",
    "hint": "#B86B45",
    "text_main": "#1E2A28",
    "text_muted": "#667572",
    "text_on_primary": "#FFFFFF",
    "focus_bg": "#EBECE8",
    "banner": "#2F564C",
    "banner_text": "#F4F6F3",
    "banner_track": "#D5DED9",
    "banner_fill": "#3A6B5E",
    "option_bg": "#F7F8F5",
    "option_hover": "#E4E9E5",
    "option_text": "#1E2A28",
    "option_border": "#D0D6D1",
    "progress_track": "#E0E5E1",
    "progress_fill": "#3A6B5E",
    "scrollbar": "#EEF0EC",
    "scrollbar_thumb": "#9AA8A2",
    "input_bg": "#FFFFFF",
    "input_fg": "#1E2A28",
    "input_border": "#D0D6D1",
    "sidebar_rule": "#E2E5DF",
    "sidebar_bg": "#FAFBF9",
    "sidebar_fg": "#1E2A28",
    "sidebar_muted": "#6E7C78",
    "sidebar_hover": "#EBECE8",
    "sidebar_active": "#3A6B5E",
    "gold": "#B86B45",
    "gold_text": "#FFFFFF",
    "hero_bg": "#FFFFFF",
    "hero_fg": "#1E2A28",
    "hero_muted": "#667572",
    "hairline": "#D8DBD4",
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
    "header_size": 26,
    "title_size": 20,
    "body_size": 16,
    "button_radius": 12,
    "animation_speed": 180,
    "high_contrast": False,
    "option_height": 56,
    "font_delta": 0,
}


class ModeInfo(TypedDict):
    name: str
    desc: str
    color: str


SUBJECT_MODES: Final[dict[str, ModeInfo]] = {
    "read": {
        "name": "שיעור עיוני",
        "desc": "קוראים בקצב שלכם: תיאוריה, דוגמה וסיכום קצר.",
        "color": "#3A6B5E",
    },
    "practice": {
        "name": "תרגול",
        "desc": "שאלות לפי הרמה שלכם, עם הסבר אחרי כל תשובה.",
        "color": "#3A6B5E",
    },
    "compose": {
        "name": "כתיבה",
        "desc": "כותבים מילה, מספר או משפט. כל שאלה אומרת מה לרשום.",
        "color": "#B86B45",
    },
    "mock": {
        "name": "מבחן דמה",
        "desc": "הציון בסוף. בלי השפעה על הפרופיל.",
        "color": "#4A7A8C",
    },
    "final": {
        "name": "מבחן אמיתי",
        "desc": "נפתח אחרי תרגול מספיק. אורך וזמן לפי הרמה.",
        "color": "#6B5A4A",
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
        "color": "#6B5F8A",
    },
    "english": {
        "name": "אנגלית",
        "desc": "אוצר מילים, דקדוק והבנת הנקרא.",
        "icon": "translate",
        "color": "#4A6F8C",
    },
    "geography": {
        "name": "גאוגרפיה",
        "desc": "מדינות, ערים, יבשות ותופעות טבע.",
        "icon": "globe",
        "color": "#4A7A5A",
    },
    "history": {
        "name": "היסטוריה",
        "desc": "אירועים, תקופות ודמויות לאורך הזמן.",
        "icon": "scroll",
        "color": "#A86B4A",
    },
    "civics": {
        "name": "אזרחות",
        "desc": "דמוקרטיה, רשויות, זכויות וחובות.",
        "icon": "landmark",
        "color": "#4A7A8C",
    },
    "chemistry": {
        "name": "כימיה",
        "desc": "אטומים, תגובות, חומרים ונוסחאות.",
        "icon": "flask",
        "color": "#8A5A6A",
    },
    "physics": {
        "name": "פיזיקה",
        "desc": "כוחות, תנועה, אנרגיה וחשמל בסיסי.",
        "icon": "atom",
        "color": "#4A6A8C",
    },
    "math": {
        "name": "מתמטיקה",
        "desc": "אלגברה, גאומטריה, אחוזים ופונקציות.",
        "icon": "sigma",
        "color": "#8A7040",
    },
    "electricity": {
        "name": "חשמל",
        "desc": "מעגלים, מתח, זרם והתנגדות.",
        "icon": "bolt",
        "color": "#8A7840",
    },
    "electronics": {
        "name": "אלקטרוניקה",
        "desc": "רכיבים, אותות ומעגלים פעילים.",
        "icon": "chip",
        "color": "#5A6A8C",
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

# מקצועות בחירה: מופיעים במסך הבית, לא במבחן הכללי ולא במימ״ד.
ELECTIVE_SUBJECTS: Final[list[str]] = [
    "electricity",
    "electronics",
]
ALL_SUBJECTS: Final[list[str]] = [*HOME_SUBJECTS, *ELECTIVE_SUBJECTS]
COMING_SOON_SUBJECTS: Final[frozenset[str]] = frozenset()
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
        "חשמל": "electricity",
        "אלקטרוניקה": "electronics",
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
