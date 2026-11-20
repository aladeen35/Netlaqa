"""Write subtitles_ar.srt and subtitles_en.srt from voice/lines.json + VO times in main.js (same timing as the burned-in captions)."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); LIB = os.environ['LIB']
VO = {k: float(v) for k, v in re.findall(r"(\w+): ([\d.]+)", re.search(r"export const VO = \{([^}]*)\}", open(os.path.join(HERE, 'main.js')).read()).group(1))}
L = {l['id']: l for l in json.load(open(os.path.join(HERE, 'voice/lines.json')))}; D = json.load(open(os.path.join(HERE, 'voice/out/dur.json')))
for lang, key in (('ar', 'ar'), ('en', 'sub')):
    cues = [{'t0': t, 't1': t + max(1.8, D[i] + .6), 'text': L[i].get(key) or L[i]['text']} for i, t in VO.items()]
    p = os.path.join(HERE, 'out', f'cues_{lang}.json'); json.dump(cues, open(p, 'w'), ensure_ascii=False)
    subprocess.run([os.path.join(LIB, '.venv/bin/python'), os.path.join(LIB, 'core/render/srt.py'), p, os.path.join(HERE, f'subtitles_{lang}.srt')], check=True)
