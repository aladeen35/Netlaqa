"""Copy chosen candidates (selection.json: {"num": k}) into images/ and write credits."""
import json, shutil
from pathlib import Path
D = Path(__file__).parent
sel = json.loads((D / "selection.json").read_text())
meta = json.loads((D / "candidates/meta.json").read_text())
(D / "images").mkdir(exist_ok=True)
credits = {}
for num, k in sel.items():
    src = num                       # "NN:k" reuses a candidate found for another fact
    if isinstance(k, str):
        src, k = k.split(":")[0], int(k.split(":")[1])
    shutil.copy(D / f"candidates/{src}_{k}.jpg", D / f"images/{num}.jpg")
    m = next(x for x in meta[src] if x["k"] == k)
    credits[num] = {kk: m[kk] for kk in ("title", "creator", "license", "source", "page")}
(D / "images/credits.json").write_text(json.dumps(credits, indent=1, ensure_ascii=False))
print(len(sel), "images")
