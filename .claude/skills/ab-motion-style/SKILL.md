---
name: ab-motion-style
description: Eng. Alaeldeen Omar's motion-graphics house style and cloned-voice workflow. Use whenever asked to make a motion graphic, explainer video, Quick Fact (معلومة على السريع) video, TikTok/Reels/Shorts/LinkedIn video, or a voice-over "بصوتي", or to explain a video/post/idea "بأسلوبي". Covers visual identity (dark + gold, AB logo, particle builds, QC cursor), layouts (1080x1920 and 1080x1080), Arabic/English text rendering, the XTTS-v2 cloned-voice pipeline, music mixing, and the render scripts in motion/.
---

# AB Motion Style — أسلوب الموشن جرافيك وصوت م. علاء الدين عمر

Everything lives in `motion/` of this repo. Reuse the code; do not start from scratch.

| What | Where |
|---|---|
| Square Quick Fact (LinkedIn 1080×1080) | `motion/render.py`, `motion/add_music.py`, `motion/run_all.sh` |
| Vertical Quick Fact (TikTok/Reels/Shorts 1080×1920) | `motion/vertical/render_vertical.py`, `motion/vertical/mix.py`, `motion/vertical/run_vertical.sh` |
| Explainer template (one idea, several scenes, voice-driven) | `motion/explainers/allergen_labelling/` — copy this folder for a new topic |
| Voice generation (cloned voice) | `motion/voice.py` (facts), `explainers/*/voice_scenes.py` (scenes) |
| Content | `motion/content/quick_facts.md` → `python3 motion/build_tips.py` → `motion/tips.json`; spoken overrides in `motion/content/speech.json` |
| Assets | `motion/assets/logo.png`, `motion/assets/fonts/Cairo.ttf`, `motion/assets/audio/background.m4a` |

## 1. Visual identity (لا تغيّرها إلا بطلب)

- **Colors**: background `#1A1718`/`(24,23,24)` (vertical) or `(41,39,40)` (square, = logo bg); gold `(229,174,61)`; highlight gold `(255,214,102)`; white titles; body `(225,222,218)`; muted grey `(170,166,160)`.
- **Font**: Cairo variable (`Black`/`ExtraBold` titles, `Bold` labels, `Medium` body). Arabic through PIL + raqm (`direction="rtl", language="ar"`).
- **Logo**: AB logo (key out its dark bg) **fixed top-left on every frame** (vertical: x60 y50 w210; square: x70 y70 w150). Hidden only in the outro where the big logo is built.
- **Decor**: slow diagonal hairlines, soft moving gold glow, thin gold wave lines ("swoosh") near image edge and bottom, gold progress bar at the very bottom, gold vertical side bar beside text blocks.
- **Typography layout (RTL)**: right-aligned at x = W-120 (vertical) to keep clear of TikTok buttons; heading = small gold tag + big white title + short gold underline; English pill (gold, dark text) under Arabic titles; big gold-gradient numbers with glow.
- **Safe zones (vertical)**: keep text between y≈300 and y≈1720.

## 2. Motion vocabulary (from his website aladeen35.github.io/test/alaeldeen)

1. **Opening (~3.4–3.6 s)**: gold particles in a spinning **helix** converge into the AB logo + gold loading line with counter `000→100` → gold flash ring → logo flies to its corner → helix opens → bolt badge pops (Quick Fact) → title slams in (scale 1.3→1 with gold glow) → gold underline → subtitle.
2. **Build from scratch**: photos/maps/logos are assembled by particles flying from the helix to their pixel grid, swept left→right, while a **"QC" mouse cursor** moves ahead of the front. Then the real image fades in.
3. **Transitions**: image dissolves back into particles that scatter upward; text slides out sideways.
4. **Text**: word-by-word reveal paced to the voice; the newest word glows gold then settles.
5. **Real screenshots**: capture the actual website with Playwright (`deviceScaleFactor: 2`, click the relevant button, crop by element boxes), show it in a dark **browser frame** with the URL bar and gold outline, built from particles (`ShotParticles` in the explainer), then slide a second screenshot over it; always add «المصدر: …» and put the link in the LinkedIn caption (`linkedin_post.md`).
6. **Explainers**: per scene one clear visual (cards, count-up bars, ✓/— tables, dot world map from `global_land_mask`, checklists with drawn check marks), cursor "clicks" with a ripple, scene progress dots top-right, subtitles at y≈1400.
7. **Outro**: particles build the big logo, then «مع تحيات المهندس علاء الدين عمر» (EN: "With regards, Eng. Alaeldeen Omar") + "تابعني على LinkedIn للمزيد" + hashtags. **Always include this greeting, on screen and spoken.**

## 3. Voice — صوته المستنسخ

- Engine: **XTTS-v2 (Coqui)**, venv `/home/user/xtts-venv` (`pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu coqui-tts torchcodec six`). The owner accepted the **CPML licence (non-commercial use only)**; run with `COQUI_TOS_AGREED=1`.
- Speaker sample: `motion/assets/voice/my_voice.wav` (mono 22.05 kHz, from his 31 s recording). It is **deliberately not in git** (the repo is public). If it is missing, ask him to upload the recording again and convert: `ffmpeg -i in.m4a -ac 1 -ar 22050 motion/assets/voice/my_voice.wav`.
- torchcodec mismatch workaround: monkey-patch `torchaudio.load` with a `soundfile` reader (see `motion/voice.py`).
- Write a **spoken version** of the text: numbers as words, Latin abbreviations in Arabic sound (HACCP → «الهاسب», FIFO/FEFO → «فايفو / فيفو», FARRP → «فارب»), add tashkeel to ambiguous words (e.g. «يَرَى ما لا نَرَاه»). Keep the on-screen text in its original form (use a separate `show`/`say`).
- English: same sample, `language="en"`, regex fixes in `voice.py` (°C → degrees Celsius, 18–20 g → 18 to 20 grams, acronyms spelled out).
- Speed: ~40–60 s per paragraph on 4 CPU cores. Run long jobs in the background.
- Timing rule: each scene/fact lasts `max(min_dur, 0.45–0.5 s lead + voice length + ~1 s)`; voice starts 0.5 s after the scene appears.

## 4. Audio mix

- Music `motion/assets/audio/background.m4a` looped, fade-in 0.6–0.8 s, fade-out 2 s; volume **0.15 under voice**, 0.8 without voice.
- Voice ×1.6, `amix normalize=0`, then `alimiter=limit=0.9`, AAC 128k.

## 5. Encoding

- x264 `-preset slow -crf 26/27 -tune animation -pix_fmt yuv420p -movflags +faststart` (particles inflate size; ~7 MB per 50 s vertical).

## 6. Pitfalls already solved — don't repeat

- Never draw semi-transparent shapes/text directly on an RGBA frame (alpha overwrites → ghosts/holes). Draw on a transparent overlay layer and `paste(ov, (0,0), ov)` onto an RGB frame.
- Make sure every frame sent to ffmpeg is **RGB** of exact size (an RGBA frame corrupts the whole stream).
- Cairo has **no arrow glyphs** (→ ←) and no ✓: replace arrows with "›" (it mirrors to "‹" in RTL) and draw check marks with lines.
- Bidi: draw Latin text with `rtl=False`; for word-by-word reveal, position each word manually right→left.
- Free images: Openverse API (`license=cc0,pdm`, no key) — slow/504s, retry with backoff; reject branded/watermarked photos; keep `credits.json`.
- Openverse/Pexels keys: Pexels key issuance may be paused; Openverse needs none.
- OneDrive connector uploads are limited to 1 MB per file — deliver via GitHub (Download ZIP) or a Remote Control folder.
- Ask before stating regulatory facts you are not sure of; mark stylised maps as «رسم توضيحي».

## 7. Workflow for a new explainer «بأسلوبي وصوتي»

1. Understand the source (download post text/video frames/captions); extract **the final idea** in one sentence.
2. Write 4–6 short scenes (hook → problem → example → tool/solution → takeaway) in simple Arabic; check facts.
3. Copy `motion/explainers/allergen_labelling/`, edit `script.json` (`say` = spoken, `show` = on screen) and the scene functions.
4. `COQUI_TOS_AGREED=1 /home/user/xtts-venv/bin/python voice_scenes.py` → `python3 render.py --preview` → review frames → `python3 render.py`.
5. Send the video, commit and push (never commit the voice sample or generated voice files).
