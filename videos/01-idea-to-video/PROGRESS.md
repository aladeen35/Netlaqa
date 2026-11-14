# PROGRESS – 01-idea-to-video   (updated 2026-11-14)
Phase: script (awaiting approval + ELEVENLABS_API_KEY)
Current version: — (no render yet)
Done:
- Preflight: node 22, ffmpeg 6.1, playwright 1.63, gsap, faster-whisper ✅
- plan/script.md (VO v1, Arabic, 7 segments), plan/storyboard.md v1, plan/sfx.json, plan/vo_segments.json
- scripts/eleven.mjs (voices | tts | sfx via ElevenLabs REST)
In progress: -
Next step: once ELEVENLABS_API_KEY is in the env → `node scripts/eleven.mjs voices` → test S1 with 2–3 voices → user picks → generate S1–S7 + SFX → faster-whisper → plan/beats.json → build scenes
Open issues: - Real logo not provided → circular "YOUR_LOGO" placeholder
Key decisions & preferences:
- 1080×1920, 30 fps, 45 s, intensity 3/5, palette FFF8ED/18202A/FF6B35/2EC4B6/FFD166, font Cairo (OFL)
- SFX only Pop / Whoosh / Soft Impact; VO + SFX via ElevenLabs (user wants to test the ElevenLabs skills)
- Watermark: 97 px wide, 78% opacity, right 42 px, top 80 px, hidden 0–1.8 s
Key files: plan/script.md, plan/storyboard.md, plan/sfx.json, plan/vo_segments.json, scripts/eleven.mjs
