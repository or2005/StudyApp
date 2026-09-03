"""לוגים וקריסות, הכל נכתב לקובץ מקומי כדי שאפשר יהיה לאבחן תקלות."""
from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
import traceback
from logging.handlers import RotatingFileHandler

from core.storage import DATA_DIR

LOG_DIR = os.path.join(DATA_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "studyapp.log")
CRASH_PATH = os.path.join(LOG_DIR, "crash.log")
CRASH_FLAG = os.path.join(LOG_DIR, "needs_help.json")

_configured = False
_logger = logging.getLogger("studyapp")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    global _configured
    if _configured:
        return _logger
    os.makedirs(LOG_DIR, exist_ok=True)
    _logger.setLevel(level)
    _logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    _logger.addHandler(file_handler)

    if os.environ.get("STUDYAPP_DEBUG"):
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(fmt)
        _logger.addHandler(stream)

    _configured = True
    _logger.info("=" * 60)
    _logger.info("StudyApp start | python=%s | pid=%s", sys.version.split()[0], os.getpid())
    return _logger


def get_logger(name: str = "studyapp") -> logging.Logger:
    setup_logging()
    return logging.getLogger(name if name.startswith("studyapp") else f"studyapp.{name}")


_STALE_AFTER = re.compile(r'invalid command name "[0-9]+')


def is_stale_widget_error(exc: BaseException | None) -> bool:
    """חריגות Tk אחרי שווידג'ט נהרס (ניווט / החלפת ערכת נושא). לא קריסה אמיתית."""
    if exc is None:
        return False
    msg = str(exc)
    if "bad window path name" in msg:
        return True
    if "invalid command name" not in msg:
        return False
    if ".!" in msg:
        return True
    return bool(_STALE_AFTER.search(msg))


def _write_crash(source: str, exc_type, exc_value, exc_tb) -> str:
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    setup_logging()
    _logger.error("CRASH (%s): %s", source, exc_value)
    _logger.error(text)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(CRASH_PATH, "a", encoding="utf-8") as handle:
            handle.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} | {source} ===\n{text}")
        import json

        with open(CRASH_FLAG, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "kind": "crash",
                    "source": str(source)[:40],
                },
                handle,
            )
    except Exception:
        pass
    return text


def install_crash_handlers(on_crash=None) -> None:
    """לוכד שגיאות בתהליך הראשי, בתהליכונים וב-Tk callbacks."""
    setup_logging()

    def handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        if is_stale_widget_error(exc_value):
            _logger.warning("stale widget (%s): %s", "main", exc_value)
            return
        _write_crash("main", exc_type, exc_value, exc_tb)
        if on_crash:
            try:
                on_crash(exc_value)
            except Exception:
                pass

    sys.excepthook = handle

    def thread_hook(args):
        if is_stale_widget_error(args.exc_value):
            _logger.warning("stale widget (%s): %s", f"thread:{args.thread.name if args.thread else '?'}", args.exc_value)
            return
        _write_crash(f"thread:{args.thread.name if args.thread else '?'}", args.exc_type, args.exc_value, args.exc_traceback)

    try:
        threading.excepthook = thread_hook
    except Exception:
        pass


def install_tk_handler(root, on_crash=None) -> None:
    """Tk בולע חריגות ב-callbacks. כאן הן נרשמות ומוצגות."""
    setup_logging()

    def report(exc_type, exc_value, exc_tb):
        if is_stale_widget_error(exc_value):
            _logger.warning("stale widget (%s): %s", "tk", exc_value)
            return
        _write_crash("tk", exc_type, exc_value, exc_tb)
        if on_crash:
            try:
                on_crash(exc_value)
            except Exception:
                pass

    root.report_callback_exception = report


class timed:
    """מודד זמן ורושם ללוג. אפשר גם as-context: with timed('nav'): ..."""

    def __init__(self, label: str, warn_ms: float = 400.0):
        self.label = label
        self.warn_ms = warn_ms
        self.ms = 0.0

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.ms = (time.perf_counter() - self._t0) * 1000
        log = get_logger("perf")
        if self.ms >= self.warn_ms:
            log.warning("%s took %.0f ms", self.label, self.ms)
        else:
            log.debug("%s took %.0f ms", self.label, self.ms)
        return False


def log_event(message: str, *args) -> None:
    get_logger("app").info(message, *args)


def log_error(message: str, *args) -> None:
    get_logger("app").error(message, *args)


def read_recent(lines: int = 200) -> str:
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as handle:
            return "".join(handle.readlines()[-lines:])
    except Exception:
        return "אין עדיין לוג."
