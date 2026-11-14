# PROGRESS – 01-idea-to-video   (updated 2026-11-14)
Phase: preview (test v1 delivered, awaiting feedback)
Current version: v1 → renders/final/idea-to-video_v1.mp4 (1080×1920, 30 fps, 45 s, −14.4 LUFS)
Done:
- VO: Chatterbox (free, local, CPU) S1–S7 in assets/vo/chatterbox/, track assets/vo/vo_chatterbox_v2.wav; S3 rewritten ("مَن هو جمهورك؟")
- SFX: procedural pop / pop_light / whoosh / logo_swoosh / soft_impact (scripts/make_sfx.py) — ElevenLabs key not available
- Timeline locked to the VO: scripts/build_beats.py → plan/beats.json + src/data.js
- Scenes: src/index.html (canvas, drawFrame(t)); render: src/render.js; mix: scripts/build_audio.py
- Real logo (assets/images/logo_source.png) inside a disc for intro + watermark
In progress: -
Next step: user feedback on v1 → fixes → v2; swap VO/SFX for ElevenLabs once ELEVENLABS_API_KEY exists (scripts/eleven.mjs), then rerun build_beats → render → build_audio
Rebuild: python3 scripts/build_beats.py assets/vo/chatterbox assets/vo/vo_chatterbox_v2.wav && node src/render.js --from 0 --to 45 --fps 30 --scale 1 --out cache/frames && python3 scripts/build_audio.py assets/vo/vo_chatterbox_v2.wav cache/mix.wav && ffmpeg -framerate 30 -i cache/frames/%05d.jpg -i cache/mix.wav -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest renders/final/idea-to-video_vN.mp4
Chatterbox venv: /home/user/.venv-chatterbox (python 3.11, CPU torch, setuptools<81 for perth)
Open issues: Chatterbox Arabic accent/pronunciation is imperfect (some words)
Key decisions & preferences:
- 1080×1920, 30 fps, 45 s, intensity 3/5, palette FFF8ED/18202A/FF6B35/2EC4B6/FFD166, font Cairo (OFL, via @fontsource)
- SFX only Pop / Whoosh / Soft Impact
- Watermark: 97 px, 78% opacity, right 42 px, top 80 px, hidden 0–1.8 s
