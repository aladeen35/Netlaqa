"""Generate the narration for each scene with the cloned voice (XTTS-v2).
Run: COQUI_TOS_AGREED=1 /home/user/xtts-venv/bin/python voice_scenes.py"""
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
MOTION = HERE.parents[1]
sys.path.insert(0, str(MOTION))
import soundfile as sf, torch, torchaudio
def _load(path, *a, **k):
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return torch.from_numpy(data.T.copy()), sr
torchaudio.load = _load
from TTS.api import TTS
torch.set_num_threads(4)
s = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
out = HERE / "voice"; out.mkdir(exist_ok=True)
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
items = [(sc["id"], sc["say"]) for sc in s["scenes"]] + [("outro", "مع تحيات المهندس علاء الدين عمر.")]
only = sys.argv[1:]
for sid, text in items:
    if only and sid not in only: continue
    p = out / f"{sid}.wav"
    tts.tts_to_file(text=text, speaker_wav=str(MOTION / "assets/voice/my_voice.wav"), language="ar", file_path=str(p))
    print("wrote", p, flush=True)
