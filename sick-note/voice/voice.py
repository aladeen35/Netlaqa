"""Voice post-processing: voice/raw/<id>.wav (core/tts/tts.py) → voice/out/<id>.wav (48 kHz, per character)
+ voice/out/dur.json + voice/out/lips.json (mouth openness o and brightness b per 1/24 s).
NODD: deadpan, slight saturation + 180 Hz bump (gravel). GUS: presence boost."""
import json, os, numpy as np, soundfile as sf, soxr
from scipy.signal import lfilter, stft

HERE = os.path.dirname(os.path.abspath(__file__)); SR = 48000
L = json.load(open(os.path.join(HERE, 'lines.json')))
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

def peq(x, f, gain_db, q=1.0):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A]); a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return lfilter(b / a[0], a / a[0], x)

dur, lips = {}, {}
for l in L:
    y, sr = sf.read(os.path.join(HERE, 'raw', l['id'] + '.wav'))
    if y.ndim > 1: y = y.mean(1)
    y = soxr.resample(y, sr, SR)
    y = y / (np.abs(y).max() + 1e-9) * .9
    if l['who'] == 'NODD':
        sat = np.tanh(y * 2.4) / np.tanh(2.4); y = .72 * y + .28 * sat
        y = peq(y, 180, 2.5, .8); y = peq(y, 2800, -1.5, 1.0)
    else:
        y = peq(y, 3200, 2.5, .9)
    y = y / (np.abs(y).max() + 1e-9) * .9
    sf.write(os.path.join(OUT, l['id'] + '.wav'), y.astype(np.float32), SR)
    dur[l['id']] = round(len(y) / SR, 3)
    hop = SR // 24
    f, t, Z = stft(y, fs=SR, nperseg=2400, noverlap=2400 - hop, nfft=4096, boundary='even', padded=True)
    S = np.abs(Z)
    rms = np.sqrt((S ** 2).mean(0)); p = np.percentile(rms, 95) + 1e-9
    cen = (S * f[:, None]).sum(0) / (S.sum(0) + 1e-9)
    n = int(np.ceil(len(y) / hop))
    o = [round(float(np.clip((rms[i] / p - .1) / .8, 0, 1)), 2) for i in range(min(n, len(rms)))]
    b = [round(float(np.clip((cen[i] - 1200) / 2600, 0, 1)), 2) for i in range(min(n, len(cen)))]
    lips[l['id']] = {'o': o, 'b': b}
    print(l['id'], dur[l['id']])
json.dump(dur, open(os.path.join(OUT, 'dur.json'), 'w'), indent=0)
json.dump(lips, open(os.path.join(OUT, 'lips.json'), 'w'))
