"""מנוע ציור להיסטוריה — דיאגרמות לימודיות אחידות (PIL), בלי קבצי מדיה כבדים."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import Any

from core.config import COLORS
from core.theme import subject_accent


def _pil():
    from PIL import Image, ImageDraw, ImageFont, ImageTk

    return Image, ImageDraw, ImageFont, ImageTk


@lru_cache(maxsize=4)
def _font(size: int, bold: bool = False):
    Image, _d, ImageFont, _t = _pil()
    size = max(10, int(size))
    names = (
        ("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf", "tahoma.ttf")
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _rgb(color: str) -> tuple[int, int, int]:
    raw = (color or "#334").lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _palette(accent: str = "") -> dict[str, str]:
    ink = COLORS.get("text") or "#1F2A2E"
    paper = COLORS.get("card_bg") or "#F7F4EF"
    mute = COLORS.get("muted") or "#6B7280"
    line = COLORS.get("card_border") or "#D7D2C8"
    wash = COLORS.get("bg") or "#EEF1F0"
    mark = accent or subject_accent("history") or COLORS.get("accent") or "#D4895A"
    return {"ink": ink, "paper": paper, "mute": mute, "line": line, "wash": wash, "mark": mark}


def render_visual_png(
    visual: dict[str, Any],
    *,
    width: int = 720,
    height: int = 220,
    mode: str = "lesson",
) -> bytes:
    """mode: lesson | question | explain"""
    Image, ImageDraw, _f, _t = _pil()
    kind = str(visual.get("kind") or "timeline")
    pal = _palette(str(visual.get("accent") or ""))
    w = max(320, int(width))
    h = max(140, int(height))
    if mode == "question":
        h = max(120, min(h, 160))
    img = Image.new("RGB", (w, h), pal["wash"])
    draw = ImageDraw.Draw(img)
    # frame
    draw.rounded_rectangle((8, 8, w - 9, h - 9), radius=18, fill=pal["paper"], outline=_rgb(pal["line"]), width=2)
    painters = {
        "timeline": _paint_timeline,
        "flag": _paint_flag,
        "menorah": _paint_menorah,
        "scroll": _paint_scroll,
        "map": _paint_map,
        "war": _paint_war,
        "peace": _paint_peace,
        "aliyah": _paint_aliyah,
        "congress": _paint_congress,
        "state": _paint_state,
        "document": _paint_document,
        "memory": _paint_memory,
    }
    painter = painters.get(kind, _paint_timeline)
    painter(draw, w, h, visual, pal, mode=mode)
    if mode == "explain":
        _paint_reveal_badge(draw, w, h, visual, pal)
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def photo_for(owner, visual: dict[str, Any], *, width: int, height: int, mode: str):
    Image, _d, _f, ImageTk = _pil()
    png = render_visual_png(visual, width=width, height=height, mode=mode)
    photo = ImageTk.PhotoImage(data=png)
    bucket = getattr(owner, "_visual_photos", None)
    if bucket is None:
        bucket = []
        owner._visual_photos = bucket
    bucket.append(photo)
    if len(bucket) > 12:
        del bucket[:-6]
    return photo


def _text(draw, xy, text: str, *, fill: str, size: int = 14, bold: bool = False, anchor: str = "mm"):
    # PIL מצייר משמאל בלי Uniscribe — עברית חייבת סדר ויזואלי
    from core.rtltext import visual_letters

    shown = visual_letters(str(text or ""))
    draw.text(xy, shown, fill=_rgb(fill), font=_font(size, bold=bold), anchor=anchor)


def _paint_timeline(draw, w, h, visual, pal, mode="lesson"):
    years = list(visual.get("years") or ["1917", "1947", "1948", "1967", "1973", "1979"])
    years = years[:6]
    y = h // 2 + 8
    draw.line((48, y, w - 48, y), fill=_rgb(pal["mark"]), width=4)
    step = (w - 96) / max(1, len(years) - 1)
    for i, year in enumerate(years):
        x = 48 + int(i * step)
        r = 8 if mode != "explain" or i != len(years) // 2 else 11
        draw.ellipse((x - r, y - r, x + r, y + r), fill=_rgb(pal["mark"]), outline=_rgb(pal["ink"]), width=2)
        _text(draw, (x, y - 28), str(year), fill=pal["ink"], size=13, bold=True)
        if mode == "explain" and i == len(years) // 2:
            draw.line((x, y + 12, x, y + 34), fill=_rgb(pal["ink"]), width=2)
            _text(draw, (x, y + 48), "נקודת מפתח", fill=pal["mute"], size=11)
    title = str(visual.get("title") or "ציר זמן")
    _text(draw, (w // 2, 28), title, fill=pal["ink"], size=15, bold=True)


def _paint_flag(draw, w, h, visual, pal, mode="lesson"):
    fw, fh = int(w * 0.42), int(h * 0.55)
    x0, y0 = (w - fw) // 2, (h - fh) // 2 + 8
    draw.rounded_rectangle((x0, y0, x0 + fw, y0 + fh), radius=8, fill=(255, 255, 255), outline=_rgb(pal["ink"]), width=2)
    band = max(6, fh // 8)
    draw.rectangle((x0 + 8, y0 + band, x0 + fw - 8, y0 + band * 2), fill=(30, 90, 180))
    draw.rectangle((x0 + 8, y0 + fh - band * 2, x0 + fw - 8, y0 + fh - band), fill=(30, 90, 180))
    cx, cy = x0 + fw // 2, y0 + fh // 2
    r = min(fw, fh) // 5
    # star of david (two triangles)
    draw.polygon([(cx, cy - r), (cx - r, cy + r // 2), (cx + r, cy + r // 2)], outline=_rgb("#1E5AA8"))
    draw.polygon([(cx, cy + r), (cx - r, cy - r // 2), (cx + r, cy - r // 2)], outline=_rgb("#1E5AA8"))
    _text(draw, (w // 2, 26), str(visual.get("title") or "סמל ודגל"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain":
        _text(draw, (w // 2, h - 24), "תכלת לבן · מגן דוד", fill=pal["mute"], size=12)


def _paint_menorah(draw, w, h, visual, pal, mode="lesson"):
    cx, base = w // 2, h - 36
    mark = _rgb(pal["mark"])
    ink = _rgb(pal["ink"])
    draw.rectangle((cx - 8, base - 70, cx + 8, base), fill=mark)
    draw.rectangle((cx - 40, base, cx + 40, base + 10), fill=ink)
    for dx in (-54, -36, -18, 0, 18, 36, 54):
        x = cx + dx
        draw.arc((x - 10, base - 88, x + 10, base - 50), start=0, end=180, fill=mark, width=4)
        draw.ellipse((x - 5, base - 96, x + 5, base - 86), fill=mark)
    # olive branches
    draw.arc((cx - 90, base - 50, cx - 20, base + 20), start=200, end=320, fill=_rgb("#3F7D4E"), width=3)
    draw.arc((cx + 20, base - 50, cx + 90, base + 20), start=220, end=340, fill=_rgb("#3F7D4E"), width=3)
    _text(draw, (w // 2, 26), str(visual.get("title") or "סמל המדינה"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain":
        _text(draw, (w // 2, 48), "מנורה וענפי זית", fill=pal["mute"], size=12)


def _paint_scroll(draw, w, h, visual, pal, mode="lesson"):
    x0, y0 = int(w * 0.22), int(h * 0.28)
    x1, y1 = int(w * 0.78), int(h * 0.82)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=(252, 246, 232), outline=_rgb(pal["ink"]), width=2)
    draw.ellipse((x0 - 14, y0, x0 + 10, y1), fill=_rgb(pal["mark"]), outline=_rgb(pal["ink"]), width=2)
    draw.ellipse((x1 - 10, y0, x1 + 14, y1), fill=_rgb(pal["mark"]), outline=_rgb(pal["ink"]), width=2)
    for i, yy in enumerate((y0 + 28, y0 + 48, y0 + 68, y0 + 88)):
        if yy >= y1 - 16:
            break
        pad = 18 if i % 2 == 0 else 34
        draw.line((x0 + pad, yy, x1 - pad, yy), fill=_rgb(pal["line"]), width=3)
    _text(draw, (w // 2, 26), str(visual.get("title") or "מגילה / מסמך"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain":
        years = visual.get("years") or ["1948"]
        _text(draw, (w // 2, y0 - 8), str(years[0]), fill=pal["mark"], size=14, bold=True)


def _paint_map(draw, w, h, visual, pal, mode="lesson"):
    # schematic Israel-like strip (not a legal map — teaching silhouette)
    cx, cy = w // 2, h // 2 + 10
    pts = [
        (cx - 18, cy - 70), (cx + 10, cy - 62), (cx + 28, cy - 20),
        (cx + 22, cy + 20), (cx + 36, cy + 55), (cx + 8, cy + 70),
        (cx - 10, cy + 40), (cx - 30, cy + 10), (cx - 26, cy - 30),
    ]
    draw.polygon(pts, fill=_rgb("#DCE8DF"), outline=_rgb(pal["ink"]), width=2)
    # mediterranean hint
    draw.ellipse((cx - 120, cy - 50, cx - 40, cy + 50), outline=_rgb("#6FA8C9"), width=2)
    _text(draw, (cx - 80, cy), "ים", fill="#3E6F8A", size=12)
    # markers
    marks = [("ירושלים", cx - 4, cy - 8), ("ת\"א", cx - 22, cy - 5), ("חיפה", cx - 8, cy - 40)]
    for label, x, y in marks[: 3 if mode != "question" else 2]:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=_rgb(pal["mark"]))
        if mode != "question":
            _text(draw, (x + 28, y), label, fill=pal["ink"], size=11, anchor="lm")
    _text(draw, (w // 2, 26), str(visual.get("title") or "מפת הקשר"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain":
        _text(draw, (w // 2, h - 22), "סכמה לימודית, לא מפה מדינית", fill=pal["mute"], size=11)


def _paint_war(draw, w, h, visual, pal, mode="lesson"):
    years = list(visual.get("years") or ["1948", "1967", "1973"])
    title = str(visual.get("title") or "מערכות ומלחמות")
    _text(draw, (w // 2, 26), title, fill=pal["ink"], size=15, bold=True)
    n = min(3, len(years))
    box_w = int((w - 80) / max(1, n))
    labels = list(visual.get("labels") or ["עצמאות", "ששת הימים", "יום כיפור"])
    for i, year in enumerate(years[:n]):
        x0 = 40 + i * box_w
        y0, y1 = 58, h - 36
        highlight = mode == "explain" and i == min(1, n - 1)
        fill = _rgb(pal["mark"]) if highlight else _rgb(pal["paper"])
        outline = _rgb(pal["ink"]) if highlight else _rgb(pal["line"])
        draw.rounded_rectangle((x0 + 8, y0, x0 + box_w - 8, y1), radius=14, fill=fill, outline=outline, width=2)
        num_fill = "#FFFFFF" if highlight else pal["ink"]
        _text(draw, (x0 + box_w // 2, (y0 + y1) // 2 - 8), str(year), fill=num_fill, size=18, bold=True)
        if i < len(labels) and mode != "question":
            lab_fill = "#F8F4F0" if highlight else pal["mute"]
            _text(draw, (x0 + box_w // 2, y1 - 18), labels[i], fill=lab_fill, size=11)


def _paint_peace(draw, w, h, visual, pal, mode="lesson"):
    cx, cy = w // 2, h // 2 + 12
    draw.ellipse((cx - 70, cy - 40, cx - 10, cy + 20), outline=_rgb(pal["ink"]), width=3)
    draw.ellipse((cx + 10, cy - 40, cx + 70, cy + 20), outline=_rgb(pal["ink"]), width=3)
    draw.line((cx - 20, cy - 10, cx + 20, cy - 10), fill=_rgb(pal["mark"]), width=5)
    # olive leaf
    draw.ellipse((cx - 12, cy + 18, cx + 12, cy + 48), fill=_rgb("#3F7D4E"))
    draw.line((cx, cy + 18, cx, cy + 52), fill=_rgb("#245536"), width=2)
    _text(draw, (w // 2, 26), str(visual.get("title") or "הסכמי שלום"), fill=pal["ink"], size=15, bold=True)
    years = visual.get("years") or ["1979", "1994"]
    if mode != "question":
        _text(draw, (w // 2, h - 24), " · ".join(str(y) for y in years[:3]), fill=pal["mute"], size=12)


def _paint_aliyah(draw, w, h, visual, pal, mode="lesson"):
    # waves + boat silhouette
    for i, yy in enumerate((h - 50, h - 38, h - 26)):
        draw.arc((30, yy - 20, w - 30, yy + 20), start=0, end=180, fill=_rgb("#6FA8C9"), width=3)
    bx, by = w // 2 - 40, h // 2 - 10
    draw.polygon([(bx, by + 30), (bx + 80, by + 30), (bx + 70, by + 50), (bx + 10, by + 50)], fill=_rgb(pal["ink"]))
    draw.polygon([(bx + 40, by - 10), (bx + 40, by + 30), (bx + 70, by + 18)], fill=_rgb(pal["mark"]))
    _text(draw, (w // 2, 26), str(visual.get("title") or "עליות והעפלה"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain":
        _text(draw, (w // 2, 50), "גלים · ספינה · קליטה", fill=pal["mute"], size=12)


def _paint_congress(draw, w, h, visual, pal, mode="lesson"):
    x0, y0 = int(w * 0.28), int(h * 0.34)
    x1, y1 = int(w * 0.72), int(h * 0.78)
    draw.rectangle((x0, y0 + 20, x1, y1), fill=_rgb(pal["paper"]), outline=_rgb(pal["ink"]), width=2)
    draw.polygon([(x0 - 10, y0 + 20), ((x0 + x1) // 2, y0 - 10), (x1 + 10, y0 + 20)], fill=_rgb(pal["mark"]), outline=_rgb(pal["ink"]))
    for i in range(5):
        xx = x0 + 18 + i * ((x1 - x0 - 36) // 4)
        draw.rectangle((xx, y0 + 36, xx + 14, y1 - 12), fill=_rgb("#E8EEF2"), outline=_rgb(pal["line"]))
    _text(draw, (w // 2, 26), str(visual.get("title") or "קונגרס / מוסדות"), fill=pal["ink"], size=15, bold=True)
    years = visual.get("years") or ["1897"]
    if mode != "question":
        _text(draw, (w // 2, h - 22), str(years[0]), fill=pal["mute"], size=13, bold=True)


def _paint_state(draw, w, h, visual, pal, mode="lesson"):
    # three pillars: knesset / government / court — civic-history bridge
    labels = list(visual.get("labels") or ["כנסת", "ממשלה", "בית משפט"])
    gap = (w - 80) // 3
    for i, label in enumerate(labels[:3]):
        x0 = 40 + i * gap
        draw.rounded_rectangle((x0 + 10, 60, x0 + gap - 10, h - 40), radius=12, fill=_rgb(pal["paper"]), outline=_rgb(pal["mark"] if mode == "explain" else pal["line"]), width=2)
        draw.rectangle((x0 + 28, 78, x0 + gap - 28, 96), fill=_rgb(pal["mark"]))
        if mode != "question":
            _text(draw, (x0 + gap // 2, h - 58), label, fill=pal["ink"], size=13, bold=True)
    _text(draw, (w // 2, 26), str(visual.get("title") or "מוסדות המדינה"), fill=pal["ink"], size=15, bold=True)


def _paint_document(draw, w, h, visual, pal, mode="lesson"):
    x0, y0 = int(w * 0.30), int(h * 0.26)
    x1, y1 = int(w * 0.70), int(h * 0.84)
    draw.rectangle((x0, y0, x1, y1), fill=(255, 255, 255), outline=_rgb(pal["ink"]), width=2)
    draw.polygon([(x1 - 34, y0), (x1, y0), (x1, y0 + 34)], fill=_rgb(pal["wash"]), outline=_rgb(pal["ink"]))
    for yy in range(y0 + 40, y1 - 20, 16):
        draw.line((x0 + 18, yy, x1 - 18, yy), fill=_rgb(pal["line"]), width=2)
    draw.rectangle((x0 + 18, y0 + 16, x0 + 90, y0 + 28), fill=_rgb(pal["mark"]))
    _text(draw, (w // 2, 22), str(visual.get("title") or "מסמך / חוק / הצהרה"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain" and visual.get("years"):
        _text(draw, (w // 2, h - 20), str(visual["years"][0]), fill=pal["mute"], size=12, bold=True)


def _paint_memory(draw, w, h, visual, pal, mode="lesson"):
    # נר זיכרון פשוט: בסיס, גוף, להבה
    cx, cy = w // 2, h // 2 + 10
    base = cy + 42
    draw.rounded_rectangle((cx - 36, base - 8, cx + 36, base + 10), radius=6, fill=_rgb(pal["ink"]))
    draw.rounded_rectangle((cx - 14, cy - 8, cx + 14, base - 8), radius=4, fill=_rgb("#F4EDE2"), outline=_rgb(pal["line"]), width=2)
    # להבה
    draw.ellipse((cx - 10, cy - 36, cx + 10, cy - 10), fill=_rgb(pal["mark"]))
    draw.polygon([(cx, cy - 48), (cx + 12, cy - 22), (cx - 12, cy - 22)], fill=_rgb(pal["mark"]))
    draw.ellipse((cx - 4, cy - 30, cx + 4, cy - 18), fill=(255, 236, 180))
    _text(draw, (w // 2, 26), str(visual.get("title") or "זיכרון וגבורה"), fill=pal["ink"], size=15, bold=True)
    if mode == "explain":
        _text(draw, (w // 2, h - 22), "יום זיכרון · שואה · גבורה", fill=pal["mute"], size=11)


def _paint_reveal_badge(draw, w, h, visual, pal):
    note = str(visual.get("reveal_note") or "")[:42]
    if not note:
        return
    draw.rounded_rectangle((18, h - 34, w - 18, h - 12), radius=8, fill=_rgb(pal["ink"]))
    # keep badge short; full caption stays in UI
    _text(draw, (w // 2, h - 23), "הדגשה אחרי תשובה", fill="#FFFFFF", size=11, bold=True)
