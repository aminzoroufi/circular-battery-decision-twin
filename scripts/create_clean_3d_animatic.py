#!/usr/bin/env python3
"""Render a clean 3D/isometric storyboard animatic for Battery Re-X.

This second version is intentionally simpler than the first animatic:
- one clean factory line,
- one highlighted battery,
- one compact UI panel per stage,
- isometric/3D-style equipment and sorting bins,
- technically accurate project logic.
"""

from __future__ import annotations

import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "presentation" / "assets"
OUT_DIR = ROOT / "presentation" / "videos"

WIDTH = 1280
HEIGHT = 720
FPS = 20

OUT_MP4 = OUT_DIR / "Battery_ReX_Clean_3D_Process_Animatic.mp4"
OUT_POSTER = OUT_DIR / "Battery_ReX_Clean_3D_Process_Animatic_poster.png"
OUT_NOTES = OUT_DIR / "clean_3d_animatic_notes.md"


COL = {
    "bg": (239, 246, 250, 255),
    "bg2": (225, 236, 244, 255),
    "floor": (232, 241, 247, 255),
    "grid": (184, 203, 214, 105),
    "navy": (12, 25, 38, 255),
    "text": (20, 31, 43, 255),
    "muted": (91, 111, 126, 255),
    "panel": (255, 255, 255, 238),
    "panel_dark": (18, 33, 48, 236),
    "cyan": (10, 166, 190, 255),
    "blue": (50, 111, 220, 255),
    "green": (28, 163, 92, 255),
    "orange": (231, 142, 28, 255),
    "red": (218, 55, 55, 255),
    "gray": (117, 132, 145, 255),
    "metal": (181, 199, 211, 255),
    "metal2": (134, 157, 173, 255),
    "belt": (78, 94, 108, 255),
    "belt_top": (112, 132, 146, 255),
    "white": (255, 255, 255, 255),
    "shadow": (36, 52, 65, 80),
}


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    paths = []
    if bold:
        paths.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    paths.extend(
        [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


F = {
    "tiny": font(12),
    "small": font(15),
    "small_b": font(15, True),
    "body": font(20),
    "body_b": font(20, True),
    "mid": font(27),
    "mid_b": font(27, True),
    "large": font(40, True),
    "hero": font(54, True),
}


def clamp(v: float, lo=0.0, hi=1.0) -> float:
    return max(lo, min(hi, v))


def ease(t: float) -> float:
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t: float) -> float:
    return 1 - (1 - clamp(t)) ** 3


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix(a, b, t: float):
    return tuple(int(lerp(a[i], b[i], t)) for i in range(4))


def alpha(c, a: int):
    return (c[0], c[1], c[2], a)


def text_size(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.ImageFont):
    box = draw.textbbox((0, 0), text, font=ft)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.ImageFont, max_w: int):
    lines = []
    current = ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if draw.textlength(candidate, font=ft) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, x, y, text, ft, fill, max_w, line_h=None):
    line_h = line_h or int(getattr(ft, "size", 18) * 1.25)
    for line in wrap_text(draw, text, ft, max_w):
        draw.text((x, y), line, font=ft, fill=fill)
        y += line_h
    return y


def rounded(img: Image.Image, box, fill, outline=None, width=1, radius=16, shadow=False):
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        x1, y1, x2, y2 = box
        sd.rounded_rectangle((x1 + 8, y1 + 12, x2 + 8, y2 + 12), radius=radius, fill=(20, 35, 48, 55))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        img.alpha_composite(sh)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(img: Image.Image, x, y, text, color, text_fill=(255, 255, 255, 255)):
    d = ImageDraw.Draw(img)
    tw, th = text_size(d, text, F["small_b"])
    rounded(img, (x, y, x + tw + 26, y + th + 16), color, radius=18)
    d = ImageDraw.Draw(img)
    d.text((x + 13, y + 7), text, font=F["small_b"], fill=text_fill)
    return tw + 26


def load_photo(name: str) -> Image.Image:
    path = ASSET_DIR / name
    if path.exists():
        return Image.open(path).convert("RGBA")
    img = Image.new("RGBA", (360, 220), (180, 190, 200, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 90), name, font=F["body_b"], fill=COL["text"])
    return img


PHOTO_CYL = load_photo("sample_cylindrical.jpg")
PHOTO_POUCH = load_photo("sample_pouch.jpg")
PHOTO_PRISM = load_photo("sample_prismatic.jpg")


def paste_cover(base: Image.Image, src: Image.Image, box, radius=12, opacity=255):
    x1, y1, x2, y2 = [int(v) for v in box]
    w, h = x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        return
    im = src.convert("RGBA")
    scale = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    crop = im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width + w) // 2, (im.height + h) // 2))
    if opacity < 255:
        crop.putalpha(crop.getchannel("A").point(lambda p: int(p * opacity / 255)))
    if radius:
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
        crop.putalpha(mask)
    base.alpha_composite(crop, (x1, y1))


class Iso:
    def __init__(self, focus_x=0.0, focus_y=0.0, scale=32.0, target=(650, 405)):
        self.scale = scale
        self.cx = target[0] - (focus_x - focus_y) * scale
        self.cy = target[1] - (focus_x + focus_y) * scale * 0.52

    def p(self, x, y, z=0.0):
        sx = self.cx + (x - y) * self.scale
        sy = self.cy + (x + y) * self.scale * 0.52 - z * self.scale
        return int(round(sx)), int(round(sy))


def poly(draw: ImageDraw.ImageDraw, pts, fill, outline=None, width=1):
    draw.polygon(pts, fill=fill)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def cuboid(
    img: Image.Image,
    iso: Iso,
    x,
    y,
    z,
    lx,
    ly,
    lz,
    color,
    outline=(120, 140, 155, 180),
):
    d = ImageDraw.Draw(img)
    x0, x1 = x - lx / 2, x + lx / 2
    y0, y1 = y - ly / 2, y + ly / 2
    z0, z1 = z, z + lz
    top = [iso.p(x0, y0, z1), iso.p(x1, y0, z1), iso.p(x1, y1, z1), iso.p(x0, y1, z1)]
    front = [iso.p(x0, y1, z1), iso.p(x1, y1, z1), iso.p(x1, y1, z0), iso.p(x0, y1, z0)]
    side = [iso.p(x1, y0, z1), iso.p(x1, y1, z1), iso.p(x1, y1, z0), iso.p(x1, y0, z0)]
    poly(d, side, mix(color, (0, 0, 0, color[3]), 0.20), outline)
    poly(d, front, mix(color, (0, 0, 0, color[3]), 0.12), outline)
    poly(d, top, color, outline)


def top_rect(img: Image.Image, iso: Iso, x, y, z, lx, ly, fill, outline=None, width=1):
    d = ImageDraw.Draw(img)
    x0, x1 = x - lx / 2, x + lx / 2
    y0, y1 = y - ly / 2, y + ly / 2
    pts = [iso.p(x0, y0, z), iso.p(x1, y0, z), iso.p(x1, y1, z), iso.p(x0, y1, z)]
    poly(d, pts, fill, outline, width)


def draw_base(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = mix(COL["bg"], COL["bg2"], t)
        d.line((0, y, WIDTH, y), fill=c)
    d.rectangle((0, 610, WIDTH, HEIGHT), fill=(214, 227, 237, 255))
    # Soft top light.
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((120, -240, 1160, 360), fill=(255, 255, 255, 95))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(glow)


def draw_floor(img: Image.Image, iso: Iso):
    d = ImageDraw.Draw(img)
    corners = [iso.p(-11, -5, -0.04), iso.p(11, -5, -0.04), iso.p(11, 5, -0.04), iso.p(-11, 5, -0.04)]
    poly(d, corners, COL["floor"], (200, 218, 230, 180), 1)
    for x in range(-11, 12):
        d.line([iso.p(x, -5, 0), iso.p(x, 5, 0)], fill=COL["grid"], width=1)
    for y in range(-5, 6):
        d.line([iso.p(-11, y, 0), iso.p(11, y, 0)], fill=COL["grid"], width=1)


def stage_label(img: Image.Image, iso: Iso, x, y, text, color):
    d = ImageDraw.Draw(img)
    sx, sy = iso.p(x, y, 0.08)
    tw, th = text_size(d, text, F["tiny"])
    rounded(img, (sx - tw // 2 - 9, sy - 12, sx + tw // 2 + 9, sy + 12), alpha(color, 220), radius=10)
    d = ImageDraw.Draw(img)
    d.text((sx - tw // 2, sy - th // 2 - 1), text, font=F["tiny"], fill=COL["white"])


def draw_conveyor(img: Image.Image, iso: Iso, t: float):
    cuboid(img, iso, 0, 0, 0.02, 18.6, 1.5, 0.35, COL["metal"])
    cuboid(img, iso, 0, 0, 0.39, 18.2, 1.05, 0.06, COL["belt_top"], outline=(70, 90, 104, 200))
    # Moving slats.
    shift = (t * 2.0) % 0.85
    sx = -8.8 + shift
    while sx < 9:
        top_rect(img, iso, sx, 0, 0.48, 0.12, 1.04, (210, 224, 233, 180), None)
        sx += 0.85
    # Connected output branch conveyors.
    for yy, color in [(-2.7, COL["green"]), (-0.95, COL["orange"]), (0.95, COL["blue"]), (2.7, COL["red"])]:
        cuboid(img, iso, 8.0, yy / 2, 0.02, 2.4, 0.55, 0.25, COL["metal"])
        cuboid(img, iso, 8.7, yy, 0.02, 3.3, 0.65, 0.25, COL["metal"])
        top_rect(img, iso, 8.7, yy, 0.32, 3.1, 0.43, alpha(color, 180), None)


def draw_camera_station(img: Image.Image, iso: Iso, active=False):
    color = COL["cyan"] if active else COL["gray"]
    cuboid(img, iso, -5.5, -0.82, 0.42, 0.20, 0.18, 2.0, COL["metal2"])
    cuboid(img, iso, -5.5, 0.82, 0.42, 0.20, 0.18, 2.0, COL["metal2"])
    cuboid(img, iso, -5.5, 0, 2.30, 1.35, 0.34, 0.28, COL["metal"])
    cuboid(img, iso, -5.5, 0, 1.95, 0.56, 0.42, 0.42, color)
    sx, sy = iso.p(-5.5, 0, 1.72)
    d = ImageDraw.Draw(img)
    d.ellipse((sx - 20, sy - 20, sx + 20, sy + 20), fill=(23, 42, 58, 255), outline=COL["cyan"], width=3)
    if active:
        beam = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam)
        bd.polygon([iso.p(-5.5, -0.22, 1.70), iso.p(-5.5, 0.22, 1.70), iso.p(-5.1, 0.56, 0.48), iso.p(-5.9, 0.56, 0.48)], fill=(10, 166, 190, 70))
        img.alpha_composite(beam)


def draw_sensor_station(img: Image.Image, iso: Iso, active=False):
    accents = [COL["orange"], COL["blue"], COL["cyan"]]
    xs = [-2.0, -0.8, 0.4]
    for i, x in enumerate(xs):
        col = accents[i] if active else COL["gray"]
        cuboid(img, iso, x, -0.78, 0.42, 0.18, 0.18, 1.4, COL["metal2"])
        cuboid(img, iso, x, 0.78, 0.42, 0.18, 0.18, 1.4, COL["metal2"])
        cuboid(img, iso, x, 0, 1.72, 0.92, 0.28, 0.24, col)
        top_rect(img, iso, x, 0, 1.98, 0.55, 0.20, alpha(COL["white"], 200), None)


def draw_ml_station(img: Image.Image, iso: Iso, active=False):
    color = COL["blue"] if active else COL["gray"]
    cuboid(img, iso, 2.75, 1.65, 0.04, 1.25, 0.95, 1.35, color)
    cuboid(img, iso, 2.75, 1.65, 1.48, 1.0, 0.12, 0.14, COL["white"])
    for i in range(4):
        cuboid(img, iso, 2.25 + i * 0.34, 1.12, 1.62, 0.13, 0.13, 0.08, COL["cyan"] if active else COL["metal"])
    # Floating backend panel.
    sx, sy = iso.p(2.8, 0.15, 2.25)
    d = ImageDraw.Draw(img)
    rounded(img, (sx - 118, sy - 74, sx + 118, sy + 32), alpha(COL["panel_dark"], 224), outline=alpha(color, 160), radius=14, shadow=True)
    d = ImageDraw.Draw(img)
    d.text((sx - 98, sy - 58), "SOH ML", font=F["body_b"], fill=COL["white"])
    d.text((sx - 98, sy - 28), "RandomForest", font=F["small_b"], fill=COL["cyan"])
    d.text((sx - 98, sy - 4), "94.49% SOH", font=F["small_b"], fill=COL["green"])


def draw_robot(img: Image.Image, iso: Iso, gripper_world=(6.8, 0.0, 0.95), active=False):
    d = ImageDraw.Draw(img)
    base = iso.p(5.95, 1.25, 0.42)
    elbow = iso.p(6.25, 0.72, 2.10)
    wrist = iso.p(gripper_world[0], gripper_world[1], gripper_world[2] + 0.55)
    grip = iso.p(gripper_world[0], gripper_world[1], gripper_world[2])
    cuboid(img, iso, 5.95, 1.25, 0.04, 0.9, 0.9, 0.42, COL["metal2"])
    d.line((base, elbow), fill=(245, 250, 253, 255), width=18)
    d.line((elbow, wrist), fill=(236, 245, 251, 255), width=16)
    d.line((wrist, grip), fill=(225, 237, 245, 255), width=12)
    for pt, r in [(base, 18), (elbow, 19), (wrist, 15), (grip, 12)]:
        d.ellipse((pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r), fill=COL["white"], outline=(112, 134, 151, 255), width=2)
    gap = 18 if active else 26
    d.line((grip[0] - gap, grip[1] + 6, grip[0] - 5, grip[1] + 18), fill=COL["navy"], width=5)
    d.line((grip[0] + gap, grip[1] + 6, grip[0] + 5, grip[1] + 18), fill=COL["navy"], width=5)


def draw_bin(img: Image.Image, iso: Iso, x, y, label, color, active=False):
    c = color if active else mix(color, COL["gray"], 0.55)
    cuboid(img, iso, x, y, 0.04, 1.25, 1.0, 0.55, alpha(c, 245))
    top_rect(img, iso, x, y, 0.74, 1.05, 0.78, (24, 37, 49, 255), alpha(c, 220), 2)
    sx, sy = iso.p(x, y - 0.68, 0.95)
    d = ImageDraw.Draw(img)
    tw, _ = text_size(d, label.upper(), F["tiny"])
    d.text((sx - tw // 2, sy), label.upper(), font=F["tiny"], fill=c)


def draw_battery(img: Image.Image, iso: Iso, x, y, z=0.58, kind="unknown", active=False):
    if active:
        sx, sy = iso.p(x, y, z + 0.25)
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((sx - 58, sy - 36, sx + 58, sy + 36), fill=(10, 166, 190, 70))
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        img.alpha_composite(glow)
    if kind == "cylindrical":
        cuboid(img, iso, x, y, z, 0.85, 0.45, 0.28, (225, 232, 237, 255), outline=(88, 104, 116, 210))
        top_rect(img, iso, x - 0.35, y, z + 0.30, 0.12, 0.42, COL["red"])
        top_rect(img, iso, x + 0.35, y, z + 0.30, 0.12, 0.42, COL["navy"])
    elif kind == "pouch":
        cuboid(img, iso, x, y, z, 0.90, 0.68, 0.15, (210, 218, 226, 255), outline=(88, 104, 116, 210))
        top_rect(img, iso, x - 0.24, y - 0.36, z + 0.18, 0.16, 0.12, COL["orange"])
        top_rect(img, iso, x + 0.24, y - 0.36, z + 0.18, 0.16, 0.12, COL["navy"])
    elif kind == "prismatic":
        cuboid(img, iso, x, y, z, 0.70, 0.58, 0.55, (199, 211, 220, 255), outline=(88, 104, 116, 210))
        top_rect(img, iso, x - 0.20, y - 0.26, z + 0.58, 0.12, 0.10, COL["red"])
        top_rect(img, iso, x + 0.20, y - 0.26, z + 0.58, 0.12, 0.10, COL["navy"])
    else:
        cuboid(img, iso, x, y, z, 0.78, 0.56, 0.36, (160, 170, 178, 255), outline=(88, 104, 116, 210))
        sx, sy = iso.p(x, y, z + 0.55)
        d = ImageDraw.Draw(img)
        d.text((sx - 7, sy - 13), "?", font=F["body_b"], fill=COL["white"])


def draw_output_bins(img: Image.Image, iso: Iso, active=""):
    data = [
        ("Reuse", 8.8, -2.7, COL["green"], "reuse"),
        ("Reman", 8.8, -0.95, COL["orange"], "reman"),
        ("Recycle", 8.8, 0.95, COL["blue"], "recycle"),
        ("Quarantine", 8.8, 2.7, COL["red"], "quarantine"),
    ]
    for label, x, y, color, key in data:
        draw_bin(img, iso, x, y, label, color, active=active == key)


def draw_full_factory(img: Image.Image, iso: Iso, t: float, stage="", battery=(-8, 0), kind="unknown", active_bin=""):
    draw_floor(img, iso)
    draw_conveyor(img, iso, t)
    draw_camera_station(img, iso, active=stage == "camera")
    draw_sensor_station(img, iso, active=stage == "sensors")
    draw_ml_station(img, iso, active=stage == "ml")
    draw_robot(img, iso, active=stage == "robot")
    draw_output_bins(img, iso, active_bin)
    draw_battery(img, iso, battery[0], battery[1], kind=kind, active=True)
    stage_label(img, iso, -8.4, -1.15, "1 intake", COL["gray"])
    stage_label(img, iso, -5.5, -1.35, "2 camera", COL["cyan"])
    stage_label(img, iso, -0.8, -1.35, "3 sensors", COL["orange"])
    stage_label(img, iso, 2.7, 0.7, "4 SOH ML", COL["blue"])
    stage_label(img, iso, 6.6, -1.15, "5 Re-X sort", COL["green"])


def stage_card(img: Image.Image, title, subtitle, rows, accent=COL["cyan"], photo=None):
    d = ImageDraw.Draw(img)
    rounded(img, (790, 86, 1218, 548), COL["panel"], outline=alpha(accent, 120), radius=24, shadow=True)
    d = ImageDraw.Draw(img)
    d.text((824, 120), title, font=F["mid_b"], fill=COL["text"])
    draw_wrapped(d, 824, 158, subtitle, F["body"], COL["muted"], 342, line_h=27)
    y = 238
    if photo is not None:
        paste_cover(img, photo, (824, y, 984, y + 104), radius=14)
        y += 126
    for label, value, color in rows:
        d.text((824, y), label, font=F["small_b"], fill=COL["muted"])
        d.text((1020, y), value, font=F["small_b"], fill=color)
        y += 33
    pill(img, 824, 494, "Project rule: SOH is not predicted from image", alpha(COL["navy"], 230))


def minimal_header(img: Image.Image, shot_no: int, title: str):
    d = ImageDraw.Draw(img)
    rounded(img, (40, 28, 520, 72), alpha(COL["white"], 225), outline=(207, 224, 235, 255), radius=18, shadow=True)
    d = ImageDraw.Draw(img)
    d.text((62, 42), "Battery Re-X Clean 3D Storyboard", font=F["small_b"], fill=COL["text"])
    rounded(img, (1076, 28, 1238, 72), alpha(COL["navy"], 230), radius=18, shadow=True)
    d.text((1098, 42), f"Shot {shot_no:02d} / 07", font=F["small_b"], fill=COL["white"])
    d.text((62, 92), title, font=F["large"], fill=COL["text"])


def footer(img: Image.Image, progress: float, caption: str):
    d = ImageDraw.Draw(img)
    rounded(img, (190, 634, 1090, 682), alpha(COL["navy"], 225), radius=18, shadow=True)
    draw_wrapped(d, 224, 647, caption, F["small_b"], COL["white"], 830, line_h=18)
    d.rounded_rectangle((42, 700, 1238, 707), radius=4, fill=(194, 211, 224, 255))
    d.rounded_rectangle((42, 700, int(42 + 1196 * progress), 707), radius=4, fill=COL["cyan"])


def new_frame():
    img = Image.new("RGBA", (WIDTH, HEIGHT), COL["bg"])
    draw_base(img)
    return img


def scene_overview(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=0.0, focus_y=0.0, scale=29.5, target=(618, 420))
    bx = lerp(-8.3, -6.2, ease(t))
    draw_full_factory(img, iso, seconds, stage="", battery=(bx, 0), kind="unknown")
    d = ImageDraw.Draw(img)
    minimal_header(img, 1, "Clean 3D Process Overview")
    draw_wrapped(
        d,
        64,
        144,
        "A single battery moves through five tidy stages: camera shape detection, sensor health data, ML SOH prediction, Re-X decision and robot sorting.",
        F["body"],
        COL["muted"],
        520,
        27,
    )
    pill(img, 64, 244, "one highlighted battery", COL["cyan"])
    pill(img, 260, 244, "no SOH from image", COL["navy"])
    return img


def scene_camera(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=-5.4, focus_y=0.0, scale=45, target=(464, 420))
    draw_full_factory(img, iso, seconds, stage="camera", battery=(-5.5, 0), kind="cylindrical")
    minimal_header(img, 2, "Stage 1: Camera Shape Detection")
    # Scan lines on battery.
    d = ImageDraw.Draw(img)
    sy = int(348 + 70 * t)
    d.line((280, sy, 642, sy - 38), fill=COL["cyan"], width=3)
    stage_card(
        img,
        "AI Vision",
        "The camera sends an image to the backend. This stage identifies only the visible battery shape.",
        [
            ("Battery ID", "BAT_001", COL["text"]),
            ("Shape", "CYLINDRICAL", COL["green"]),
            ("Vision trust", "92%", COL["cyan"]),
            ("SOH status", "not predicted", COL["orange"]),
        ],
        accent=COL["cyan"],
        photo=PHOTO_CYL,
    )
    return img


def scene_sensors(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=-0.6, focus_y=0.0, scale=42, target=(500, 420))
    bx = lerp(-2.2, 0.4, ease(t))
    draw_full_factory(img, iso, seconds, stage="sensors", battery=(bx, 0), kind="cylindrical")
    minimal_header(img, 3, "Stage 2: Health Sensor Data")
    rows = [
        ("Cycle count", "430", COL["text"]),
        ("Temperature", "31.2 C", COL["orange"]),
        ("Voltage", "3.72 V", COL["blue"]),
        ("Resistance", "0.052 ohm", COL["cyan"]),
        ("Safety", "passed", COL["green"]),
    ]
    visible = int(lerp(1, len(rows), ease_out(t)))
    stage_card(
        img,
        "Sensor Line",
        "Mock health data is generated in Unity because the image dataset contains shape labels, not real BMS health values.",
        rows[:visible],
        accent=COL["orange"],
    )
    return img


def scene_ml(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=2.4, focus_y=0.55, scale=42, target=(472, 420))
    draw_full_factory(img, iso, seconds, stage="ml", battery=(2.1, 0), kind="cylindrical")
    minimal_header(img, 4, "Stage 3: ML-Based SOH Prediction")
    d = ImageDraw.Draw(img)
    # Clean gauge in the panel area.
    rounded(img, (790, 86, 1218, 548), COL["panel"], outline=alpha(COL["blue"], 140), radius=24, shadow=True)
    d = ImageDraw.Draw(img)
    d.text((824, 120), "SOH Prediction", font=F["mid_b"], fill=COL["text"])
    draw_wrapped(
        d,
        824,
        158,
        "The backend predicts battery health from cycle count, temperature, voltage, resistance and type.",
        F["body"],
        COL["muted"],
        340,
        27,
    )
    rows = [
        ("Model used", "RandomForestRegressor", COL["blue"]),
        ("SOH target", "capacity based", COL["text"]),
        ("Input source", "sensor data", COL["green"]),
    ]
    y = 246
    for label, value, color in rows:
        d.text((824, y), label, font=F["small_b"], fill=COL["muted"])
        d.text((1015, y), value, font=F["small_b"], fill=color)
        y += 32
    center = (1008, 402)
    radius = 92
    d.arc((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), 180, 360, fill=(207, 222, 232, 255), width=18)
    soh = 94.49
    ang = 180 + 180 * (soh / 100.0) * ease_out(t)
    d.arc((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), 180, ang, fill=COL["green"], width=18)
    a = math.radians(ang)
    d.line((center[0], center[1], center[0] + math.cos(a) * 70, center[1] + math.sin(a) * 70), fill=COL["navy"], width=4)
    d.ellipse((center[0] - 7, center[1] - 7, center[0] + 7, center[1] + 7), fill=COL["navy"])
    d.text((936, 420), f"{soh:.2f}%", font=F["large"], fill=COL["green"])
    d.text((924, 470), "Predicted SOH", font=F["small_b"], fill=COL["muted"])
    return img


def scene_decision(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=5.0, focus_y=0.0, scale=39, target=(464, 420))
    draw_full_factory(img, iso, seconds, stage="", battery=(5.0, 0), kind="cylindrical", active_bin="reuse")
    minimal_header(img, 5, "Stage 4: Re-X Decision")
    stage_card(
        img,
        "Decision Engine",
        "SOH thresholds and safety rules choose the final lifecycle route.",
        [
            ("SOH >= 80", "Reuse", COL["green"]),
            ("60 to 79", "Remanufacture", COL["orange"]),
            ("30 to 59", "Recycle", COL["blue"]),
            ("Unsafe / <30", "Quarantine", COL["red"]),
            ("BAT_001 route", "reuse_bin", COL["green"]),
        ],
        accent=COL["green"],
    )
    d = ImageDraw.Draw(img)
    p1 = iso.p(5.0, 0.0, 0.92)
    p2 = iso.p(8.15, -2.7, 0.52)
    mx = int(lerp(p1[0], p2[0], ease(t)))
    my = int(lerp(p1[1], p2[1], ease(t)))
    d.line((p1[0], p1[1], mx, my), fill=COL["green"], width=7)
    d.ellipse((mx - 8, my - 8, mx + 8, my + 8), fill=COL["green"])
    return img


def scene_robot(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=6.7, focus_y=-0.9, scale=45, target=(520, 420))
    if t < 0.25:
        p = ease(t / 0.25)
        grip = (lerp(6.4, 5.2, p), lerp(0.4, 0.0, p), lerp(1.45, 1.0, p))
        bat = (5.2, 0.0)
        carried = False
    elif t < 0.43:
        p = ease((t - 0.25) / 0.18)
        grip = (5.2, 0.0, lerp(1.0, 1.75, p))
        bat = (5.2, 0.0)
        carried = True
    elif t < 0.78:
        p = ease((t - 0.43) / 0.35)
        grip = (lerp(5.2, 8.75, p), lerp(0.0, -2.7, p), lerp(1.75, 1.15, p))
        bat = (grip[0], grip[1])
        carried = True
    else:
        p = ease((t - 0.78) / 0.22)
        grip = (lerp(8.75, 6.5, p), lerp(-2.7, 0.5, p), lerp(1.15, 1.55, p))
        bat = (8.75, -2.7)
        carried = False

    draw_floor(img, iso)
    draw_conveyor(img, iso, seconds)
    draw_camera_station(img, iso)
    draw_sensor_station(img, iso)
    draw_ml_station(img, iso)
    draw_output_bins(img, iso, "reuse")
    draw_robot(img, iso, gripper_world=grip, active=carried)
    draw_battery(img, iso, bat[0], bat[1], kind="cylindrical", active=True)
    minimal_header(img, 6, "Stage 5: Robot Sorting")
    stage_card(
        img,
        "Pick And Place",
        "The robot performs one clear task: pick the inspected battery and release it into the correct Re-X bin.",
        [
            ("Target bin", "reuse_bin", COL["green"]),
            ("Motion", "pick, lift, release", COL["text"]),
            ("Queue rule", "next battery waits", COL["cyan"]),
            ("Digital passport", "updated", COL["green"]),
        ],
        accent=COL["green"],
    )
    return img


def scene_final(t: float, seconds: float) -> Image.Image:
    img = new_frame()
    iso = Iso(focus_x=0.0, focus_y=0.0, scale=29.5, target=(618, 420))
    draw_full_factory(img, iso, seconds, stage="", battery=(lerp(-8.0, 7.0, t), 0), kind="cylindrical", active_bin="reuse")
    minimal_header(img, 7, "Final Digital Twin View")
    d = ImageDraw.Draw(img)
    rounded(img, (760, 112, 1205, 518), COL["panel"], outline=alpha(COL["cyan"], 130), radius=24, shadow=True)
    d = ImageDraw.Draw(img)
    d.text((794, 146), "Live Battery Record", font=F["mid_b"], fill=COL["text"])
    paste_cover(img, PHOTO_CYL, (794, 196, 944, 292), radius=14)
    rows = [
        ("Battery ID", "BAT_001", COL["text"]),
        ("Shape", "Cylindrical", COL["cyan"]),
        ("Sensor health", "valid", COL["green"]),
        ("Predicted SOH", "94.49%", COL["green"]),
        ("Re-X decision", "Reuse", COL["green"]),
        ("Target bin", "reuse_bin", COL["text"]),
    ]
    y = 310
    for label, value, color in rows:
        d.text((794, y), label, font=F["small_b"], fill=COL["muted"])
        d.text((984, y), value, font=F["small_b"], fill=color)
        y += 30
    pill(img, 64, 244, "Computer vision", COL["cyan"])
    pill(img, 224, 244, "SOH prediction", COL["blue"])
    pill(img, 386, 244, "Re-X robot sorting", COL["green"])
    return img


SHOTS = [
    ("Clean 3D Process Overview", 7, "A tidy isometric view introduces the full Battery Re-X digital twin pipeline.", scene_overview),
    ("Camera Shape Detection", 7, "The camera captures an image and classifies only the visible battery shape.", scene_camera),
    ("Health Sensor Data", 8, "The battery moves through sensor stations that provide the data needed for SOH prediction.", scene_sensors),
    ("ML SOH Prediction", 8, "The backend model predicts State of Health from health parameters, not from the image.", scene_ml),
    ("Re-X Decision", 7, "SOH thresholds and safety rules determine reuse, remanufacture, recycle or quarantine.", scene_decision),
    ("Robot Sorting", 9, "The robot picks the battery and releases it into the correct colored bin.", scene_robot),
    ("Final Digital Twin View", 6, "The clean 3D overview ends with the live battery record and synchronized decision result.", scene_final),
]


def render():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_frames = sum(int(duration * FPS) for _, duration, _, _ in SHOTS)
    rendered = 0
    samples = []
    with imageio.get_writer(
        OUT_MP4,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=16,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    ) as writer:
        seconds = 0.0
        for idx, (title, duration, caption, func) in enumerate(SHOTS, 1):
            frames = int(duration * FPS)
            for f in range(frames):
                local = f / max(frames - 1, 1)
                img = func(local, seconds + local * duration)
                footer(img, (rendered + 1) / total_frames, caption)
                if f == frames // 2:
                    samples.append((title, img.copy()))
                writer.append_data(np.asarray(img.convert("RGB")))
                rendered += 1
            seconds += duration
            print(f"Rendered clean 3D shot {idx:02d}: {title}")
    make_poster(samples)
    write_notes()
    print(f"Saved {OUT_MP4}")
    print(f"Saved {OUT_POSTER}")
    print(f"Saved {OUT_NOTES}")


def make_poster(samples):
    tw, th = 426, 240
    rows = 3
    cols = 3
    poster = Image.new("RGBA", (cols * tw, rows * (th + 46)), COL["bg"])
    d = ImageDraw.Draw(poster)
    for i, (title, img) in enumerate(samples):
        x = (i % cols) * tw
        y = (i // cols) * (th + 46)
        poster.alpha_composite(img.resize((tw, th), Image.LANCZOS), (x, y))
        d.rectangle((x, y + th, x + tw, y + th + 46), fill=COL["navy"])
        d.text((x + 16, y + th + 13), f"{i + 1:02d}. {title}", font=F["body_b"], fill=COL["white"])
    poster.save(OUT_POSTER)


def write_notes():
    duration = sum(s[1] for s in SHOTS)
    lines = [
        "# Clean 3D Battery Re-X Animatic Notes",
        "",
        f"Generated MP4: `{OUT_MP4.name}`",
        f"Duration: approximately {duration} seconds",
        f"Resolution: {WIDTH}x{HEIGHT}",
        f"Frame rate: {FPS} fps",
        "",
        "## Design Direction",
        "",
        "- Cleaner and tidier than the first storyboard.",
        "- Uses one isometric 3D factory line instead of many dense panels.",
        "- Shows one highlighted battery at a time.",
        "- Uses one main UI card per stage for readability.",
        "- Keeps the project logic technically correct.",
        "",
        "## Technical Rules Preserved",
        "",
        "- Image data is used only for physical shape classification.",
        "- SOH prediction uses health parameters: cycle count, temperature, voltage, resistance and battery type.",
        "- The model shown is RandomForestRegressor.",
        "- The decision thresholds are reuse >=80, remanufacture 60-79, recycle 30-59 and quarantine below 30 or unsafe.",
        "",
        "## Shot List",
        "",
    ]
    start = 0
    for i, (title, duration, caption, _) in enumerate(SHOTS, 1):
        end = start + duration
        lines.append(f"{i}. {title} ({start:02d}-{end:02d}s): {caption}")
        start = end
    OUT_NOTES.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    render()
