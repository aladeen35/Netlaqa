---
name: chatterbox-local-tts
description: Generate local multilingual voiceovers and optional voice cloning with open-source Chatterbox TTS. Use when producing narration, character dialogue, or Arabic and multilingual audio without a paid voice API.
license: MIT
---

# Chatterbox Local TTS

Use this skill for local text-to-speech and voice cloning when a paid ElevenLabs API is unavailable or the user wants audio generated on their own machine. Chatterbox supports Arabic and 22 other listed languages, reference-audio voice cloning, expressive controls, and local inference.

## Important status

The upstream repository states that Chatterbox was retired as research and is no longer maintained as of August 2026. Treat it as a free, self-hosted fallback rather than a guaranteed long-term production service. For the most stable non-cloning narration, prefer Kokoro-82M when its language and voice options are sufficient.

## Setup

Use Python 3.11 in an isolated virtual environment:

```bash
python3.11 -m venv .venv-chatterbox
source .venv-chatterbox/bin/activate
pip install --upgrade pip
pip install chatterbox-tts soundfile
```

Use a CUDA GPU when available. CPU inference may be slow and memory-heavy. Never download or use a reference voice without the speaker's permission.

## Generate speech

```python
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
audio = model.generate(
    "ضع النص العربي هنا.",
    language_id="ar",
    audio_prompt_path="voice-reference.wav",  # omit for the default voice
)
ta.save("voiceover.wav", audio, model.sr)
```

For English-only work, use `ChatterboxTTS`. For faster English cloning, use the Turbo model. Keep reference clips clean, with one speaker, little background noise, and roughly 5–15 seconds of speech.

## Production workflow

1. Normalize the script for spoken delivery and split it into short paragraphs.
2. Generate one test sentence first and check pronunciation, pacing, and speaker similarity.
3. Keep the same model, language ID, reference clip, and settings across all scenes.
4. Render each scene to WAV, then assemble and loudness-normalize with ffmpeg.
5. Preserve the source script, model name, reference-consent record, and generation settings beside the output.

## Quality controls

Use the default settings first. If speech is unstable or repeats, shorten the input chunk and lower exaggeration or CFG weight. If Arabic pronunciation inherits the wrong accent, use an Arabic reference clip or reduce CFG weight. Listen for clipping, breaths, repetitions, and unnatural pauses before using the track in a video.

## Licensing and safety

The code is MIT-licensed, but model-card and voice-data terms still apply. Do not imitate a real person without documented permission, and disclose synthetic narration where appropriate. For commercial projects, verify the exact model weights and dependencies before publishing.

## References

- Upstream repository: https://github.com/resemble-ai/chatterbox
- Stable local alternative without cloning: https://github.com/hexgrad/kokoro
