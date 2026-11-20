"""Master out/mix.wav to -14 LUFS integrated (ITU-R BS.1770 K-weighting, gated) with a 4x-oversampled
true-peak limiter at -1.2 dBTP → out/master.wav. Used instead of mux.sh's loudnorm when only ffmpeg 6 is present."""
import sys, numpy as np, soundfile as sf, soxr
from scipy.signal import lfilter

def kweight(x, sr):
    # BS.1770 pre-filter (high shelf) + RLB high-pass, coefficients for 48 kHz
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
def lufs(x, sr):
    y = kweight(x, sr); blk, hop = int(.4 * sr), int(.1 * sr)
    z = np.array([(y[i:i + blk] ** 2).mean(0).sum() for i in range(0, len(y) - blk, hop)])
    l = -0.691 + 10 * np.log10(z + 1e-12); z = z[l > -70]
    rel = -0.691 + 10 * np.log10(z.mean()) - 10; l2 = -0.691 + 10 * np.log10(z + 1e-12)
    return -0.691 + 10 * np.log10(z[l2 > rel].mean())
def true_peak(x, sr): return np.abs(soxr.resample(x, sr, sr * 4)).max()
def limit(x, sr, ceil):
    up = soxr.resample(x, sr, sr * 4); a = np.abs(up).max(1)
    g = np.minimum(1, ceil / (a + 1e-12)); w = int(.002 * sr * 4)
    g = -np.convolve(-g, np.ones(1), 'same'); from scipy.ndimage import minimum_filter1d, uniform_filter1d
    g = uniform_filter1d(minimum_filter1d(g, 2 * w + 1), 2 * w + 1)
    rel = np.exp(-1 / (.08 * sr * 4)); out = np.empty_like(g); cur = 1.0
    for i, v in enumerate(g): cur = v if v < cur else v + (cur - v) * rel; out[i] = cur
    return soxr.resample(up * out[:, None], sr * 4, sr)[:len(x)]

x, sr = sf.read(sys.argv[1]); target = -14.0; ceil = 10 ** (-1.6 / 20)
for it in range(4):
    L = lufs(x, sr); x = x * 10 ** ((target - L) / 20)
    if true_peak(x, sr) > ceil: x = limit(x, sr, ceil * .97)
L = lufs(x, sr); tp = 20 * np.log10(true_peak(x, sr))
sf.write(sys.argv[2], x.astype(np.float32), sr, subtype='FLOAT')
print(f'integrated {L:.2f} LUFS, true peak {tp:.2f} dBTP -> {sys.argv[2]}')
