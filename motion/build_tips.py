#!/usr/bin/env python3
"""Parse content/quick_facts.md into tips.json (2 facts per video)."""
import json, re
from pathlib import Path

ROOT = Path(__file__).parent
md = (ROOT / "content/quick_facts.md").read_text(encoding="utf-8")
section = md.split("## ثانياً")[0]
facts = []
for num, block in re.findall(r"### #(\d+)[^\n]*\n+```\n(.*?)```", section, re.S):
    parts = [p.strip() for p in block.strip().split("\n\n")]
    # parts: [ar header+title, ar body, en header+title, en body, hashtags]
    ar_title = parts[0].split("\n", 1)[1].strip()
    en_title = parts[2].split("\n", 1)[1].strip()
    facts.append({"num": num, "title": ar_title, "en_title": en_title,
                  "body": parts[1], "en_body": parts[3]})

videos = []
for i in range(0, len(facts), 2):
    pair = facts[i:i + 2]
    vid = "-".join(f["num"] for f in pair)
    videos.append({"id": vid, "tips": pair})

data = {"series_title": "معلومة على السريع", "series_en": "Quick Fact",
        "cta": "تابعني على LinkedIn للمزيد", "videos": videos}
(ROOT / "tips.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(facts), "facts ->", len(videos), "videos")
