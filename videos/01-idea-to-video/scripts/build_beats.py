# Lock the timeline to the real VO: lay segments out, get word timestamps, write src/data.js + plan/beats.json + the VO track.
# Usage: python3 scripts/build_beats.py <vo_dir> <out_vo_wav>
import json, subprocess, sys, pathlib, numpy as np
from faster_whisper import WhisperModel
root = pathlib.Path(__file__).resolve().parent.parent
vo_dir, out_wav = pathlib.Path(sys.argv[1]), sys.argv[2]
ids = [f"S{i}" for i in range(1, 8)]
def load(p):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout, np.float32)
def bounds(a, thr=0.01):  # speech bounds in seconds (strip leading/trailing silence)
    idx = np.where(np.abs(a) > thr)[0]
    return (max(0, idx[0] - 800) / 16000, min(len(a), idx[-1] + 1600) / 16000) if len(idx) else (0, len(a) / 16000)
raw = {i: load(vo_dir / f"{i}.wav") for i in ids}
cut = {i: bounds(raw[i]) for i in ids}
audio = {i: raw[i][int(cut[i][0] * 16000): int(cut[i][1] * 16000)] for i in ids}
dur = {i: len(audio[i]) / 16000 for i in ids}
START, CTA_END, gaps = 1.95, 43.4, {"S2": 0.45, "S3": 0.6, "S4": 0.6, "S5": 0.6, "S6": 0.6, "S7": 0.75}
total = START + sum(dur.values()) + sum(gaps.values())
if total > CTA_END:
    k = max(0.3, 1 - (total - CTA_END) / sum(gaps.values())); gaps = {a: b * k for a, b in gaps.items()}
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
beats, t = {}, START
for i in ids:
    t += gaps.get(i, 0)
    segs, _ = m.transcribe(audio[i], language="ar", word_timestamps=True)
    words = [{"w": w.word.strip(), "s": round(t + w.start, 3), "e": round(t + w.end, 3)} for s in segs for w in s.words]
    beats[i] = {"start": round(t, 3), "end": round(t + dur[i], 3), "words": words}
    print(f"{i} {t:6.2f}–{t + dur[i]:6.2f}  {' '.join(w['w'] for w in words)}")
    t += dur[i]
(root / "plan/beats.json").write_text(json.dumps(beats, ensure_ascii=False, indent=1))
(root / "src/data.js").write_text("window.BEATS = " + json.dumps(beats, ensure_ascii=False) + ";\n")
# VO track: original-quality segments, trimmed and placed at their beats, 48 kHz, 45 s
args, fl = ["ffmpeg", "-v", "error", "-y"], []
for n, i in enumerate(ids):
    args += ["-i", str(vo_dir / f"{i}.wav")]
    a, b = cut[i]; d = int(beats[i]["start"] * 1000)
    fl.append(f"[{n}]aresample=48000,atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,adelay={d}|{d}[a{n}]")
fl.append("".join(f"[a{n}]" for n in range(len(ids))) + f"amix=inputs={len(ids)}:normalize=0,apad,atrim=0:45[out]")
subprocess.run(args + ["-filter_complex", ";".join(fl), "-map", "[out]", "-ac", "1", out_wav], check=True)
print("VO track →", out_wav)
