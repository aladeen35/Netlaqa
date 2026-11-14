// ElevenLabs helper — reads ELEVENLABS_API_KEY from env or ./.env, never prints it.
// Usage:
//   node scripts/eleven.mjs voices                     # list premade voices
//   node scripts/eleven.mjs tts <voice_id> [S1 S2 …]   # generate VO segments from plan/vo_segments.json
//   node scripts/eleven.mjs sfx [name …]               # generate SFX from plan/sfx.json
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
if (!process.env.ELEVENLABS_API_KEY && fs.existsSync(path.join(root, '.env'))) process.loadEnvFile(path.join(root, '.env'));
const KEY = process.env.ELEVENLABS_API_KEY;
if (!KEY) { console.error('ELEVENLABS_API_KEY is not set'); process.exit(1); }
const API = 'https://api.elevenlabs.io/v1';
const log = (msg) => fs.appendFileSync(path.join(root, 'LOG.md'), `- ${new Date().toISOString()} ${msg}\n`);

async function call(url, body) {
  const res = await fetch(url, { method: body ? 'POST' : 'GET', headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' }, body: body && JSON.stringify(body) });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res;
}

const [cmd, ...args] = process.argv.slice(2);
if (cmd === 'voices') {
  const { voices } = await (await call(`${API}/voices`)).json();
  for (const v of voices.filter((v) => v.category === 'premade')) console.log(`${v.voice_id}  ${v.name}  ${JSON.stringify(v.labels || {})}`);
} else if (cmd === 'tts') {
  const [voiceId, ...ids] = args;
  const cfg = JSON.parse(fs.readFileSync(path.join(root, 'plan/vo_segments.json'), 'utf8'));
  for (const seg of cfg.segments.filter((s) => !ids.length || ids.includes(s.id))) {
    const res = await call(`${API}/text-to-speech/${voiceId}?output_format=mp3_44100_192`, {
      text: seg.text, model_id: cfg.model_id, language_code: cfg.language_code, voice_settings: cfg.voice_settings,
    });
    const out = path.join(root, 'assets/vo', `${seg.id}.mp3`);
    fs.writeFileSync(out, Buffer.from(await res.arrayBuffer()));
    console.log('✅', out); log(`TTS ${seg.id} voice=${voiceId} model=${cfg.model_id} → assets/vo/${seg.id}.mp3`);
  }
} else if (cmd === 'sfx') {
  const list = JSON.parse(fs.readFileSync(path.join(root, 'plan/sfx.json'), 'utf8'));
  for (const s of list.filter((s) => !args.length || args.includes(s.name))) {
    const res = await call(`${API}/sound-generation?output_format=mp3_44100_192`, {
      text: s.prompt, model_id: 'eleven_text_to_sound_v3', duration_seconds: s.duration, prompt_influence: s.influence ?? 0.5,
    });
    const out = path.join(root, 'assets/sfx', `${s.name}.mp3`);
    fs.writeFileSync(out, Buffer.from(await res.arrayBuffer()));
    console.log('✅', out); log(`SFX ${s.name} (${s.duration}s) → assets/sfx/${s.name}.mp3`);
  }
} else {
  console.log('usage: voices | tts <voice_id> [ids] | sfx [names]');
}
