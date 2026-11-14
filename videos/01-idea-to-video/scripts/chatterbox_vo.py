# Local VO with Chatterbox Multilingual (CPU). Usage: python chatterbox_vo.py [S1 S2 ...]
import json, re, sys, time, pathlib
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

root = pathlib.Path(__file__).resolve().parent.parent
cfg = json.loads((root / "plan/vo_segments.json").read_text())
ids = sys.argv[1:]
out = root / "assets/vo/chatterbox"; out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
print(f"model loaded in {time.time()-t0:.0f}s", flush=True)
for seg in cfg["segments"]:
    if ids and seg["id"] not in ids: continue
    text = re.sub(r"\[[^\]]*\]\s*", "", seg["text"]).replace("\n", " ").replace("—", "،")
    t = time.time()
    wav = model.generate(text, language_id="ar", exaggeration=0.55, cfg_weight=0.5)
    ta.save(str(out / f"{seg['id']}.wav"), wav, model.sr)
    print(f"{seg['id']}: {wav.shape[-1]/model.sr:.1f}s audio in {time.time()-t:.0f}s", flush=True)
