"""Copy chosen candidates (selection.json: {"num": k}) into images/ and write credits."""
import json, shutil
from pathlib import Path
D = Path(__file__).parent
sel = json.loads((D / "selection.json").read_text())
meta = json.loads((D / "candidates/meta.json").read_text())
(D / "images").mkdir(exist_ok=True)
credits = {}
for num, k in sel.items():
    shutil.copy(D / f"candidates/{num}_{k}.jpg", D / f"images/{num}.jpg")
    m = next(x for x in meta[num] if x["k"] == k)
    credits[num] = {kk: m[kk] for kk in ("title", "creator", "license", "source", "page")}
(D / "images/credits.json").write_text(json.dumps(credits, indent=1, ensure_ascii=False))
print(len(sel), "images")
