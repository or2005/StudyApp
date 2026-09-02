"""תצוגה חדה ב־Windows: DPI אמיתי, בלי הגדלה מטושטשת של כל החלון."""
from __future__ import annotations

import sys

_AWARE = False
_SCALE = 1.0

# Per-monitor V2. חייב לפני יצירת חלון, אחרת Windows מגדיל ביטמאפ.
_DPI_CONTEXT_PER_MONITOR_AWARE_V2 = -4
_PROCESS_PER_MONITOR_DPI_AWARE = 2
_PROCESS_SYSTEM_DPI_AWARE = 1


def is_windows() -> bool:
    return sys.platform.startswith("win")


def ui_scale() -> float:
    return _SCALE


def dip(px: int) -> int:
    return max(1, int(round(float(px) * _SCALE)))


def enable_dpi_awareness() -> bool:
    """מצהיר שהתהליך יודע DPI. קוראים לזה לפני כל חלון Tk."""
    global _AWARE, _SCALE
    _SCALE = max(_SCALE, _system_scale())
    if not is_windows() or _AWARE:
        return _AWARE
    try:
        import ctypes

        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(_DPI_CONTEXT_PER_MONITOR_AWARE_V2)
            _AWARE = True
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(_PROCESS_PER_MONITOR_DPI_AWARE)
                _AWARE = True
            except Exception:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(_PROCESS_SYSTEM_DPI_AWARE)
                    _AWARE = True
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
                    _AWARE = True
    except Exception:
        _AWARE = False
    _SCALE = max(_SCALE, _system_scale())
    return _AWARE


def quiet_ctk_auto_scale() -> None:
    """מונע מ־CustomTkinter להכפיל גדלים אחרי שכבר הצהרנו DPI בעצמנו."""
    try:
        import customtkinter as ctk

        ctk.deactivate_automatic_dpi_awareness()
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
    except Exception:
        pass


def _system_scale() -> float:
    if not is_windows():
        return 1.0
    try:
        import ctypes

        dpi = int(ctypes.windll.user32.GetDpiForSystem())
        if dpi >= 72:
            return max(1.0, min(dpi / 96.0, 3.0))
    except Exception:
        pass
    try:
        import ctypes

        factor = int(ctypes.windll.shcore.GetScaleFactorForDevice(0))
        if factor >= 100:
            return max(1.0, min(factor / 100.0, 3.0))
    except Exception:
        pass
    return 1.0


def _window_ppi(root) -> float:
    samples = [96.0]
    if is_windows():
        try:
            import ctypes

            hwnd = int(root.winfo_id())
            dpi = int(ctypes.windll.user32.GetDpiForWindow(hwnd))
            if dpi >= 72:
                samples.append(float(dpi))
        except Exception:
            pass
        try:
            import ctypes

            samples.append(float(int(ctypes.windll.user32.GetDpiForSystem())))
        except Exception:
            pass
    try:
        samples.append(float(root.winfo_fpixels("1i")))
    except Exception:
        pass
    ppi = max(samples)
    return max(96.0, min(ppi, 288.0))


def apply_display_quality(root) -> float:
    """סנכרון tk scaling ל־DPI האמיתי, כדי שהגופן יצויר חד ולא יומתח."""
    global _SCALE
    enable_dpi_awareness()
    ppi = _window_ppi(root)
    _SCALE = max(1.0, min(ppi / 96.0, 3.0))
    try:
        root.tk.call("tk", "scaling", ppi / 72.0)
    except Exception:
        pass
    try:
        import tkinter.font as tkfont

        from core.config import ADHD_CONFIG

        family = str(ADHD_CONFIG.get("font_family") or "Segoe UI")
        for name in (
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkIconFont",
            "TkTooltipFont",
        ):
            try:
                tkfont.nametofont(name).configure(family=family)
            except Exception:
                pass
    except Exception:
        pass
    return _SCALE
