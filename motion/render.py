#!/usr/bin/env python3
"""Motion-graphic renderer for the "معلومة على السريع | Quick Fact" series.

LinkedIn square video (1080x1080). Each video = intro -> 2 facts -> outro,
with the AB logo fixed as a watermark on every frame.

Usage:
    python3 build_tips.py            # rebuild tips.json from content/quick_facts.md
    python3 render.py                # render every video
    python3 render.py --id 01-02     # render one video
    python3 render.py --preview 01-02  # still PNG frames only
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
BG = (41, 39, 40)          # same as the logo background
GOLD = (229, 174, 61)
WHITE = (255, 255, 255)
GREY = (170, 166, 160)
BODY = (225, 222, 218)

INTRO = 2.4
TIP = 8.5
OUTRO = 2.8

RIGHT = W - 110            # right text edge (RTL)
LEFT = 110                 # left text edge (LTR)
TEXT_W = W - 250           # max text width

LANG = "ar"
TEXTS = {
    "ar": {"title": "معلومة على السريع", "sub": "Quick Fact",
           "cta": "تابعني على LinkedIn للمزيد",
           "regards": "مع تحيات المهندس علاء الدين",
           "tags": "#معلومة_على_السريع   #QuickFact"},
    "en": {"title": "Quick Fact", "sub": "Quality · Food Safety · AI",
           "cta": "Follow me on LinkedIn for more",
           "regards": "With regards, Eng. Alaeldeen",
           "tags": "#QuickFact   #FoodSafety"},
}


def set_lang(lang):
    """Switch language: affects layout direction, texts and in/out folders."""
    global LANG, OUT, VOICE_DIR
    LANG = lang
    sfx = "" if lang == "ar" else f"_{lang}"
    OUT = ROOT / f"output{sfx}"
    VOICE_DIR = ROOT / f"voice{sfx}"


def rtl():
    return LANG == "ar"

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
    return 1 - (1 - clamp(t)) ** 3


def ease_in(t):
    return clamp(t) ** 3


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
            opx[x, y] = (r, g, b, int(clamp(d / 60) * 255))
    return out.crop(out.getbbox())


LOGO_IMG = load_logo()


def logo_sized(width, alpha=1.0):
    h = int(LOGO_IMG.height * width / LOGO_IMG.width)
    lg = LOGO_IMG.resize((width, h), Image.LANCZOS)
    if alpha < 1:
        lg.putalpha(lg.getchannel("A").point(lambda v: int(v * alpha)))
    return lg


WATERMARK = logo_sized(150, 0.9)


# ---------- text ----------
def tlen(d, txt, fnt):
    return d.textlength(txt, font=fnt, direction="rtl", language="ar")


def put(d, xy, txt, fnt, fill, alpha=1.0, anchor="ra", rtl=True):
    # Cairo has no arrow glyphs; "›" is mirrored to "‹" inside RTL runs
    txt = txt.replace("←", "›").replace("→", "›")
    kw = {"direction": "rtl", "language": "ar"} if rtl else {}
    d.text(xy, txt, font=fnt, fill=fill + (int(255 * clamp(alpha)),), anchor=anchor, **kw)


def wrap(d, txt, fnt, max_w):
    lines = []
    for para in txt.split("\n"):
        cur = ""
        for w in para.split():
            test = (cur + " " + w).strip()
            if tlen(d, test, fnt) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def fit_lines(d, txt, weight, sizes, max_w, max_h, lh=1.5):
    """Largest font size whose wrapped text fits in max_h."""
    for s in sizes:
        f = font(s, weight)
        lines = wrap(d, txt, f, max_w)
        if len(lines) * s * lh <= max_h:
            return f, lines, int(s * lh)
    return f, lines, int(s * lh)


def bolt(d, cx, cy, s, fill):
    pts = [(0.15, -1), (-0.55, 0.12), (-0.05, 0.12), (-0.25, 1), (0.55, -0.2), (0.05, -0.2), (0.3, -1)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=fill)


# ---------- background ----------
def background(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx = W * 0.75 + math.sin(t * 0.6) * 60
    cy = H * 0.25 + math.cos(t * 0.5) * 40
    gd.ellipse((cx - 330, cy - 330, cx + 330, cy + 330), fill=GOLD + (28,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    off = (t * 25) % 80
    for i in range(-14, 20):
        x = i * 80 + off
        ld.line((x, H, x + 380, H - 1100), fill=(255, 255, 255, 9), width=2)
    img.alpha_composite(lines)
    return img


# ---------- scenes ----------
def scene_intro(d, t, data, video):
    p_in = ease_out(prog(t, 0.2, 0.7))
    a = p_in * (1 - ease_in(prog(t, INTRO - 0.45, 0.45)))
    # bolt badge
    pb = ease_out(prog(t, 0.0, 0.6))
    if pb > 0:
        r = 62 * pb
        d.ellipse((W / 2 - r, 330 - r, W / 2 + r, 330 + r), fill=GOLD + (int(255 * a),))
        bolt(d, W / 2, 330, 40 * pb, BG + (int(255 * a),))
    tx = TEXTS[LANG]
    put(d, (W / 2, 430 + 30 * (1 - p_in)), tx["title"], font(96 if rtl() else 110, "Black"),
        WHITE, a, "ma", rtl=rtl())
    lw = 380 * ease_out(prog(t, 0.6, 0.8)) * a
    d.rectangle((W / 2 - lw / 2, 600, W / 2 + lw / 2, 606), fill=GOLD + (int(255 * a),))
    put(d, (W / 2, 625), tx["sub"], font(52 if rtl() else 44, "Bold"), GOLD, a, "ma", rtl=False)
    nums = " · ".join("#" + tp["num"] for tp in video["tips"])
    put(d, (W / 2, 710), nums, font(36, "Medium"), GREY, a, "ma", rtl=False)


def scene_tip(d, t, tip, dur=TIP):
    out = ease_in(prog(t, dur - 0.5, 0.5))
    vis = 1 - out
    r = rtl()
    sgn = 1 if r else -1               # direction of "inwards" motion
    edge = RIGHT if r else LEFT        # text anchor edge
    anc = "ra" if r else "la"
    sx = -80 * out * sgn
    title = tip["title"] if r else tip["en_title"]
    body = tip["body"] if r else tip["en_body"]
    pill = tip["en_title"] if r else f"Quick Fact #{tip['num']}"

    # big background number (always top-right)
    pn = ease_out(prog(t, 0.0, 0.6))
    put(d, (RIGHT + 20 * (1 - pn), 20), tip["num"], font(220, "Black"), GOLD,
        0.22 * pn * vis, "ra", rtl=False)

    # title (wraps to max 2 lines)
    tf, tlines, tlh = fit_lines(d, title, "ExtraBold", [74, 66, 58], TEXT_W, 2 * 74 * 1.45, 1.45)
    y = 270
    pt = ease_out(prog(t, 0.3, 0.6))
    for line in tlines:
        put(d, (edge - 60 * (1 - pt) * sgn + sx, y), line, tf, WHITE, pt * vis, anc, rtl=r)
        y += tlh
    y += 18

    # pill
    ph = ease_out(prog(t, 0.7, 0.6))
    for sz in (40, 36, 32, 28):
        ef = font(sz, "Bold")
        if d.textlength(pill, font=ef) <= TEXT_W - 50:
            break
    ew = d.textlength(pill, font=ef)
    if ph > 0.01:
        a_edge = edge + sx
        b_edge = a_edge - (ew + 50) * ph * sgn
        d.rounded_rectangle((min(a_edge, b_edge), y, max(a_edge, b_edge), y + 70), 16,
                            fill=GOLD + (int(255 * vis),))
        put(d, (a_edge - 25 * sgn, y + 35), pill, ef, BG,
            clamp((ph - 0.6) / 0.4) * vis, "rm" if r else "lm", rtl=False)
    y += 70 + 40

    # gold side bar spans the whole block
    bh = (900 - 270) * ease_out(prog(t, 0.15, 0.7)) * vis
    bx = RIGHT + 22 if r else LEFT - 30
    d.rectangle((bx, 280, bx + 8, 280 + bh), fill=GOLD + (255,))

    # body, auto-sized, line-by-line reveal
    bf, blines, blh = fit_lines(d, body, "Medium", [44, 41, 38, 35, 32], TEXT_W, 960 - y, 1.55)
    step = min(0.35, max(0.0, (dur - 3.0) * 0.6) / max(1, len(blines)))
    for i, line in enumerate(blines):
        pl = ease_out(prog(t, 1.3 + i * step, 0.6))
        put(d, (edge - 40 * (1 - pl) * sgn + sx, y + i * blh), line, bf, BODY, pl * vis, anc, rtl=r)


def scene_outro(img, d, t, data):
    p = ease_out(prog(t, 0.0, 0.8))
    lg = logo_sized(int(300 + 40 * p), p)
    img.alpha_composite(lg, ((W - lg.width) // 2, int(280 - 30 * (1 - p))))
    pc = ease_out(prog(t, 0.6, 0.7))
    y = 280 + lg.height + 50
    tx = TEXTS[LANG]
    put(d, (W / 2, y), tx["regards"], font(46, "Bold"), WHITE, pc, "ma", rtl=rtl())
    pc2 = ease_out(prog(t, 1.2, 0.7))
    put(d, (W / 2, y + 80), tx["cta"], font(40, "Bold"), GOLD, pc2, "ma", rtl=rtl())
    put(d, (W / 2, y + 150), tx["tags"], font(30, "Medium"), GREY, pc2, "ma", rtl=rtl())


VOICE_DIR = ROOT / "voice"
VOICE_LEAD = 0.5           # voice starts this long after a fact appears


def voice_len(num):
    p = VOICE_DIR / f"{num}.wav"
    if not p.exists():
        return None
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(p)])
    return float(out)


def tip_durations(video):
    durs = []
    for tp in video["tips"]:
        v = voice_len(tp["num"])
        durs.append(TIP if v is None else max(TIP, VOICE_LEAD + v + 1.2))
    return durs


def outro_len():
    v = voice_len("outro")
    return OUTRO if v is None else max(OUTRO, VOICE_LEAD + v + 1.5)


def total_time(video):
    return INTRO + sum(tip_durations(video)) + outro_len()


def render_frame(t, data, video):
    durs = tip_durations(video) if "_durs" not in video else video["_durs"]
    total = INTRO + sum(durs) + video.get("_outro", OUTRO)
    base = background(t)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # frame lines
    p = ease_out(prog(t, 0, 1.0))
    m, L = 48, int((W - 96) * p)
    d.line((W - m - L, m, W - m, m), fill=GOLD + (200,), width=3)
    d.line((m, H - m, m + L, H - m), fill=GOLD + (200,), width=3)

    tips_end = INTRO + sum(durs)
    if t < INTRO:
        scene_intro(d, t, data, video)
    elif t < tips_end:
        k, start = 0, INTRO
        while t >= start + durs[k]:
            start += durs[k]
            k += 1
        scene_tip(d, t - start, video["tips"][k], durs[k])
    else:
        scene_outro(img, d, t - tips_end, data)

    # fixed logo watermark (fades only when the big logo takes over in the outro)
    wm_a = 1 - ease_out(prog(t, tips_end, 0.4))
    if wm_a > 0.01:
        img.alpha_composite(WATERMARK if wm_a >= 0.99 else logo_sized(150, 0.9 * wm_a), (70, 70))

    d.rectangle((0, H - 8, int(W * clamp(t / total)), H), fill=GOLD + (255,))
    base.alpha_composite(img)
    return base.convert("RGB")


def render_video(data, video):
    OUT.mkdir(exist_ok=True)
    path = OUT / f"quick_fact_{video['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    video["_durs"] = tip_durations(video)   # cache: avoid ffprobe per frame
    video["_outro"] = outro_len()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(total_time(video) * FPS)):
        proc.stdin.write(render_frame(i / FPS, data, video).tobytes())
    proc.stdin.close()
    proc.wait()
    print("wrote", path, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", nargs="*")
    ap.add_argument("--preview")
    ap.add_argument("--lang", default="ar", choices=["ar", "en"])
    a = ap.parse_args()
    set_lang(a.lang)
    data = json.loads((ROOT / "tips.json").read_text(encoding="utf-8"))
    vids = data["videos"]
    if a.preview:
        v = next(v for v in vids if v["id"] == a.preview)
        v["_durs"] = tip_durations(v)
        v["_outro"] = outro_len()
        OUT.mkdir(exist_ok=True)
        ts = [1.8] + [INTRO + k * TIP + 5 for k in range(len(v["tips"]))] + [total_time(v) - 0.3]
        for t in ts:
            render_frame(t, data, v).save(OUT / f"preview_{v['id']}_{t:.1f}.png")
        return
    for v in vids:
        if a.id and v["id"] not in a.id:
            continue
        render_video(data, v)


if __name__ == "__main__":
    main()
