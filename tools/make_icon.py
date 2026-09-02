"""יוצר סמל האפליקציה (PNG + ICO) מתוך איור המקור."""
from __future__ import annotations

import math
import os
import struct
import zlib
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
SOURCE = os.path.join(ASSETS, "icon_source.png")
OUT_ICO = os.path.join(ASSETS, "icon.ico")
OUT_PNG = os.path.join(ASSETS, "icon.png")

TEAL_TOP = (63, 208, 192, 255)
TEAL_BOT = (12, 122, 114, 255)
WHITE = (255, 255, 255, 255)
SPARK = (247, 198, 48, 255)


def _png(width: int, height: int, rgba: bytes) -> bytes:
    raw = b"".join(b"\x00" + rgba[y * width * 4 : (y + 1) * width * 4] for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def _set(buf: bytearray, size: int, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < size and 0 <= y < size:
        i = (y * size + x) * 4
        buf[i : i + 4] = bytes(color)


def _blend(buf: bytearray, size: int, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if not (0 <= x < size and 0 <= y < size):
        return
    ca = color[3]
    if ca >= 255:
        _set(buf, size, x, y, color)
        return
    if ca <= 0:
        return
    i = (y * size + x) * 4
    a = ca / 255.0
    buf[i] = int(buf[i] * (1 - a) + color[0] * a)
    buf[i + 1] = int(buf[i + 1] * (1 - a) + color[1] * a)
    buf[i + 2] = int(buf[i + 2] * (1 - a) + color[2] * a)
    buf[i + 3] = min(255, int(buf[i + 3] + (255 - buf[i + 3]) * a))


def _lerp(a: tuple, b: tuple, t: float) -> tuple[int, int, int, int]:
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
        int(a[3] + (b[3] - a[3]) * t),
    )


def _fill_polygon(buf: bytearray, size: int, pts: list[tuple[float, float]], color) -> None:
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)))
    n = len(pts)
    for y in range(y0, y1 + 1):
        ymid = y + 0.5
        xs: list[float] = []
        for i in range(n):
            x1, y1_ = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if y1_ > y2:
                x1, y1_, x2, y2 = x2, y2, x1, y1_
            if y2 == y1_ or not (y1_ <= ymid < y2):
                continue
            xs.append(x1 + (x2 - x1) * (ymid - y1_) / (y2 - y1_))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa, xb = int(xs[i]), int(xs[i + 1])
            for x in range(max(0, xa), min(size, xb + 1)):
                _set(buf, size, x, y, color)


def _fill_star(buf: bytearray, size: int, cx: float, cy: float, outer: float, inner: float, color) -> None:
    pts: list[tuple[float, float]] = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    _fill_polygon(buf, size, pts, color)


def _draw_hires(size: int, simple: bool) -> bytearray:
    buf = bytearray(size * size * 4)
    cx = cy = size * 0.5
    rx = ry = size * 0.5 - 1
    n = 4.8
    for y in range(size):
        gy = y / max(1, size - 1)
        base = _lerp(TEAL_TOP, TEAL_BOT, gy ** 0.9)
        sheen = max(0.0, 1.0 - gy / 0.38) * 0.10
        for x in range(size):
            dx = abs(x + 0.5 - cx) / rx
            dy = abs(y + 0.5 - cy) / ry
            d = dx ** n + dy ** n
            if d > 1.02:
                continue
            col = _lerp(base, WHITE, sheen) if sheen else base
            if d > 0.94:
                cover = max(0.0, min(1.0, (1.02 - d) / 0.08))
                _blend(buf, size, x, y, (col[0], col[1], col[2], int(255 * cover)))
            else:
                _set(buf, size, x, y, col)

    pad = size * (0.18 if simple else 0.19)
    mid = size * 0.5
    top = size * 0.33
    bot = size * 0.76
    gutter = max(2.0, size * 0.02)
    rise = size * 0.06
    left = [
        (pad, top + rise * 0.2),
        (mid - gutter, top + rise),
        (mid - gutter, bot),
        (pad + size * 0.012, bot - size * 0.025),
    ]
    right = [
        (mid + gutter, top + rise),
        (size - pad, top + rise * 0.2),
        (size - pad - size * 0.012, bot - size * 0.025),
        (mid + gutter, bot),
    ]
    _fill_polygon(buf, size, left, WHITE)
    _fill_polygon(buf, size, right, WHITE)
    spine = [
        (mid - gutter * 0.65, top + rise * 0.9),
        (mid + gutter * 0.65, top + rise * 0.9),
        (mid + gutter * 0.65, bot),
        (mid - gutter * 0.65, bot),
    ]
    _fill_polygon(buf, size, spine, TEAL_BOT)
    if not simple:
        _fill_star(buf, size, size * 0.73, size * 0.29, size * 0.08, size * 0.028, SPARK)
    return buf


def _downsample(src: bytearray, src_size: int, factor: int) -> bytes:
    dst = src_size // factor
    out = bytearray(dst * dst * 4)
    n = factor * factor
    for y in range(dst):
        for x in range(dst):
            r = g = b = a = 0
            for dy in range(factor):
                for dx in range(factor):
                    i = ((y * factor + dy) * src_size + (x * factor + dx)) * 4
                    r += src[i]
                    g += src[i + 1]
                    b += src[i + 2]
                    a += src[i + 3]
            j = (y * dst + x) * 4
            out[j : j + 4] = bytes((r // n, g // n, b // n, a // n))
    return bytes(out)


def _draw(size: int) -> bytes:
    factor = 4
    hi = size * factor
    return _png(size, size, _downsample(_draw_hires(hi, simple=size <= 24), hi, factor))


def _is_bg(r: int, g: int, b: int) -> bool:
    mx, mn = max(r, g, b), min(r, g, b)
    if mn < 200:
        return False
    return (mx - mn) / max(mx, 1) < 0.12


def _knockout(image) -> object:
    im = image.convert("RGBA")
    width, height = im.size
    pix = im.load()
    seen = bytearray(width * height)
    queue: deque[int] = deque()
    for x, y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        queue.append(y * width + x)
    while queue:
        i = queue.popleft()
        if seen[i]:
            continue
        seen[i] = 1
        x, y = i % width, i // width
        r, g, b, _a = pix[x, y]
        if not _is_bg(r, g, b):
            continue
        pix[x, y] = (0, 0, 0, 0)
        if x > 0:
            queue.append(i - 1)
        if x + 1 < width:
            queue.append(i + 1)
        if y > 0:
            queue.append(i - width)
        if y + 1 < height:
            queue.append(i + width)
    return im


def _master_from_source(path: str):
    from PIL import Image

    return _knockout(Image.open(path))


def _resize_image(image, size: int):
    from PIL import Image, ImageFilter

    out = image.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 48:
        out = out.filter(ImageFilter.UnsharpMask(radius=1.05, percent=145, threshold=1))
    return out


def _image_png_bytes(image) -> bytes:
    import io

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _pack_ico(path: str, png_by_size: dict[int, bytes]) -> None:
    sizes = sorted(png_by_size)
    offset = 6 + 16 * len(sizes)
    entries = b""
    payload = b""
    for size in sizes:
        data = png_by_size[size]
        w = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(struct.pack("<HHH", 0, 1, len(sizes)) + entries + payload)


def write_ico(path: str = OUT_ICO) -> str:
    sizes = (16, 32, 48, 256)
    png_by_size: dict[int, bytes] = {}
    os.makedirs(ASSETS, exist_ok=True)
    master = None
    if os.path.isfile(SOURCE):
        try:
            master = _master_from_source(SOURCE)
        except Exception:
            master = None
    for size in sizes:
        if master is not None:
            png_by_size[size] = _image_png_bytes(_resize_image(master, size))
        else:
            png_by_size[size] = _draw(size)

    with open(OUT_PNG, "wb") as handle:
        handle.write(png_by_size[256])
    _pack_ico(path, png_by_size)
    return path


if __name__ == "__main__":
    print(write_ico())
