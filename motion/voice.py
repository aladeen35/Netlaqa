#!/usr/bin/env python3
"""Generate a voice-over for every fact with XTTS-v2, cloned from assets/voice/my_voice.wav.

Run with the XTTS venv:  /home/user/xtts-venv/bin/python voice.py [--only 01 02]
Writes voice/<num>.wav (skips files that already exist; use --force to redo).
Spoken text comes from content/speech.json when present, otherwise title + body
with Latin parentheticals removed.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SPEAKER = ROOT / "assets/voice/my_voice.wav"
OUT = ROOT / "voice"


def spoken(tip, overrides):
    if tip["num"] in overrides:
        return overrides[tip["num"]]
    txt = f'{tip["title"]}. {tip["body"]}'
    txt = re.sub(r"\s*\([A-Za-z0-9 .,'-]+\)", "", txt)
    return txt.replace("←", "،").replace("«", "").replace("»", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    data = json.loads((ROOT / "tips.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "content/speech.json").read_text(encoding="utf-8"))
    tips = [t for v in data["videos"] for t in v["tips"]]
    todo = [t for t in tips if (not a.only or t["num"] in a.only)
            and (a.force or not (OUT / f'{t["num"]}.wav').exists())]
    if not todo:
        print("nothing to do")
        return
    import torch
    from TTS.api import TTS
    torch.set_num_threads(4)
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    OUT.mkdir(exist_ok=True)
    for t in todo:
        path = OUT / f'{t["num"]}.wav'
        tts.tts_to_file(text=spoken(t, overrides), speaker_wav=str(SPEAKER),
                        language="ar", file_path=str(path))
        print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
