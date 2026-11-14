# Mix VO + SFX cues (cache/cues.json from the page) → loudness-normalised track. Usage: python3 build_audio.py <vo.wav> <out.wav>
import json, subprocess, sys
vo, out = sys.argv[1], sys.argv[2]
cues = json.load(open("cache/cues.json"))
args, fl = ["ffmpeg", "-v", "error", "-y", "-i", vo], ["[0]aresample=48000,volume=1.0[v]"]
for n, c in enumerate(cues, 1):
    args += ["-i", f"assets/sfx/{c['name']}.wav"]
    d = int(c["t"] * 1000)
    fl.append(f"[{n}]aresample=48000,highpass=f=120,volume={c['gain'] * 0.32:.3f},adelay={d}[s{n}]")
mix = "[v]" + "".join(f"[s{n}]" for n in range(1, len(cues) + 1))
fl.append(f"{mix}amix=inputs={len(cues) + 1}:normalize=0,atrim=0:45,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
subprocess.run(args + ["-filter_complex", ";".join(fl), "-map", "[out]", "-ar", "48000", "-ac", "2", out], check=True)
print(len(cues), "cues mixed →", out)
