#!/usr/bin/env python3
"""Create a polished storyboard/animatic MP4 for the Battery Re-X project.

The video is intentionally generated as an animatic: readable storyboard motion,
project-specific UI overlays, and technical captions. It does not claim to be a
photoreal render; it is a presentation-ready preview of the intended cinematic
industrial demo.
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "presentation" / "assets"
FIGURE_DIR = ROOT / "presentation" / "figures"
OUT_DIR = ROOT / "presentation" / "videos"

WIDTH = 1280
HEIGHT = 720
FPS = 20

OUT_MP4 = OUT_DIR / "Battery_ReX_Digital_Twin_Storyboard_Animatic.mp4"
OUT_POSTER = OUT_DIR / "Battery_ReX_Digital_Twin_Storyboard_Animatic_poster.png"
OUT_NOTES = OUT_DIR / "storyboard_animatic_notes.md"


PALETTE = {
    "bg_top": (5, 12, 18, 255),
    "bg_bottom": (15, 24, 30, 255),
    "floor": (24, 33, 40, 255),
    "floor_line": (51, 67, 78, 90),
    "panel": (12, 20, 27, 224),
    "panel_light": (24, 35, 44, 228),
    "text": (235, 246, 250, 255),
    "muted": (160, 180, 190, 255),
    "cyan": (34, 211, 238, 255),
    "green": (34, 197, 94, 255),
    "orange": (245, 158, 11, 255),
    "blue": (37, 99, 235, 255),
    "red": (220, 38, 38, 255),
    "gray": (107, 114, 128, 255),
    "belt": (185, 203, 215, 255),
    "belt_dark": (62, 76, 86, 255),
    "metal": (195, 213, 228, 255),
    "metal_dark": (102, 121, 137, 255),
    "white_arm": (226, 238, 248, 255),
    "shadow": (0, 0, 0, 90),
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    candidates.extend(
        [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT = {
    "tiny": load_font(12),
    "small": load_font(15),
    "small_b": load_font(15, True),
    "body": load_font(19),
    "body_b": load_font(19, True),
    "mid": load_font(24),
    "mid_b": load_font(24, True),
    "large": load_font(34, True),
    "hero": load_font(48, True),
    "massive": load_font(62, True),
}


def rgba(color, alpha=None):
    if alpha is None:
        return color
    return (color[0], color[1], color[2], alpha)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def ease(t: float) -> float:
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t: float) -> float:
    return 1 - (1 - clamp(t)) ** 3


def pulse(t: float) -> float:
    return 0.5 + 0.5 * math.sin(t * math.tau)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy,
    text: str,
    font: ImageFont.ImageFont,
    fill,
    max_width: int,
    line_spacing: float = 1.25,
):
    x, y = xy
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = int(font.size * line_spacing) if hasattr(font, "size") else 18
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def soft_shadow(img: Image.Image, xy, radius: int = 18, alpha: int = 120):
    x1, y1, x2, y2 = xy
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((x1 + 6, y1 + 8, x2 + 6, y2 + 8), radius=radius, fill=(0, 0, 0, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(12))
    img.alpha_composite(overlay)


def rounded_box(
    img: Image.Image,
    xy,
    fill,
    outline=None,
    width: int = 1,
    radius: int = 16,
    shadow: bool = False,
):
    if shadow:
        soft_shadow(img, xy, radius=radius)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    img.alpha_composite(overlay)


def glow(img: Image.Image, center, radius: int, color, strength: int = 110):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx, cy = center
    for i in range(6, 0, -1):
        r = radius * i / 6
        alpha = int(strength * (i / 6) ** 2 / 4)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(color, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius // 4))
    img.alpha_composite(overlay)


def pill(
    img: Image.Image,
    x: int,
    y: int,
    text: str,
    fill,
    text_fill=None,
    pad_x: int = 18,
    pad_y: int = 7,
    font=None,
):
    draw = ImageDraw.Draw(img)
    font = font or FONT["small_b"]
    text_fill = text_fill or PALETTE["text"]
    tw, th = text_size(draw, text, font)
    w = tw + pad_x * 2
    h = th + pad_y * 2 + 2
    rounded_box(img, (x, y, x + w, y + h), fill=fill, radius=h // 2)
    draw = ImageDraw.Draw(img)
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=text_fill)
    return w, h


def make_base_background() -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), PALETTE["bg_top"])
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = tuple(int(lerp(PALETTE["bg_top"][i], PALETTE["bg_bottom"][i], t)) for i in range(3)) + (255,)
        draw.line((0, y, WIDTH, y), fill=c)

    # Factory floor.
    floor_y = 420
    draw.rectangle((0, floor_y, WIDTH, HEIGHT), fill=PALETTE["floor"])
    for x in range(-200, WIDTH + 200, 90):
        draw.line((x, HEIGHT, 610 + (x - 610) * 0.12, floor_y), fill=PALETTE["floor_line"], width=1)
    for i in range(13):
        y = int(floor_y + (HEIGHT - floor_y) * (i / 12) ** 1.5)
        draw.line((0, y, WIDTH, y), fill=PALETTE["floor_line"], width=1)

    # Ceiling beams.
    for x in range(-100, WIDTH + 100, 180):
        draw.line((x, 0, x + 180, 210), fill=(48, 64, 75, 70), width=1)
    return img


BASE_BG = make_base_background()


def new_frame(t: float = 0.0) -> Image.Image:
    img = BASE_BG.copy()
    draw = ImageDraw.Draw(img)
    # Animated soft factory light.
    cx = int(220 + 840 * pulse(t * 0.05))
    glow(img, (cx, 165), 230, PALETTE["cyan"], strength=42)
    draw.rectangle((0, 0, WIDTH, HEIGHT), outline=(255, 255, 255, 18), width=2)
    return img


def paste_cover(base: Image.Image, src: Image.Image, box, radius: int = 0, opacity: int = 255):
    x1, y1, x2, y2 = map(int, box)
    w, h = x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        return
    source = src.convert("RGBA")
    sw, sh = source.size
    scale = max(w / sw, h / sh)
    resized = source.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
    rx = (resized.width - w) // 2
    ry = (resized.height - h) // 2
    crop = resized.crop((rx, ry, rx + w, ry + h))
    if opacity < 255:
        alpha = crop.getchannel("A").point(lambda p: int(p * opacity / 255))
        crop.putalpha(alpha)
    if radius > 0:
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
        crop.putalpha(mask)
    base.alpha_composite(crop, (x1, y1))


def load_asset(name: str, fallback_color=(40, 50, 60, 255)) -> Image.Image:
    path = ASSET_DIR / name
    if path.exists():
        return Image.open(path).convert("RGBA")
    img = Image.new("RGBA", (400, 240), fallback_color)
    d = ImageDraw.Draw(img)
    d.text((24, 100), name, font=FONT["body_b"], fill=PALETTE["text"])
    return img


def load_figure(name: str) -> Image.Image:
    path = FIGURE_DIR / name
    if path.exists():
        return Image.open(path).convert("RGBA")
    img = Image.new("RGBA", (1280, 720), (12, 20, 27, 255))
    d = ImageDraw.Draw(img)
    d.text((80, 320), name, font=FONT["large"], fill=PALETTE["text"])
    return img


PHOTO_CYL = load_asset("sample_cylindrical.jpg")
PHOTO_POUCH = load_asset("sample_pouch.jpg")
PHOTO_PRISM = load_asset("sample_prismatic.jpg")
SLIDE_ARCH = load_figure("slide-04.png")
SLIDE_DASH = load_figure("slide-13.png")
SLIDE_RESULTS = load_figure("slide-18.png")


def draw_header_footer(
    img: Image.Image,
    shot_idx: int,
    title: str,
    caption: str,
    progress: float,
):
    draw = ImageDraw.Draw(img)
    rounded_box(img, (28, 22, 430, 64), rgba(PALETTE["panel"], 210), radius=12)
    draw.text((46, 34), "Battery Re-X Digital Twin | Storyboard Animatic", font=FONT["small_b"], fill=PALETTE["text"])
    rounded_box(img, (1060, 22, 1248, 64), rgba(PALETTE["panel"], 210), radius=12)
    draw.text((1080, 34), f"Shot {shot_idx:02d} / 11", font=FONT["small_b"], fill=PALETTE["cyan"])

    # Overall progress.
    rounded_box(img, (36, 682, 1244, 700), rgba((0, 0, 0, 255), 120), radius=9)
    draw.rounded_rectangle((42, 688, 1238, 694), radius=3, fill=(54, 66, 74, 255))
    draw.rounded_rectangle((42, 688, int(42 + 1196 * progress), 694), radius=3, fill=PALETTE["cyan"])

    rounded_box(img, (170, 620, 1110, 672), rgba((4, 9, 13, 255), 180), radius=16)
    draw.text((196, 631), title, font=FONT["body_b"], fill=PALETTE["cyan"])
    draw_wrapped(draw, (435, 632), caption, FONT["small"], PALETTE["text"], 640, line_spacing=1.15)


def draw_conveyor(
    img: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    t: float,
    label: str = "",
    glow_color=None,
):
    draw = ImageDraw.Draw(img)
    soft_shadow(img, (x, y, x + w, y + h), radius=16, alpha=110)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=16, fill=(58, 71, 82, 255))
    draw.rounded_rectangle((x + 14, y + 12, x + w - 14, y + h - 12), radius=10, fill=PALETTE["belt"])
    draw.rectangle((x + 18, y + h // 2 - 7, x + w - 18, y + h // 2 + 7), fill=(222, 233, 240, 180))
    offset = int((t * 120) % 86)
    for sx in range(x + 24 - offset, x + w - 20, 86):
        draw.rounded_rectangle((sx, y + 18, sx + 24, y + h - 18), radius=4, fill=(132, 151, 164, 130))
    draw.ellipse((x - 10, y + 12, x + 22, y + h - 12), fill=(188, 205, 220, 255), outline=(91, 105, 116, 255), width=2)
    draw.ellipse((x + w - 22, y + 12, x + w + 10, y + h - 12), fill=(188, 205, 220, 255), outline=(91, 105, 116, 255), width=2)
    if glow_color:
        glow(img, (x + w // 2, y + h // 2), max(80, w // 6), glow_color, strength=55)
    if label:
        draw.text((x + 10, y - 26), label, font=FONT["small_b"], fill=PALETTE["muted"])


def draw_station_camera(img: Image.Image, x: int, y: int, t: float, active: bool = False):
    draw = ImageDraw.Draw(img)
    color = PALETTE["cyan"] if active else PALETTE["metal"]
    draw.rounded_rectangle((x - 18, y - 95, x + 18, y), radius=8, fill=PALETTE["metal_dark"])
    draw.rounded_rectangle((x - 62, y - 135, x + 62, y - 88), radius=14, fill=(205, 222, 235, 255))
    draw.ellipse((x - 27, y - 132, x + 27, y - 78), fill=(16, 24, 35, 255), outline=color, width=4)
    draw.ellipse((x - 15, y - 120, x + 15, y - 90), fill=(46, 92, 118, 255))
    if active:
        beam_alpha = int(70 + 40 * pulse(t * 2))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.polygon([(x - 26, y - 82), (x + 26, y - 82), (x + 78, y + 70), (x - 78, y + 70)], fill=rgba(PALETTE["cyan"], beam_alpha))
        img.alpha_composite(overlay)
        glow(img, (x, y - 105), 82, PALETTE["cyan"], strength=95)
    draw.text((x - 64, y + 12), "AI camera", font=FONT["small_b"], fill=PALETTE["cyan"] if active else PALETTE["muted"])


def draw_station_sensor(img: Image.Image, x: int, y: int, kind: str, accent, active: bool = False):
    draw = ImageDraw.Draw(img)
    if kind == "thermal":
        draw.rounded_rectangle((x - 34, y - 86, x + 34, y + 8), radius=10, fill=(50, 56, 64, 255))
        draw.rectangle((x - 18, y - 70, x + 18, y - 22), fill=(28, 31, 37, 255))
        for i, c in enumerate([PALETTE["red"], PALETTE["orange"], PALETTE["cyan"]]):
            draw.arc((x - 24 + i * 5, y - 77 + i * 5, x + 24 - i * 5, y - 29 - i * 5), 205, 335, fill=c, width=2)
        label = "Thermal"
    elif kind == "voltage":
        draw.rounded_rectangle((x - 70, y - 80, x + 70, y + 8), radius=14, fill=(68, 82, 92, 255))
        draw.rectangle((x - 48, y - 62, x + 48, y - 26), fill=(8, 15, 19, 255))
        draw.text((x - 37, y - 56), "3.72 V", font=FONT["small_b"], fill=accent)
        draw.line((x - 36, y + 8, x - 36, y + 42), fill=accent, width=4)
        draw.line((x + 36, y + 8, x + 36, y + 42), fill=accent, width=4)
        label = "Voltage"
    elif kind == "impedance":
        draw.rounded_rectangle((x - 54, y - 94, x + 54, y + 10), radius=16, fill=(64, 77, 90, 255))
        draw.arc((x - 36, y - 76, x + 36, y - 4), 180, 360, fill=accent, width=4)
        draw.rectangle((x - 7, y - 48, x + 7, y + 30), fill=accent)
        label = "Resistance"
    else:
        draw.rounded_rectangle((x - 28, y - 110, x + 28, y + 20), radius=12, fill=(65, 76, 88, 255))
        draw.ellipse((x - 20, y - 84, x + 20, y - 44), fill=(14, 19, 24, 255), outline=accent, width=3)
        label = "Safety IR"
    if active:
        glow(img, (x, y - 40), 70, accent, strength=80)
    draw.text((x - 42, y + 48), label, font=FONT["small_b"], fill=accent if active else PALETTE["muted"])


def draw_bin(img: Image.Image, x: int, y: int, label: str, color, active: bool = False, scale: float = 1.0):
    draw = ImageDraw.Draw(img)
    w = int(126 * scale)
    h = int(88 * scale)
    if active:
        glow(img, (x + w // 2, y + h // 2), 84, color, strength=100)
    shadow = (x + 8, y + h - 12, x + w + 8, y + h + 12)
    draw.ellipse(shadow, fill=(0, 0, 0, 80))
    draw.polygon(
        [(x + 8, y + 22), (x + w - 8, y + 22), (x + w - 28, y + h), (x + 28, y + h)],
        fill=(78, 90, 106, 255),
        outline=rgba(color, 230),
    )
    draw.polygon(
        [(x, y), (x + w, y), (x + w - 8, y + 22), (x + 8, y + 22)],
        fill=(159, 177, 208, 255),
        outline=rgba(color, 230),
    )
    draw.rectangle((x + 10, y + h - 10, x + w - 10, y + h - 3), fill=color)
    draw.text((x + 4, y - 25), label.upper(), font=FONT["small_b"], fill=color)


def draw_battery(img: Image.Image, cx: float, cy: float, scale: float, kind: str, label: str = "", active=False):
    draw = ImageDraw.Draw(img)
    kind = kind.lower()
    x = int(cx)
    y = int(cy)
    s = scale
    if active:
        glow(img, (x, y), int(70 * s), PALETTE["cyan"], strength=90)

    if kind == "cylindrical":
        w = int(112 * s)
        h = int(34 * s)
        draw.ellipse((x - w // 2 - 7, y - h // 2, x - w // 2 + 17, y + h // 2), fill=(92, 107, 117, 255))
        draw.rounded_rectangle((x - w // 2, y - h // 2, x + w // 2, y + h // 2), radius=h // 2, fill=(186, 196, 204, 255), outline=(74, 84, 94, 255), width=2)
        draw.ellipse((x + w // 2 - 17, y - h // 2, x + w // 2 + 7, y + h // 2), fill=(224, 232, 238, 255), outline=(74, 84, 94, 255), width=2)
        draw.rectangle((x - int(18 * s), y - h // 2, x + int(14 * s), y + h // 2), fill=(68, 87, 100, 120))
        draw.rectangle((x - w // 2 + 7, y - 3, x - w // 2 + 18, y + 3), fill=PALETTE["red"])
        draw.rectangle((x + w // 2 - 22, y - 3, x + w // 2 - 9, y + 3), fill=(25, 33, 38, 255))
    elif kind == "pouch":
        w = int(120 * s)
        h = int(70 * s)
        draw.rounded_rectangle((x - w // 2, y - h // 2, x + w // 2, y + h // 2), radius=int(10 * s), fill=(185, 193, 202, 255), outline=(86, 98, 112, 255), width=2)
        for i in range(5):
            yy = y - h // 2 + int((i + 1) * h / 6)
            draw.line((x - w // 2 + 10, yy, x + w // 2 - 10, yy), fill=(229, 237, 242, 100), width=max(1, int(1 * s)))
        draw.rectangle((x - int(32 * s), y - h // 2 - int(14 * s), x - int(10 * s), y - h // 2 + 2), fill=PALETTE["orange"])
        draw.rectangle((x + int(12 * s), y - h // 2 - int(14 * s), x + int(34 * s), y - h // 2 + 2), fill=PALETTE["gray"])
        draw.text((x - int(38 * s), y - int(6 * s)), "POUCH", font=FONT["tiny"], fill=(52, 66, 76, 255))
    elif kind == "prismatic":
        w = int(94 * s)
        h = int(64 * s)
        depth = int(20 * s)
        draw.polygon([(x - w // 2, y - h // 2), (x + w // 2, y - h // 2), (x + w // 2 + depth, y - h // 2 - depth), (x - w // 2 + depth, y - h // 2 - depth)], fill=(202, 216, 226, 255), outline=(82, 96, 109, 255))
        draw.polygon([(x + w // 2, y - h // 2), (x + w // 2 + depth, y - h // 2 - depth), (x + w // 2 + depth, y + h // 2 - depth), (x + w // 2, y + h // 2)], fill=(139, 156, 172, 255), outline=(82, 96, 109, 255))
        draw.rectangle((x - w // 2, y - h // 2, x + w // 2, y + h // 2), fill=(178, 193, 207, 255), outline=(82, 96, 109, 255), width=2)
        draw.rectangle((x - int(30 * s), y - h // 2 - int(10 * s), x - int(16 * s), y - h // 2 + 4), fill=PALETTE["red"])
        draw.rectangle((x + int(16 * s), y - h // 2 - int(10 * s), x + int(30 * s), y - h // 2 + 4), fill=(33, 40, 47, 255))
        draw.text((x - int(34 * s), y - int(3 * s)), "PRISM", font=FONT["tiny"], fill=(54, 70, 83, 255))
    else:
        w = int(96 * s)
        h = int(52 * s)
        draw.rounded_rectangle((x - w // 2, y - h // 2, x + w // 2, y + h // 2), radius=12, fill=(98, 109, 118, 255), outline=PALETTE["gray"], width=2)
        draw.text((x - 7, y - 10), "?", font=FONT["mid_b"], fill=PALETTE["text"])

    if label:
        draw.text((x - 52, y + int(42 * s)), label, font=FONT["small_b"], fill=PALETTE["text"])


def draw_metric_row(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    value: str,
    color=None,
    font=None,
):
    font = font or FONT["small"]
    color = color or PALETTE["text"]
    draw.text((x, y), label, font=FONT["small_b"], fill=PALETTE["muted"])
    draw.text((x + 190, y), value, font=font, fill=color)


def draw_project_ai_panel(
    img: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    status: str,
    accent,
    lines,
    thumbnail: Image.Image | None = None,
):
    rounded_box(img, (x, y, x + w, y + h), rgba(PALETTE["panel"], 232), outline=rgba(accent, 130), radius=18, shadow=True)
    draw = ImageDraw.Draw(img)
    draw.text((x + 22, y + 18), "AI Inspection Panel", font=FONT["mid_b"], fill=PALETTE["text"])
    pill(img, x + w - 170, y + 16, status, rgba(accent, 220), font=FONT["small_b"])
    yy = y + 70
    for label, value, col in lines:
        draw_metric_row(draw, x + 22, yy, label, value, col)
        yy += 29
    if thumbnail is not None:
        ty = y + h - 136
        draw.text((x + 22, ty - 25), "Captured Image", font=FONT["small_b"], fill=PALETTE["text"])
        rounded_box(img, (x + 22, ty, x + 172, ty + 94), rgba((0, 0, 0, 255), 120), radius=10)
        paste_cover(img, thumbnail, (x + 26, ty + 4, x + 168, ty + 90), radius=8)


def draw_threshold_ladder(img: Image.Image, x: int, y: int, active: str):
    draw = ImageDraw.Draw(img)
    rules = [
        ("Reuse", "SOH >= 80%", PALETTE["green"]),
        ("Remanufacture", "60% to 79%", PALETTE["orange"]),
        ("Recycle", "30% to 59%", PALETTE["blue"]),
        ("Quarantine", "< 30% or unsafe", PALETTE["red"]),
    ]
    for i, (name, rule, color) in enumerate(rules):
        yy = y + i * 58
        fill = rgba(color, 205 if name.lower() == active.lower() else 52)
        outline = rgba(color, 240 if name.lower() == active.lower() else 120)
        rounded_box(img, (x, yy, x + 310, yy + 44), fill, outline=outline, radius=12)
        draw.text((x + 16, yy + 10), name, font=FONT["body_b"], fill=PALETTE["text"])
        draw.text((x + 180, yy + 12), rule, font=FONT["small_b"], fill=PALETTE["text"])


def draw_robot_arm(img: Image.Image, gripper, open_amount: float = 1.0, active: bool = True):
    draw = ImageDraw.Draw(img)
    gx, gy = gripper
    base = (820, 540)
    elbow = (int(lerp(base[0], gx, 0.42)), int(min(base[1] - 120, gy - 95)))
    wrist = (int(lerp(elbow[0], gx, 0.72)), int(lerp(elbow[1], gy, 0.72)))
    if active:
        glow(img, gripper, 60, PALETTE["cyan"], strength=50)
    draw.ellipse((base[0] - 34, base[1] - 20, base[0] + 34, base[1] + 20), fill=(68, 78, 88, 255))
    draw.line((base, elbow), fill=PALETTE["white_arm"], width=26)
    draw.line((elbow, wrist), fill=PALETTE["white_arm"], width=22)
    draw.line((wrist, (gx, gy - 16)), fill=PALETTE["white_arm"], width=16)
    for pt, r in [(base, 22), (elbow, 24), (wrist, 18), ((gx, gy - 16), 14)]:
        draw.ellipse((pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r), fill=(205, 222, 237, 255), outline=(98, 112, 126, 255), width=3)
    claw_gap = int(22 + 28 * clamp(open_amount))
    draw.line((gx - claw_gap, gy - 14, gx - claw_gap, gy + 26), fill=(36, 45, 54, 255), width=8)
    draw.line((gx + claw_gap, gy - 14, gx + claw_gap, gy + 26), fill=(36, 45, 54, 255), width=8)
    draw.line((gx - claw_gap, gy + 24, gx - 12, gy + 24), fill=(36, 45, 54, 255), width=8)
    draw.line((gx + 12, gy + 24, gx + claw_gap, gy + 24), fill=(36, 45, 54, 255), width=8)


def draw_factory_line(img: Image.Image, t: float, focus: str = "", batteries=None, active_bin: str = ""):
    draw_conveyor(img, 82, 456, 940, 90, t, "continuous inspection conveyor")
    draw_station_camera(img, 270, 456, t, active=(focus == "camera"))
    draw_station_sensor(img, 438, 456, "thermal", PALETTE["orange"], active=(focus == "thermal"))
    draw_station_sensor(img, 610, 456, "voltage", (250, 215, 80, 255), active=(focus == "voltage"))
    draw_station_sensor(img, 744, 456, "impedance", PALETTE["cyan"], active=(focus == "impedance"))
    draw_station_sensor(img, 892, 456, "ir", PALETTE["green"], active=(focus == "safety"))

    # Connected final conveyors to bins.
    draw_conveyor(img, 1010, 362, 170, 60, t, "", glow_color=PALETTE["green"] if active_bin == "reuse" else None)
    draw_conveyor(img, 1010, 432, 170, 60, t, "", glow_color=PALETTE["orange"] if active_bin == "remanufacture" else None)
    draw_conveyor(img, 1010, 502, 170, 60, t, "", glow_color=PALETTE["blue"] if active_bin == "recycle" else None)
    draw_conveyor(img, 1010, 572, 170, 60, t, "", glow_color=PALETTE["red"] if active_bin == "quarantine" else None)
    draw_bin(img, 1130, 326, "Reuse", PALETTE["green"], active=active_bin == "reuse", scale=0.78)
    draw_bin(img, 1130, 396, "Reman", PALETTE["orange"], active=active_bin == "remanufacture", scale=0.78)
    draw_bin(img, 1130, 466, "Recycle", PALETTE["blue"], active=active_bin == "recycle", scale=0.78)
    draw_bin(img, 1130, 536, "Quarantine", PALETTE["red"], active=active_bin == "quarantine", scale=0.78)

    draw_robot_arm(img, (948, 430), open_amount=0.9, active=focus == "robot")
    draw = ImageDraw.Draw(img)
    draw.text((842, 582), "Re-X decision gate", font=FONT["body_b"], fill=PALETTE["text"])

    if batteries:
        for b in batteries:
            draw_battery(
                img,
                b.get("x", 200),
                b.get("y", 502),
                b.get("scale", 0.72),
                b.get("kind", "unknown"),
                b.get("label", ""),
                active=b.get("active", False),
            )


def scene_hero(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw = ImageDraw.Draw(img)
    draw.text((76, 100), "AI-Powered Battery Re-X Sorting", font=FONT["hero"], fill=PALETTE["text"])
    draw_wrapped(
        draw,
        (82, 166),
        "Computer vision identifies shape. Sensor stations collect health data. ML predicts SOH. Re-X rules route each battery.",
        FONT["body"],
        PALETTE["muted"],
        760,
    )
    pill(img, 82, 230, "Digital Twin Controlled Circular Manufacturing", rgba(PALETTE["cyan"], 150), font=FONT["small_b"])
    pill(img, 405, 230, "CV + SOH ML + Robot Sorting", rgba(PALETTE["green"], 150), font=FONT["small_b"])

    batteries = [
        {"x": 156 + 44 * pulse(g * 0.10), "kind": "unknown", "label": "BAT_001", "active": True},
        {"x": 360, "kind": "cylindrical", "label": "Cyl"},
        {"x": 560, "kind": "pouch", "label": "Pouch"},
        {"x": 720, "kind": "prismatic", "label": "Prism"},
    ]
    draw_factory_line(img, g, focus="camera", batteries=batteries, active_bin="reuse")

    # Premium dashboard preview.
    rounded_box(img, (905, 94, 1215, 300), rgba(PALETTE["panel"], 226), outline=rgba(PALETTE["cyan"], 90), radius=18, shadow=True)
    draw.text((928, 116), "Live Factory Status", font=FONT["mid_b"], fill=PALETTE["text"])
    rows = [
        ("Queue", "3 batteries"),
        ("Vision", "Shape only"),
        ("SOH Model", "RandomForestRegressor"),
        ("Safety", "Passed"),
        ("Active Route", "reuse_bin"),
    ]
    yy = 164
    for label, value in rows:
        draw_metric_row(draw, 928, yy, label, value, PALETTE["cyan"] if label == "Active Route" else PALETTE["text"])
        yy += 27
    return img


def scene_pov(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw = ImageDraw.Draw(img)
    # Low conveyor perspective.
    offset = int(t * 160)
    draw.polygon([(90, 690), (1190, 690), (790, 270), (490, 270)], fill=(55, 69, 78, 255))
    draw.polygon([(130, 690), (1150, 690), (755, 300), (525, 300)], fill=PALETTE["belt"])
    for i in range(-2, 15):
        yy = 680 - ((i * 58 + offset) % 760)
        if yy < 285 or yy > HEIGHT:
            continue
        width = int(max(160, 900 * (yy / HEIGHT)))
        draw.rounded_rectangle((640 - width // 2, yy, 640 + width // 2, yy + 16), radius=5, fill=(139, 156, 168, 120))
    # Battery fixed in foreground as if camera rides behind it.
    draw_battery(img, 640, 560, 1.65, "unknown", "Unknown intake battery", active=True)
    draw_station_camera(img, 640, 315, g, active=True)
    rounded_box(img, (830, 95, 1185, 246), rgba(PALETTE["panel"], 222), outline=rgba(PALETTE["cyan"], 110), radius=18, shadow=True)
    draw.text((854, 118), "Conveyor Queue Logic", font=FONT["mid_b"], fill=PALETTE["text"])
    draw_wrapped(
        draw,
        (854, 158),
        "The next battery waits until image capture and backend response finish. No battery overlap or collision is allowed.",
        FONT["body"],
        PALETTE["muted"],
        292,
    )
    return img


def scene_camera(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw_factory_line(
        img,
        g,
        focus="camera",
        batteries=[
            {"x": 270, "kind": "cylindrical", "label": "BAT_001", "active": True},
            {"x": 120, "kind": "unknown", "label": "waiting"},
        ],
    )
    draw = ImageDraw.Draw(img)
    rounded_box(img, (760, 96, 1198, 396), rgba(PALETTE["panel"], 235), outline=rgba(PALETTE["cyan"], 140), radius=20, shadow=True)
    draw.text((786, 122), "Camera Feed", font=FONT["mid_b"], fill=PALETTE["text"])
    paste_cover(img, PHOTO_CYL, (786, 166, 1002, 304), radius=12)
    scan_y = int(172 + 126 * pulse(g * 1.3))
    draw.line((790, scan_y, 998, scan_y), fill=PALETTE["cyan"], width=3)
    draw.text((1025, 170), "Image Captured", font=FONT["body_b"], fill=PALETTE["green"])
    draw.text((1025, 204), "Sending to AI Backend", font=FONT["body"], fill=PALETTE["text"])
    draw.text((1025, 236), "Visual Classification", font=FONT["body"], fill=PALETTE["text"])
    draw.text((1025, 268), "SOH: not estimated here", font=FONT["body_b"], fill=PALETTE["orange"])
    pill(img, 786, 330, "Camera image used for physical type only", rgba(PALETTE["cyan"], 135), font=FONT["small_b"])
    return img


def scene_classification(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw = ImageDraw.Draw(img)
    draw.text((72, 96), "Stage 1: Computer Vision Shape Classification", font=FONT["large"], fill=PALETTE["text"])
    draw_wrapped(
        draw,
        (76, 143),
        "The vision backend detects only the physical shape: cylindrical, pouch, prismatic, or unknown. It does not predict battery health.",
        FONT["body"],
        PALETTE["muted"],
        840,
    )
    cards = [
        ("Cylindrical", PHOTO_CYL, PALETTE["green"], True),
        ("Pouch", PHOTO_POUCH, PALETTE["gray"], False),
        ("Prismatic", PHOTO_PRISM, PALETTE["gray"], False),
    ]
    for i, (name, photo, color, active) in enumerate(cards):
        x = 80 + i * 310
        y = 230
        rounded_box(img, (x, y, x + 270, y + 240), rgba(PALETTE["panel"], 225), outline=rgba(color, 210 if active else 80), radius=18, shadow=True)
        paste_cover(img, photo, (x + 18, y + 24, x + 252, y + 148), radius=12)
        if active:
            sy = int(y + 30 + 108 * pulse(g * 1.8))
            draw.line((x + 22, sy, x + 248, sy), fill=PALETTE["cyan"], width=3)
            pill(img, x + 18, y + 164, "Detected", rgba(PALETTE["green"], 180), font=FONT["small_b"])
        draw.text((x + 18, y + 202), name, font=FONT["body_b"], fill=PALETTE["text"])

    draw_project_ai_panel(
        img,
        965,
        165,
        260,
        360,
        "CLASSIFIED",
        PALETTE["green"],
        [
            ("Battery ID", "BAT_001", PALETTE["text"]),
            ("Physical Shape", "CYLINDRICAL", PALETTE["green"]),
            ("Vision Trust", "92%", PALETTE["cyan"]),
            ("Lifecycle Decision", "waiting", PALETTE["orange"]),
            ("Data Used", "image only", PALETTE["text"]),
        ],
        PHOTO_CYL,
    )
    return img


def scene_sensors(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    x = lerp(350, 780, ease(t))
    focus = "thermal"
    if t > 0.30:
        focus = "voltage"
    if t > 0.55:
        focus = "impedance"
    if t > 0.76:
        focus = "safety"
    draw_factory_line(
        img,
        g,
        focus=focus,
        batteries=[
            {"x": x, "kind": "cylindrical", "label": "BAT_001", "active": True},
            {"x": 208, "kind": "unknown", "label": "BAT_002 waits"},
        ],
    )
    draw = ImageDraw.Draw(img)
    rounded_box(img, (78, 88, 510, 344), rgba(PALETTE["panel"], 228), outline=rgba(PALETTE["orange"], 90), radius=18, shadow=True)
    draw.text((104, 114), "Stage 2: Sensor Health Data", font=FONT["mid_b"], fill=PALETTE["text"])
    data = [
        (0.08, "Cycle Count", "430 cycles", PALETTE["text"]),
        (0.22, "Temperature", "31.2 C", PALETTE["orange"]),
        (0.38, "Voltage", "3.72 V", (250, 215, 80, 255)),
        (0.54, "Internal Resistance", "0.052 ohm", PALETTE["cyan"]),
        (0.70, "Safety Flags", "normal", PALETTE["green"]),
    ]
    yy = 166
    for threshold, label, value, color in data:
        alpha = 255 if t >= threshold else 80
        draw_metric_row(draw, 106, yy, label, value if t >= threshold else "waiting", rgba(color, alpha))
        yy += 32
    draw_wrapped(
        draw,
        (106, 318),
        "These values are mock sensor data in the Unity prototype, because the image dataset does not contain health measurements.",
        FONT["small"],
        PALETTE["muted"],
        360,
    )
    return img


def scene_ml(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw = ImageDraw.Draw(img)
    draw.text((70, 82), "Backend ML: SOH Prediction From Health Parameters", font=FONT["large"], fill=PALETTE["text"])
    paste_cover(img, SLIDE_RESULTS, (72, 148, 560, 423), radius=18, opacity=205)
    rounded_box(img, (604, 120, 1202, 560), rgba(PALETTE["panel"], 236), outline=rgba(PALETTE["cyan"], 140), radius=22, shadow=True)
    draw.text((634, 150), "SOH Prediction API", font=FONT["mid_b"], fill=PALETTE["text"])
    pill(img, 1008, 148, "RandomForestRegressor", rgba(PALETTE["cyan"], 140), font=FONT["small_b"])

    inputs = [
        ("battery_type", "cylindrical"),
        ("cycle_count", "430"),
        ("temperature", "31.2 C"),
        ("voltage", "3.72 V"),
        ("resistance", "0.052 ohm"),
    ]
    yy = 206
    draw.text((634, yy), "Input feature vector", font=FONT["body_b"], fill=PALETTE["cyan"])
    yy += 34
    for label, value in inputs:
        draw_metric_row(draw, 654, yy, label, value, PALETTE["text"])
        yy += 30

    # Gauge.
    center = (984, 382)
    radius = 98
    draw.arc((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), 180, 360, fill=(61, 74, 84, 255), width=16)
    soh = 94.49
    angle = 180 + 180 * min(soh / 100.0, 1.0) * ease_out(t)
    draw.arc((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), 180, angle, fill=PALETTE["green"], width=16)
    needle_angle = math.radians(angle)
    nx = center[0] + int(math.cos(needle_angle) * (radius - 18))
    ny = center[1] + int(math.sin(needle_angle) * (radius - 18))
    draw.line((center[0], center[1], nx, ny), fill=PALETTE["text"], width=4)
    draw.ellipse((center[0] - 7, center[1] - 7, center[0] + 7, center[1] + 7), fill=PALETTE["text"])
    draw.text((914, 394), f"{soh:.2f}%", font=FONT["large"], fill=PALETTE["green"])
    draw.text((902, 440), "Predicted SOH", font=FONT["small_b"], fill=PALETTE["muted"])

    rounded_box(img, (634, 474, 1170, 526), rgba(PALETTE["green"], 55), outline=rgba(PALETTE["green"], 160), radius=14)
    draw.text((654, 490), "Important: SOH is predicted from sensor data, not image pixels.", font=FONT["body_b"], fill=PALETTE["text"])
    return img


def scene_decision(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw = ImageDraw.Draw(img)
    draw.text((70, 84), "Re-X Decision Engine", font=FONT["large"], fill=PALETTE["text"])
    draw_wrapped(
        draw,
        (74, 128),
        "The decision layer combines predicted SOH with safety overrides. Abnormal readings or missing data go to quarantine.",
        FONT["body"],
        PALETTE["muted"],
        760,
    )
    draw_threshold_ladder(img, 78, 214, "Reuse")
    draw_factory_line(
        img,
        g,
        focus="robot",
        batteries=[{"x": 895, "kind": "cylindrical", "label": "SOH 94.49%", "active": True}],
        active_bin="reuse",
    )
    # Route highlight.
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    route_t = ease(t)
    end_x = int(895 + (1110 - 895) * route_t)
    od.line((895, 490, end_x, 390), fill=rgba(PALETTE["green"], 230), width=8)
    od.ellipse((end_x - 8, 390 - 8, end_x + 8, 390 + 8), fill=PALETTE["green"])
    img.alpha_composite(overlay)
    rounded_box(img, (780, 116, 1194, 274), rgba(PALETTE["panel"], 230), outline=rgba(PALETTE["green"], 150), radius=18, shadow=True)
    draw.text((806, 142), "Decision Output", font=FONT["mid_b"], fill=PALETTE["text"])
    draw_metric_row(draw, 806, 190, "Re-X Category", "REUSE", PALETTE["green"], FONT["body_b"])
    draw_metric_row(draw, 806, 224, "Target Bin", "reuse_bin", PALETTE["text"], FONT["body"])
    return img


def scene_robot(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw_conveyor(img, 150, 500, 700, 88, g, "robot pick zone")
    draw_conveyor(img, 930, 350, 210, 68, g, "connected route to reuse bin", glow_color=PALETTE["green"])
    draw_bin(img, 1080, 285, "Reuse", PALETTE["green"], active=True, scale=1.05)

    # Gripper and battery trajectory.
    if t < 0.18:
        p = ease(t / 0.18)
        gripper = (int(lerp(835, 650, p)), int(lerp(365, 462, p)))
        battery = (650, 532)
        open_amount = 1.0
        carried = False
    elif t < 0.34:
        gripper = (650, 462)
        battery = (650, 532)
        open_amount = 1.0 - ease((t - 0.18) / 0.16)
        carried = False
    elif t < 0.52:
        p = ease((t - 0.34) / 0.18)
        gripper = (650, int(lerp(462, 362, p)))
        battery = (650, int(lerp(532, 432, p)))
        open_amount = 0.0
        carried = True
    elif t < 0.78:
        p = ease((t - 0.52) / 0.26)
        gripper = (int(lerp(650, 1050, p)), int(lerp(362, 310, p)))
        battery = (int(lerp(650, 1050, p)), int(lerp(432, 380, p)))
        open_amount = 0.0
        carried = True
    elif t < 0.90:
        p = ease((t - 0.78) / 0.12)
        gripper = (1050, 310)
        battery = (1050, int(lerp(380, 355, p)))
        open_amount = ease((t - 0.78) / 0.12)
        carried = p < 0.72
    else:
        p = ease((t - 0.90) / 0.10)
        gripper = (int(lerp(1050, 850, p)), int(lerp(310, 365, p)))
        battery = (1050, 355)
        open_amount = 1.0
        carried = False

    if not carried:
        draw_battery(img, battery[0], battery[1], 0.85, "cylindrical", active=t < 0.80)
    draw_robot_arm(img, gripper, open_amount=open_amount, active=True)
    if carried:
        draw_battery(img, battery[0], battery[1], 0.85, "cylindrical", active=True)

    draw = ImageDraw.Draw(img)
    rounded_box(img, (72, 96, 438, 268), rgba(PALETTE["panel"], 230), outline=rgba(PALETTE["green"], 140), radius=18, shadow=True)
    draw.text((96, 122), "Robot Pick and Release", font=FONT["mid_b"], fill=PALETTE["text"])
    draw_wrapped(
        draw,
        (96, 164),
        "The collaborative arm aligns, closes the gripper, lifts the battery, moves to the target bin, releases it, and returns home.",
        FONT["body"],
        PALETTE["muted"],
        300,
    )
    pill(img, 96, 224, "Robot task confirmed -> reuse_bin", rgba(PALETTE["green"], 160), font=FONT["small_b"])
    return img


def scene_dashboard(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    paste_cover(img, SLIDE_DASH, (64, 98, 1218, 610), radius=22, opacity=188)
    draw = ImageDraw.Draw(img)
    rounded_box(img, (88, 116, 410, 560), rgba(PALETTE["panel"], 235), outline=rgba(PALETTE["cyan"], 140), radius=18, shadow=True)
    draw.text((112, 144), "Unity Digital Twin", font=FONT["mid_b"], fill=PALETTE["text"])
    cards = [
        ("BAT_001", "Cylindrical", "94.49%", "Reuse", PALETTE["green"], PHOTO_CYL),
        ("BAT_002", "Pouch", "78.40%", "Reman", PALETTE["orange"], PHOTO_POUCH),
        ("BAT_003", "Prismatic", "51.70%", "Recycle", PALETTE["blue"], PHOTO_PRISM),
    ]
    yy = 196
    for idx, (bid, typ, soh, rex, col, photo) in enumerate(cards):
        rounded_box(img, (112, yy, 386, yy + 92), rgba(PALETTE["panel_light"], 220), outline=rgba(col, 145), radius=14)
        paste_cover(img, photo, (124, yy + 12, 188, yy + 74), radius=8)
        draw.text((204, yy + 12), bid, font=FONT["small_b"], fill=PALETTE["text"])
        draw.text((204, yy + 34), typ, font=FONT["small"], fill=PALETTE["muted"])
        draw.text((204, yy + 57), f"SOH {soh} | {rex}", font=FONT["small_b"], fill=col)
        yy += 108

    rounded_box(img, (850, 132, 1175, 544), rgba(PALETTE["panel"], 235), outline=rgba(PALETTE["green"], 120), radius=18, shadow=True)
    draw.text((874, 160), "Selected Battery Detail", font=FONT["mid_b"], fill=PALETTE["text"])
    paste_cover(img, PHOTO_CYL, (874, 206, 1040, 310), radius=12)
    detail = [
        ("Battery ID", "BAT_001"),
        ("Vision Type", "CYLINDRICAL"),
        ("Cycle Count", "430"),
        ("Temperature", "31.2 C"),
        ("Voltage", "3.72 V"),
        ("Resistance", "0.052 ohm"),
        ("Predicted SOH", "94.49%"),
        ("Re-X", "REUSE"),
    ]
    yy = 330
    for label, value in detail:
        draw_metric_row(draw, 874, yy, label, value, PALETTE["green"] if label in {"Predicted SOH", "Re-X"} else PALETTE["text"])
        yy += 24
    return img


def scene_arvr(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    draw = ImageDraw.Draw(img)
    draw.text((74, 86), "Remote AR/VR Supervision", font=FONT["large"], fill=PALETTE["text"])
    draw_wrapped(
        draw,
        (78, 132),
        "Supervisors monitor the digital twin virtually. No operator physically touches batteries on the factory floor.",
        FONT["body"],
        PALETTE["muted"],
        720,
    )

    # Holographic avatars and control panels.
    for i, x in enumerate([278, 1010]):
        y = 394
        glow(img, (x, y - 80), 120, PALETTE["cyan"], strength=55)
        draw.ellipse((x - 42, y - 164, x + 42, y - 80), fill=(44, 82, 99, 160), outline=PALETTE["cyan"], width=2)
        draw.rounded_rectangle((x - 64, y - 136, x + 64, y - 105), radius=12, fill=(12, 22, 29, 230), outline=PALETTE["cyan"], width=2)
        draw.polygon([(x - 82, y - 72), (x + 82, y - 72), (x + 112, y + 86), (x - 112, y + 86)], fill=(42, 93, 115, 70), outline=rgba(PALETTE["cyan"], 150))
        draw.text((x - 57, y + 102), f"Remote node {i + 1}", font=FONT["small_b"], fill=PALETTE["cyan"])

    rounded_box(img, (420, 208, 858, 506), rgba(PALETTE["panel"], 235), outline=rgba(PALETTE["cyan"], 160), radius=22, shadow=True)
    draw.text((450, 236), "Virtual Control Room", font=FONT["mid_b"], fill=PALETTE["text"])
    controls = [
        ("Conveyor speed", "normal"),
        ("Robot cycle time", "8.7 s"),
        ("AI confidence threshold", "0.65"),
        ("Reuse SOH threshold", "80%"),
        ("Manual override", "available"),
        ("Twin sync", "active"),
    ]
    yy = 292
    for label, value in controls:
        draw_metric_row(draw, 452, yy, label, value, PALETTE["cyan"] if value == "active" else PALETTE["text"])
        yy += 32
    return img


def scene_final(t: float, g: float) -> Image.Image:
    img = new_frame(g)
    batteries = [
        {"x": 200 + 28 * pulse(g * 0.1), "kind": "unknown", "label": "intake"},
        {"x": 310, "kind": "cylindrical", "label": "vision", "active": True},
        {"x": 520, "kind": "pouch", "label": "sensors"},
        {"x": 760, "kind": "prismatic", "label": "ML"},
        {"x": 920, "kind": "cylindrical", "label": "sort"},
    ]
    draw_factory_line(img, g, focus="robot", batteries=batteries, active_bin="reuse")
    draw = ImageDraw.Draw(img)
    rounded_box(img, (86, 82, 1194, 250), rgba((3, 9, 13, 255), 185), outline=rgba(PALETTE["cyan"], 130), radius=24, shadow=True)
    draw.text((118, 112), "AI-Powered Robotic Battery Sorting", font=FONT["hero"], fill=PALETTE["text"])
    draw.text((122, 174), "Computer Vision + SOH Prediction + Re-X Decision Support", font=FONT["mid_b"], fill=PALETTE["cyan"])
    pill(img, 122, 214, "Automated reuse, remanufacturing, recycling and quarantine workflow", rgba(PALETTE["green"], 150), font=FONT["small_b"])
    # Four category counters.
    x = 126
    for label, count, col in [
        ("Reuse", "1", PALETTE["green"]),
        ("Remanufacture", "1", PALETTE["orange"]),
        ("Recycle", "1", PALETTE["blue"]),
        ("Quarantine", "0", PALETTE["red"]),
    ]:
        rounded_box(img, (x, 288, x + 220, 356), rgba(PALETTE["panel"], 225), outline=rgba(col, 140), radius=16)
        draw.text((x + 22, 304), label, font=FONT["body_b"], fill=col)
        draw.text((x + 172, 300), count, font=FONT["large"], fill=PALETTE["text"])
        x += 240
    return img


SHOTS = [
    {
        "title": "Smart Factory Hero",
        "duration": 6,
        "caption": "Opening view of the Battery Re-X digital twin: conveyors, inspection stations, robot sorting and live dashboards.",
        "func": scene_hero,
    },
    {
        "title": "Unknown Battery Intake",
        "duration": 6,
        "caption": "The next battery waits until the current image classification and backend response are complete.",
        "func": scene_pov,
    },
    {
        "title": "Camera Image Capture",
        "duration": 7,
        "caption": "The camera captures an image and sends it to the AI backend for physical shape classification only.",
        "func": scene_camera,
    },
    {
        "title": "Computer Vision Shape Detection",
        "duration": 7,
        "caption": "The model detects cylindrical, pouch, prismatic or unknown. Battery health is not inferred from the image.",
        "func": scene_classification,
    },
    {
        "title": "Sensor Health Data Collection",
        "duration": 8,
        "caption": "Thermal, voltage, internal resistance, safety and cycle-count data update one by one for the battery.",
        "func": scene_sensors,
    },
    {
        "title": "ML-Based SOH Prediction",
        "duration": 7,
        "caption": "The backend predicts State of Health from sensor parameters using the selected RandomForestRegressor model.",
        "func": scene_ml,
    },
    {
        "title": "Re-X Decision Engine",
        "duration": 7,
        "caption": "Lifecycle rules and safety overrides assign the final Re-X category and target bin.",
        "func": scene_decision,
    },
    {
        "title": "Robot Pick And Release",
        "duration": 9,
        "caption": "The collaborative robot grips, lifts and releases the battery into the correct colored bin.",
        "func": scene_robot,
    },
    {
        "title": "Unity-Style Digital Twin Dashboard",
        "duration": 6,
        "caption": "Each battery has its own inspection record with captured image, sensor data, SOH and Re-X decision.",
        "func": scene_dashboard,
    },
    {
        "title": "AR/VR Remote Supervision",
        "duration": 6,
        "caption": "Remote supervisors monitor speed, safety, AI thresholds and sorting outcomes through a virtual control room.",
        "func": scene_arvr,
    },
    {
        "title": "Final Circular Workflow",
        "duration": 6,
        "caption": "The full automated line supports reuse, remanufacturing, recycling and quarantine decision support.",
        "func": scene_final,
    },
]


def make_contact_sheet(frames):
    thumb_w = 320
    thumb_h = 180
    cols = 3
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGBA", (cols * thumb_w, rows * (thumb_h + 42)), (7, 13, 18, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (title, frame) in enumerate(frames):
        x = (i % cols) * thumb_w
        y = (i // cols) * (thumb_h + 42)
        thumb = frame.resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.alpha_composite(thumb, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + 42), fill=(12, 20, 27, 255))
        draw.text((x + 10, y + thumb_h + 12), f"{i + 1:02d}. {title}", font=FONT["small_b"], fill=PALETTE["text"])
    sheet.save(OUT_POSTER)


def write_notes():
    total_duration = sum(shot["duration"] for shot in SHOTS)
    lines = [
        "# Battery Re-X Storyboard Animatic Notes",
        "",
        f"Generated MP4: `{OUT_MP4.name}`",
        f"Duration: approximately {total_duration} seconds",
        f"Resolution: {WIDTH}x{HEIGHT}",
        f"Frame rate: {FPS} fps",
        "",
        "## Technical Accuracy",
        "",
        "- The camera image is shown only as the source for physical battery type classification.",
        "- SOH prediction is shown as a second-stage backend ML task using cycle count, temperature, voltage, internal resistance and battery type.",
        "- The displayed SOH example is 94.49 percent and the selected model is RandomForestRegressor.",
        "- Re-X decision thresholds are: >=80 reuse, 60-79 remanufacture, 30-59 recycle, below 30 or unsafe quarantine.",
        "- Unity sensor readings are represented as mock values because the available image dataset does not contain health measurements.",
        "",
        "## Shot List",
        "",
    ]
    start = 0
    for i, shot in enumerate(SHOTS, 1):
        end = start + shot["duration"]
        lines.append(f"{i}. {shot['title']} ({start:02d}-{end:02d}s): {shot['caption']}")
        start = end
    lines.extend(
        [
            "",
            "## Suggested Voiceover",
            "",
            "Battery lifecycle decisions require more than visual inspection. In this Battery Re-X digital twin, each incoming battery is first identified by computer vision. The camera detects only the physical type: cylindrical, pouch, prismatic, or unknown. Health prediction happens in the second stage, where sensor stations collect cycle count, temperature, voltage and internal resistance. The backend ML model predicts State of Health from these health parameters, not from the image. The Re-X decision engine combines predicted SOH with safety rules to route each battery to reuse, remanufacturing, recycling or quarantine. The digital twin updates every battery record in real time, while a collaborative robot performs the final pick-and-place sorting task.",
        ]
    )
    OUT_NOTES.write_text("\n".join(lines), encoding="utf-8")


def render():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_frames = sum(int(shot["duration"] * FPS) for shot in SHOTS)
    rendered = 0
    sample_frames = []

    with imageio.get_writer(
        OUT_MP4,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=16,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    ) as writer:
        elapsed = 0.0
        for idx, shot in enumerate(SHOTS, 1):
            frames = int(shot["duration"] * FPS)
            for f in range(frames):
                local = f / max(frames - 1, 1)
                global_seconds = elapsed + local * shot["duration"]
                frame = shot["func"](local, global_seconds)
                progress = (rendered + 1) / total_frames
                draw_header_footer(frame, idx, shot["title"], shot["caption"], progress)
                if f == frames // 2:
                    sample_frames.append((shot["title"], frame.copy()))
                writer.append_data(np.asarray(frame.convert("RGB")))
                rendered += 1
            elapsed += shot["duration"]
            print(f"Rendered shot {idx:02d}: {shot['title']}")

    make_contact_sheet(sample_frames)
    write_notes()
    print(f"Saved {OUT_MP4}")
    print(f"Saved {OUT_POSTER}")
    print(f"Saved {OUT_NOTES}")


if __name__ == "__main__":
    render()
