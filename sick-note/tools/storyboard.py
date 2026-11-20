"""Storyboard sheet: frames + caption (shot, framing, duration, line). Usage: python storyboard.py out.jpg"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = [
 ('1.6',  '1  Full · static', '0.0–2.5s', 'Gus face-plants on the bed (boing). Nodd asleep standing.'),
 ('6.0',  '2  Two-shot · slow push', '2.5–8.9s', 'GUS: "Doctor, I feel completely exhausted…"'),
 ('10.3', '3  CU Nodd · hard cut', '8.9–10.8s', 'NODD: "Hmm. Let\'s scan you." Scanner out.'),
 ('12.8', '4  Insert screen · push', '10.8–13.3s', 'FATIGUE 87% SEVERE (sting on the beat)'),
 ('14.1', '5  Reaction CU Gus · jitter', '13.3–15.0s', 'GUS: "87%?!"'),
 ('15.8', '6a Whip pan → Nodd', '15.0–16.25s', 'He points the scanner at himself.'),
 ('18.5', '6b Insert screen · shake', '16.25–18.75s', '100→250→999→ERROR (machine-gun beeps)'),
 ('19.8', '7  Wide · rush out + shake', '18.75–21.25s', 'SIGNATURE: overload rips a portal to the sleep dimension'),
 ('22.6', '8  Two-shot · still push', '21.25–24.0s', 'COLD SILENCE. Nodd sips coffee from his IV.'),
 ('25.8', '9  MCU Nodd · static', '24.0–27.6s', 'NODD: "Honestly, my friend… you won\'t be able to keep up with me!"'),
 ('28.4', '10 Wide', '27.6–30.6s', 'He falls asleep backwards into the portal. Fwump.'),
 ('33.0', '11 Full · same as #1', '30.6–35.0s', 'Callback: Gus flops and sleeps. Title SICK NOTE.'),
]
cols, w = 4, 360; h = w * 1920 // 1080; cap = 92
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
rows = (len(S) + cols - 1) // cols
im = Image.new('RGB', (cols * w + (cols + 1) * 12, 70 + rows * (h + cap + 12)), (24, 20, 30)); d = ImageDraw.Draw(im)
d.text((14, 18), 'SICK NOTE — storyboard (Sci-Fi Sitcom Toon · 1080×1920 · 35 s)', fill=(255, 240, 200), font=F(26))
for k, (t, a, b, c) in enumerate(S):
    x = 12 + (k % cols) * (w + 12); y = 70 + (k // cols) * (h + cap + 12)
    fr = Image.open(os.path.join(HERE, 'stills', f'sb_{t}.jpg')).convert('RGB').resize((w, h)); im.paste(fr, (x, y))
    d.rectangle([x, y + h, x + w, y + h + cap], fill=(250, 244, 228))
    d.text((x + 8, y + h + 6), a, fill=(34, 23, 42), font=F(17)); d.text((x + w - 8, y + h + 6), b, fill=(120, 60, 30), font=F(15), anchor='ra')
    words, line, ly = c.split(), '', y + h + 32
    for wd in words:
        tr = (line + ' ' + wd).strip()
        if d.textlength(tr, font=F(14)) > w - 16: d.text((x + 8, ly), line, fill=(34, 23, 42), font=F(14)); ly += 19; line = wd
        else: line = tr
    d.text((x + 8, ly), line, fill=(34, 23, 42), font=F(14))
im.save(sys.argv[1], quality=90); print(sys.argv[1], im.size)
