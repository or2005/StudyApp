"""הקראה קולית, בלי תלויות חיצוניות חובה.

Windows: pyttsx3 או System.Speech.
לינוקס: pyttsx3, ואם אין, espeak-ng / espeak / spd-say.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading

from core.applog import get_logger

log = get_logger("speech")


def _linux_tts() -> list[str] | None:
    for binary, prefix in (
        ("espeak-ng", ["-v", "he"]),
        ("espeak", ["-v", "he"]),
        ("spd-say", ["-l", "he"]),
    ):
        path = shutil.which(binary)
        if path:
            return [path, *prefix]
    return None


class Speaker:
    def __init__(self, enabled: bool = False):
        self.enabled = bool(enabled)
        self._proc: subprocess.Popen | None = None
        self._engine = None
        self._linux_cmd = _linux_tts()
        self._lock = threading.Lock()
        self._try_pyttsx3()

    def _try_pyttsx3(self) -> None:
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
            log.info("tts engine: pyttsx3")
        except Exception:
            self._engine = None

    @property
    def available(self) -> bool:
        if self._engine is not None:
            return True
        if os.name == "nt":
            return True
        return self._linux_cmd is not None

    def say(self, text: str) -> None:
        if not self.enabled or not text:
            return
        clean = " ".join(str(text).replace("\u200f", "").split())[:600]
        if not clean:
            return
        threading.Thread(target=self._speak, args=(clean,), daemon=True).start()

    def _speak(self, text: str) -> None:
        with self._lock:
            self.stop()
            if self._engine is not None:
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                    return
                except Exception as exc:
                    log.warning("pyttsx3 failed: %s", exc)
            if os.name == "nt":
                self._speak_windows(text)
                return
            if self._linux_cmd:
                try:
                    self._proc = subprocess.Popen(
                        [*self._linux_cmd, text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception as exc:
                    log.warning("linux tts failed: %s", exc)

    def _speak_windows(self, text: str) -> None:
        safe = text.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Speak('{safe}')"
        )
        try:
            self._proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as exc:
            log.warning("powershell tts failed: %s", exc)

    def stop(self) -> None:
        proc = self._proc
        self._proc = None
        if proc and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
