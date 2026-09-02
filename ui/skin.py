"""ציור כרטיסים מעוגלים, כפתורי גלולה וטבעות. תמונה סטטית, בלי Canvas של CTk בגלילה."""
from __future__ import annotations

import os
from functools import lru_cache
from io import BytesIO

from core.config import COLORS, ICON_PNG_PATH


def hex_rgb(color: str) -> tuple[int, int, int]:
    raw = (color or "#FFFFFF").lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) < 6:
        return (255, 255, 255)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _pil():
    from PIL import Image, ImageDraw, ImageFilter, ImageTk

    return Image, ImageDraw, ImageFilter, ImageTk


def _down(img, w: int, h: int):
    Image, _d, _f, _t = _pil()
    if img.size == (w, h):
        return img
    return img.resize((w, h), Image.Resampling.LANCZOS)


@lru_cache(maxsize=256)
def _rounded_bytes(w: int, h: int, radius: int, fill: str, shadow: bool) -> bytes:
    Image, ImageDraw, _ImageFilter, _ImageTk = _pil()
    w, h = max(24, w), max(24, h)
    radius = max(6, min(int(radius), w // 2, h // 2))
    s = 2
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    if shadow:
        shade = ImageDraw.Draw(img)
        shade.rounded_rectangle((4 * s, 5 * s, w * s - 1, h * s - 1), radius=radius * s, fill=(20, 45, 40, 38))
        box = (0, 0, w * s - 6 * s, h * s - 7 * s)
    else:
        box = (0, 0, w * s - 1, h * s - 1)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(box, radius=radius * s, fill=(*hex_rgb(fill), 255))
    img = _down(img, w, h)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@lru_cache(maxsize=256)
def _pill_bytes(w: int, h: int, fill: str, outline: str) -> bytes:
    Image, ImageDraw, _f, _t = _pil()
    w, h = max(24, w), max(20, h)
    s = 2
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = max(8, h // 2) * s
    if outline:
        draw.rounded_rectangle(
            (1 * s, 1 * s, w * s - 2 * s, h * s - 2 * s),
            radius=radius,
            fill=(*hex_rgb(fill), 255),
            outline=(*hex_rgb(outline), 255),
            width=2 * s,
        )
    else:
        draw.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=radius, fill=(*hex_rgb(fill), 255))
    img = _down(img, w, h)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@lru_cache(maxsize=128)
def _circle_bytes(size: int, fill: str) -> bytes:
    Image, ImageDraw, _f, _t = _pil()
    size = max(16, size)
    s = 2
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((1 * s, 1 * s, size * s - 2 * s, size * s - 2 * s), fill=(*hex_rgb(fill), 255))
    img = _down(img, size, size)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@lru_cache(maxsize=128)
def _ring_bytes(size: int, pct: int, color: str, track: str) -> bytes:
    Image, ImageDraw, _f, _t = _pil()
    size = max(28, size)
    s = 2
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    width = max(4, size // 8) * s
    box = (2 * s, 2 * s, size * s - 3 * s, size * s - 3 * s)
    draw.arc(box, start=0, end=360, fill=(*hex_rgb(track), 255), width=width)
    sweep = max(0, min(360, int(360 * (pct / 100.0))))
    if sweep:
        draw.arc(box, start=-90, end=-90 + sweep, fill=(*hex_rgb(color), 255), width=width)
    img = _down(img, size, size)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@lru_cache(maxsize=64)
def _bar_bytes(w: int, h: int, pct: int, fill: str, track: str) -> bytes:
    Image, ImageDraw, _f, _t = _pil()
    w, h = max(40, w), max(8, h)
    s = 2
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = (h // 2) * s
    draw.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=r, fill=(*hex_rgb(track), 255))
    fw = max(h * s, int((w * s - 1) * max(0, min(100, pct)) / 100.0))
    draw.rounded_rectangle((0, 0, fw, h * s - 1), radius=r, fill=(*hex_rgb(fill), 255))
    img = _down(img, w, h)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _photo(png: bytes, owner):
    from PIL import ImageTk

    photo = ImageTk.PhotoImage(data=png)
    bucket = getattr(owner, "_skin_photos", None)
    if bucket is None:
        bucket = []
        owner._skin_photos = bucket
    bucket.append(photo)
    if len(bucket) > 8:
        del bucket[:-4]
    return photo


def card_photo(owner, w: int, h: int, fill: str | None = None, radius: int = 24, shadow: bool = True):
    try:
        return _photo(_rounded_bytes(int(w), int(h), int(radius), fill or COLORS["card_bg"], shadow), owner)
    except Exception:
        return None


def pill_photo(owner, w: int, h: int, fill: str, outline: str = ""):
    try:
        return _photo(_pill_bytes(int(w), int(h), fill, outline or ""), owner)
    except Exception:
        return None


def circle_photo(owner, size: int, fill: str):
    try:
        return _photo(_circle_bytes(int(size), fill), owner)
    except Exception:
        return None


def ring_photo(owner, size: int, pct: float, color: str, track: str):
    try:
        return _photo(_ring_bytes(int(size), int(round(pct * 100)), color, track), owner)
    except Exception:
        return None


def bar_photo(owner, w: int, h: int, pct: float, fill: str, track: str):
    try:
        return _photo(_bar_bytes(int(w), int(h), int(round(pct * 100)), fill, track), owner)
    except Exception:
        return None


def _draw_logo_png(size: int) -> bytes:
    import importlib.util

    from core.config import BASE_DIR

    path = os.path.join(BASE_DIR, "tools", "make_icon.py")
    spec = importlib.util.spec_from_file_location("studyapp_make_icon", path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._draw(size)


@lru_cache(maxsize=8)
def _logo_png(size: int) -> bytes:
    """לוגו הספר מהאייקון. אם הקובץ חסר, מציירים את אותו איור."""
    size = max(16, int(size))
    Image, _d, _f, _t = _pil()
    if os.path.isfile(ICON_PNG_PATH):
        src = Image.open(ICON_PNG_PATH).convert("RGBA")
        out = src.resize((size, size), Image.Resampling.LANCZOS)
        buf = BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()
    raw = _draw_logo_png(size if size >= 32 else 64)
    if size >= 32:
        return raw
    img = Image.open(BytesIO(raw)).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def logo_photo(owner, size: int = 36):
    """אייקון הספר ליד שם האפליקציה, לא האות ס."""
    try:
        return _photo(_logo_png(max(16, int(size))), owner)
    except Exception:
        return None
