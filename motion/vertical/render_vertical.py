#!/usr/bin/env python3
"""Vertical (1080x1920) Quick Fact videos for TikTok / Reels / YouTube Shorts.

Layout follows the reference design: photo on top, big gold number, title,
English pill, body text, fixed AB logo top-left. Motion follows the website:
gold particles spiral in a helix, then fly in to build each photo from scratch
while a "QC" cursor sweeps across; photos dissolve back into particles between
facts; the outro builds the logo from particles.

Reuses voice-over, timings and texts from ../render.py.

    python3 vertical/render_vertical.py --lang ar --id 11-12
    python3 vertical/render_vertical.py --lang en --preview 11-12
"""
import argparse
import json
import math
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import render as R  # noqa: E402

W, H = 1080, 1920
FPS = 30
BG = (24, 23, 24)
GOLD = R.GOLD
GOLD_HI = (255, 214, 102)
WHITE = R.WHITE
BODY = R.BODY
GREY = R.GREY

IMG_H = 880                 # photo area height
RIGHT = W - 120              # text edges (leave room for TikTok side buttons)
LEFT = 90
TEXT_W = W - 230
REVEAL = 1.9                 # seconds to build a photo from particles
DISSOLVE = 0.7               # seconds to dissolve at the end of a fact
GRID = 18                    # particle spacing in px

IMAGES = HERE / "images"

# ---------------------------------------------------------------- helpers
clamp, ease_out, ease_in, prog = R.clamp, R.ease_out, R.ease_in, R.prog


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def rtl():
    return R.LANG == "ar"


_photo_cache = {}


def photo(num):
    """Cover-cropped photo with a soft fade into the background."""
    if num in _photo_cache:
        return _photo_cache[num]
    p = IMAGES / f"{num}.jpg"
    if p.exists():
        im = ImageOps.fit(Image.open(p).convert("RGB"), (W, IMG_H), Image.LANCZOS, centering=(0.5, 0.45))
    else:
        im = Image.new("RGB", (W, IMG_H), (60, 55, 45))
    im = im.convert("RGBA")
    # vignette + fade at bottom
    mask = Image.new("L", (W, IMG_H), 255)
    md = ImageDraw.Draw(mask)
    fade = 380
    for i in range(fade):
        md.line((0, IMG_H - fade + i, W, IMG_H - fade + i), fill=int(255 * (1 - i / fade) ** 1.6))
    for i in range(120):
        md.line((0, i, W, i), fill=int(255 * (0.55 + 0.45 * i / 120)))
    im.putalpha(mask)
    small = im.resize((W // GRID, IMG_H // GRID), Image.BILINEAR)
    _photo_cache[num] = (im, small)
    return _photo_cache[num]


class Particles:
    """Particles that travel from a helix to the photo's pixel grid."""

    def __init__(self, num, seed):
        rnd = random.Random(seed)
        _, small = photo(num)
        px = small.load()
        self.p = []
        for gy in range(small.height):
            for gx in range(small.width):
                r, g, b, a = px[gx, gy]
                if a < 40:
                    continue
                tx, ty = gx * GRID + GRID / 2, gy * GRID + GRID / 2
                ang = rnd.uniform(0, math.tau)
                hy = rnd.uniform(-200, IMG_H + 100)       # start on a vertical helix (as on the website)
                self.p.append({
                    "tx": tx, "ty": ty, "c": (r, g, b), "a": a,
                    "ang": ang, "hy": hy, "rad": rnd.uniform(140, 260),
                    "delay": (tx / W) * 0.75 + rnd.uniform(0, 0.25),   # follows the cursor sweep
                    "vx": rnd.uniform(-1, 1), "vy": rnd.uniform(-1.6, -0.4),
                })

    def draw(self, d, t, mode):
        """mode 'in': helix -> photo (t in 0..REVEAL). mode 'out': photo -> scatter (t in 0..DISSOLVE)."""
        for q in self.p:
            if mode == "in":
                k = ease_io(prog(t, q["delay"], REVEAL - 0.9))
                spin = q["ang"] + t * 3.2
                hx = W * 0.62 + math.cos(spin) * q["rad"]
                hy = q["hy"] + math.sin(spin) * 40
                x = hx + (q["tx"] - hx) * k
                y = hy + (q["ty"] - hy) * k
                col = tuple(int(GOLD_HI[i] + (q["c"][i] - GOLD_HI[i]) * k) for i in range(3))
                alpha = int(min(255, q["a"]) * (0.35 + 0.65 * min(1, t / 0.4)))
                s = 1.6 + 2.4 * k
            else:
                k = ease_in(clamp(t / DISSOLVE))
                x = q["tx"] + q["vx"] * 260 * k
                y = q["ty"] + q["vy"] * 320 * k
                col = tuple(int(q["c"][i] + (GOLD_HI[i] - q["c"][i]) * k) for i in range(3))
                alpha = int(min(255, q["a"]) * (1 - k))
                s = 4 - 2.4 * k
            if alpha > 6:
                d.rectangle((x - s, y - s, x + s, y + s), fill=col + (alpha,))


def cursor(d, x, y, alpha=1.0, label="QC"):
    a = int(255 * alpha)
    pts = [(0, 0), (0, 34), (9, 26), (16, 41), (22, 38), (15, 24), (27, 24)]
    d.polygon([(x + px, y + py) for px, py in pts], fill=(250, 250, 250, a), outline=(20, 20, 20, a))
    f = R.font(24, "Bold")
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((x + 26, y + 34, x + 26 + tw + 24, y + 74), 12, fill=GOLD + (a,))
    d.text((x + 38 + tw / 2, y + 54), label, font=f, fill=BG + (a,), anchor="mm")


def swoosh(d, t, y0, alpha=1.0, flip=False):
    """Thin gold curves like the reference design."""
    for j, (amp, wdt, a) in enumerate(((26, 3, 200), (40, 2, 120), (16, 2, 90))):
        pts = []
        for i in range(0, 61):
            u = i / 60
            x = u * (W + 200) - 100
            yy = y0 + math.sin(u * math.pi * 1.1 + j * 0.5 + t * 0.4) * amp * (-1 if flip else 1)
            pts.append((x, yy))
        d.line(pts, fill=GOLD + (int(a * alpha),), width=wdt)


def gold_text(img, xy, txt, fnt, anchor, alpha=1.0):
    """Big number filled with a vertical gold gradient + soft glow."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).text(xy, txt, font=fnt, fill=int(255 * alpha), anchor=anchor)
    bbox = m.getbbox()
    if not bbox:
        return
    grad = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    y0, y1 = bbox[1], bbox[3]
    for y in range(y0, y1):
        u = (y - y0) / max(1, y1 - y0)
        c = tuple(int(GOLD_HI[i] + (GOLD[i] * 0.8 - GOLD_HI[i]) * u) for i in range(3))
        gd.line((bbox[0], y, bbox[2], y), fill=c + (255,))
    glow = Image.new("RGBA", img.size, GOLD + (0,))
    glow.putalpha(m.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.5)))
    img.alpha_composite(glow)
    grad.putalpha(m)
    img.alpha_composite(grad)


def words_reveal(d, lines, fnt, lh, y, t, t0, t1, edge, r):
    """Word-by-word reveal; the newest word glows gold, then settles to white."""
    words = [(li, w) for li, line in enumerate(lines) for w in line.split()]
    n = max(1, len(words))
    span = max(0.5, t1 - t0)
    sp = d.textlength(" ", font=fnt)
    idx = 0
    for li, line in enumerate(lines):
        x = edge
        for w in line.split():
            ts = t0 + span * idx / n
            p = ease_out(prog(t, ts, 0.35))
            hot = 1 - prog(t, ts + 0.25, 0.6)
            col = tuple(int(BODY[i] + (GOLD_HI[i] - BODY[i]) * hot) for i in range(3)) if p > 0 else BODY
            ww = d.textlength(w, font=fnt, direction="rtl" if r else None, language="ar" if r else None)
            if p > 0.01:
                kw = {"direction": "rtl", "language": "ar"} if r else {}
                d.text((x, y + li * lh + 18 * (1 - p)), w, font=fnt,
                       fill=col + (int(255 * p),), anchor="ra" if r else "la", **kw)
            x = x - ww - sp if r else x + ww + sp
            idx += 1


# ---------------------------------------------------------------- scenes
def background(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx = W / 4 * (0.7 + 0.05 * math.sin(t * 0.5))
    cy = H / 4 * (0.62 + 0.03 * math.cos(t * 0.4))
    gd.ellipse((cx - 110, cy - 110, cx + 110, cy + 110), fill=GOLD + (34,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)).resize((W, H), Image.BILINEAR))
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    off = (t * 25) % 90
    for i in range(-24, 16):
        x = i * 90 + off
        ld.line((x, H, x + 700, 0), fill=(255, 255, 255, 7), width=2)
    img.alpha_composite(lines)
    return img


def helix(d, t, cx, cy, h, n=420, alpha=1.0, conv=0.0, target=None):
    """The website's spinning helix of gold dots; conv>0 pulls dots to target points."""
    rnd = random.Random(7)
    for i in range(n):
        u = i / n
        ang = u * math.tau * 5 + t * 2.4
        x = cx + math.cos(ang) * (150 + 30 * math.sin(u * 9))
        y = cy - h / 2 + u * h + math.sin(ang) * 26 + rnd.uniform(-6, 6)
        if target and conv > 0:
            tx, ty = target[i % len(target)]
            x += (tx - x) * conv
            y += (ty - y) * conv
        s = 1.5 + 1.8 * (0.5 + 0.5 * math.sin(ang))
        a = int(255 * alpha * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(ang))))
        d.rectangle((x - s, y - s, x + s, y + s), fill=GOLD_HI + (a,))


_logo_pts = None


def logo_points(w=520, y0=520):
    global _logo_pts
    if _logo_pts is None:
        lg = R.logo_sized(w)
        a = lg.getchannel("A")
        pts = []
        for y in range(0, lg.height, 9):
            for x in range(0, lg.width, 9):
                if a.getpixel((x, y)) > 128:
                    pts.append(((W - w) / 2 + x, y0 + y))
        random.Random(3).shuffle(pts)
        _logo_pts = pts
    return _logo_pts


def scene_intro(img, d, t, video):
    tx = R.TEXTS[R.LANG]
    a = 1 - ease_in(prog(t, R.INTRO - 0.4, 0.4))
    helix(d, t, W / 2, 620, 760, alpha=a * ease_out(prog(t, 0, 0.5)))
    p = ease_out(prog(t, 0.35, 0.7))
    R.put(d, (W / 2, 1080 + 40 * (1 - p)), tx["title"], R.font(118 if rtl() else 130, "Black"),
          WHITE, p * a, "ma", rtl=rtl())
    lw = 460 * ease_out(prog(t, 0.7, 0.8)) * a
    d.rectangle((W / 2 - lw / 2, 1290, W / 2 + lw / 2, 1297), fill=GOLD + (int(255 * a),))
    R.put(d, (W / 2, 1320), tx["sub"], R.font(58 if rtl() else 50, "Bold"), GOLD, p * a, "ma", rtl=False)
    nums = "  ·  ".join("#" + tp["num"] for tp in video["tips"])
    R.put(d, (W / 2, 1420), nums, R.font(44, "Medium"), GREY, p * a, "ma", rtl=False)


def scene_tip(img, d, t, tip, dur, parts, voice):
    r = rtl()
    sgn = 1 if r else -1
    edge = RIGHT if r else LEFT
    anc = "ra" if r else "la"
    out = ease_in(prog(t, dur - DISSOLVE, DISSOLVE))
    vis = 1 - out

    # --- photo: particles build it, then the real photo fades in
    ph, _ = photo(tip["num"])
    if t < REVEAL + 0.3:
        parts.draw(d, t, "in")
    pa = ease_out(prog(t, REVEAL - 0.35, 0.6)) * (1 - prog(t, dur - DISSOLVE, 0.25))
    if pa > 0.01:
        layer = ph.copy()
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * pa)))
        img.alpha_composite(layer, (0, 0))
    if t > dur - DISSOLVE:
        parts.draw(d, t - (dur - DISSOLVE), "out")
    # QC cursor sweeps left->right ahead of the particle front
    if t < REVEAL + 0.4:
        u = ease_io(prog(t, 0.1, REVEAL - 0.2))
        cx = -40 + u * (W + 40)
        cy = IMG_H * 0.62 - math.sin(u * math.pi) * 330
        cursor(d, cx, cy, alpha=1 - prog(t, REVEAL, 0.4))
    swoosh(d, t, IMG_H - 60, alpha=vis)

    # --- big gold number
    pn = ease_out(prog(t, 0.5, 0.7))
    if pn > 0.01:
        nx = RIGHT + 10 if r else LEFT - 10
        gold_text(img, (nx + 40 * (1 - pn) * sgn, IMG_H + 175), tip["num"], R.font(300, "Black"),
                  "rs" if r else "ls", pn * vis)

    # --- title
    title = tip["title"] if r else tip["en_title"]
    tf, tl, tlh = R.fit_lines(d, title, "ExtraBold", [96, 86, 76, 68], TEXT_W, 2 * 96 * 1.4, 1.4)
    y = IMG_H + 175
    pt = ease_out(prog(t, 0.8, 0.6))
    for line in tl:
        R.put(d, (edge - 60 * (1 - pt) * sgn - 80 * out * sgn, y), line, tf, WHITE, pt * vis, anc, rtl=r)
        y += tlh
    y += 22

    # --- pill
    pill = tip["en_title"] if r else f"Quick Fact #{tip['num']}"
    for sz in (52, 46, 40, 34):
        ef = R.font(sz, "Bold")
        if d.textlength(pill, font=ef) <= TEXT_W - 60:
            break
    ew = d.textlength(pill, font=ef)
    pp = ease_out(prog(t, 1.1, 0.6))
    if pp > 0.01:
        a_edge = edge - 80 * out * sgn
        b_edge = a_edge - (ew + 64) * pp * sgn
        d.rounded_rectangle((min(a_edge, b_edge), y, max(a_edge, b_edge), y + 92), 22,
                            fill=GOLD + (int(255 * vis),))
        R.put(d, (a_edge - 32 * sgn, y + 46), pill, ef, BG, clamp((pp - 0.6) / 0.4) * vis,
              "rm" if r else "lm", rtl=False)
    y += 92 + 48

    # --- side bar
    bh = (1700 - (IMG_H + 150)) * ease_out(prog(t, 0.6, 0.8)) * vis
    bx = RIGHT + 28 if r else LEFT - 36
    d.rectangle((bx, IMG_H + 150, bx + 9, IMG_H + 150 + bh), fill=GOLD + (255,))

    # --- body, word by word, paced to the voice-over
    body = tip["body"] if r else tip["en_body"]
    bf, bl, blh = R.fit_lines(d, body, "Medium", [54, 50, 46, 43, 40, 37], TEXT_W, 1720 - y, 1.5)
    t0 = R.VOICE_LEAD + 0.6
    t1 = (R.VOICE_LEAD + voice * 0.92) if voice else dur - 2.5
    if vis < 1:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        words_reveal(ImageDraw.Draw(layer), bl, bf, blh, y, t, t0, t1, edge - 80 * out * sgn, r)
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * vis)))
        img.alpha_composite(layer)
    else:
        words_reveal(d, bl, bf, blh, y, t, t0, t1, edge, r)


def scene_outro(img, d, t):
    tx = R.TEXTS[R.LANG]
    pts = logo_points()
    conv = ease_io(prog(t, 0.0, 1.3))
    helix(d, t + 3, W / 2, 780, 760, n=len(pts), alpha=1 - prog(t, 1.2, 0.5), conv=conv, target=pts)
    pl = ease_out(prog(t, 1.0, 0.6))
    if pl > 0.01:
        lg = R.logo_sized(520, pl)
        img.alpha_composite(lg, ((W - lg.width) // 2, 520))
    y = 520 + R.logo_sized(520).height + 70
    p1 = ease_out(prog(t, 1.2, 0.6))
    R.put(d, (W / 2, y), tx["regards"], R.font(58, "Bold"), WHITE, p1, "ma", rtl=rtl())
    p2 = ease_out(prog(t, 1.7, 0.6))
    R.put(d, (W / 2, y + 100), tx["cta"], R.font(50, "Bold"), GOLD, p2, "ma", rtl=rtl())
    R.put(d, (W / 2, y + 185), tx["tags"], R.font(38, "Medium"), GREY, p2, "ma", rtl=rtl())


# ---------------------------------------------------------------- frame / video
def plan(video):
    durs = R.tip_durations(video)
    voices = [R.voice_len(tp["num"]) for tp in video["tips"]]
    outro = max(R.outro_len(), 3.4)
    parts = [Particles(tp["num"], i) for i, tp in enumerate(video["tips"])]
    return {"durs": durs, "voices": voices, "outro": outro, "parts": parts,
            "total": R.INTRO + sum(durs) + outro}


def frame(t, video, pl):
    img = background(t)
    d = ImageDraw.Draw(img)
    durs = pl["durs"]
    tips_end = R.INTRO + sum(durs)
    if t < R.INTRO:
        scene_intro(img, d, t, video)
    elif t < tips_end:
        k, start = 0, R.INTRO
        while t >= start + durs[k]:
            start += durs[k]
            k += 1
        scene_tip(img, d, t - start, video["tips"][k], durs[k], pl["parts"][k], pl["voices"][k])
    else:
        scene_outro(img, d, t - tips_end)
    swoosh(d, t, H - 95, alpha=0.8, flip=True)
    # fixed logo (top-left); hidden only while the outro builds the big logo
    wm = 1 - ease_out(prog(t, tips_end, 0.4))
    if wm > 0.01:
        img.alpha_composite(R.logo_sized(210, 0.95 * wm), (60, 50))
    d.rectangle((0, H - 10, int(W * clamp(t / pl["total"])), H), fill=GOLD + (255,))
    return img.convert("RGB")


def render_video(video, out_dir):
    pl = plan(video)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"quick_fact_{video['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(pl["total"] * FPS)):
        proc.stdin.write(frame(i / FPS, video, pl).tobytes())
    proc.stdin.close()
    proc.wait()
    print("wrote", path, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ar", choices=["ar", "en"])
    ap.add_argument("--id", nargs="*")
    ap.add_argument("--preview")
    a = ap.parse_args()
    R.set_lang(a.lang)
    data = json.loads((HERE.parent / "tips.json").read_text(encoding="utf-8"))
    out_dir = HERE / ("output" if a.lang == "ar" else f"output_{a.lang}")
    if a.preview:
        v = next(v for v in data["videos"] if v["id"] == a.preview)
        pl = plan(v)
        out_dir.mkdir(parents=True, exist_ok=True)
        s = R.INTRO
        for t in (1.5, s + 0.8, s + 1.5, s + pl["durs"][0] * 0.6, s + pl["durs"][0] - 0.35,
                  pl["total"] - 2.6, pl["total"] - 0.3):
            frame(t, v, pl).save(out_dir / f"preview_{v['id']}_{t:05.1f}.png")
        return
    for v in data["videos"]:
        if a.id and v["id"] not in a.id:
            continue
        render_video(v, out_dir)


if __name__ == "__main__":
    main()
