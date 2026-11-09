#!/usr/bin/env python3
"""Motion-graphic renderer for "quick quality tips" (LinkedIn, 1080x1080).

Each video = intro -> tip 1 -> tip 2 -> outro, with the AB logo
fixed as a watermark on every frame.

Usage:
    python3 render.py                # render every video in tips.json
    python3 render.py --id 01        # render one video
    python3 render.py --preview 01   # write a few still frames only
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
FONT = ROOT / "assets/fonts/Cairo.ttf"
LOGO = ROOT / "assets/logo.png"
OUT = ROOT / "output"

W = H = 1080
FPS = 30
BG = (41, 39, 40)          # same as logo background
GOLD = (229, 174, 61)
WHITE = (255, 255, 255)
GREY = (170, 166, 160)

# timeline (seconds)
INTRO = 2.2
TIP = 6.0
OUTRO = 2.8
TOTAL = INTRO + 2 * TIP + OUTRO

_font_cache = {}


def font(size, weight="Bold"):
    key = (size, weight)
    if key not in _font_cache:
        f = ImageFont.truetype(str(FONT), size, layout_engine=ImageFont.Layout.RAQM)
        f.set_variation_by_name(weight)
        _font_cache[key] = f
    return _font_cache[key]


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def prog(t, start, dur):
    return clamp((t - start) / dur)


# ---------- logo ----------
def load_logo():
    """Logo with its dark background keyed out to transparency."""
    im = Image.open(LOGO).convert("RGB")
    px = im.load()
    out = Image.new("RGBA", im.size)
    opx = out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]
            d = max(abs(r - BG[0]), abs(g - BG[1]), abs(b - BG[2]))
            a = int(clamp(d / 60) * 255)
            opx[x, y] = (r, g, b, a)
    return out.crop(out.getbbox())


LOGO_IMG = load_logo()


def logo_sized(width, alpha=1.0):
    h = int(LOGO_IMG.height * width / LOGO_IMG.width)
    lg = LOGO_IMG.resize((width, h), Image.LANCZOS)
    if alpha < 1:
        a = lg.getchannel("A").point(lambda v: int(v * alpha))
        lg.putalpha(a)
    return lg


WATERMARK = logo_sized(150, 0.9)


# ---------- text helpers (RTL) ----------
def text_rtl(draw, right_x, y, txt, fnt, fill, alpha=1.0, anchor="ra"):
    col = fill + (int(255 * alpha),)
    draw.text((right_x, y), txt, font=fnt, fill=col, anchor=anchor,
              direction="rtl", language="ar")


def text_center(draw, cx, y, txt, fnt, fill, alpha=1.0):
    col = fill + (int(255 * alpha),)
    draw.text((cx, y), txt, font=fnt, fill=col, anchor="ma",
              direction="rtl", language="ar")


def wrap(txt, fnt, max_w, draw):
    lines = []
    for para in txt.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            test = (cur + " " + w).strip()
            if draw.textlength(test, font=fnt, direction="rtl", language="ar") <= max_w:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


# ---------- background ----------
def background(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    # slow-moving gold glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx = W * 0.75 + math.sin(t * 0.6) * 60
    cy = H * 0.25 + math.cos(t * 0.5) * 40
    gd.ellipse((cx - 330, cy - 330, cx + 330, cy + 330), fill=GOLD + (28,))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img.alpha_composite(glow)
    # subtle diagonal lines (echo the logo's slanted A)
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    off = (t * 25) % 80
    for i in range(-14, 20):
        x = i * 80 + off
        ld.line((x, H, x + 380, H - 1100), fill=(255, 255, 255, 9), width=2)
    img.alpha_composite(lines)
    return img


def frame_border(d, t):
    p = ease_out(prog(t, 0, 1.0))
    m = 48
    L = int((W - 2 * m) * p)
    d.line((W - m - L, m, W - m, m), fill=GOLD + (200,), width=3)
    d.line((m, H - m, m + L, H - m), fill=GOLD + (200,), width=3)


def progress_bar(d, t):
    p = clamp(t / TOTAL)
    d.rectangle((0, H - 8, int(W * p), H), fill=GOLD + (255,))


# ---------- scenes ----------
def scene_intro(img, t, data):
    d = ImageDraw.Draw(img)
    p_in = ease_out(prog(t, 0.2, 0.7))
    p_out = ease_in(prog(t, INTRO - 0.45, 0.45))
    a = p_in * (1 - p_out)
    # gold tag
    tag_f = font(34, "SemiBold")
    tag = "LinkedIn  |  Quality Tips"
    tw = d.textlength(tag, font=tag_f)
    y0 = 400 - 40 * (1 - p_in)
    bx = (W - tw) / 2 - 24
    d.rounded_rectangle((bx, y0, bx + tw + 48, y0 + 58), 29,
                        outline=GOLD + (int(255 * a),), width=2)
    d.text((W / 2, y0 + 8), tag, font=tag_f, fill=GOLD + (int(255 * a),), anchor="ma")
    # title
    text_center(d, W / 2, 490 + 30 * (1 - p_in), data["series_title"],
                font(88, "Black"), WHITE, a)
    # underline grows
    lw = 360 * ease_out(prog(t, 0.6, 0.8)) * (1 - p_out)
    d.rectangle((W / 2 - lw / 2, 640, W / 2 + lw / 2, 646), fill=GOLD + (255,))
    text_center(d, W / 2, 670, "معلومتان في أقل من 20 ثانية", font(38, "Regular"), GREY, a)


def scene_tip(img, t, tip, n):
    """t is local time inside the tip scene (0..TIP)."""
    d = ImageDraw.Draw(img)
    right = W - 110
    out = ease_in(prog(t, TIP - 0.5, 0.5))
    slide_out = -80 * out

    # big number
    pn = ease_out(prog(t, 0.0, 0.6))
    num = f"0{n}"
    nf = font(230, "Black")
    d.text((right + 20 * (1 - pn), 40), num, font=nf,
           fill=GOLD + (int(55 * pn * (1 - out)),), anchor="ra")

    # gold bar on the right edge
    bh = 520 * ease_out(prog(t, 0.15, 0.7)) * (1 - out)
    d.rectangle((right + 22, 300, right + 30, 300 + bh), fill=GOLD + (255,))

    # title
    pt = ease_out(prog(t, 0.3, 0.6))
    text_rtl(d, right - 60 * (1 - pt) + slide_out, 300, tip["title"],
             font(76, "ExtraBold"), WHITE, pt * (1 - out))

    # highlight pill
    ph = ease_out(prog(t, 0.7, 0.6))
    hf = font(52, "Bold")
    hw = d.textlength(tip["highlight"], font=hf, direction="rtl", language="ar")
    x1 = right + slide_out
    x0 = x1 - (hw + 60) * ph
    if ph > 0.01:
        d.rounded_rectangle((x0, 425, x1, 515), 18,
                            fill=GOLD + (int(255 * (1 - out)),))
        if ph > 0.6:
            text_rtl(d, x1 - 30, 433, tip["highlight"], hf, BG,
                     clamp((ph - 0.6) / 0.4) * (1 - out))

    # body lines, staggered
    bf = font(44, "Medium")
    lines = wrap(tip["body"], bf, W - 260, d)
    for i, line in enumerate(lines):
        pl = ease_out(prog(t, 1.3 + i * 0.25, 0.6))
        text_rtl(d, right - 40 * (1 - pl) + slide_out, 570 + i * 72, line,
                 bf, (225, 222, 218), pl * (1 - out))


def scene_outro(img, t, data):
    d = ImageDraw.Draw(img)
    p = ease_out(prog(t, 0.0, 0.8))
    size = int(300 + 40 * p)
    lg = logo_sized(size, p)
    img.alpha_composite(lg, ((W - lg.width) // 2, int(300 - 30 * (1 - p))))
    pc = ease_out(prog(t, 0.6, 0.7))
    text_center(d, W / 2, 300 + lg.height + 50, data["cta"], font(46, "Bold"), GOLD, pc)


def render_frame(t, data, video):
    base = background(t)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # scenes draw on a transparent layer
    d = ImageDraw.Draw(img)
    frame_border(d, t)
    if t < INTRO:
        scene_intro(img, t, data)
    elif t < INTRO + TIP:
        scene_tip(img, t - INTRO, video["tips"][0], 1)
    elif t < INTRO + 2 * TIP:
        scene_tip(img, t - INTRO - TIP, video["tips"][1], 2)
    else:
        scene_outro(img, t - INTRO - 2 * TIP, data)
    # fixed logo watermark (hidden only during the outro where the logo is centred)
    wm_a = 1 - ease_out(prog(t, INTRO + 2 * TIP, 0.4))
    if wm_a > 0.01:
        wm = WATERMARK if wm_a >= 0.99 else logo_sized(150, 0.9 * wm_a)
        img.alpha_composite(wm, (70, 70))
    progress_bar(d, t)
    base.alpha_composite(img)
    return base.convert("RGB")


def render_video(data, video):
    OUT.mkdir(exist_ok=True)
    path = OUT / f"quality_tip_{video['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        proc.stdin.write(render_frame(i / FPS, data, video).tobytes())
    proc.stdin.close()
    proc.wait()
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--preview")
    a = ap.parse_args()
    data = json.loads((ROOT / "tips.json").read_text(encoding="utf-8"))
    vids = data["videos"]
    if a.preview:
        v = next(v for v in vids if v["id"] == a.preview)
        OUT.mkdir(exist_ok=True)
        for t in (1.5, INTRO + 3.5, INTRO + TIP + 3.5, TOTAL - 0.5):
            render_frame(t, data, v).save(OUT / f"preview_{v['id']}_{t:.1f}.png")
        return
    for v in vids:
        if a.id and v["id"] != a.id:
            continue
        render_video(data, v)


if __name__ == "__main__":
    main()
