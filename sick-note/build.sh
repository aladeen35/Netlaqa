#!/bin/sh
# One-command rebuild: voices → lip-sync → events → picture → score/mix → master → mux → subtitles
set -e
LIB=${LIB:-/root/lemo-opuscar}
HERE=$(cd "$(dirname "$0")" && pwd)
export LIB
PY="$LIB/.venv/bin/python"
cd "$LIB"
"$PY" core/tts/tts.py "$HERE/voice/lines.json" "$HERE/voice/raw"
"$PY" "$HERE/voice/voice.py"
"$PY" core/tts/asr_check.py "$HERE/voice/lines.json" "$HERE/voice/out" --lang en
node core/render/events.mjs "$HERE" --size 1080x1920
node core/render/video.mjs "$HERE" --fps 24 --workers 4 --size 1080x1920 --out "$HERE/out/video.mp4"
"$PY" "$HERE/mix.py"
if ffmpeg -version | head -1 | grep -qE 'version n?([7-9]|[1-9][0-9])\.'; then
  sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/sick-note.mp4" 24 0
else   # ffmpeg 6: master in Python (BS.1770, -14 LUFS, true-peak limit), then mux
  "$PY" "$HERE/tools/master.py" "$HERE/out/mix.wav" "$HERE/out/master.wav"
  ffmpeg -v error -y -i "$HERE/out/video.mp4" -i "$HERE/out/master.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$HERE/sick-note.mp4"
fi
"$PY" "$HERE/tools/subs.py"
ffmpeg -v error -y -ss 20.2 -i "$HERE/sick-note.mp4" -frames:v 1 -q:v 2 "$HERE/poster.jpg"
echo "done: $HERE/sick-note.mp4"
