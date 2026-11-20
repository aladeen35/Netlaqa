"""SICK NOTE — synthesized score + procedural foley + voices → out/mix.wav (48 kHz stereo).
Everything is numpy synthesis; event times come from events.json (exported from main.js), voice times from main.js VO.
Usage: $LIB/.venv/bin/python mix.py"""
import json, os, re, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, lfilter, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']
SR = 48000; N = int(DUR * SR) + SR; BEAT = 60 / 96
rng = np.random.default_rng(7)
VO = {k: float(v) for k, v in re.findall(r"(\w+): ([\d.]+)", re.search(r"export const VO = \{([^}]*)\}", open(os.path.join(HERE, 'main.js')).read()).group(1))}
LINES = {l['id']: l for l in json.load(open(os.path.join(HERE, 'voice/lines.json')))}

def tt(d): return np.arange(int(round(d * SR))) / SR
def mf(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, min(f, SR * .45), 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(round(d * SR)))
def env(n, a=.005, r=.1):
    i = np.arange(n); A = max(int(a * SR), 1); R = max(int(r * SR), 1)
    return np.minimum(np.minimum(i / A, 1), np.clip((n - i) / R, 0, 1))
def expd(n, tau): return np.exp(-np.arange(n) / SR / tau)
def osc_f(f):   # phase from a frequency array
    return np.cumsum(f) / SR

class Bus:
    def __init__(s): s.b = np.zeros((N, 2))
    def add(s, x, at, g=1., pan=0.):
        st = int(round(at * SR))
        if x.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414; x = np.stack([x * l, x * r], 1)
        if st < 0: x = x[-st:]; st = 0
        e = min(N, st + len(x))
        if e > st: s.b[st:e] += x[:e - st] * g
    def cut(s, t0, t1, fade=.006):
        a, b = int(t0 * SR), int(t1 * SR); f = int(fade * SR); s.b[a:b] = 0
        if a - f > 0: s.b[a - f:a] *= np.linspace(1, 0, f)[:, None]
MUS, FX, VOX, AMB = Bus(), Bus(), Bus(), Bus()

# ———————— instruments ————————
def theremin(notes, v=1., bright=.14):
    """notes [(t, dur, midi)], legato with ~70 ms portamento and delayed vibrato"""
    t0 = notes[0][0]; t1 = max(t + d for t, d, _ in notes) + .3; n = int((t1 - t0) * SR)
    target = np.full(n, float(notes[0][2])); amp = np.zeros(n); vib = np.zeros(n)
    for t, d, m in notes:
        a, b = int((t - t0) * SR), int((t + d - t0) * SR); target[a:] = m
        e = env(b - a + int(.15 * SR), .04, .15); amp[a:a + len(e)] = np.maximum(amp[a:a + len(e)], e[:n - a])
        vv = np.clip((np.arange(n - a) / SR - .15) / .25, 0, 1); vib[a:] = vv
    k = 1 - np.exp(-1 / (.07 * SR)); mid = lfilter([k], [1, -(1 - k)], target, zi=[target[0] * (1 - k)])[0]
    tq = np.arange(n) / SR; mid = mid + vib * .3 * np.sin(2 * np.pi * 5.6 * tq)
    ph = osc_f(mf(mid)) * 2 * np.pi
    x = np.sin(ph) + bright * np.sin(2 * ph) + bright * .5 * np.sin(3 * ph)
    return t0, x * amp * .3 * v
def spring(x, mix=.22):
    ir = np.zeros(int(.9 * SR)); idx = (np.array([.031, .047, .062, .089, .113, .151, .19, .23]) * SR).astype(int)
    ir[idx] = [.6, .5, .45, .35, .3, .25, .18, .12]; ir = ir * np.exp(-np.arange(len(ir)) / SR / .35) + noise(.9) * .01 * np.exp(-np.arange(len(ir)) / SR / .25)
    w = fftconvolve(x, ir)[:len(x)]; return x * (1 - mix) + w * mix
def bass(m, d, v=1.):
    n = int(d * SR); f = mf(m); tq = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * f * tq)) * .4 + np.sin(2 * np.pi * f * tq) + .35 * np.sin(4 * np.pi * f * tq)
    return lp(x, 900) * env(n, .005, .06) * expd(n, .5) * .35 * v
def sqnote(m, d, v=1., w=.25):
    n = int(d * SR); ph = mf(m) * np.arange(n) / SR
    return lp(np.where(ph % 1 < w, 1., -1.), 3500) * env(n, .002, .03) * expd(n, .12) * .08 * v
def kick(v=1.):
    n = int(.3 * SR); tq = np.arange(n) / SR; f = 50 + 110 * np.exp(-tq * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * expd(n, .12) * .7 * v
def snare(v=1.):
    n = int(.2 * SR); return (bp(noise(.2), 1500, 7000) * .5 + np.sin(2 * np.pi * 190 * np.arange(n) / SR) * .3) * expd(n, .06) * .5 * v
def hat(v=1.):
    n = int(.06 * SR); x = bp(noise(.06), 6000, 11000) + .3 * np.sin(2 * np.pi * 7400 * np.arange(n) / SR + 3 * np.sin(2 * np.pi * 10300 * np.arange(n) / SR))
    return x * expd(n, .015) * .18 * v
def toy(m, d=.6, v=1.):
    n = int(d * SR); tq = np.arange(n) / SR; f = mf(m)
    x = np.sin(2 * np.pi * f * tq) + .5 * np.sin(2 * np.pi * f * 3.98 * tq) * expd(n, .05) + .2 * np.sin(2 * np.pi * f * 2 * tq)
    return x * expd(n, .35) * env(n, .002, .05) * .16 * v
def strings_trem(m0, m1, t0, t1, v=1.):
    n = int((t1 - t0) * SR); tq = np.arange(n) / SR; u = tq / (t1 - t0)
    out = np.zeros(n)
    for dm in (0, 3, 7):
        f = mf(m0 + dm + (m1 - m0) * u); ph = np.cumsum(f) / SR
        out += (2 * (ph % 1) - 1) * .3
    trem = .55 + .45 * np.sign(np.sin(2 * np.pi * 12 * tq))
    return t0, lp(out, 2600) * trem * np.clip(u * 1.2, .15, 1) * env(n, .05, .02) * .12 * v

# ———————— score ————————
b = BEAT; bar = 4 * b
A0 = 0.0
# A: complaint (0 – 8.9): nervous theme on theremin, bass, arp, light drums
theme = [(0, 1, 'A4'), (1, .5, 'C5'), (1.5, .5, 'B4'), (2, 1, 'Bb4'), (3, 1, 'A4'), (4, 1.5, 'E4'), (5.5, .5, 'F4'), (6, 1, 'E4'), (7, 1, 'Eb4')]
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
def M(s): return 12 * (int(s[-1]) + 1) + NOTE[s[:-1]]
t0, x = theremin([(A0 + bt * b, d * b * .95, M(n)) for bt, d, n in theme], v=1.0)
MUS.add(spring(x), t0, .9, -.15)
bassline = ['A2', 'A2', 'F2', 'E2']
for k in range(int(8.9 / bar) + 1):
    for j in range(4):
        tb = k * bar + j * b
        if tb >= 8.9: break
        MUS.add(bass(M(bassline[k % 4]) if j % 2 == 0 else M(bassline[k % 4]) + 12, b * .9), tb, .9)
        MUS.add(kick(.8), tb, .7) if j in (0, 2) else MUS.add(snare(.7), tb, .6)
        for h in range(2): MUS.add(hat(.8), tb + h * b / 2, .7, .3)
arpN = [M('A4'), M('C5'), M('E5'), M('C5')]
for k in range(int(15.0 / (b / 4))):
    tb = k * b / 4
    if 0 <= tb < 15.0: MUS.add(sqnote(arpN[k % 4] + (-4 if (tb // bar) % 4 == 2 else 0), b / 4), tb, .8 if tb > 8.9 else .55, .25)
# B: scan (8.9 – 15): pedal bass, ticking hats
for k in range(int((15.0 - 8.9) / (b / 2))):
    tb = 8.9 + k * b / 2
    MUS.add(hat(1.0), tb, .8, -.3)
    if k % 2 == 0: MUS.add(bass(M('A1') + 12, b * .45, .8), tb, .8)
# sting on 87 %
t0, x = theremin([(12.5, .5, M('Bb4')), (12.95, .7, M('A4'))], v=1.2); MUS.add(spring(x), t0, 1.0)
MUS.add(kick(1.), 12.5, .9); MUS.add(snare(1.), 12.5, .6)
# C: overload (15 – 18.75): rising tremolo strings + accelerating drum roll
t0, x = strings_trem(M('A3'), M('E4'), 15.0, 18.75, 1.3); MUS.add(x, t0, 1.0)
tr = 15.6; gap = .3
while tr < 18.7: MUS.add(snare(.5 + (tr - 15.6) / 6), tr, .5); tr += gap; gap = max(.045, gap * .88)
# D: portal (18.75 – 21.25): full theme stab
t0, x = theremin([(18.75, .6, M('A5')), (19.35, .3, M('C6')), (19.65, .3, M('B5')), (19.95, .6, M('Bb5')), (20.55, .6, M('A5'))], v=1.1, bright=.2)
MUS.add(spring(x, .3), t0, 1.0)
for k in range(4):
    tb = 18.75 + k * b
    MUS.add(kick(1.), tb, .8); MUS.add(bass(M('A2'), b * .9, 1.1), tb, 1.0); MUS.add(hat(1.), tb + b / 2, .7)
    for j in range(4): MUS.add(sqnote(arpN[j] + 12, b / 4), tb + j * b / 4, .6)
MUS.cut(21.25, 24.0)                     # silence is the punchline (reverb tails included)
# E: single theremin note under "me!", then slide whistle as he falls
t0, x = theremin([(VO['d1'] + 2.85, 1.0, M('E5'))], v=.8); MUS.add(spring(x), t0, .8)
n = int(.8 * SR); f = np.linspace(1700, 500, n) ** 1; MUS.add(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .02, .1) * .12, 27.8, 1.0)
MUS.cut(29.5, 30.55, .05)
# F: lullaby (30.6 – 35): toy piano + soft theremin, half speed
lb = BEAT * 1.4
lull = [(0, 'E5'), (1, 'C5'), (2, 'D5'), (3, 'A4'), (4, 'C5'), (5, 'B4'), (6, 'A4')]
for k, nn in lull: MUS.add(toy(M(nn), 1.0), 30.6 + k * lb, 1.0, .2); MUS.add(toy(M(nn) - 24, 1.2, .6), 30.6 + k * lb, .7, -.2)
t0, x = theremin([(30.6 + k * lb, lb * .95, M(nn) - 12) for k, nn in lull[:5]], v=.45); MUS.add(spring(x, .35), t0, .7)

# ———————— foley ————————
def boing(v=1.):
    n = int(.6 * SR); tq = np.arange(n) / SR; f = 180 + 140 * np.exp(-tq * 6) * (1 + .5 * np.sin(2 * np.pi * 14 * tq))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * expd(n, .2) * .5 * v
def thud(v=1.): n = int(.25 * SR); return (lp(noise(.25), 300) * .6 + np.sin(2 * np.pi * 70 * np.arange(n) / SR)) * expd(n, .06) * .5 * v
def whoosh(d=.35, v=1., up=True):
    x = noise(d); n = len(x); u = np.arange(n) / n; fc = 400 + 3000 * (u if up else 1 - u)
    y = np.zeros(n)
    for k in range(0, n, 480): y[k:k + 480] = bp(x[k:k + 480], max(150, fc[k] * .6), min(16000, fc[k] * 1.6))
    return y * np.sin(np.pi * u) * .5 * v
def blip(v=1.): n = int(.09 * SR); f = np.linspace(1100, 1900, n); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .03) * .22 * v
def beep(d=.12, f=1600, v=1.): n = int(d * SR); ph = f * np.arange(n) / SR; return lp(np.where(ph % 1 < .5, 1., -1.), 5000) * env(n, .002, .01) * .12 * v
def hum(d, f=300, v=1.): n = int(d * SR); tq = np.arange(n) / SR; return (np.sin(2 * np.pi * f * tq) + .4 * np.sin(4 * np.pi * f * tq)) * (.7 + .3 * np.sin(2 * np.pi * 9 * tq)) * env(n, .05, .1) * .07 * v
def slurp(v=1.):
    d = .9; x = noise(d); n = len(x); y = np.zeros(n); tq = np.arange(n) / SR
    for k in range(0, n, 480): fc = 700 + 500 * np.sin(2 * np.pi * 7 * tq[k]); y[k:k + 480] = bp(x[k:k + 480], fc * .7, fc * 1.4, 2)
    gate = (np.sin(2 * np.pi * 11 * tq) > -.2).astype(float); return y * gate * env(n, .05, .2) * .5 * v
def snore(v=1., d=1.4):
    n = int(d * SR); tq = np.arange(n) / SR; u = tq / d
    buzz = np.sign(np.sin(2 * np.pi * np.cumsum(55 + 20 * np.sin(np.pi * u)) / SR)) * .5
    x = lp(buzz, 600) * .6 + bp(noise(d), 300, 1500) * .3
    return x * np.sin(np.pi * u) ** 1.5 * .35 * v
def explode(v=1.):
    d = 1.6; n = int(d * SR); tq = np.arange(n) / SR
    return (lp(noise(d), 1200) * expd(n, .35) * .8 + np.sin(2 * np.pi * np.cumsum(70 * np.exp(-tq * 2) + 30) / SR) * expd(n, .5)) * .6 * v
def portal_open(v=1.):
    d = 1.4; n = int(d * SR); tq = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-tq * 3) + 40) / SR) * expd(n, .4)
    swirl = np.sin(2 * np.pi * np.cumsum(300 + 900 * tq / d + 120 * np.sin(2 * np.pi * 6 * tq)) / SR) * np.clip(tq / d, 0, 1) * .3
    return (sub * .8 + whoosh(d, .8, False) + swirl) * env(n, .005, .3) * .6 * v
def portal_hum(d):
    n = int(d * SR); tq = np.arange(n) / SR
    x = np.sin(2 * np.pi * 110 * tq + 2 * np.sin(2 * np.pi * .7 * tq)) + .4 * np.sin(2 * np.pi * 165.5 * tq) + .2 * bp(noise(d), 400, 900)
    return x * env(n, .3, .2) * .05
def fwump(v=1.):
    n = int(.5 * SR); tq = np.arange(n) / SR
    return (np.sin(2 * np.pi * np.cumsum(160 * np.exp(-tq * 8) + 50) / SR) * expd(n, .12) + lp(noise(.5), 500) * expd(n, .08)) * .6 * v
def clickbeep(v=1.):
    c = hp(noise(.01), 2000) * .4; return np.concatenate([c, np.zeros(int(.05 * SR)), beep(.08, 2100, 1.)]) * v
def typing(t0, t1):
    t = t0
    while t < t1: FX.add(hp(noise(.008), 3000) * expd(int(.008 * SR) or 1, .002)[:len(noise(.008))] * .2, t, .6, .4); t += .05 + rng.random() * .04

for e in EV:
    t, ty = e['t'], e['type']
    if ty == 'door': FX.add(whoosh(.5, .6), t, .7, .7); [FX.add(thud(.35), t + .3 + k * .32, .5, .5) for k in range(3)]
    elif ty == 'boing': FX.add(boing(), t, .8); FX.add(thud(.8), t, .7)
    elif ty == 'blip': FX.add(blip(), t, .7)
    elif ty == 'clickbeep': FX.add(clickbeep(), t, .8, .2)
    elif ty == 'beam': FX.add(hum(1.5, 300), t, 1.0)
    elif ty == 'sting': FX.add(beep(.25, 900, 1.), t, .8)
    elif ty == 'whoosh': FX.add(whoosh(.3, 1.), t, .9, -.4)
    elif ty == 'beep': FX.add(beep(.1, 1600 + (t - 16) * 300), t, 1.0)
    elif ty == 'error': FX.add(beep(.35, 180, 2.), t, 1.0); FX.add(hp(noise(.15), 3000) * expd(int(.15 * SR), .04) * .5, t, .7)
    elif ty == 'portalOpen': FX.add(explode(), t, 1.0); FX.add(portal_open(), t, 1.0)
    elif ty == 'slurp': FX.add(slurp(), t, .8, -.3)
    elif ty == 'slide': pass                          # slide whistle lives in the score
    elif ty == 'snore': FX.add(snore(1., 1.4), t, .9)
    elif ty == 'fwump': FX.add(fwump(), t, 1.0)
typing(11.0, 12.4); typing(16.3, 18.3)
for tb in (2.0,): FX.add(hp(noise(.03), 1500) * .3, tb + .05, .5)            # paper sheet crinkle
FX.add(thud(.6), 2.05, .6, .3)                                                  # briefcase
FX.add(np.concatenate([snore(.6, 1.2), np.zeros(int(.5 * SR)), snore(.6, 1.2)]), .1, .5, -.5)  # Nodd snoring standing up (0–2.5)
# ambience: fluorescent hum all film; portal hum while open (J-cut 0.3 s before the explosion)
tq = np.arange(N) / SR; fl = (np.sin(2 * np.pi * 120 * tq) + .5 * np.sin(2 * np.pi * 240 * tq) + .3 * np.sin(2 * np.pi * 360 * tq)) * .012
AMB.add(fl + hp(rng.standard_normal(N), 4000) * .002, 0, 1.0)
AMB.add(portal_hum(29.5 - 18.45), 18.45, 1.0)
for k in range(int(DUR)): AMB.add(hp(noise(.004), 3000) * .05, k + .5, .5, .6)   # clock tick

# ———————— voices ————————
def compress(x, thr=.2, ratio=3.5):
    e = np.abs(x); k = 1 - np.exp(-1 / (.01 * SR)); env_ = lfilter([k], [1, -(1 - k)], e)
    g = np.where(env_ > thr, (thr + (env_ - thr) / ratio) / (env_ + 1e-9), 1.); return x * g
duck = np.ones(N)
for vid, t0 in VO.items():
    y, sr = sf.read(os.path.join(HERE, 'voice/out', vid + '.wav'))
    y = compress(y); y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * .09
    ref = np.zeros(int(.03 * SR)); ref[0] = 1; ref[int(.011 * SR)] = .18; ref[int(.023 * SR)] = .1   # small-room early reflections
    y = fftconvolve(y, ref)[:len(y)]
    pan = -.12 if LINES[vid]['who'] == 'NODD' else .12
    VOX.add(y, t0, 1.0, pan)
    a, b2 = int((t0 - .15) * SR), int((t0 + len(y) / SR + .2) * SR)
    duck[a:b2] = 10 ** (-7 / 20)
k = 1 - np.exp(-1 / (.06 * SR)); duck = lfilter([k], [1, -(1 - k)], duck, zi=[duck[0] * (1 - k)])[0]

mus = MUS.b * duck[:, None] * .55
mix = mus + FX.b * .8 + VOX.b * 1.25 + AMB.b
mix = hp(mix.T, 35).T
peak = np.abs(mix).max(); mix = mix / peak * .89 if peak > .89 else mix
mix = mix[:int(DUR * SR)]
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out/mix.wav'), mix.astype(np.float32), SR)
for name, bus in (('music', mus), ('fx', FX.b), ('voice', VOX.b), ('amb', AMB.b)):
    r = np.sqrt(np.mean(bus ** 2)) + 1e-12; print(f'{name:6s} rms {20 * np.log10(r):6.1f} dB')
print('mix ->', os.path.join(HERE, 'out/mix.wav'), round(len(mix) / SR, 2), 's')
