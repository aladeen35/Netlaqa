#!/usr/bin/env python3
"""Explainer motion graphic: allergen labelling differs between markets.

Vertical 1080x1920, in the AB house style (dark + gold, particle builds, QC
cursor, fixed logo, word-by-word subtitles, cloned voice-over).

    COQUI_TOS_AGREED=1 /home/user/xtts-venv/bin/python voice_scenes.py   # narration
    python3 render.py --preview      # still frames
    python3 render.py                # video -> out/allergen_labelling.mp4 (+ final with audio)
"""
import argparse
import json
import math
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
MOTION = HERE.parents[1]
sys.path.insert(0, str(MOTION / "vertical"))
sys.path.insert(0, str(MOTION))
import render as R            # noqa: E402
import render_vertical as V   # noqa: E402

W, H, FPS = V.W, V.H, V.FPS
BG, GOLD, GOLD_HI, WHITE, BODY, GREY = V.BG, V.GOLD, V.GOLD_HI, V.WHITE, V.BODY, V.GREY
clamp, ease_out, ease_in, prog, ease_io = V.clamp, V.ease_out, V.ease_in, V.prog, V.ease_io
RIGHT, LEFT, TEXT_W = V.RIGHT, V.LEFT, V.TEXT_W
F = R.font
R.set_lang("ar")

S = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
VOICE = HERE / "voice"
MUSIC = MOTION / "assets/audio/background.m4a"
INTRO = 3.4
LEAD = 0.45
OUT_T = 0.45                 # scene exit time
SUB_Y = 1400                 # subtitle block top
HEAD_Y = 330                 # scene heading


def wav_len(p):
    if not p.exists():
        return None
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]))


def plan():
    scenes = []
    t = INTRO
    for sc in S["scenes"]:
        v = wav_len(VOICE / f"{sc['id']}.wav")
        dur = max(5.0, LEAD + (v or 4.0) + 1.0)
        scenes.append({**sc, "start": t, "dur": dur, "voice": v})
        t += dur
    ov = wav_len(VOICE / "outro.wav")
    outro = max(3.6, LEAD + (ov or 2.0) + 1.4)
    return {"scenes": scenes, "outro_start": t, "outro": outro, "total": t + outro, "outro_voice": ov}


# ---------------------------------------------------------------- small drawing helpers
def check(d, cx, cy, r, p, col=BG, fill=GOLD, a=1.0):
    """Gold disc with a check mark drawn progressively (p 0..1)."""
    if p <= 0:
        return
    rr = r * min(1, p * 1.8)
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=fill + (int(255 * a),))
    k = clamp((p - 0.4) / 0.6)
    if k > 0:
        p1, p2, p3 = (cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.35), (cx + r * 0.48, cy - r * 0.32)
        seg1 = min(1, k * 2)
        mid = (p1[0] + (p2[0] - p1[0]) * seg1, p1[1] + (p2[1] - p1[1]) * seg1)
        d.line((p1, mid), fill=col + (int(255 * a),), width=max(3, int(r * 0.18)))
        if k > 0.5:
            s2 = (k - 0.5) * 2
            end = (p2[0] + (p3[0] - p2[0]) * s2, p2[1] + (p3[1] - p2[1]) * s2)
            d.line((p2, end), fill=col + (int(255 * a),), width=max(3, int(r * 0.18)))


def dash(d, cx, cy, r, p, a=1.0):
    if p <= 0:
        return
    rr = r * min(1, p * 1.8)
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(110, 106, 100, int(255 * a)), width=3)
    w = r * 0.45 * clamp((p - 0.4) / 0.6)
    d.line((cx - w, cy, cx + w, cy), fill=(130, 126, 120, int(255 * a)), width=5)


def chip(d, cx, cy, txt, fnt, a, fill=None, outline=GOLD, color=GOLD, pad=26, h=64):
    tw = d.textlength(txt, font=fnt, direction="rtl", language="ar")
    box = (cx - tw / 2 - pad, cy - h / 2, cx + tw / 2 + pad, cy + h / 2)
    if fill:
        d.rounded_rectangle(box, h // 2, fill=fill + (int(255 * a),))
    else:
        d.rounded_rectangle(box, h // 2, fill=(30, 29, 30, int(230 * a)), outline=outline + (int(255 * a),), width=3)
    R.put(d, (cx, cy), txt, fnt, color, a, "mm")
    return box


def heading(d, t, dur, tag, title):
    """Scene heading: small gold tag + white title, slides in from the right."""
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    p = ease_out(prog(t, 0.05, 0.5))
    a = p * (1 - out)
    R.put(d, (RIGHT + 60 * (1 - p), HEAD_Y), tag, F(38, "Bold"), GOLD, a)
    tf, tl, lh = R.fit_lines(d, title, "ExtraBold", [74, 66, 58], TEXT_W, 74 * 1.4, 1.4)
    p2 = ease_out(prog(t, 0.2, 0.5))
    R.put(d, (RIGHT + 60 * (1 - p2), HEAD_Y + 52), tl[0], tf, WHITE, p2 * (1 - out))
    lw = 160 * ease_out(prog(t, 0.35, 0.5)) * (1 - out)
    d.rectangle((RIGHT - lw, HEAD_Y + 52 + lh + 6, RIGHT, HEAD_Y + 52 + lh + 12), fill=GOLD + (255,))


def subtitles(img, d, t, sc):
    """Narration shown word-by-word in sync with the voice."""
    txt = sc.get("show", sc["say"])
    bf, bl, blh = R.fit_lines(d, txt, "Medium", [50, 46, 42, 39], TEXT_W, 1720 - SUB_Y, 1.5)
    v = sc["voice"] or (sc["dur"] - 1.5)
    out = ease_in(prog(t, sc["dur"] - OUT_T, OUT_T))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    V.words_reveal(ImageDraw.Draw(layer), bl, bf, blh, SUB_Y, t, LEAD, LEAD + v * 0.92, RIGHT, True)
    if out > 0:
        layer.putalpha(layer.getchannel("A").point(lambda x: int(x * (1 - out))))
    V.comp(img, layer)
    bh = (1720 - SUB_Y) * ease_out(prog(t, 0.2, 0.6)) * (1 - out)
    d.rectangle((RIGHT + 28, SUB_Y, RIGHT + 37, SUB_Y + bh), fill=GOLD + (255,))


# ---------------------------------------------------------------- scenes
def scene1(img, d, t, sc):
    """Label card: 'compliant at home' -> '? abroad' with markets orbiting."""
    dur, v = sc["dur"], sc["voice"] or 4
    heading(d, t, dur, "المشكلة", "ملصق واحد… وأسواق كثيرة")
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    a = 1 - out
    pc = ease_out(prog(t, 0.2, 0.7))
    x0, y0, x1, y1 = 330, 600 + 60 * (1 - pc), 750, 1230 + 60 * (1 - pc)
    d.rounded_rectangle((x0, y0, x1, y1), 34, fill=(244, 240, 232, int(255 * pc * a)))
    ink = (40, 38, 38)
    R.put(d, (x1 - 50, y0 + 40), "المكونات", F(46, "ExtraBold"), ink, pc * a)
    for i in range(5):  # ingredient lines draw in one by one
        pl = ease_out(prog(t, 0.6 + i * 0.12, 0.4))
        ww = [320, 260, 300, 220, 280][i] * pl
        d.rounded_rectangle((x1 - 50 - ww, y0 + 130 + i * 50, x1 - 50, y0 + 150 + i * 50), 10,
                            fill=(200, 194, 184, int(255 * pc * a)))
    pa = ease_out(prog(t, 1.2, 0.5))
    d.rounded_rectangle((x0 + 30, y0 + 395, x1 - 30, y0 + 492), 16, fill=(255, 236, 190, int(255 * pa * a)))
    R.put(d, ((x0 + x1) / 2, y0 + 425), "يحتوي على:", F(32, "Bold"), ink, pa * a, "mm")
    R.put(d, ((x0 + x1) / 2, y0 + 462), "حليب، قمح، صويا", F(32, "Bold"), ink, pa * a, "mm")
    # stamp: check (home) then question (export) at the 'لكن' moment
    flip = LEAD + v * 0.45
    ps = prog(t, 1.5, 0.5)
    q = prog(t, flip, 0.4)
    scx, scy = x0 + 20, y1 - 30
    if ps > 0 and q < 0.5:
        check(d, scx, scy, 70, ps, a=a * (1 - q * 2))
        R.put(d, (scx, scy + 95), "مطابق محلياً", F(32, "Bold"), GOLD, ps * a * (1 - q * 2), "mm")
    if q > 0.5:
        k = ease_out((q - 0.5) * 2)
        d.ellipse((scx - 70 * k, scy - 70 * k, scx + 70 * k, scy + 70 * k), fill=GOLD + (int(255 * a),))
        R.put(d, (scx, scy - 6), "؟", F(int(96 * k) + 1, "Black"), BG, a, "mm")
    # markets orbit in after the flip
    markets = ["السعودية", "الاتحاد الأوروبي", "أمريكا", "اليابان", "كندا", "مصر"]
    for i, m in enumerate(markets):
        pm = ease_out(prog(t, flip + 0.15 + i * 0.12, 0.5))
        if pm <= 0:
            continue
        side = 1 if i % 2 == 0 else -1
        cx = 540 + side * (375 + 30 * (1 - pm))
        cy = 680 + (i // 2) * 230 + math.sin(t * 1.6 + i) * 8
        chip(d, cx, cy, m, F(28, "Bold"), pm * a, pad=18, h=56)


def scene2(img, d, t, sc):
    """Count of mandatory allergens per market."""
    dur, v = sc["dur"], sc["voice"] or 5
    heading(d, t, dur, "الاختلاف", "عدد المسببات الإلزامية")
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    a = 1 - out
    cols = [("الاتحاد الأوروبي", 14, 0.42), ("أمريكا", 9, 0.68), ("اليابان", 8, 0.84)]
    base = 1230
    for i, (name, n, when) in enumerate(cols):
        cx = RIGHT - 150 - i * 300
        pt = ease_out(prog(t, LEAD + v * when - 0.6, 0.9))
        if pt <= 0:
            continue
        bh = 34 * n * pt
        d.rounded_rectangle((cx - 85, base - bh, cx + 85, base), 18, fill=GOLD + (int(70 * a),),
                            outline=GOLD + (int(255 * a),), width=3)
        V.gold_text(img, (cx, base - bh - 20), str(int(round(n * pt))), F(130, "Black"), "ms", a * pt)
        R.put(d, (cx, base + 30), name, F(36, "Bold"), WHITE, a * pt, "ma")
    pl = ease_out(prog(t, 0.3, 0.8))
    d.line((80, base, 80 + (W - 160) * pl, base), fill=GOLD + (int(200 * a),), width=3)


def scene3(img, d, t, sc):
    """Example table: mandatory? EU / USA / Japan."""
    dur, v = sc["dur"], sc["voice"] or 5
    heading(d, t, dur, "مثال", "نفس المكوّن… حكم مختلف")
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    a = 1 - out
    cols = ["أوروبا", "أمريكا", "اليابان"]
    rows = [("الكرفس", (1, 0, 0)), ("الخردل", (1, 0, 0)), ("الترمس", (1, 0, 0)), ("الحنطة السوداء", (0, 0, 1))]
    col_x = [590, 410, 230]
    top = 620
    ph = ease_out(prog(t, 0.3, 0.5))
    for j, c in enumerate(cols):
        R.put(d, (col_x[j], top), c, F(38, "Bold"), GOLD, ph * a, "ma")
    d.line((120, top + 70, RIGHT, top + 70), fill=GOLD + (int(160 * ph * a),), width=2)
    when = [0.12, 0.22, 0.32, 0.72]
    for i, (name, vals) in enumerate(rows):
        tr = LEAD + v * when[i]
        pr = ease_out(prog(t, tr - 0.3, 0.5))
        if pr <= 0:
            continue
        y = top + 140 + i * 145
        R.put(d, (RIGHT - 30 * (1 - pr), y), name, F(46, "Bold"), WHITE, pr * a, "rm")
        for j, ok in enumerate(vals):
            pj = prog(t, tr + j * 0.15, 0.45)
            (check if ok else dash)(d, col_x[j], y, 36, pj, a=a)
        d.line((120, y + 72, RIGHT, y + 72), fill=(255, 255, 255, int(25 * a)), width=1)
    pk = ease_out(prog(t, LEAD + v * 0.8, 0.5))
    if pk > 0:  # legend
        check(d, 640, top + 140 + 4 * 145, 18, 1, a=pk * a)
        R.put(d, (610, top + 140 + 4 * 145), "إلزامي على الملصق", F(30, "Medium"), GREY, pk * a, "rm")
        dash(d, 330, top + 140 + 4 * 145, 18, 1, a=pk * a)
        R.put(d, (300, top + 140 + 4 * 145), "غير مدرج", F(30, "Medium"), GREY, pk * a, "rm")
    # QC cursor follows the rows being read
    k = min(3, int(max(0, (t - LEAD) / max(0.1, v)) / 0.25))
    cy = top + 140 + k * 145
    pc = ease_out(prog(t, 0.6, 0.4)) * a
    if pc > 0:
        V.cursor(d, 665 + 8 * math.sin(t * 3), cy - 12, pc)


# --- dot world map (equirectangular, land mask)
_map = None
MAP_X0, MAP_Y0, MAP_W, MAP_H = 50, 560, 980, 540
LAT0, LAT1 = 80, -56


def map_dots():
    global _map
    if _map is None:
        from global_land_mask import globe
        rnd = random.Random(5)
        pts = []
        step = 15
        for py in range(0, MAP_H, step):
            lat = LAT0 + (LAT1 - LAT0) * py / MAP_H
            for px in range(0, MAP_W, step):
                lon = -170 + 360 * px / MAP_W
                if lon <= 180 and globe.is_land(lat, lon):
                    pts.append({"x": MAP_X0 + px, "y": MAP_Y0 + py, "lat": lat, "lon": lon,
                                "sx": rnd.uniform(0, W), "sy": rnd.uniform(400, 1300),
                                "d": (px / MAP_W) * 0.5 + rnd.uniform(0, 0.2)})
        _map = pts
    return _map


# Illustrative regions that list milk (stylised, not a legal reference)
MILK = [(35, 71, -10, 40), (25, 50, -125, -66), (49, 70, -140, -55), (14, 33, -118, -86), (-56, 13, -82, -34),
        (12, 32, 34, 60), (22, 32, 25, 35), (30, 46, 129, 146), (34, 39, 125, 130), (20, 45, 98, 123),
        (-44, -10, 112, 154), (-47, -34, 166, 179), (-35, -22, 16, 33), (8, 30, 68, 90), (-11, 7, 95, 141)]


def in_milk(p):
    return any(a <= p["lat"] <= b and c <= p["lon"] <= e for a, b, c, e in MILK)


def scene4(img, d, t, sc):
    """FARRP chart idea: pick an allergen, see the countries light up."""
    dur, v = sc["dur"], sc["voice"] or 6
    heading(d, t, dur, "أداة مفيدة", "الجدول الدولي FARRP")
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    a = 1 - out
    click = LEAD + v * 0.62
    for p in map_dots():
        k = ease_io(prog(t, 0.2 + p["d"], 0.9))
        x = p["sx"] + (p["x"] - p["sx"]) * k
        y = p["sy"] + (p["y"] - p["sy"]) * k
        lit = in_milk(p) and prog(t, click + 0.1 + (p["lon"] + 170) / 360 * 0.8, 0.3)
        if lit:
            col, s = GOLD_HI, 4.6
        else:
            col, s = (120, 116, 110), 3.4
        al = int(255 * a * (0.4 + 0.6 * k))
        d.ellipse((x - s, y - s, x + s, y + s), fill=col + (al,))
    # allergen chips
    names = ["القمح", "البيض", "الحليب", "السمسم", "الفول السوداني"]
    pc = ease_out(prog(t, 0.9, 0.6))
    cf = F(30, "Bold")
    widths = [d.textlength(n, font=cf, direction="rtl", language="ar") + 40 for n in names]
    gap = 18
    x = 540 + (sum(widths) + gap * (len(names) - 1)) / 2
    xs = []
    for wdt in widths:          # right-to-left row
        xs.append(x - wdt / 2)
        x -= wdt + gap
    for i, n in enumerate(names):
        sel = n == "الحليب" and t > click
        chip(d, xs[i], 1230, n, cf, pc * a, fill=GOLD if sel else None,
             color=BG if sel else GOLD, h=60, pad=20)
    # cursor travels to "الحليب" and clicks
    if pc > 0:
        u = ease_io(prog(t, click - 1.2, 1.1))
        cx = 1000 + (xs[2] - 10 - 1000) * u
        cy = 1120 + (1235 - 1120) * u
        V.cursor(d, cx, cy, pc * a)
        rp = prog(t, click, 0.6)
        if 0 < rp < 1:
            r_ = 20 + 90 * rp
            d.ellipse((xs[2] - r_, 1230 - r_, xs[2] + r_, 1230 + r_), outline=GOLD_HI + (int(220 * (1 - rp)),), width=4)
    R.put(d, (540, 1300), S["source"], F(30, "Medium"), GREY, pc * a, "ma", rtl=False)
    R.put(d, (540, 1340), "رسم توضيحي", F(26, "Medium"), (120, 116, 110), pc * a, "ma")


def scene5(img, d, t, sc):
    """The takeaway + 3-step checklist."""
    dur, v = sc["dur"], sc["voice"] or 6
    heading(d, t, dur, "الخلاصة", "قبل اعتماد الملصق")
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    a = 1 - out
    p1 = ease_out(prog(t, LEAD + v * 0.12, 0.5))
    R.put(d, (RIGHT, 600), "الجدول = نقطة بداية", F(60, "Bold"), BODY, p1 * a)
    p2 = ease_out(prog(t, LEAD + v * 0.45, 0.5))
    tf = F(66, "ExtraBold")
    R.put(d, (RIGHT, 690), "القرار = التشريع الرسمي", tf, GOLD_HI, p2 * a)
    lw = 620 * p2
    d.rectangle((RIGHT - lw, 790, RIGHT, 796), fill=GOLD + (int(255 * a),))
    steps = ["حدّد السوق المستهدف", "قارن بالجدول الدولي", "راجع التشريع الرسمي", "اعتمد الملصق"]
    for i, s_ in enumerate(steps):
        ts = LEAD + v * (0.5 + i * 0.12)
        pi = ease_out(prog(t, ts, 0.45))
        if pi <= 0:
            continue
        y = 900 + i * 110
        check(d, RIGHT - 30, y, 34, prog(t, ts + 0.1, 0.5), a=a)
        R.put(d, (RIGHT - 90 - 40 * (1 - pi), y), s_, F(48, "Bold"), WHITE, pi * a, "rm")


class ShotParticles:
    """Build a screenshot from gold particles (helix -> pixel grid), like the vertical photos."""

    def __init__(self, img, box, grid=14, seed=1):
        x0, y0, w, h = box
        small = img.convert("RGB").resize((w // grid, h // grid), Image.BILINEAR)
        px = small.load()
        rnd = random.Random(seed)
        self.p = []
        for gy in range(small.height):
            for gx in range(small.width):
                tx, ty = x0 + gx * grid + grid / 2, y0 + gy * grid + grid / 2
                self.p.append((tx, ty, px[gx, gy], rnd.uniform(0, math.tau), rnd.uniform(400, 1300),
                               rnd.uniform(140, 260), (tx / W) * 0.45 + rnd.uniform(0, 0.12)))

    def draw(self, d, t, dur=1.3, alpha=1.0):
        for tx, ty, c, ang, hy, rad, delay in self.p:
            k = ease_io(prog(t, delay, dur - 0.6))
            spin = ang + t * 3.2
            hx = W * 0.6 + math.cos(spin) * rad
            x = hx + (tx - hx) * k
            y = hy + math.sin(spin) * 40 + (ty - hy - math.sin(spin) * 40) * k
            col = tuple(int(GOLD_HI[i] + (c[i] - GOLD_HI[i]) * k) for i in range(3))
            s = 1.6 + 2.6 * k
            d.rectangle((x - s, y - s, x + s, y + s), fill=col + (int(255 * alpha * (0.4 + 0.6 * k)),))


SHOTS = HERE / "assets"
_shot = {}


def browser_card(name, w):
    """Screenshot inside a dark browser frame with the site URL."""
    if name in _shot:
        return _shot[name]
    im = Image.open(SHOTS / name).convert("RGB")
    h = int(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    bar = 54
    card = Image.new("RGBA", (w + 16, h + bar + 16), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, card.width - 1, card.height - 1), 22, fill=(48, 46, 46, 255), outline=GOLD + (255,), width=3)
    for i, c in enumerate([(236, 95, 88), (244, 190, 80), (98, 197, 84)]):
        cd.ellipse((22 + i * 30, 19, 38 + i * 30, 35), fill=c + (255,))
    cd.rounded_rectangle((130, 12, card.width - 24, 42), 15, fill=(28, 27, 28, 255))
    cd.text((150, 27), S["url"], font=F(22, "Medium"), fill=(220, 216, 210, 255), anchor="lm")
    card.paste(im, (8, bar + 8))
    _shot[name] = (card, im)
    return _shot[name]


_sp = {}


def scene4b(img, d, t, sc):
    """Real screenshots from the FARRP site: map (milk) built from particles, then the table."""
    dur, v = sc["dur"], sc["voice"] or 6
    heading(d, t, dur, "من داخل الموقع", S["url"])
    out = ease_in(prog(t, dur - OUT_T, OUT_T))
    a = 1 - out
    card, shot = browser_card("farrp_map_milk.png", 920)
    cx, cy = (W - card.width) // 2, 520
    if "map" not in _sp:
        _sp["map"] = ShotParticles(shot, (cx + 8, cy + 62, shot.width, shot.height))
    build = 1.4
    if t < build + 0.3:
        _sp["map"].draw(d, t, build, a)
    pa = ease_out(prog(t, build - 0.3, 0.5)) * a
    if pa > 0.01:
        c = card.copy()
        c.putalpha(c.getchannel("A").point(lambda x: int(x * pa)))
        V.comp(img, c, (cx, cy))
    # table screenshot slides up over the map
    tt = LEAD + v * 0.5
    pt = ease_out(prog(t, tt, 0.6)) * a
    if pt > 0.01:
        tcard, _ = browser_card("farrp_table.png", 900)
        c = tcard.copy()
        c.putalpha(c.getchannel("A").point(lambda x: int(x * pt)))
        V.comp(img, c, ((W - tcard.width) // 2, int(1330 - tcard.height + 120 * (1 - pt))))
    # QC cursor hovers: Milk button first, then the EU row of the table
    pc = ease_out(prog(t, build, 0.4)) * a
    if pc > 0:
        if t < tt:
            tx_, ty_ = cx + 8 + int(shot.width * 0.38), cy + 62 + int(shot.height * 0.82)
        else:
            tx_, ty_ = 200, 1330 - 120
        V.cursor(d, tx_ + 6 * math.sin(t * 3), ty_, pc)
    R.put(d, (540, 1345), "المصدر: " + S["source"], F(26, "Medium"), GREY, pc, "ma")


SCENES = {"s1": scene1, "s2": scene2, "s3": scene3, "s4": scene4, "s4b": scene4b, "s5": scene5}


def intro(img, d, t):
    """Branded opening: logo from particles + loader, logo flies to the corner, title slams in."""
    a = 1 - ease_in(prog(t, INTRO - 0.4, 0.4))
    pts = V.logo_points(w=360, y0=720)
    if t < 1.3:
        V.helix(d, t, W / 2, 820, 700, n=len(pts), alpha=1 - prog(t, 0.95, 0.3),
                conv=ease_io(prog(t, 0.0, 0.9)), target=pts)
    fly = ease_io(prog(t, 1.2, 0.5))
    if t > 0.75:
        la = ease_out(prog(t, 0.75, 0.35))
        w = int(360 + (V.WM_W - 360) * fly)
        V.comp(img, R.logo_sized(w, la), ((W - 360) / 2 + (V.WM_POS[0] - (W - 360) / 2) * fly,
                                          720 + (V.WM_POS[1] - 720) * fly))
    if t < 1.5:
        la = 1 - prog(t, 1.2, 0.3)
        p = ease_io(prog(t, 0.1, 1.0))
        d.rectangle((W / 2 - 200, 1040, W / 2 - 200 + 400 * p, 1043), fill=GOLD + (int(255 * la),))
        R.put(d, (W / 2, 1075), f"{int(p * 100):03d}", F(40, "Bold"), GOLD, la, "ma", rtl=False)
    fr = prog(t, 1.2, 0.6)
    if 0 < fr < 1:
        r_ = 80 + 900 * ease_out(fr)
        d.ellipse((W / 2 - r_, 900 - r_, W / 2 + r_, 900 + r_), outline=GOLD_HI + (int(200 * (1 - fr)),), width=6)
    if t > 1.3:
        V.helix(d, t, W / 2, 760, 900 * ease_out(prog(t, 1.3, 0.8)) + 200, n=360,
                alpha=0.5 * a * ease_out(prog(t, 1.3, 0.8)))
    pt = prog(t, 1.6, 0.45)
    if pt > 0:
        e = ease_out(pt)
        sz = 104
        while d.textlength(S["title"], font=F(sz, "Black"), direction="rtl", language="ar") > W - 140:
            sz -= 4
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        R.put(ld, (W / 2, 860), S["title"], F(int(sz * (1.3 - 0.3 * e)), "Black"), WHITE, e * a, "ma")
        g = layer.filter(ImageFilter.GaussianBlur(14))
        tint = Image.new("RGBA", (W, H), GOLD_HI + (0,))
        tint.putalpha(g.getchannel("A").point(lambda x: int(x * 0.6 * (1 - prog(t, 2.1, 0.6)))))
        V.comp(img, tint)
        V.comp(img, layer)
    lw = 460 * ease_out(prog(t, 2.0, 0.5)) * a
    d.rectangle((W / 2 - lw / 2, 1010, W / 2 + lw / 2, 1017), fill=GOLD + (int(255 * a),))
    p2 = ease_out(prog(t, 2.2, 0.5))
    R.put(d, (W / 2, 1050), S["subtitle"], F(48, "Bold"), GOLD, p2 * a, "ma")


def outro(img, d, t, dur):
    tx = R.TEXTS["ar"]
    pts = V.logo_points()
    V.helix(d, t + 3, W / 2, 780, 760, n=len(pts), alpha=1 - prog(t, 1.2, 0.5),
            conv=ease_io(prog(t, 0.0, 1.3)), target=pts)
    pl = ease_out(prog(t, 1.0, 0.6))
    if pl > 0.01:
        lg = R.logo_sized(520, pl)
        V.comp(img, lg, ((W - lg.width) // 2, 520))
    y = 520 + R.logo_sized(520).height + 70
    R.put(d, (W / 2, y), tx["regards"], F(58, "Bold"), WHITE, ease_out(prog(t, LEAD, 0.6)), "ma")
    p2 = ease_out(prog(t, 1.6, 0.6))
    R.put(d, (W / 2, y + 100), tx["cta"], F(50, "Bold"), GOLD, p2, "ma")
    R.put(d, (W / 2, y + 185), "#سلامة_الغذاء   #FoodSafety", F(38, "Medium"), GREY, p2, "ma")


def frame(t, pl):
    img = V.background(t)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if t < INTRO:
        intro(img, d, t)
    elif t < pl["outro_start"]:
        sc = next(s for s in pl["scenes"] if s["start"] <= t < s["start"] + s["dur"])
        lt = t - sc["start"]
        SCENES[sc["id"]](img, d, lt, sc)
        subtitles(img, d, lt, sc)
    else:
        outro(img, d, t - pl["outro_start"], pl["outro"])
    V.swoosh(d, t, H - 95, alpha=0.8, flip=True)
    wm = 1 - ease_out(prog(t, pl["outro_start"], 0.4))
    if t >= 1.7 and wm > 0.01:
        V.comp(img, R.logo_sized(V.WM_W, 0.95 * wm), V.WM_POS)
    # scene dots (progress) at the top-right
    if INTRO <= t < pl["outro_start"]:
        for i, s in enumerate(pl["scenes"]):
            on = s["start"] <= t
            d.ellipse((RIGHT - i * 30 - 8, 120 - 8, RIGHT - i * 30 + 8, 120 + 8),
                      fill=(GOLD if on else (90, 88, 84)) + (255,))
    d.rectangle((0, H - 10, int(W * clamp(t / pl["total"])), H), fill=GOLD + (255,))
    img.paste(ov, (0, 0), ov)
    return img


def render(pl, path):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-tune", "animation",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(pl["total"] * FPS)):
        proc.stdin.write(frame(i / FPS, pl).tobytes())
    proc.stdin.close()
    proc.wait()


def mix(pl, video, out):
    """Voice per scene + greeting, music ducked under the voice."""
    ins, fc, labels = ["-i", str(video), "-stream_loop", "-1", "-i", str(MUSIC)], [], ["[m]"]
    total = pl["total"]
    fc.append(f"[1:a]volume=0.15,afade=t=in:st=0:d=0.8,afade=t=out:st={total - 2:.2f}:d=2,atrim=0:{total:.3f}[m]")
    items = [(VOICE / f"{s['id']}.wav", s["start"] + LEAD) for s in pl["scenes"]]
    items.append((VOICE / "outro.wav", pl["outro_start"] + LEAD))
    n = 2
    for wav, off in items:
        if not wav.exists():
            continue
        ins += ["-i", str(wav)]
        ms = int(off * 1000)
        fc.append(f"[{n}:a]aresample=44100,pan=stereo|c0=c0|c1=c0,adelay={ms}|{ms},volume=1.6[v{n}]")
        labels.append(f"[v{n}]")
        n += 1
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.9[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v",
                    "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}",
                    "-movflags", "+faststart", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    pl = plan()
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    if a.preview:
        ts = [1.0, 2.6]
        for s in pl["scenes"]:
            ts += [s["start"] + s["dur"] * 0.35, s["start"] + s["dur"] * 0.85]
        ts.append(pl["total"] - 0.4)
        for t in ts:
            frame(t, pl).save(out / f"preview_{t:05.1f}.png")
        print("total", round(pl["total"], 1))
        return
    silent = out / "allergen_labelling_silent.mp4"
    render(pl, silent)
    final = HERE / "allergen_labelling.mp4"
    mix(pl, silent, final)
    print("wrote", final)


if __name__ == "__main__":
    main()
