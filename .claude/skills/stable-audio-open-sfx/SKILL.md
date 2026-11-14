---
name: stable-audio-open-sfx
description: Generate local sound effects, ambiences, impacts, and short audio beds from text with Stable Audio Open. Use for motion graphics, stickman videos, foley, transitions, UI sounds, and cinematic effects without a paid sound-generation API.
license: stable-audio-community
---

# Stable Audio Open SFX

Use this skill when the user needs locally generated sound effects instead of a paid ElevenLabs sound-effects API. Stable Audio Open 1.0 generates stereo audio up to 47 seconds at 44.1 kHz and is especially useful for sound effects and field recordings. It is weaker at realistic vocals and may require several prompt iterations.

## Setup

Use a dedicated Python environment and a CUDA GPU when available:

```bash
python3 -m venv .venv-stable-audio
source .venv-stable-audio/bin/activate
pip install --upgrade pip
pip install stable-audio-tools torch torchaudio einops
```

The model files are downloaded from Hugging Face. Accept the model's access conditions and authenticate with `huggingface-cli login` if required. Keep the model cache outside the project if disk space is limited.

## Generate an effect

```python
import torch
import torchaudio
from einops import rearrange
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond

model, config = get_pretrained_model("stabilityai/stable-audio-open-1.0")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

conditioning = [{
    "prompt": "cartoon stickman punch impact, crisp snap, short low thump, dry studio sound, no music",
    "seconds_start": 0,
    "seconds_total": 3,
}]

output = generate_diffusion_cond(
    model,
    steps=100,
    cfg_scale=7,
    conditioning=conditioning,
    sample_size=config["sample_size"],
    sigma_min=0.3,
    sigma_max=500,
    sampler_type="dpmpp-3m-sde",
    device=device,
)
output = rearrange(output, "b d n -> d (b n)")
output = output.float().div(output.abs().max().clamp_min(1e-8)).clamp(-1, 1).mul(32767).short().cpu()
torchaudio.save("impact.wav", output, config["sample_rate"])
```

## Prompting workflow

Describe the event, material, environment, distance, texture, duration, and what must not appear. Example: `0.8-second bright cartoon whoosh, elastic rubber texture, close microphone, clean tail, no melody, no speech`. Generate short effects separately instead of asking for a complete layered soundtrack in one pass.

For loopable ambience, request a seamless loop and generate 10–30 seconds. For impacts and transitions, use 0.5–4 seconds. Trim silence and normalize each result before mixing it under narration.

## Production workflow

1. Create a sound list from the storyboard: entry whooshes, impacts, footsteps, ambience, UI tones, and transitions.
2. Generate two or three candidates per important effect.
3. Select by sync accuracy and absence of noise, not by prompt similarity alone.
4. Trim, fade, EQ, and loudness-normalize with ffmpeg or a DAW.
5. Duck effects under narration and keep a source log with prompt, model, and license.

## Limitations and license

The model performs better on sound effects and field recordings than music, and it was trained primarily on English descriptions. The model card says commercial use requires checking Stability AI's license terms. Do not assume that “free to download” means unrestricted commercial use. For maximum legal stability, use properly licensed Foley libraries such as Freesound assets with a verified license when a generated effect is not essential.

## References

- Model card: https://huggingface.co/stabilityai/stable-audio-open-1.0
- Inference library: https://github.com/Stability-AI/stable-audio-tools
- Licensed sound-library option: https://freesound.org
