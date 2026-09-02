"""כניסה לחדר מפתח. ההשוואה ב־hash, בלי לשמור סיסמה ביומן."""
from __future__ import annotations

import hashlib
import hmac


def _digest(user: str, password: str) -> str:
    raw = f"studyapp-studio-v1\0{(user or '').strip().lower()}\0{password or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check(user: str, password: str) -> bool:
    got = _digest(user, password)
    want = _digest("ordadshev", "Aa" + "327806" + "279@")
    return hmac.compare_digest(got, want)
