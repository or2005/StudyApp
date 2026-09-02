"""ערכות צבע, בהיר וכהה. מנטה רגוע + כתום נקודתי, בלי ניאון על שחור."""
from __future__ import annotations

from core.config import COLORS, SUBJECTS, subject_key

LIGHT: dict[str, str] = {
    "bg": "#F0F9F6",
    "bg_dark": "#264A45",
    "card_bg": "#FFFFFF",
    "card_hover": "#F0F7F4",
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
    "text_main": "#1A3532",
    "text_muted": "#5B7570",
    "text_on_primary": "#FFFFFF",
    "focus_bg": "#F0F7F4",
    "banner": "#0F766E",
    "banner_text": "#F0FDFA",
    "banner_track": "#B7E4D8",
    "banner_fill": "#0D9488",
    "option_bg": "#F7FBFA",
    "option_hover": "#E4F4EF",
    "option_text": "#134E4A",
    "option_border": "#D0E4DE",
    "progress_track": "#E4EFEA",
    "progress_fill": "#0D9488",
    "scrollbar": "#EEF5F2",
    "scrollbar_thumb": "#8FB3AB",
    "input_bg": "#FFFFFF",
    "input_fg": "#1A3532",
    "input_border": "#D0E4DE",
    "sidebar_rule": "#E4EEEA",
    "sidebar_bg": "#FFFFFF",
    "sidebar_fg": "#1A3532",
    "sidebar_muted": "#6A837E",
    "sidebar_hover": "#F0F7F4",
    "sidebar_active": "#0D9488",
    "gold": "#EA7A3A",
    "gold_text": "#FFFFFF",
    "hero_bg": "#FFFFFF",
    "hero_fg": "#1A3532",
    "hero_muted": "#5B7570",
    "hairline": "#DCEAE4",
}

DARK: dict[str, str] = {
    "bg": "#151C1A",
    "bg_dark": "#101816",
    "card_bg": "#1E2826",
    "card_hover": "#273330",
    "card_border": "#33423E",
    "shadow": "#0B100F",
    "primary": "#3FA89A",
    "primary_hover": "#348C81",
    "accent": "#E08A4A",
    "success": "#4CAF7A",
    "success_hover": "#3D9A68",
    "success_text": "#FFFFFF",
    "danger": "#E06B7A",
    "danger_hover": "#C85A68",
    "danger_text": "#FFFFFF",
    "streak": "#E08A4A",
    "hint": "#E08A4A",
    "text_main": "#E6EEEC",
    "text_muted": "#8FA09C",
    "text_on_primary": "#FFFFFF",
    "focus_bg": "#1E2826",
    "banner": "#2A6B63",
    "banner_text": "#F0FDFA",
    "banner_track": "#273330",
    "banner_fill": "#3FA89A",
    "option_bg": "#24302D",
    "option_hover": "#2E3C38",
    "option_text": "#E6EEEC",
    "option_border": "#33423E",
    "progress_track": "#273330",
    "progress_fill": "#3FA89A",
    "scrollbar": "#1E2826",
    "scrollbar_thumb": "#4A5C58",
    "input_bg": "#1A2321",
    "input_fg": "#E6EEEC",
    "input_border": "#33423E",
    "sidebar_rule": "#273330",
    "sidebar_bg": "#121A18",
    "sidebar_fg": "#E6EEEC",
    "sidebar_muted": "#7A8C87",
    "sidebar_hover": "#1E2826",
    "sidebar_active": "#3FA89A",
    "gold": "#E08A4A",
    "gold_text": "#FFFFFF",
    "hero_bg": "#1E2826",
    "hero_fg": "#E6EEEC",
    "hero_muted": "#8FA09C",
    "hairline": "#33423E",
}

_mode = "Light"

SUBJECT_WASH_LIGHT: dict[str, str] = {
    "hebrew": "#EEE8F8",
    "english": "#E3F0FC",
    "math": "#FFF6E0",
    "history": "#FDE8DC",
    "geography": "#E5F6EA",
    "civics": "#DFF4F8",
    "chemistry": "#FCE8F0",
    "physics": "#E8EEF8",
    "arabic": "#DFF3EA",
    "first_aid": "#FCE8EC",
}

SUBJECT_WASH_DARK: dict[str, str] = {
    "hebrew": "#2A2438",
    "english": "#1E2A38",
    "math": "#332A18",
    "history": "#33241C",
    "geography": "#1C2E24",
    "civics": "#1C2C32",
    "chemistry": "#322028",
    "physics": "#222830",
    "arabic": "#1C2E26",
    "first_aid": "#322024",
}

SUBJECT_ACCENTS_DARK: dict[str, str] = {
    "hebrew": "#A99AD4",
    "english": "#7BA3C9",
    "math": "#D4A04A",
    "history": "#D4895A",
    "geography": "#6BA87A",
    "civics": "#6BA3B8",
    "chemistry": "#C984A4",
    "physics": "#6BB0B8",
    "arabic": "#5EAD88",
    "first_aid": "#D46A78",
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
