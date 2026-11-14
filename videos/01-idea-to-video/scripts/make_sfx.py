# Procedural SFX (pop / whoosh / soft impact) — free, no licence issues. Usage: python3 make_sfx.py <outdir>
import sys, wave, numpy as np
SR = 48000; rng = np.random.default_rng(7); out = sys.argv[1]

def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.89
    with wave.open(f"{out}/{name}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def lp(x, fc):  # time-varying one-pole lowpass, fc may be array
    fc = np.broadcast_to(fc, x.shape); a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a[i]) * x[i] + a[i] * s; y[i] = s
    return y

def t(d): return np.arange(int(SR * d)) / SR

def pop(f0, f1, d, bright):
    tt = t(d); f = f1 + (f0 - f1) * np.exp(-tt * 40); ph = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-tt * 900)) * np.exp(-tt * 28)
    click = lp(rng.standard_normal(len(tt)), 4000) * np.exp(-tt * 300) * bright
    return np.sin(ph) * env + click

def whoosh(d, fa, fb, peak=0.55):
    tt = t(d); n = rng.standard_normal(len(tt)); x = tt / d
    fc = fa * (fb / fa) ** np.sin(np.pi * x)          # sweep up then down
    band = lp(n, fc) - lp(n, fc * 0.35)
    env = np.where(x < peak, (x / peak) ** 2, ((1 - x) / (1 - peak)) ** 1.6)
    return band * env

def impact(d):
    tt = t(d); f = 48 + 70 * np.exp(-tt * 25); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 9) * (1 - np.exp(-tt * 600))
    thud = lp(rng.standard_normal(len(tt)), 600) * np.exp(-tt * 35) * 2.5
    return body + thud

save("pop", pop(950, 380, 0.25, 0.25))
save("pop_light", pop(1500, 700, 0.18, 0.15) * 0.6)
save("whoosh", whoosh(0.6, 500, 5000))
save("logo_swoosh", whoosh(0.9, 400, 7000, 0.7))
save("soft_impact", impact(0.6))
print("ok")
