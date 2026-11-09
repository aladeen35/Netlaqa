#!/usr/bin/env python3
"""Add background music to every rendered video: output/*.mp4 -> final/*.mp4

    python3 add_music.py              # music at 0.8 volume (no voice-over)
    python3 add_music.py --volume 0.15  # quieter, for use under a voice-over
"""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
MUSIC = ROOT / "assets/audio/background.m4a"


def duration(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(p)])
    return float(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=float, default=0.8)
    a = ap.parse_args()
    dst = ROOT / "final"
    dst.mkdir(exist_ok=True)
    for vid in sorted((ROOT / "output").glob("quick_fact_*.mp4")):
        d = duration(vid)
        af = (f"volume={a.volume},afade=t=in:st=0:d=0.6,"
              f"afade=t=out:st={max(d - 2.0, 0):.2f}:d=2.0")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(vid),
                        "-stream_loop", "-1", "-i", str(MUSIC),
                        "-filter:a", af, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                        "-t", f"{d:.3f}", "-movflags", "+faststart",
                        str(dst / vid.name)], check=True)
        print("wrote", dst / vid.name)


if __name__ == "__main__":
    main()
