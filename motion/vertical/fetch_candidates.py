"""Search Openverse (CC0/PDM only) and download up to 6 candidate images per fact."""
import json, time, urllib.parse, urllib.request, sys
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw
D = Path(__file__).parent
Q = json.loads((D / "image_queries.json").read_text())
cand = D / "candidates"; cand.mkdir(exist_ok=True)
meta = {}
UA = {"User-Agent": "QuickFactVideos/1.0"}
only = sys.argv[1:]
for num, q in Q.items():
    if only and num not in only: continue
    url = ("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "license": "cc0,pdm", "page_size": 12}))
    res = None
    for attempt in range(4):
        try:
            res = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))["results"]
            break
        except Exception as e:
            print(num, "search failed", e, flush=True); time.sleep(10 * (attempt + 1))
    if res is None: continue
    meta[num] = []
    sheet = Image.new("RGB", (3 * 400, 2 * 300), (30, 30, 30)); k = 0
    for r in res:
        if k >= 6: break
        try:
            raw = urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=30).read()
            im = Image.open(BytesIO(raw)).convert("RGB")
        except Exception:
            continue
        if im.width < 800 or im.height < 500: continue
        im.thumbnail((2000, 2000))
        im.save(cand / f"{num}_{k}.jpg", quality=90)
        meta[num].append({"k": k, "id": r["id"], "title": r["title"], "license": r["license"],
                          "source": r["source"], "url": r["url"], "page": r.get("foreign_landing_url"),
                          "creator": r.get("creator")})
        th = im.copy(); th.thumbnail((400, 300))
        sheet.paste(th, ((k % 3) * 400, (k // 3) * 300))
        ImageDraw.Draw(sheet).text(((k % 3) * 400 + 8, (k // 3) * 300 + 8), str(k), fill=(255, 220, 0))
        k += 1
    sheet.save(cand / f"sheet_{num}.jpg", quality=80)
    print(num, q, k, flush=True)
    time.sleep(3)
old = json.loads((cand / "meta.json").read_text()) if (cand / "meta.json").exists() else {}
old.update(meta)
(cand / "meta.json").write_text(json.dumps(old, indent=1, ensure_ascii=False))
