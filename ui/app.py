from __future__ import annotations

import json
import os
import random
import sys
import threading
import tkinter as tk

try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:
    raise SystemExit(
        "חסרה החבילה customtkinter. התקינו עם: pip install -r requirements.txt"
    ) from exc

from core import applog, dialogs, i18n, studio_brief, theme
from core.adaptive_engine import LEVEL_HE, AdaptiveEngine, session_params
from core.analytics import AnalyticsEngine
from core.config import (
    ADHD_CONFIG,
    APP_TITLE,
    COLORS,
    FONT_STEPS,
    ALL_SUBJECTS,
    ELECTIVE_SUBJECTS,
    HOME_SUBJECTS,
    ICON_PATH,
    ICON_PNG_PATH,
    SUBJECTS,
    VERSION,
    rtl,
    is_coming_soon,
    subject_key,
    subject_label,
)
from core.exam_engine import ExamSession
from core.general_exam import (
    GENERAL_EXAM_SECONDS,
    GENERAL_EXAM_SIZE,
    build_general_exam,
    build_report,
    can_take_general_exam,
    unlock_progress,
)
from core.loader import load_subject
from core.meimad_exam import (
    PER_SECTION,
    SECTION_SECONDS,
    SECTIONS,
    build_meimad_exam,
    can_take_meimad,
)
from core.session_review import session_weak_topics
from core.session_state import SessionStateManager
from core.speech import Speaker
from core.srs import SpacedRepetition
from core.stats import DatabaseManager
from core.storage import UserStorage, get_persistent_app_dir
from core import nativeos, profiles, telemetry, updates
from ui.toast import ToastHost
from ui.fast import FastRow, FastScroll, fast_label
from ui.screens.about import AboutScreen
from ui.screens.general_report import GeneralExamReportScreen
from ui.screens.lesson import LessonScreen
from ui.screens.mistakes import MistakesScreen
from ui.screens.onboarding import OnboardingFrame
from ui.screens.practice import PracticeScreen
from ui.screens.question_editor import QuestionEditorScreen
from ui.screens.results import ResultsScreen
from ui.screens.settings import SettingsScreen
from ui.screens.studio import StudioScreen
from ui.screens.subject_hub import SubjectHubScreen
from ui.widgets import (
    CompactSubjectTile,
    ContextRail,
    GhostButton,
    ModernButton,
    PAGE_WIDTH,
    RAIL_BREAKPOINT,
    ProgressBar,
    Sidebar,
    StartLessonCard,
    StudioHero,
    body,
    heading,
    kicker,
    make_card,
    page_header,
)

log = applog.get_logger("ui")

# כמה שאלות בחזרה יומית אחת. יותר מזה הופך את החזרה למטלה שנוטים לדחות.
REVIEW_BATCH = 20


class StudyApp(ctk.CTk):
    def __init__(self):
        from core.display import apply_display_quality, enable_dpi_awareness, quiet_ctk_auto_scale

        enable_dpi_awareness()
        quiet_ctk_auto_scale()
        super().__init__()
        applog.setup_logging()
        applog.install_tk_handler(self, on_crash=self._on_crash)
        from core.platformutil import apply_ui_font

        apply_ui_font(self)
        apply_display_quality(self)

        self.storage = UserStorage()
        from core import i18n, textfix

        saved = self.storage.get_pref(i18n.PREF_KEY)
        i18n.set_lang(saved or textfix.guess_helper())
        from core import rtltext

        rtltext.set_mode(str(self.storage.get_pref("hebrew_fix") or "auto"))
        theme.apply_mode(self.storage.get_pref("appearance", "Light"))
        ADHD_CONFIG["font_delta"] = int(self.storage.get_pref("font_delta", 0) or 0)

        ctk.set_appearance_mode("Dark" if theme.current_mode() == "Dark" else "Light")
        ctk.set_default_color_theme("green")

        self.title(APP_TITLE)
        self._apply_window_icon()
        self._fit_to_screen()
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.db = DatabaseManager()
        self.analytics = AnalyticsEngine()
        self.session_store = SessionStateManager()
        self.adaptive_engine = AdaptiveEngine(self.storage)
        self.srs = SpacedRepetition(self.storage)
        self.speaker = Speaker(enabled=bool(self.storage.get_pref("tts", False)))
        self.current_subject = None
        self.current_session = None
        self.current_mode = "practice"
        self.focus_mode = False
        self.appearance = theme.current_mode()
        self.active_tab = "dashboard"
        self._studio_ok = False
        self._studio_taps = 0
        self._update_busy = False
        self._rebuilding = False
        self._chrome_job = None

        self._build_shell()
        self.toasts = ToastHost(self)
        self._bind_keys()
        threading.Thread(target=self._preload_banks, daemon=True).start()
        self._choose_start_screen()
        self._boot_job = self.after(1800, self._boot_network_tasks)
        self._nudge_job = self.after(2600, self._maybe_reminder_nudge)
        log.info("window ready")

    # ---------- תשתית ----------
    def _apply_window_icon(self) -> None:
        if os.path.isfile(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass
        if os.path.isfile(ICON_PNG_PATH):
            try:
                from core.display import dip
                from PIL import Image, ImageTk

                size = max(32, dip(32))
                src = Image.open(ICON_PNG_PATH).convert("RGBA")
                icon = src.resize((size, size), Image.Resampling.LANCZOS)
                self._icon_image = ImageTk.PhotoImage(icon)
                self.iconphoto(True, self._icon_image)
            except Exception:
                try:
                    self._icon_image = tk.PhotoImage(file=ICON_PNG_PATH)
                    self.iconphoto(True, self._icon_image)
                except Exception:
                    log.exception("window icon png")

    def _fit_to_screen(self):
        """חלון שנכנס למסך. קודם הוא היה 1280x820 וחתך תוכן במסכים נמוכים."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1360, max(980, screen_w - 60))
        height = min(860, max(560, screen_h - 120))
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 2 - 20)
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.minsize(980, 540)
        log.info("screen=%sx%s window=%sx%s", screen_w, screen_h, width, height)

    def _on_crash(self, exc):
        try:
            telemetry.send_crash(self.storage, exc)
        except Exception:
            pass
        try:
            dialogs.error(
                "שגיאה",
                f"קרתה תקלה והיא נרשמה ביומן.\n\n{type(exc).__name__}: {exc}\n\nהיומן: {applog.LOG_PATH}",
            )
        except Exception:
            pass

    def _preload_banks(self):
        for key in ALL_SUBJECTS:
            try:
                load_subject(key)
            except Exception as exc:
                log.warning("preload failed for %s: %s", key, exc)

    def _ui_after(self, ms, fn):
        try:
            return self.after(ms, fn)
        except (tk.TclError, RuntimeError):
            return None

    def _cancel_idle_jobs(self):
        for attr in ("_boot_job", "_nudge_job", "_chrome_job"):
            job = getattr(self, attr, None)
            if job is None:
                continue
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
            setattr(self, attr, None)

    def destroy(self):
        self._cancel_idle_jobs()
        host = getattr(self, "toasts", None)
        if host is not None:
            host.dismiss()
        try:
            super().destroy()
        except tk.TclError:
            pass

    def _on_close(self):
        log.info("closing app")
        self._cancel_idle_jobs()
        try:
            self.speaker.stop()
            self.storage.close()
            self.db.close()
        except Exception as exc:
            log.warning("cleanup on close failed: %s", exc)
        finally:
            try:
                self.quit()
            except tk.TclError:
                pass
            try:
                self.destroy()
            except tk.TclError:
                pass

    def _set_window_title(self, *parts: str) -> None:
        bits = [APP_TITLE]
        for part in parts:
            text = str(part or "").strip()
            if text:
                bits.append(text)
        try:
            self.title("  ·  ".join(bits))
        except tk.TclError:
            pass

    def _toast(self, title: str, detail: str = "", kind: str = "info") -> None:
        if self.current_mode in {"mock", "final", "timed", "general", "meimad"}:
            return
        host = getattr(self, "toasts", None)
        if host is not None:
            host.show(title, detail, kind=kind)

    def _build_shell(self):
        self._want_nav = False
        self._want_rail = False
        self._chrome_state = None
        self.sidebar = Sidebar(self, on_nav=self._nav)
        self.rail = ContextRail(self, on_weak=self._open_weak_from_rail)
        self.scroll = FastScroll(self, bg=COLORS["bg"], max_width=PAGE_WIDTH)
        self.content = self.scroll.body
        self._apply_chrome()

    def _bind_keys(self):
        self.bind("<Key>", self._on_key)
        self.bind("<Escape>", lambda _e: self._on_escape())
        self.bind("<Control-Shift-D>", lambda _e: self._open_studio())
        self.bind("<Control-Shift-d>", lambda _e: self._open_studio())
        self.bind("<Configure>", self._on_shell_configure, add="+")

    def _on_key(self, event):
        screen = self._active_screen()
        if screen is not None and hasattr(screen, "on_key"):
            try:
                screen.on_key(event)
            except Exception as exc:
                log.warning("key handler failed: %s", exc)

    def _on_escape(self):
        if self.current_session and self.current_mode in {"mock", "final", "timed", "general", "meimad"}:
            return
        if self.active_tab == "studio":
            self._leave_studio()
            return
        self._nav("dashboard")

    def _active_screen(self):
        for widget in self.content.winfo_children():
            if isinstance(widget, (PracticeScreen, LessonScreen)):
                return widget
        return None

    def _nav(self, key: str):
        with applog.timed(f"nav {key}"):
            self.active_tab = key
            if key == "dashboard":
                self._show_dashboard()
            elif key == "subjects":
                self._show_dashboard()
            elif key == "meimad":
                self._show_meimad_hub()
            elif key == "general_exam":
                self._show_general_exam_hub()
            elif key == "mistakes":
                self._show_mistakes()
            elif key == "settings":
                self._show_settings()
            elif key == "about":
                self._show_about()
            elif key == "studio":
                self._open_studio()

    def _on_shell_configure(self, event):
        if event.widget is not self:
            return
        if getattr(self, "_rebuilding", False):
            return
        job = getattr(self, "_chrome_job", None)
        if job is not None:
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
        try:
            self._chrome_job = self.after_idle(self._flush_chrome)
        except tk.TclError:
            self._chrome_job = None

    def _flush_chrome(self):
        self._chrome_job = None
        if getattr(self, "_rebuilding", False):
            return
        try:
            if self.winfo_exists():
                self._apply_chrome()
        except tk.TclError:
            pass

    def _rail_fits(self) -> bool:
        try:
            width = int(self.winfo_width() or 0)
        except tk.TclError:
            width = 0
        if width < 50:
            width = 1280
        return width >= RAIL_BREAKPOINT

    def _show_chrome(self):
        self._set_chrome(nav=True, rail=False, refresh=False)

    def _set_chrome(self, nav: bool | None = None, rail: bool | None = None, refresh: bool = True):
        if nav is not None:
            self._want_nav = bool(nav)
        if rail is not None:
            self._want_rail = bool(rail)
        self._apply_chrome(refresh=refresh)

    def _apply_chrome(self, refresh: bool = False):
        sidebar = getattr(self, "sidebar", None)
        rail = getattr(self, "rail", None)
        scroll = getattr(self, "scroll", None)
        if sidebar is None or rail is None or scroll is None:
            return
        try:
            if not sidebar.winfo_exists() or not rail.winfo_exists() or not scroll.winfo_exists():
                return
        except tk.TclError:
            return
        show_nav = bool(getattr(self, "_want_nav", False))
        show_rail = False
        state = (show_nav, show_rail)
        changed = state != getattr(self, "_chrome_state", None)
        if changed:
            self._chrome_state = state
            try:
                self.sidebar.pack_forget()
                self.rail.pack_forget()
                self.scroll.pack_forget()
            except tk.TclError:
                return
            if show_nav:
                self.sidebar.pack(side="right", fill="y", padx=(8, 16), pady=16)
            pad_left = 24
            pad_right = 8 if show_nav else 24
            self.scroll.pack(side="left", fill="both", expand=True, padx=(pad_left, pad_right), pady=16)
        if show_nav:
            if changed or refresh:
                self._refresh_sidebar()
            else:
                try:
                    self.sidebar.set_active(self.active_tab)
                except tk.TclError:
                    pass
        if (changed or refresh) and show_rail:
            self._refresh_rail()

    def _open_weak_from_rail(self, key: str):
        if key and not is_coming_soon(key):
            self._show_subject_hub(key)

    def _overall_level_he(self) -> str:
        levels = [self.adaptive_engine.level_of(key) for key in ALL_SUBJECTS]
        if "advanced" in levels:
            return LEVEL_HE["advanced"]
        if "intermediate" in levels:
            return LEVEL_HE["intermediate"]
        return LEVEL_HE["beginner"]

    def _refresh_sidebar(self):
        student = self.storage.get_student() or {}
        level_he = self._overall_level_he()
        xp_val = int(self.storage.get("xp", 0) or 0)
        level = 1 + xp_val // 100
        streak = self.storage.get_streak().get("current", 0)
        self.sidebar.set_user(student.get("name") or "תלמיד", level_he, streak, level)
        self.sidebar.set_active(self.active_tab)

    def _refresh_rail(self):
        snapshot = self.storage.get_learning_snapshot()
        daily = snapshot.get("daily_goal") or {}
        overall = snapshot.get("overall") or {}
        weak = snapshot.get("weak_subjects") or []
        days = self.storage.days_to_exam()
        exam_when = ""
        exam_label = ""
        if days is not None:
            target = self.storage.get_exam_date() or {}
            exam_label = target.get("label") or "מבחן יעד"
            if days == 0:
                exam_when = "היום"
            elif days > 0:
                exam_when = f"בעוד {days} ימים"
            else:
                exam_when = "התאריך עבר"
        weak_key = weak[0] if weak else None
        mastery = snapshot.get("mastery") or {}
        week = [
            int((mastery.get(key) or {}).get("accuracy") or (18 + i * 14))
            for i, key in enumerate(HOME_SUBJECTS[:5])
        ]
        alerts = []
        if exam_when:
            alerts.append(f"{exam_label}: {exam_when}")
        if weak_key:
            alerts.append(f"לחיזוק: {subject_label(weak_key)}")
        self.rail.set_data(
            {
                "daily": daily,
                "streak": self.storage.get_streak().get("current", 0),
                "accuracy": overall.get("accuracy", 0),
                "exam_when": exam_when,
                "exam_label": exam_label,
                "weak_label": subject_label(weak_key) if weak_key else "",
                "weak_key": weak_key,
                "mistakes": len(self.storage.get_mistakes() or []),
                "due": self.srs.due_count(),
                "week": week,
                "alerts": alerts,
            }
        )

    def _clear(self):
        try:
            children = list(self.content.winfo_children())
        except tk.TclError:
            return
        for widget in children:
            try:
                widget.destroy()
            except tk.TclError:
                pass
        scroll = getattr(self, "scroll", None)
        if scroll is not None:
            try:
                scroll.to_top()
            except tk.TclError:
                pass

    def _rebuild_shell(self):
        """אחרי שינוי ערכת צבע או גודל גופן: סרגל מחדש, הגלילה נשארת כדי לא לקרוס."""
        tab = self.active_tab
        self._rebuilding = True
        try:
            try:
                self.focus_set()
            except tk.TclError:
                pass
            for attr in ("sidebar", "rail"):
                widget = getattr(self, attr, None)
                if widget is None:
                    continue
                try:
                    widget.destroy()
                except tk.TclError:
                    pass
            try:
                self.configure(fg_color=COLORS["bg"])
                scroll = getattr(self, "scroll", None)
                if scroll is not None and scroll.winfo_exists():
                    scroll.set_bg(COLORS["bg"])
                    scroll.to_top()
            except tk.TclError:
                pass
            self.sidebar = Sidebar(self, on_nav=self._nav)
            self.rail = ContextRail(self, on_weak=self._open_weak_from_rail)
            self._chrome_state = None
            self._apply_chrome(refresh=True)
            self._nav(tab if tab in {"dashboard", "subjects", "meimad", "general_exam", "mistakes", "settings", "about", "studio"} else "dashboard")
        finally:
            self._rebuilding = False

    def _choose_start_screen(self):
        if self.storage.has_profile() and self.storage.get_diagnostic():
            self._show_chrome()
            self._show_dashboard()
        else:
            self._set_chrome(nav=False, rail=False)
            self._show_onboarding()

    def _boot_network_tasks(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        threading.Thread(target=self._boot_network_worker, daemon=True).start()

    def _boot_network_worker(self):
        try:
            telemetry.maybe_hello(self.storage)
            telemetry.maybe_weekly(self.storage)
        except Exception as exc:
            log.info("telemetry boot skipped: %s", exc)
        try:
            from core import health

            report = health.scan_and_repair(self)
            if report.get("crash"):
                from core.i18n import block, ui as i18n_ui

                self._ui_after(
                    0,
                    lambda: self._safe_ui(
                        lambda: dialogs.info(i18n_ui("dlg.health"), block("crash.boot"))
                    ),
                )
        except Exception as exc:
            log.info("health scan skipped: %s", exc)
        if self.storage.get_pref("auto_update_check", True):
            self._run_update_check(manual=False)

    def _pack_update_card(self, parent):
        pending = self.storage.get_pref("pending_update") or {}
        if not isinstance(pending, dict) or not pending.get("newer"):
            return
        latest = pending.get("latest") or ""
        if not updates.is_newer(str(latest), VERSION):
            self.storage.set_pref("pending_update", {})
            return
        card, inner = make_card(parent, accent=COLORS["primary"], pady=12)
        card.pack(fill="x", pady=(0, 10))
        fast_label(
            inner,
            f"יש עדכון {latest} (אצלך {VERSION})",
            size=16, bold=True, bg=COLORS["card_bg"],
        ).pack(anchor="e")
        notes = str(pending.get("notes") or pending.get("message") or "").strip()
        if notes:
            fast_label(inner, notes, size=13, muted=True, bg=COLORS["card_bg"], wrap=780).pack(
                anchor="e", pady=(4, 0)
            )
        row = tk.Frame(inner, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=(8, 0))
        ModernButton(
            row, text=rtl(i18n.ui("btn.update_now")), width=180,
            command=self._install_pending_update,
        ).pack(side="right", padx=5)
        GhostButton(
            row, text=rtl(i18n.ui("nav.settings")), width=140,
            command=lambda: self._nav("settings"),
        ).pack(side="right", padx=5)

    def _run_update_check(self, manual: bool = False):
        if getattr(self, "_update_busy", False):
            if manual:
                dialogs.info("עדכון", "בדיקה או התקנה כבר רצה.")
            return
        if manual:
            self.storage.set_pref("update_status", "בודק עדכון ברשת…")
            if self.active_tab == "settings":
                self._show_settings()
        threading.Thread(target=self._update_check_worker, args=(manual,), daemon=True).start()

    def _update_check_worker(self, manual: bool):
        try:
            result = updates.check_latest()
        except Exception as exc:
            result = {
                "ok": False,
                "newer": False,
                "current": VERSION,
                "latest": VERSION,
                "message": f"הבדיקה נכשלה: {exc}",
            }
        self._ui_after(0, lambda r=result, m=manual: self._safe_ui(lambda: self._apply_update_check(r, m)))

    def _apply_update_check(self, result: dict, manual: bool):
        status = str(result.get("message") or "")
        self.storage.set_pref("update_status", status)
        if result.get("ok") and result.get("newer"):
            pending = {
                key: result[key]
                for key in (
                    "newer", "latest", "current", "notes", "download",
                    "windows_setup", "windows_zip", "linux_portable", "page", "source", "message",
                )
                if key in result
            }
            self.storage.set_pref("pending_update", pending)
            auto = bool(self.storage.get_pref("auto_update_check", True))
            has_file = bool(
                pending.get("download")
                or pending.get("windows_setup")
                or pending.get("windows_zip")
                or pending.get("linux_portable")
            )
            if auto and has_file and not manual and not getattr(self, "_update_busy", False):
                self._update_busy = True
                self.storage.set_pref("update_status", "מוריד את העדכון החלק אוטומטית…")
                threading.Thread(
                    target=self._install_update_worker, args=(pending,), daemon=True,
                ).start()
        elif result.get("ok"):
            self.storage.set_pref("pending_update", {})
        if manual:
            dialogs.info("עדכון", status)
        if self.active_tab == "settings":
            self._show_settings()
        elif self.active_tab == "dashboard" and result.get("newer"):
            self._show_dashboard()

    def _install_pending_update(self):
        pending = self.storage.get_pref("pending_update") or {}
        if not isinstance(pending, dict) or not pending.get("newer"):
            dialogs.info("עדכון", "אין עדכון ממתין. לחצו «בדוק עדכון» קודם, או התקינו מקובץ.")
            return
        latest = pending.get("latest") or ""
        if not updates.is_newer(str(latest), VERSION):
            self.storage.set_pref("pending_update", {})
            dialogs.info("עדכון", "התוכנה כבר מעודכנת.")
            return
        if not dialogs.confirm(
            "עדכון",
            f"להוריד ולהתקין גרסה {latest}?\nההתקדמות בלימוד לא תימחק. התוכנה עלולה להיסגר לרגע.",
        ):
            return
        if getattr(self, "_update_busy", False):
            return
        self._update_busy = True
        self.storage.set_pref("update_status", "מוריד ומעדכן…")
        if self.active_tab == "settings":
            self._show_settings()
        threading.Thread(target=self._install_update_worker, args=(pending,), daemon=True).start()

    def _install_update_worker(self, pending: dict):
        try:
            result = updates.download_and_apply(pending)
        except Exception as exc:
            result = {"ok": False, "message": f"ההתקנה נכשלה: {exc}"}
        self._ui_after(0, lambda r=result: self._safe_ui(lambda: self._after_apply_update(r)))

    def _after_apply_update(self, result: dict):
        self._update_busy = False
        message = str(result.get("message") or "לא הצליח.")
        self.storage.set_pref("update_status", message)
        if result.get("ok"):
            dialogs.info("עדכון", message)
            if result.get("restart"):
                self._on_close()
                return
        else:
            dialogs.error("עדכון", message)
        if self.active_tab == "settings":
            self._show_settings()

    def _pick_update_file(self):
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="קובץ עדכון של StudyApp",
            filetypes=[
                ("קובץ התקנה", "*.exe"),
                ("ZIP", "*.zip"),
                ("חבילת לינוקס", "*.gz"),
                ("כל הקבצים", "*.*"),
            ],
        )
        if not path:
            return
        if not dialogs.confirm(
            "עדכון מקובץ",
            f"להתקין מ:\n{path}\n\nההתקדמות בלימוד לא תימחק.",
        ):
            return
        self._update_busy = True
        try:
            result = updates.apply_local_file(path)
        except Exception as exc:
            result = {"ok": False, "message": f"ההתקנה נכשלה: {exc}"}
        self._after_apply_update(result)

    def _toggle_auto_update(self):
        current = bool(self.storage.get_pref("auto_update_check", True))
        self.storage.set_pref("auto_update_check", not current)
        if self.active_tab == "settings":
            self._show_settings()

    def _toggle_telemetry(self):
        current = bool(self.storage.get_pref("telemetry_opt_in", False))
        if current:
            self.storage.set_pref("telemetry_opt_in", False)
            dialogs.info("פינג אנונימי", "כבוי. לא יישלח יותר כלום.")
        else:
            if not dialogs.confirm(
                "פינג אנונימי",
                "יישלח רק: גרסה, מערכת הפעלה, ומזהה אקראי.\n"
                "בלי שם, בלי גיל, בלי תעודת זהות, ובלי שאלות או ציונים.\nלהדליק?",
            ):
                return
            self.storage.set_pref("telemetry_opt_in", True)

            def _hello():
                result = telemetry.send_ping(self.storage, "hello")
                if result.get("ok") and not result.get("queued"):
                    self.storage.set_pref("telemetry_hello_sent", True)

            threading.Thread(target=_hello, daemon=True).start()
        if self.active_tab == "settings":
            self._show_settings()

    # ---------- מסכים ----------
    def _show_onboarding(self):
        self._set_chrome(nav=False, rail=False)
        self._clear()
        self._set_window_title("הרשמה")
        OnboardingFrame(self.content, storage=self.storage, on_done=self._after_onboarding).pack(
            fill="both", expand=True
        )

    def _after_onboarding(self):
        self.active_tab = "dashboard"
        self._show_chrome()
        self._show_dashboard()

    def _dashboard_rail_visible(self) -> bool:
        return bool(getattr(self, "_want_rail", False)) and self._rail_fits() and not self.focus_mode

    def _exam_when_line(self) -> str:
        days = self.storage.days_to_exam()
        if days is None:
            return ""
        target = self.storage.get_exam_date() or {}
        label = (target.get("label") or "מבחן").strip()
        if days == 0:
            when = "היום"
        elif days > 0:
            when = f"בעוד {days} ימים"
        else:
            when = "התאריך עבר"
        return f"{label}  ·  {when}"

    @staticmethod
    def _grid_rtl(grid, widget, index: int, columns: int = 2, padx: int = 6, pady: int = 6):
        row, offset = divmod(index, columns)
        widget.grid(row=row, column=columns - 1 - offset, sticky="nsew", padx=padx, pady=pady)

    def _show_dashboard(self):
        """הבית: ברכה וקיצור למקצועות, בלי כרטיס צעד ובלי עמודת סטטיסטיקה."""
        self.active_tab = "dashboard"
        self._show_chrome()
        try:
            self._refresh_sidebar()
        except tk.TclError:
            pass
        self._clear()
        self._set_window_title("הבית")
        student = self.storage.get_student() or {}
        snapshot = self.storage.get_learning_snapshot()
        daily = snapshot.get("daily_goal", {})
        mastery = snapshot.get("mastery", {})
        level_he = self._overall_level_he()

        StudioHero(
            self.content,
            name=student.get("name") or "תלמיד",
            level_he=level_he,
            daily=daily,
            exam_line=self._exam_when_line(),
            streak=int(self.storage.get_streak().get("current", 0) or 0),
        ).pack(fill="x", pady=(0, 10))
        self._pack_update_card(self.content)

        heading(self.content, "מקצועות", 15).pack(anchor="e", pady=(2, 4))
        self._pack_subject_grid(mastery, HOME_SUBJECTS)
        heading(self.content, "מקצועות בחירה", 15).pack(anchor="e", pady=(10, 2))
        body(
            self.content,
            "ערבית ועזרה ראשונה בהכנה. מופיעים כאן, עדיין אי אפשר להיכנס.",
            muted=True,
        ).pack(anchor="e", pady=(0, 4))
        self._pack_subject_grid(mastery, ELECTIVE_SUBJECTS)

    def _pack_subject_grid(self, mastery: dict, keys: list[str]):
        grid = tk.Frame(self.content, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1, uniform="dash")
        grid.columnconfigure(1, weight=1, uniform="dash")
        index = 0
        for key in keys:
            if key not in SUBJECTS:
                continue
            info = mastery.get(key) or {}
            tile = CompactSubjectTile(
                grid, key, LEVEL_HE.get(self.adaptive_engine.level_of(key), "מתחיל"),
                float(info.get("accuracy") or 0), int(info.get("total") or 0),
                on_open=lambda k=key: self._show_subject_hub(k),
                coming_soon=is_coming_soon(key),
            )
            self._grid_rtl(grid, tile, index, padx=5, pady=4)
            index += 1

    def _pack_next_action(self, nxt: dict, note: str = ""):
        detail = nxt.get("detail") or ""
        if note:
            detail = f"{detail}\n{note}".strip()
        StartLessonCard(
            self.content,
            kicker_text="הצעד הבא",
            title=nxt.get("title") or "למקצועות",
            detail=detail,
            button=nxt.get("title") or "המשך",
            command=lambda: self._run_next_action(nxt),
        ).pack(fill="x", pady=(0, 14))

    def _run_next_action(self, nxt: dict):
        kind = nxt.get("id")
        if kind == "resume":
            self._restore_last_session()
        elif kind == "review":
            self._start_daily_review()
        elif kind == "mistakes":
            self._start_mistake_drill()
        elif kind == "weak":
            key = nxt.get("subject")
            if key:
                self._start_mode(key, "practice")
            else:
                self._start_smart_practice()
        elif kind == "unpracticed":
            key = nxt.get("subject")
            if key:
                self._show_subject_hub(key)
            else:
                self._nav("subjects")
        else:
            self._nav("subjects")

    def _review_pool(self) -> list[dict]:
        pool: list[dict] = []
        for key in ALL_SUBJECTS:
            data = load_subject(key) or {}
            pool.extend(self._clean_pool(data.get("questions") or []))
        return pool

    def _start_daily_review(self):
        questions = self.srs.due_questions(self._review_pool(), limit=REVIEW_BATCH)
        if not questions:
            dialogs.info("חזרה", "אין כרגע שאלות שממתינות לחזרה.")
            return
        self.current_subject = subject_key(questions[0].get("subject") or "hebrew")
        self.current_mode = "review"
        self.current_session = ExamSession(
            questions, mode="practice", subject_key=self.current_subject
        )
        self.session_store.save(self.current_session.to_state(self.current_subject))
        log.info("daily review started with %s questions", len(questions))
        self._render_practice()

    def _show_subjects(self):
        self._show_dashboard()

    def _show_mistakes(self):
        self.active_tab = "mistakes"
        self._show_chrome()
        self._clear()
        self._set_window_title("הטעויות שלי")
        MistakesScreen(
            self.content,
            mistakes=self.storage.get_mistakes(),
            on_drill=self._start_mistake_drill,
            on_clear=self._clear_mistakes,
        ).pack(fill="both", expand=True)

    def _clear_mistakes(self):
        if not dialogs.confirm("ניקוי", "למחוק את כל רשימת הטעויות?"):
            return
        self.storage.forget_mistakes()
        self._show_mistakes()

    def _show_settings(self):
        self.active_tab = "settings"
        self._show_chrome()
        self._clear()
        self._set_window_title("הגדרות")
        SettingsScreen(
            self.content,
            storage=self.storage,
            focus_on=self.focus_mode,
            on_focus=self._toggle_focus_mode,
            on_reset=self._reset_learning,
            on_theme=self._set_theme,
            appearance=self.appearance,
            on_font=self._set_font_size,
            on_export=self._export_data,
            on_import=self._import_data,
            on_logs=self._open_logs,
            on_exam_date=self._save_exam_date,
            on_tts=self._toggle_tts,
            tts_on=self.speaker.enabled,
            on_clear_reports=self._clear_reports,
            on_check_update=lambda: self._run_update_check(manual=True),
            on_install_update=self._install_pending_update,
            on_pick_update=self._pick_update_file,
            on_auto_update=self._toggle_auto_update,
            update_status=str(self.storage.get_pref("update_status") or ""),
            pending_update=self.storage.get_pref("pending_update") or {},
            on_telemetry=self._toggle_telemetry,
            telemetry_on=bool(self.storage.get_pref("telemetry_opt_in", False)),
            profile_name=profiles.current_name(),
            profile_names=[item.get("name") or "תלמיד" for item in profiles.list_profiles()],
            on_switch_profile=self._switch_profile,
            on_add_profile=self._add_profile,
            on_delete_profile=self._delete_profile,
            on_parent_report=self._export_parent_report,
            on_question_editor=self._show_question_editor,
            on_open_data=self._open_data_folder,
            on_toggle_autostart=self._toggle_autostart,
            autostart_on=bool(profiles.get_os_pref("autostart", False)),
            on_toggle_reminder=self._toggle_reminder,
            reminder_on=bool(profiles.get_os_pref("daily_reminder", False)),
            reminder_time=f"{int(profiles.get_os_pref('reminder_hour', 17)):02d}:{int(profiles.get_os_pref('reminder_minute', 0)):02d}",
            on_save_reminder_time=self._save_reminder_time,
            on_install_shortcuts=self._install_os_shortcuts,
            on_test_notify=self._test_notify,
            on_secret=self._open_studio,
            on_health=self._run_health_scan,
            on_helper_lang=self._set_helper_lang,
            helper_lang=i18n.get_lang(),
            on_hebrew_fix=self._set_hebrew_fix,
            hebrew_fix=str(self.storage.get_pref("hebrew_fix") or "auto"),
        ).pack(fill="both", expand=True)

    def _set_hebrew_fix(self, mode: str):
        from core import rtltext

        rtltext.set_mode(mode)
        self.storage.set_pref("hebrew_fix", mode)
        try:
            self.sidebar.destroy()
        except Exception:
            pass
        self.sidebar = Sidebar(self, on_nav=self._nav)
        self._chrome_state = None
        self._show_settings()

    def _set_helper_lang(self, code: str):
        i18n.set_lang(code)
        self.storage.set_pref(i18n.PREF_KEY, code)
        try:
            self.sidebar.destroy()
        except Exception:
            pass
        self.sidebar = Sidebar(self, on_nav=self._nav)
        self._chrome_state = None
        self._show_settings()

    def _run_health_scan(self):
        from core import health

        report = health.scan_and_repair(self)
        dialogs.info(i18n.ui("dlg.health"), report.get("message") or i18n.block("health.ok", version=VERSION))
        if self.active_tab == "settings":
            self._show_settings()

    def _clear_reports(self):
        if not dialogs.confirm("דיווחים", "לנקות את כל הדיווחים? השאלות יחזרו לתרגול."):
            return
        self.storage.clear_reports()
        self._show_settings()

    def _show_about(self):
        self.active_tab = "about"
        self._show_chrome()
        self._clear()
        self._set_window_title("אודות")
        AboutScreen(self.content, on_secret=self._open_studio).pack(fill="both", expand=True)

    def _open_studio(self):
        if self.current_session and self.current_mode in {
            "mock", "final", "timed", "general", "meimad",
        }:
            return
        self.active_tab = "studio"
        self._set_chrome(nav=False, rail=False)
        try:
            self.scroll.set_bg("#000000")
            self.configure(fg_color="#000000")
        except Exception:
            pass
        self._clear()
        self._set_window_title("חדר מפתח")
        StudioScreen(
            self.content,
            unlocked=self._studio_ok,
            on_auth=self._studio_auth,
            on_exit=self._leave_studio,
            actions={
                "info": lambda: studio_brief.info_text(self.storage),
                "brief": lambda: studio_brief.briefing(self.storage),
                "editor": self._studio_editor,
                "data": self._studio_open_data,
                "logs": self._studio_open_logs,
                "tail": lambda: applog.read_recent(40),
                "skip_diag": self._studio_skip_diag,
                "unlock": self._studio_unlock,
                "update": lambda: self._run_update_check(manual=True) or "בדיקת העדכון התחילה.",
                "report": self._export_parent_report,
                "json": self._studio_open_json,
                "cache": self._studio_clear_cache,
                "pack_files": self._studio_pack_files,
                "pack_usb": self._studio_pack_usb,
                "project": self._studio_open_project,
                "vscode": self._studio_open_vscode,
                "backup": self._studio_backup_student,
                "restore": self._studio_restore_student,
                "build": self._studio_build_windows,
                "jump": self._show_subject_hub,
            },
        ).pack(fill="both", expand=True)

    def _studio_auth(self, ok: bool):
        self._studio_ok = bool(ok)

    def _leave_studio(self):
        try:
            self.scroll.set_bg(COLORS["bg"])
            self.configure(fg_color=COLORS["bg"])
        except Exception:
            pass
        self._show_chrome()
        self._show_dashboard()

    def _studio_editor(self):
        self.active_tab = "studio"
        self._set_chrome(nav=False, rail=False)
        self._clear()
        QuestionEditorScreen(self.content, on_back=self._open_studio).pack(fill="both", expand=True)
        return "עורך השאלות נפתח."

    def _studio_skip_diag(self):
        from core.diagnostic import EXAM_LENGTH

        student = self.storage.get_student() or {}
        if not student.get("name"):
            self.storage.save_student("מפתח", 18, "")
        self.storage.save_diagnostic(
            EXAM_LENGTH, EXAM_LENGTH, "advanced", [],
            recommendations=[], weak_topics=[],
        )
        return "האבחון דולג. הפרופיל סומן כמתקדם."

    def _studio_unlock(self):
        self.storage.set_pref("studio_unlock_gates", True)
        return "המבחן הסופי והמבחן הכללי פתוחים בפרופיל הזה."

    def _studio_open_json(self):
        from core.config import QUESTIONS_DIR

        if not nativeos.open_path(QUESTIONS_DIR):
            dialogs.info("מאגר", QUESTIONS_DIR)
        return f"תיקיית השאלות:\n{QUESTIONS_DIR}"

    def _studio_clear_cache(self):
        from core.loader import clear_cache

        clear_cache()
        return "המטמון נוקה. הטעינה הבאה תקרא שוב את קבצי השאלות."

    def _studio_open_data(self):
        folder = get_persistent_app_dir()
        if not nativeos.open_path(folder):
            dialogs.info("נתונים", folder)
        return f"תיקיית הנתונים:\n{folder}"

    def _studio_open_logs(self):
        if not nativeos.open_path(applog.LOG_DIR):
            dialogs.info("יומן", applog.LOG_DIR)
        return f"תיקיית היומן:\n{applog.LOG_DIR}"

    def _studio_open_project(self):
        from core.studio_pack import project_root

        folder = project_root()
        if not nativeos.open_path(folder):
            dialogs.info("קוד", folder)
        return f"תיקיית הקוד:\n{folder}\nאפשר לפתוח אותה ב-VS Code: File ואז Open Folder."

    def _studio_open_vscode(self):
        from core.studio_pack import project_root

        folder = project_root()
        if nativeos.open_in_vscode(folder):
            return f"נפתח ב-VS Code:\n{folder}"
        return (
            "לא מצאתי את VS Code.\n"
            "פתחו ידנית: File ואז Open Folder, ובחרו את תיקיית הקוד.\n"
            f"{folder}"
        )

    def _studio_backup_student(self):
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            title="גיבוי נתוני תלמיד",
            defaultextension=".json",
            initialfile="studyapp-backup.json",
            filetypes=[("StudyApp backup", "*.json")],
        )
        if not path:
            return "בוטל."
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.storage.export_bundle(), handle, ensure_ascii=False, indent=2)
        nativeos.open_path(os.path.dirname(path))
        return f"גיבוי הנתונים נשמר:\n{path}"

    def _studio_restore_student(self):
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="טעינת גיבוי תלמיד",
            filetypes=[("StudyApp backup", "*.json")],
        )
        if not path:
            return "בוטל."
        if not dialogs.confirm("טעינת גיבוי", "הנתונים הנוכחיים יוחלפו. להמשיך?"):
            return "בוטל."
        with open(path, "r", encoding="utf-8") as handle:
            bundle = json.load(handle)
        if not self.storage.import_bundle(bundle):
            return "הקובץ לא נראה כמו גיבוי של StudyApp."
        return "הנתונים נטענו. אפשר לחזור לתוכנה."

    def _studio_build_windows(self):
        import subprocess

        from core.config import BASE_DIR

        script = os.path.join(BASE_DIR, "tools", "build_release.py")
        if not os.path.isfile(script):
            return "לא מצאתי את כלי הבנייה."
        flags = int(getattr(subprocess, "CREATE_NEW_CONSOLE", 0) or 0)
        subprocess.Popen(
            [sys.executable, script, "--windows"],
            cwd=BASE_DIR,
            creationflags=flags,
        )
        return "נפתח חלון בניית התקנה. כשזה נגמר, החבילה תהיה בתיקיית dist."

    def _studio_pack_files(self):
        from tkinter import filedialog

        from core.studio_pack import write_source_zip

        path = filedialog.asksaveasfilename(
            title="שמירת קבצי תוכנה",
            defaultextension=".zip",
            initialfile="StudyAppFiles.zip",
            filetypes=[("ZIP", "*.zip")],
        )
        if not path:
            return "בוטל."
        write_source_zip(path)
        nativeos.open_path(os.path.dirname(path))
        return (
            f"נשמרו קבצי התוכנה:\n{path}\n\n"
            "זה קוד המקור המלא (StudyApp Files).\n"
            "חלצו את התיקייה StudyAppFiles ופתחו אותה ב-VS Code."
        )

    def _studio_pack_usb(self):
        from tkinter import filedialog

        from core.studio_pack import write_usb_zip

        path = filedialog.asksaveasfilename(
            title="חבילת דיסק און קי",
            defaultextension=".zip",
            initialfile="StudyApp-USB.zip",
            filetypes=[("ZIP", "*.zip")],
        )
        if not path:
            return "בוטל."
        write_usb_zip(path)
        nativeos.open_path(os.path.dirname(path))
        return (
            f"נשמרה חבילת הדיסק:\n{path}\n"
            "חלצו את כל התיקייה לדיסק, ואז StudyApp.exe או הפעל-מהדיסק.bat"
        )

    def _pack_meimad_card(self, parent):
        last = (self.storage.get("meimad_last") or {}) if hasattr(self.storage, "get") else {}
        unlocked = can_take_meimad(self.storage)
        card, inner = make_card(
            parent,
            accent=COLORS["primary"] if unlocked else COLORS["card_border"],
            thick=2,
        )
        card.pack(fill="x", pady=(0, 12))
        kicker(inner, "מימ״ד", bg=COLORS["card_bg"]).pack(anchor="e")
        heading(inner, "ישיבת מימ״ד מלאה", 18).pack(anchor="e", pady=(2, 0))
        minutes = (SECTION_SECONDS * len(SECTIONS)) // 60
        fast_label(
            inner,
            f"שלושה פרקים ברצף: עברית, אנגלית, חשבון. "
            f"{PER_SECTION} שאלות לכל פרק, {SECTION_SECONDS // 60} דקות לפרק, {minutes} דקות סה״כ. "
            f"כשנגמר הזמן לפרק, עוברים אוטומטית לבא.",
            size=13, muted=True, bg=COLORS["card_bg"], wrap=780,
        ).pack(anchor="e", pady=(4, 6))
        if last.get("percent") is not None:
            parts = " · ".join(
                f"{row.get('name')}: {row.get('percent')}%"
                for row in (last.get("chapters") or [])
            )
            fast_label(
                inner,
                f"ישיבה אחרונה: {last.get('percent')}%  ·  {parts}  ({last.get('date', '')})",
                size=13, muted=True, bg=COLORS["card_bg"], wrap=780,
            ).pack(anchor="e", pady=(0, 8))
        btns = tk.Frame(inner, bg=COLORS["card_bg"])
        btns.pack(fill="x", pady=(2, 0))
        if unlocked:
            ModernButton(btns, text=rtl("לישיבת מימ״ד"), width=180,
                         command=lambda: self._nav("meimad")).pack(side="right", padx=4)
        else:
            GhostButton(btns, text=rtl("נעול. סיימו אבחון"), width=200,
                        command=lambda: self._nav("dashboard")).pack(side="right", padx=4)

    def _show_meimad_hub(self):
        self.active_tab = "meimad"
        self._show_chrome()
        self._clear()
        page_header(
            self.content,
            "מבחן מימ״ד",
            "שלושה פרקים ברצף, שעון לכל פרק. הציון בסוף, לפי פרקים.",
        )

        for key, name, count, seconds in SECTIONS:
            snap = self.adaptive_engine.snapshot(key)
            card, inner = make_card(self.content, pady=10)
            card.pack(fill="x", pady=4)
            fast_label(
                inner,
                f"{name}  ·  {count} שאלות  ·  {seconds // 60} דקות  ·  רמה כרגע: {snap.get('level_he', 'מתחיל')}",
                size=15, bold=True, bg=COLORS["card_bg"],
            ).pack(anchor="e")
            fast_label(
                inner,
                snap.get("blurb") or "האנליסט יבחר שאלות לפי הרמה במקצוע הזה.",
                size=13, muted=True, bg=COLORS["card_bg"], wrap=760,
            ).pack(anchor="e", pady=(4, 0))

        actions = tk.Frame(self.content, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(8, 10))
        if can_take_meimad(self.storage):
            ModernButton(actions, text=rtl("התחלת ישיבה"), width=200,
                         command=self._start_meimad_exam).pack(side="right", padx=5)
        else:
            GhostButton(actions, text=rtl("קודם סיימו אבחון"), width=220,
                        command=lambda: self._nav("dashboard")).pack(side="right", padx=5)

    def _start_meimad_exam(self):
        if not can_take_meimad(self.storage):
            dialogs.info("נעול", "סיימו את האבחון הקצר ואז אפשר לשבת לישיבת מימ״ד.")
            return
        if not dialogs.confirm(
            "ישיבת מימ״ד",
            f"שלושה פרקים: עברית, אנגלית, חשבון.\n"
            f"{PER_SECTION} שאלות ו־{SECTION_SECONDS // 60} דקות לכל פרק.\n"
            f"כשנגמר הזמן לפרק, עוברים אוטומטית הלאה.\n"
            f"בלי הסבר באמצע. הציון לפי פרקים בסוף.\n\nלהתחיל עכשיו?",
        ):
            return
        built = build_meimad_exam(load_subject)
        questions = built.get("questions") or []
        if len(questions) < PER_SECTION * 2:
            dialogs.error("שגיאה", "אין מספיק שאלות לבנות ישיבה. פתחו מקצוע ותרגלו קודם.")
            return
        self.current_subject = "hebrew"
        self.current_mode = "meimad"
        self.current_session = ExamSession(
            questions, mode="meimad", subject_key="meimad",
            total_limit_sec=built.get("total_limit_sec"),
            chapters=built.get("chapters") or [],
        )
        self.session_store.save(self.current_session.to_state("meimad"))
        log.info("start meimad exam count=%s chapters=%s", len(questions), len(built.get("chapters") or []))
        self._render_practice()

    def _pack_general_exam_card(self, parent):
        status = unlock_progress(self.storage)
        last = self.storage.get_general_exam_report()
        unlocked = bool(status.get("unlocked"))
        border = COLORS["primary"] if unlocked else COLORS["card_border"]
        card, inner = make_card(parent, accent=border, thick=2)
        card.pack(fill="x", pady=(0, 12))
        kicker(inner, "מבחן כללי", bg=COLORS["card_bg"]).pack(anchor="e")
        heading(inner, "50 שאלות אמריקאיות", 18).pack(anchor="e", pady=(2, 0))
        if last:
            fast_label(
                inner,
                f"דוח אחרון: {last.get('percent')}%  ·  Grade {last.get('grade')}  ·  "
                f"Scaled {last.get('scaled')}  ·  רמה {last.get('level_he')}  ({last.get('date', '')})",
                size=13, muted=True, bg=COLORS["card_bg"], wrap=780,
            ).pack(anchor="e", pady=(4, 4))
        if unlocked:
            fast_label(
                inner,
                "50 שאלות רב־ברירה (A-D) מכל המקצועות. בלי הסבר באמצע, 50 דקות, ובסוף דוח רמה מפורט.",
                size=13, muted=True, bg=COLORS["card_bg"], wrap=780,
            ).pack(anchor="e", pady=(0, 8))
        else:
            missing = " · ".join(status.get("missing") or [])
            fast_label(
                inner,
                f"נעול. תרגלו לפחות 50% מכל מקצוע (כ־20 שאלות ייחודיות בכל אחד). "
                f"מוכן: {status.get('ready_subjects')}/{status.get('total_subjects')}. חסר: {missing}",
                size=13, muted=True, bg=COLORS["card_bg"], wrap=780,
            ).pack(anchor="e", pady=(0, 8))
        btns = tk.Frame(inner, bg=COLORS["card_bg"])
        btns.pack(fill="x")
        ModernButton(
            btns, text=rtl("למבחן הכללי"), width=180,
            command=lambda: self._nav("general_exam"),
        ).pack(side="right", padx=4)
        if last:
            GhostButton(
                btns, text=rtl("הדוח האחרון"), width=160,
                command=lambda: self._show_saved_general_report(),
            ).pack(side="right", padx=4)

    def _show_general_exam_hub(self):
        self.active_tab = "general_exam"
        self._show_chrome()
        self._clear()
        status = unlock_progress(self.storage)
        last = self.storage.get_general_exam_report()
        page_header(
            self.content,
            "מבחן כללי",
            "50 שאלות מכל המקצועות. בלי משוב עד הסוף, ואז ציון ודוח.",
        )

        listing = tk.Frame(self.content, bg=COLORS["bg"])
        listing.pack(fill="x", pady=(0, 12))
        for key in HOME_SUBJECTS:
            row = (status.get("rows") or {}).get(key) or {}
            card, inner = make_card(listing, pady=10)
            card.pack(fill="x", pady=4)
            pct = float(row.get("pct") or 0)
            ready = "מוכן" if row.get("ready") else "עוד לא 50%"
            fast_label(
                inner,
                f"{row.get('name', key)}  ·  כיסוי {pct}%  ({row.get('covered', 0)}/{row.get('need', 20)} לפתיחה)  ·  {ready}",
                size=14, bg=COLORS["card_bg"],
            ).pack(anchor="e")
            ProgressBar(
                inner, pct=pct / 100, height=8,
                color=COLORS["primary"] if row.get("ready") else COLORS["accent"],
            ).pack(fill="x", pady=(8, 0))

        actions = tk.Frame(self.content, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(4, 10))
        if status.get("unlocked"):
            ModernButton(
                actions, text=rtl("התחלת מבחן 50 שאלות"), width=240,
                command=self._start_general_exam,
            ).pack(side="right", padx=5)
        else:
            GhostButton(
                actions, text=rtl("עדיין נעול. חזרה לבית"), width=240,
                command=lambda: self._nav("subjects"),
            ).pack(side="right", padx=5)
        if last:
            GhostButton(
                actions, text=rtl("צפייה בדוח האחרון"), width=200,
                command=self._show_saved_general_report,
            ).pack(side="right", padx=5)

    def _start_general_exam(self):
        if not can_take_general_exam(self.storage):
            dialogs.info(
                "המבחן נעול",
                "תרגלו לפחות 50% מכל מקצוע (כ־20 שאלות ייחודיות בכל אחד) כדי לפתוח את המבחן הכללי.",
            )
            self._show_general_exam_hub()
            return
        if not dialogs.confirm(
            "מבחן כללי",
            "50 שאלות אמריקאיות (A-D) מכל המקצועות.\n"
            "50 דקות, בלי הסבר באמצע ובלי חזרה אחורה.\n"
            "בסוף תקבלו ציון 200-800 ודוח לימודי מפורט.\n\nלהתחיל עכשיו?",
        ):
            return
        questions = build_general_exam(load_subject)
        if len(questions) < GENERAL_EXAM_SIZE:
            dialogs.error("שגיאה", "לא הצלחנו לבנות מספיק שאלות למבחן הכללי.")
            return
        self.current_subject = None
        self.current_mode = "general"
        self.current_session = ExamSession(
            questions, mode="general", subject_key="general",
            total_limit_sec=GENERAL_EXAM_SECONDS,
        )
        self.session_store.save(self.current_session.to_state("general"))
        log.info("start general exam count=%s", len(questions))
        self._render_practice()

    def _show_saved_general_report(self):
        report = self.storage.get_general_exam_report()
        if not report:
            dialogs.info("מידע", "עדיין אין דוח מבחן כללי.")
            return
        self.active_tab = "general_exam"
        self._show_chrome()
        self._clear()
        GeneralExamReportScreen(
            self.content, report=report, on_home=self._show_dashboard,
            on_retry=self._show_general_exam_hub,
        ).pack(fill="both", expand=True)

    # ---------- הגדרות ----------
    def _safe_ui(self, fn):
        try:
            if self.winfo_exists():
                fn()
        except tk.TclError:
            pass

    def _windows_set_titlebar_color(self, color_mode: str):
        """CTk מחזיר פוקוס עם after(1, widget.focus). אחרי rebuild זה ווידג'ט מת."""
        try:
            self.focus_set()
        except tk.TclError:
            pass
        try:
            super()._windows_set_titlebar_color(color_mode)
        except tk.TclError:
            try:
                if self.winfo_exists():
                    self.deiconify()
            except tk.TclError:
                pass

    def _set_theme(self, mode: str):
        self.appearance = mode
        self.storage.set_pref("appearance", mode)
        theme.apply_mode(mode)
        log.info("theme -> %s", mode)
        try:
            self.focus_set()
        except tk.TclError:
            pass
        ctk.set_appearance_mode("Dark" if mode == "Dark" else "Light")
        self.active_tab = "settings"
        self._rebuild_shell()

    def _set_font_size(self, label: str):
        delta = FONT_STEPS.get(label, 0)
        ADHD_CONFIG["font_delta"] = delta
        self.storage.set_pref("font_delta", delta)
        self.storage.set_pref("font_label", label)
        log.info("font delta -> %s", delta)
        try:
            self.focus_set()
        except tk.TclError:
            pass
        self.active_tab = "settings"
        self._rebuild_shell()

    def _toggle_tts(self):
        new_state = not self.speaker.enabled
        if new_state and not self.speaker.available:
            dialogs.info("הקראה", "אין מנוע דיבור זמין במחשב הזה.")
            return
        self.speaker.enabled = new_state
        self.storage.set_pref("tts", new_state)
        self._show_settings()

    def _save_exam_date(self, iso_date: str, label: str):
        self.storage.set_exam_date(iso_date, label)
        self._show_settings()

    def _export_data(self):
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            title="שמירת גיבוי",
            defaultextension=".json",
            initialfile="studyapp-backup.json",
            filetypes=[("StudyApp backup", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.storage.export_bundle(), handle, ensure_ascii=False, indent=2)
            log.info("exported backup to %s", path)
            dialogs.info("גיבוי", f"הגיבוי נשמר:\n{path}")
        except Exception as exc:
            log.error("export failed: %s", exc)
            dialogs.error("שגיאה", f"לא הצלחתי לשמור: {exc}")

    def _import_data(self):
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="טעינת גיבוי", filetypes=[("StudyApp backup", "*.json")])
        if not path:
            return
        if not dialogs.confirm("טעינת גיבוי", "הנתונים הנוכחיים יוחלפו. להמשיך?"):
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                bundle = json.load(handle)
            if not self.storage.import_bundle(bundle):
                dialogs.error("שגיאה", "הקובץ לא נראה כמו גיבוי של StudyApp.")
                return
            log.info("imported backup from %s", path)
            dialogs.info("גיבוי", "הנתונים נטענו.")
            self._choose_start_screen()
        except Exception as exc:
            log.error("import failed: %s", exc)
            dialogs.error("שגיאה", f"לא הצלחתי לטעון: {exc}")

    def _open_logs(self):
        if not nativeos.open_path(applog.LOG_DIR):
            dialogs.info("יומן", f"תיקיית היומן:\n{applog.LOG_DIR}")

    def _open_data_folder(self):
        folder = get_persistent_app_dir()
        if not nativeos.open_path(folder):
            dialogs.info("נתונים", f"תיקיית הנתונים:\n{folder}")

    def _rebind_profile_stores(self):
        try:
            self.storage.close()
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass
        files = profiles.current_files()
        self.storage = UserStorage(path=files["user_profile"])
        self.db = DatabaseManager(db_path=files["user_stats"])
        self.analytics = AnalyticsEngine(db_path=files["user_stats"])
        self.session_store = SessionStateManager(path=files["session_state"])
        self.adaptive_engine = AdaptiveEngine(self.storage)
        self.srs = SpacedRepetition(self.storage)
        self.speaker.enabled = bool(self.storage.get_pref("tts", False))
        self.appearance = self.storage.get_pref("appearance", "Light") or "Light"
        theme.apply_mode(self.appearance)
        ADHD_CONFIG["font_delta"] = int(self.storage.get_pref("font_delta", 0) or 0)
        self.current_session = None
        self.current_mode = "practice"

    def _switch_profile(self):
        rows = profiles.list_profiles()
        if len(rows) < 2:
            dialogs.info("פרופילים", "יש פרופיל אחד בלבד. הוסיפו פרופיל חדש קודם.")
            return
        names = [str(item.get("name") or "תלמיד") for item in rows]
        chosen = dialogs.choose("החלפת פרופיל", "באיזה פרופיל להמשיך?", names)
        if not chosen:
            return
        match = next((item for item in rows if item.get("name") == chosen), None)
        if not match or match.get("current"):
            return
        self.storage.close()
        if not profiles.switch_profile(str(match["id"])):
            dialogs.error("פרופילים", "לא הצלחתי להחליף פרופיל.")
            return
        self._rebind_profile_stores()
        log.info("switched profile to %s", match.get("id"))
        self._choose_start_screen()

    def _add_profile(self):
        name = dialogs.ask_text("פרופיל חדש", "שם התלמיד או התלמידה:", "אח/ות")
        if name is None:
            return
        pid = profiles.create_profile(name)
        if dialogs.confirm("פרופיל חדש", "לעבור עכשיו לפרופיל החדש? ההתקדמות הנוכחית נשמרת בצד."):
            self.storage.close()
            profiles.switch_profile(pid)
            self._rebind_profile_stores()
            self._choose_start_screen()
            return
        self._show_settings()

    def _delete_profile(self):
        rows = profiles.list_profiles()
        if len(rows) < 2:
            dialogs.info("פרופילים", "אי אפשר למחוק את הפרופיל האחרון. אפשר לאפס נתונים בהגדרות.")
            return
        names = [str(item.get("name") or "תלמיד") for item in rows]
        chosen = dialogs.choose("מחיקת פרופיל", "איזה פרופיל למחוק? הפעולה לא ניתנת לביטול.", names)
        if not chosen:
            return
        match = next((item for item in rows if item.get("name") == chosen), None)
        if not match:
            return
        if not dialogs.confirm("מחיקה", f"למחוק את הפרופיל «{chosen}» ואת כל ההתקדמות שלו?"):
            return
        was_current = bool(match.get("current"))
        if was_current:
            self.storage.close()
        nxt = profiles.delete_profile(str(match["id"]))
        if not nxt:
            dialogs.error("פרופילים", "לא הצלחתי למחוק.")
            return
        if was_current:
            self._rebind_profile_stores()
            self._choose_start_screen()
            return
        self._show_settings()

    def _export_parent_report(self):
        from tkinter import filedialog

        from core.parent_report import build_report as build_parent_report
        from core.parent_report import write_report as write_parent_report

        insight = ""
        try:
            card = self.analytics.get_insight_card()
            insight = str(card.get("recommendation") or "")
            if not insight:
                insight = str((self.adaptive_engine.evaluate() or {}).get("message") or "")
        except Exception:
            insight = ""
        report = build_parent_report(self.storage, insight=insight)
        path = filedialog.asksaveasfilename(
            title="שמירת דוח שבועי",
            defaultextension=".html",
            initialdir=nativeos.documents_dir(),
            initialfile=report.get("filename") or "studyapp-weekly.html",
            filetypes=[("HTML", "*.html"), ("טקסט", "*.txt")],
        )
        if not path:
            return
        try:
            write_parent_report(path, report)
        except Exception as exc:
            dialogs.error("דוח", f"לא הצלחתי לשמור: {exc}")
            return
        log.info("parent report saved %s", path)
        if dialogs.confirm("דוח שבועי", f"הדוח נשמר:\n{path}\n\nלפתוח אותו עכשיו?"):
            nativeos.open_path(path)

    def _show_question_editor(self):
        self.active_tab = "settings"
        self._show_chrome()
        self._clear()
        QuestionEditorScreen(self.content, on_back=self._show_settings).pack(fill="both", expand=True)

    def _toggle_autostart(self):
        enabled = not bool(profiles.get_os_pref("autostart", False))
        if not nativeos.set_autostart(enabled):
            dialogs.error("מערכת", "לא הצלחתי לעדכן הפעלה אוטומטית. בדקו הרשאות במחשב.")
            return
        profiles.set_os_pref("autostart", enabled)
        self._show_settings()

    def _toggle_reminder(self):
        enabled = not bool(profiles.get_os_pref("daily_reminder", False))
        hour = int(profiles.get_os_pref("reminder_hour", 17) or 17)
        minute = int(profiles.get_os_pref("reminder_minute", 0) or 0)
        if not nativeos.set_daily_reminder(enabled, hour, minute):
            dialogs.error(
                "תזכורת",
                "לא הצלחתי לקבוע תזכורת במערכת. ב-Windows זה משתמש במתוזמן המשימות, בלינוקס ב-systemd של המשתמש.",
            )
            return
        profiles.set_os_pref("daily_reminder", enabled)
        self._show_settings()

    def _save_reminder_time(self, raw: str):
        hour, minute = nativeos.parse_hhmm(raw)
        profiles.set_os_pref("reminder_hour", hour)
        profiles.set_os_pref("reminder_minute", minute)
        if profiles.get_os_pref("daily_reminder", False):
            if not nativeos.install_daily_reminder(hour, minute):
                dialogs.error("תזכורת", "השעה נשמרה, אבל עדכון המתוזמן במערכת נכשל.")
                return
        dialogs.info("תזכורת", f"שעת התזכורת: {hour:02d}:{minute:02d}")
        self._show_settings()

    def _install_os_shortcuts(self):
        if nativeos.install_user_shortcuts():
            dialogs.info("מערכת", "נוצר קיצור דרך בתפריט היישומים של המשתמש.")
        else:
            dialogs.error("מערכת", "לא הצלחתי ליצור קיצור דרך.")

    def _test_notify(self):
        student = self.storage.get_student() or {}
        name = student.get("name") or "תלמיד"
        if nativeos.notify("StudyApp", f"{name}, זו בדיקת התראה מהמערכת."):
            dialogs.info("התראה", "נשלחה התראת מערכת. אם לא הופיעה, בדקו את הגדרות ההתראות במחשב.")
        else:
            dialogs.error("התראה", "המערכת לא איפשרה לשלוח התראה.")

    def _maybe_reminder_nudge(self):
        try:
            if not self.winfo_exists() or not self.storage.has_profile():
                return
        except tk.TclError:
            return
        try:
            from core.reminders import maybe_nudge

            maybe_nudge(self.storage)
        except Exception as exc:
            log.info("reminder nudge skipped: %s", exc)

    def _toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode
        bg = COLORS["focus_bg"] if self.focus_mode else COLORS["bg"]
        self.storage.record_focus_event("focus_mode_on" if self.focus_mode else "focus_mode_off")
        # קודם בונים מחדש את המסך, ורק אז צובעים את הגלילה החיה.
        self._show_settings()
        try:
            self.configure(fg_color=bg)
            scroll = getattr(self, "scroll", None)
            if scroll is not None and scroll.winfo_exists():
                scroll.set_bg(bg)
        except tk.TclError:
            pass

    def _reset_learning(self):
        if not dialogs.confirm("התחלה מחדש", "למחוק פרופיל והתקדמות מהמחשב הזה?"):
            return
        log.warning("user reset all data")
        self.storage.reset_all()
        self.session_store.clear()
        self._show_onboarding()

    # ---------- מקצוע ----------
    def _show_subject_hub(self, subject_key_value):
        if is_coming_soon(subject_key_value):
            dialogs.info("בהכנה", f"{subject_label(subject_key_value)} עדיין בהכנה.")
            return
        self.current_subject = subject_key_value
        self.active_tab = "dashboard"
        self._show_chrome()
        self._clear()
        data = load_subject(subject_key_value) or {}
        snap = self.adaptive_engine.snapshot(subject_key_value)
        visible_lessons = self.adaptive_engine.lessons_for(
            subject_key_value, data.get("lessons") or []
        )
        stats = {
            "questions": len(data.get("questions") or []),
            "lessons": len(visible_lessons),
            "mistakes": len(self.storage.get_mistakes(subject_key_value)),
        }
        # המספרים בכרטיסים חייבים להיות מה שבאמת יקרה, הם משתנים לפי הרמה.
        level = self.adaptive_engine.level_of(subject_key_value)
        specs = {
            mode: session_params(level, mode) for mode in ("practice", "compose", "mock", "final")
        }
        from core.compose import compose_pool
        from core.session_review import subject_topic_catalog

        topics = subject_topic_catalog(data, compose_pool(subject_key_value, []))
        SubjectHubScreen(
            self.content, subject_key_value,
            on_mode_select=self._start_mode, on_back=self._show_dashboard, stats=stats,
            storage=self.storage, level_info=snap, specs=specs, topics=topics,
        ).pack(fill="both", expand=True)

    def _clean_pool(self, pool):
        """מסנן שאלות הטעיה, וגם שאלות שהתלמיד דיווח עליהן כשגויות."""
        reported = self.storage.reported_ids()
        clean = [
            q for q in pool
            if q.get("kind") != "trick" and str(q.get("id") or "") not in reported
        ]
        return clean or [q for q in pool if q.get("kind") != "trick"] or list(pool)

    def _report_question(self, question):
        if not question or not question.get("id"):
            return
        reason = dialogs.choose(
            "דיווח על שאלה",
            "מה לא בסדר בשאלה הזאת?",
            [
                "התשובה המסומנת כנכונה שגויה",
                "השאלה מנוסחת לא ברור",
                "יש יותר מתשובה נכונה אחת",
                "ההסבר לא מסביר כלום",
                "משהו אחר",
            ],
            parent=self,
        )
        if not reason:
            return
        self.storage.report_question(question, reason)
        log.info("question reported: %s (%s)", question.get("id"), reason)
        dialogs.info(
            "תודה",
            "השאלה סומנה ולא תחזור אליך יותר.\nאפשר לראות את כל הדיווחים בהגדרות.",
        )

    def _start_mode(self, subject, mode, topic=None, topic_only=False, topics=None):
        subject = subject_key(subject)
        if is_coming_soon(subject):
            dialogs.info("בהכנה", f"{subject_label(subject)} עדיין בהכנה.")
            return
        if mode in {"read", "lessons", "guided"}:
            self._show_lessons(subject)
            return
        if mode == "mistakes":
            self._start_mistake_drill(subject)
            return
        if mode == "exam":
            mode = "timed"

        if mode == "final" and not self.storage.can_take_final(subject):
            dialogs.info(
                "מבחן אמיתי נעול",
                "תרגלו לפחות 20 שאלות במקצוע עם דיוק 50% ומעלה כדי לפתוח את המבחן האמיתי.",
            )
            return

        data = load_subject(subject)
        if not data:
            dialogs.error("שגיאה", "לא נמצא חומר למקצוע הזה.")
            return
        pool = self._clean_pool(data.get("questions") or [])
        if mode == "compose":
            from core.compose import compose_pool

            pool = compose_pool(subject, pool)
        if not pool:
            dialogs.info("מידע", "אין עדיין שאלות במקצוע הזה.")
            return

        srs = self.srs if mode in {"practice", "smart_practice", "compose"} else None
        wanted = [str(item) for item in (topics or []) if item]
        if topic and str(topic) not in wanted:
            wanted.insert(0, str(topic))
        if topic_only and wanted:
            scoped = [q for q in pool if q.get("topic") in set(wanted)]
            if not scoped:
                dialogs.info("מידע", "אין עדיין שאלות בנושא הזה.")
                return
            pool = scoped
        questions, params = self.adaptive_engine.select_questions(
            pool, subject, mode=mode, srs=srs,
            prefer_topic=topic, prefer_topics=wanted or None, topic_only=topic_only,
        )
        if not questions:
            dialogs.info("מידע", "אין עדיין שאלות במקצוע הזה.")
            return

        limit = params.get("seconds")
        total_limit = params.get("total_limit_sec")
        self.current_subject = subject
        self.current_mode = mode
        self.current_session = ExamSession(
            questions, mode=mode, time_limit_sec=limit, subject_key=subject, topic=topic,
            total_limit_sec=total_limit,
        )
        self.session_store.save(self.current_session.to_state(subject))
        log.info(
            "start mode=%s subject=%s count=%s level=%s",
            mode, subject, len(questions), params.get("level"),
        )
        self._render_practice()

    def _live_weak_subjects(self) -> list[str]:
        snaps = self.adaptive_engine.all_snapshots(ALL_SUBJECTS)
        ranked = []
        for key, item in snaps.items():
            if int(item.get("recent_total") or 0) < 4:
                continue
            acc = float(item.get("recent_accuracy") or 0)
            if acc < 72:
                ranked.append((acc, -int(item.get("recent_total") or 0), key))
        ranked.sort()
        return [key for _, __, key in ranked]

    def _start_smart_practice(self):
        weak = [key for key in self._live_weak_subjects() if key in SUBJECTS]
        if not weak:
            diagnostic = self.storage.get_diagnostic() or {}
            weak = [subject_key(item) for item in (diagnostic.get("weak_topics") or [])]
            weak = [item for item in weak if item in SUBJECTS]
        if not weak:
            weak = [
                subject_key(item)
                for item in (self.storage.get_learning_snapshot().get("weak_subjects") or [])
            ]
            weak = [item for item in weak if item in SUBJECTS]
        if not weak:
            weak = list(HOME_SUBJECTS[:2])
        pool = []
        for key in weak:
            data = load_subject(key) or {}
            pool.extend(self._clean_pool(data.get("questions") or []))
        if not pool:
            dialogs.info("מידע", "לא נמצאו שאלות לנושאים לחיזוק.")
            return
        questions, _params = self.adaptive_engine.select_questions(
            pool, weak[0], count=min(8, len(pool)), mode="practice", srs=self.srs,
        )
        if not questions:
            questions = random.sample(pool, min(8, len(pool)))
        self.current_subject = weak[0]
        self.current_mode = "smart_practice"
        self.current_session = ExamSession(questions, mode="practice", subject_key=weak[0])
        self.session_store.save(self.current_session.to_state(self.current_subject))
        self._render_practice()

    def _start_mistake_drill(self, subject=None):
        saved = self.storage.get_mistakes(subject)
        if not saved:
            dialogs.info("מצוין", "אין כרגע טעויות פתוחות לתרגול.")
            return
        questions = []
        for item in saved[:15]:
            questions.append(
                {
                    "id": item.get("id"),
                    "subject": item.get("subject"),
                    "topic": item.get("topic"),
                    "question": item.get("question"),
                    "options": item.get("options") or [],
                    "answer": item.get("answer"),
                    "correct_answer": item.get("correct_answer"),
                    "explanation": item.get("explanation"),
                    "difficulty": "חזרה",
                    "hint": "כבר טעית כאן פעם. קראו לאט.",
                }
            )
        self.current_subject = subject or subject_key(questions[0].get("subject") or "hebrew")
        self.current_mode = "review"
        self.current_session = ExamSession(questions, mode="practice", subject_key=self.current_subject)
        self._render_practice()

    def _start_fix_questions(self, answers: list | None = None):
        items = list(answers or [])
        if not items:
            dialogs.info("מצוין", "אין כאן שאלה לתיקון.")
            return
        questions = []
        for item in items:
            questions.append(
                {
                    "id": item.get("question_id") or item.get("id"),
                    "subject": item.get("subject") or self.current_subject,
                    "topic": item.get("topic"),
                    "question": item.get("question"),
                    "options": item.get("options") or [],
                    "answer": item.get("answer"),
                    "correct_answer": item.get("correct_answer"),
                    "explanation": item.get("explanation"),
                    "difficulty": "חזרה",
                    "hint": "כבר טעית כאן. קראו לאט ובדקו מה נשאל.",
                }
            )
        first_subj = subject_key(questions[0].get("subject") or self.current_subject or "hebrew")
        self.current_subject = first_subj
        self.current_mode = "review"
        self.current_session = ExamSession(questions, mode="practice", subject_key=first_subj)
        self._render_practice()

    def _show_lessons(self, subject):
        self.current_subject = subject
        self.active_tab = "subjects"
        self._show_chrome()
        self._clear()
        self._set_window_title(subject_label(subject), "שיעורים")
        data = load_subject(subject) or {}
        lessons = self.adaptive_engine.lessons_for(subject, data.get("lessons") or [])
        snap = self.adaptive_engine.snapshot(subject)

        bar = tk.Frame(self.content, bg=COLORS["bg"])
        bar.pack(fill="x")
        GhostButton(bar, text=rtl("‹  חזרה"), width=120,
                    command=lambda: self._show_subject_hub(subject)).pack(side="right")
        heading(self.content, f"שיעורים עיוניים: {subject_label(subject)}", 24).pack(anchor="e", pady=(12, 4))
        if not lessons:
            body(self.content, "עדיין אין שיעור כאן. אפשר לתרגל לפי שאלות.").pack(anchor="e")
            return
        body(
            self.content,
            f"{snap.get('headline', '')}. מוצגים שיעורים שמתאימים לרמה שלך. כשתעלו רמה, ייפתח חומר רציני יותר.",
            muted=True,
        ).pack(anchor="e", pady=(0, 8))
        listing = tk.Frame(self.content, bg=COLORS["bg"])
        listing.pack(fill="both", expand=True)
        display = list(lessons)
        random.shuffle(display)
        undone = [item for item in display if not self.storage.is_lesson_complete(str(item.get("id")))]
        if undone:
            featured = undone[0]
            display = [featured] + [item for item in display if item is not featured]
        body(
            self.content,
            "בכל כניסה הסדר משתנה, כדי שלא תישארו תמיד על אותו שיעור ראשון. תרגול על שיעור שולף שאלות אחרות מהמאגר.",
            muted=True,
        ).pack(anchor="e", pady=(0, 8))
        for lesson in display:
            done = self.storage.is_lesson_complete(str(lesson.get("id")))
            FastRow(
                listing,
                text=lesson.get("title", "שיעור"),
                subtitle=lesson.get("category") or "",
                on_click=lambda item=lesson: self._open_lesson(subject, item["id"]),
                done=done,
            ).pack(fill="x", pady=4)

    def _open_lesson(self, subject, lesson_id):
        data = load_subject(subject) or {}
        pool = self._clean_pool(data.get("questions") or [])
        lessons = self.adaptive_engine.lessons_for(subject, data.get("lessons") or [], pool)
        lesson = next((item for item in lessons if str(item.get("id")) == str(lesson_id)), None)
        if not lesson:
            lesson = next(
                (item for item in (data.get("lessons") or []) if str(item.get("id")) == str(lesson_id)),
                None,
            )
            lessons = data.get("lessons") or []
        if not lesson:
            dialogs.info("מידע", "השיעור לא נמצא.")
            return
        index = next((i for i, item in enumerate(lessons) if str(item.get("id")) == str(lesson_id)), 0)
        self.storage.award_lesson_once(str(lesson_id))
        self._set_window_title(subject_label(subject), lesson.get("title") or "שיעור")
        self._set_window_title(subject_label(subject), lesson.get("title") or "שיעור")
        self._clear()
        prev_id = lessons[index - 1]["id"] if index > 0 else None
        next_id = lessons[index + 1]["id"] if index + 1 < len(lessons) else None
        LessonScreen(
            self.content,
            lesson=lesson,
            index=index,
            total=len(lessons),
            on_back=lambda: self._show_lessons(subject),
            on_prev=(lambda: self._open_lesson(subject, prev_id)) if prev_id else None,
            on_next=(lambda: self._open_lesson(subject, next_id)) if next_id else None,
            on_practice=lambda: self._start_mode(subject, "practice", topic=lesson.get("topic")),
            speaker=self.speaker,
        ).pack(fill="both", expand=True)

    # ---------- תרגול ----------
    def _practice_back(self):
        if self.current_mode == "general":
            self._show_general_exam_hub()
            return
        if self.current_mode == "meimad":
            self._show_meimad_hub()
            return
        if self.current_subject:
            self._show_subject_hub(self.current_subject)
            return
        self._show_dashboard()

    def _render_practice(self):
        self._clear()
        if not self.current_session:
            self._show_subjects()
            return
        hide_nav = self.current_mode in {"mock", "final", "timed", "general", "meimad"}
        self._set_chrome(nav=not hide_nav, rail=False)
        show_feedback = self.current_mode not in {"mock", "final", "timed", "exam", "general", "meimad"}
        level_he = None
        if self.current_mode != "general" and self.current_subject:
            level_he = LEVEL_HE.get(self.adaptive_engine.level_of(self.current_subject), "מתחיל")
        mode_he = {
            "practice": "תרגול", "compose": "יצור", "review": "חזרה", "mock": "מבחן דמה",
            "final": "מבחן אמיתי", "timed": "מבחן", "general": "מבחן כללי",
            "meimad": "מימ״ד",
        }.get(self.current_mode, "תרגול")
        self._set_window_title(subject_label(self.current_subject or ""), mode_he)
        PracticeScreen(
            self.content,
            session=self.current_session,
            on_back=self._practice_back,
            on_finished=self._show_results,
            on_persist=self._persist_answer,
            show_feedback=show_feedback,
            exam_mode=self.current_mode in {"mock", "final", "timed", "general", "meimad"},
            speaker=self.speaker,
            level_he=level_he,
            on_report=self._report_question,
            subject_key=self.current_subject,
        ).pack(fill="both", expand=True)

    def _persist_answer(self, question, is_correct, elapsed, selected_index=-1):
        if not question:
            return
        if self.current_session:
            self.session_store.save(
                self.current_session.to_state(
                    self.current_subject or self.current_session.subject_key
                )
            )
        # מבחן דמה / כללי / מימ״ד: הציון בסוף בלבד, בלי לגעת בפרופיל / ברמה / במחברת.
        if self.current_mode in {"mock", "general", "meimad"}:
            return
        topic = question.get("topic", "כללי")
        subj = subject_key(question.get("subject") or self.current_subject or "כללי")
        self.db.log_answer(topic, question.get("difficulty", "בסיסי"), is_correct, elapsed, subject=subj)
        self.storage.record_answer(subj, topic, is_correct, elapsed, question_id=question.get("id"))
        if subj in SUBJECTS:
            self.adaptive_engine.observe(
                subj, is_correct, question.get("difficulty", "Easy"),
                topic=topic, time_sec=elapsed,
            )
        self.storage.award_points(10 if is_correct else 3, "answer_" + ("correct" if is_correct else "attempt"))
        before_xp = int(self.storage.get("xp", 0) or 0)
        self.storage.add_xp(10 if is_correct else 2)
        after_xp = int(self.storage.get("xp", 0) or 0)
        if before_xp // 100 < after_xp // 100:
            self._toast("עליתם רמה", f"רמה {1 + after_xp // 100}", kind="success")
        if question.get("id"):
            self.srs.record(str(question["id"]), is_correct)
            if is_correct:
                self.storage.clear_mistake(str(question["id"]))
            else:
                self.storage.record_mistake(question, selected_index)
        self.storage.record_focus_event(
            "answer_correct" if is_correct else "answer_attempt", {"count": 1, "topic": topic}
        )

    def _restore_last_session(self):
        saved = self.session_store.load()
        if not saved or not saved.get("questions"):
            dialogs.info("מידע", "אין סשן שמור.")
            return
        session = ExamSession.from_state(saved)
        if not session:
            return
        self.current_subject = saved.get("subject_key") or self.current_subject
        mode = saved.get("mode") or "practice"
        if mode == "exam":
            mode = "timed"
        self.current_mode = mode
        self.current_session = session
        self._render_practice()

    def _finish_meta(self, session) -> dict:
        gained = 0
        for row in getattr(session, "user_answers", None) or []:
            correct = row.get("correct") if isinstance(row, dict) else getattr(row, "correct", False)
            gained += 10 if correct else 2
        xp = int(self.storage.get("xp", 0) or 0)
        daily = self.storage.get_daily_goal()
        if daily.get("is_done"):
            import time as _time
            stamp = "toasted_daily_" + _time.strftime("%Y-%m-%d")
            if not self.storage.get_pref(stamp):
                self.storage.set_pref(stamp, True)
                self._toast("יעד היום הושלם", f"{daily.get('completed')} שאלות", kind="success")
        return {
            "xp_info": {"xp": xp, "level": 1 + xp // 100, "gained": gained},
            "streak": int(self.storage.get_streak().get("current", 0) or 0),
        }

    def _show_results(self):
        self.session_store.clear()
        session = self.current_session
        if not session:
            self._show_dashboard()
            return
        session.fill_unanswered()
        if self.current_mode not in {"mock", "general", "meimad"}:
            self.storage.record_session(
                self.current_subject or "כללי", self.current_mode, session.score, len(session.questions)
            )
        if self.current_mode == "general":
            report = build_report(session.user_answers, total=len(session.questions))
            self.storage.save_general_exam_report(report)
            self._show_chrome()
            self.active_tab = "general_exam"
            self._refresh_sidebar()
            self._clear()
            GeneralExamReportScreen(
                self.content, report=report, session=session,
                on_home=self._show_dashboard,
                on_retry=self._show_general_exam_hub,
            ).pack(fill="both", expand=True)
            self.current_session = None
            self.current_mode = "practice"
            return
        if self.current_mode == "meimad":
            chapters = session.chapter_breakdown()
            percent = round(100 * session.score / max(1, len(session.questions)))
            self.storage.set(
                "meimad_last",
                {
                    "percent": percent,
                    "score": session.score,
                    "total": len(session.questions),
                    "chapters": chapters,
                    "date": __import__("time").strftime("%Y-%m-%d %H:%M"),
                },
            )
            self._show_chrome()
            self.active_tab = "meimad"
            self._refresh_sidebar()
            self._clear()
            self._set_window_title("תוצאות", "מימ״ד")
            meta = self._finish_meta(session)
            ResultsScreen(
                self.content, session=session, summary=self.analytics.get_summary(),
                insight=self.analytics.get_insight_card(),
                on_home=self._show_meimad_hub,
                mode="meimad",
                subject=None,
                on_retry_wrong=self._start_mistake_drill,
                on_fix_questions=self._start_fix_questions,
                xp_info=meta["xp_info"],
                streak=meta["streak"],
                weak_report=session_weak_topics(session.user_answers),
            ).pack(fill="both", expand=True)
            self.current_session = None
            self.current_mode = "practice"
            return
        if self.current_mode == "final":
            percent = round(100 * session.score / max(1, len(session.questions)))
            if percent >= 60:
                self.storage.record_exam_official(
                    self.current_subject or "כללי", session.score, len(session.questions)
                )
        self._show_chrome()
        self.active_tab = "subjects"
        self._refresh_sidebar()
        self._clear()
        subj = self.current_subject or "hebrew"
        self._set_window_title("תוצאות", subject_label(subj))
        meta = self._finish_meta(session)
        drill_mode = "compose" if self.current_mode == "compose" else "practice"
        ResultsScreen(
            self.content, session=session, summary=self.analytics.get_summary(subject=subj),
            insight=self.analytics.get_insight_card(subject=subj),
            on_home=lambda: self._show_subject_hub(self.current_subject) if self.current_subject else self._show_subjects(),
            mode=self.current_mode,
            subject=self.current_subject,
            on_retry_wrong=self._start_mistake_drill,
            on_fix_questions=self._start_fix_questions,
            level_event=self.adaptive_engine.consume_event(subj),
            level_info=self.adaptive_engine.snapshot(subj),
            xp_info=meta["xp_info"],
            streak=meta["streak"],
            weak_report=session_weak_topics(session.user_answers),
            on_practice_weak=lambda topics, key=subj, kind=drill_mode: self._start_mode(
                key, kind, topics=topics, topic_only=True,
            ),
        ).pack(fill="both", expand=True)
        self.current_session = None
        self.current_mode = "practice"


def run():
    """מפעיל את חלון שולחן העבודה."""
    app = StudyApp()
    app.mainloop()
    log.info("mainloop ended cleanly")
