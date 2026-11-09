#!/usr/bin/env python3
"""Mix audio into every rendered video: output/*.mp4 -> final/*.mp4

- Background music: assets/audio/background.m4a (looped, faded in/out).
- Voice-over: voice/<num>.wav (from voice.py), placed when each fact appears.
  When a video has voice-over the music drops to --duck volume.

    python3 add_music.py
    python3 add_music.py --volume 0.8 --duck 0.15
"""
import argparse
import json
import subprocess
from pathlib import Path

import render

ROOT = Path(__file__).parent
MUSIC = ROOT / "assets/audio/background.m4a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=float, default=0.8, help="music volume without voice")
    ap.add_argument("--duck", type=float, default=0.15, help="music volume under voice")
    a = ap.parse_args()
    data = json.loads((ROOT / "tips.json").read_text(encoding="utf-8"))
    dst = ROOT / "final"
    dst.mkdir(exist_ok=True)
    for video in data["videos"]:
        src = ROOT / "output" / f"quick_fact_{video['id']}.mp4"
        if not src.exists():
            continue
        durs = render.tip_durations(video)
        total = render.INTRO + sum(durs) + render.OUTRO
        voices, start = [], render.INTRO
        for tp, d in zip(video["tips"], durs):
            wav = render.VOICE_DIR / f"{tp['num']}.wav"
            if wav.exists():
                voices.append((wav, start + render.VOICE_LEAD))
            start += d
        vol = a.duck if voices else a.volume
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src),
               "-stream_loop", "-1", "-i", str(MUSIC)]
        for wav, _ in voices:
            cmd += ["-i", str(wav)]
        fc = [f"[1:a]volume={vol},afade=t=in:st=0:d=0.6,"
              f"afade=t=out:st={max(total - 2.0, 0):.2f}:d=2.0,atrim=0:{total:.3f}[m]"]
        labels = ["[m]"]
        for i, (_, off) in enumerate(voices):
            ms = int(off * 1000)
            fc.append(f"[{i + 2}:a]aresample=44100,pan=stereo|c0=c0|c1=c0,"
                      f"adelay={ms}|{ms},volume=1.6[v{i}]")
            labels.append(f"[v{i}]")
        fc.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.9[a]")
        cmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-t", f"{total:.3f}", "-movflags", "+faststart",
                str(dst / src.name)]
        subprocess.run(cmd, check=True)
        print("wrote", dst / src.name, "(voice)" if voices else "(music only)")


if __name__ == "__main__":
    main()
