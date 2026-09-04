"""ערכות צבע, בהיר וכהה.
שולחן לימוד: נייר אבן רגוע, דיו כהה, ירוק־יער שקט.
בלי מנטה־SaaS, בלי ניאון, בלי כתום צועק."""
from __future__ import annotations

from core.config import COLORS, SUBJECTS, subject_key

LIGHT: dict[str, str] = {
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

DARK: dict[str, str] = {
    "bg": "#151917",
    "bg_dark": "#0E1210",
    "card_bg": "#1C2220",
    "card_hover": "#252C29",
    "card_border": "#313A37",
    "shadow": "#0A0C0B",
    "primary": "#6FA896",
    "primary_hover": "#5C9181",
    "accent": "#C88964",
    "success": "#5FA87A",
    "success_hover": "#4E9168",
    "success_text": "#FFFFFF",
    "danger": "#D06B78",
    "danger_hover": "#B85A66",
    "danger_text": "#FFFFFF",
    "streak": "#C88964",
    "hint": "#C88964",
    "text_main": "#E8EEEC",
    "text_muted": "#8F9C98",
    "text_on_primary": "#102018",
    "focus_bg": "#1C2220",
    "banner": "#3A5A50",
    "banner_text": "#F0F5F2",
    "banner_track": "#252C29",
    "banner_fill": "#6FA896",
    "option_bg": "#222926",
    "option_hover": "#2C3431",
    "option_text": "#E8EEEC",
    "option_border": "#313A37",
    "progress_track": "#252C29",
    "progress_fill": "#6FA896",
    "scrollbar": "#1C2220",
    "scrollbar_thumb": "#4A5753",
    "input_bg": "#181E1C",
    "input_fg": "#E8EEEC",
    "input_border": "#313A37",
    "sidebar_rule": "#252C29",
    "sidebar_bg": "#121614",
    "sidebar_fg": "#E8EEEC",
    "sidebar_muted": "#7A8884",
    "sidebar_hover": "#1C2220",
    "sidebar_active": "#6FA896",
    "gold": "#C88964",
    "gold_text": "#102018",
    "hero_bg": "#1C2220",
    "hero_fg": "#E8EEEC",
    "hero_muted": "#8F9C98",
    "hairline": "#313A37",
}

_mode = "Light"

# רחיצות מקצוע שקטות, בלי פסטל צועק
SUBJECT_WASH_LIGHT: dict[str, str] = {
    "hebrew": "#EFECEF",
    "english": "#E9EEF3",
    "math": "#F3EFE6",
    "history": "#F2EBE6",
    "geography": "#E8F0EA",
    "civics": "#E8EFF1",
    "chemistry": "#F1E9ED",
    "physics": "#E9EDF2",
    "electricity": "#F2EFE4",
    "electronics": "#E8ECF3",
    "driving_theory": "#E8F0EA",
}

SUBJECT_WASH_DARK: dict[str, str] = {
    "hebrew": "#262228",
    "english": "#1E242A",
    "math": "#2A261C",
    "history": "#2A231E",
    "geography": "#1C2620",
    "civics": "#1C2428",
    "chemistry": "#282022",
    "physics": "#1E2228",
    "electricity": "#2A2618",
    "electronics": "#1C222A",
    "driving_theory": "#1C2620",
}

SUBJECT_ACCENTS_DARK: dict[str, str] = {
    "hebrew": "#A89BC4",
    "english": "#7FA0BC",
    "math": "#C9A05A",
    "history": "#C48968",
    "geography": "#6FA87E",
    "civics": "#6FA3B0",
    "chemistry": "#B888A0",
    "physics": "#6EB0B0",
    "electricity": "#D0B05A",
    "electronics": "#7FA0D8",
    "driving_theory": "#5EAD88",
}


def subject_wash(key: str) -> str:
    resolved = subject_key(key)
    table = SUBJECT_WASH_DARK if _mode == "Dark" else SUBJECT_WASH_LIGHT
    return table.get(resolved) or COLORS["card_bg"]


def subject_accent(key: str) -> str:
    """צבע ייחודי למקצוע. לא אותו ירוק לכל הכרטיסים."""
    resolved = subject_key(key)
    if _mode == "Dark":
        return SUBJECT_ACCENTS_DARK.get(resolved) or COLORS["primary"]
    info = SUBJECTS.get(resolved) or {}
    return str(info.get("color") or COLORS["primary"])


def apply_mode(mode: str) -> dict[str, str]:
    global _mode
    _mode = "Dark" if str(mode).lower().startswith("d") else "Light"
    COLORS.clear()
    COLORS.update(DARK if _mode == "Dark" else LIGHT)
    return COLORS


def current_mode() -> str:
    return _mode


apply_mode("Light")
