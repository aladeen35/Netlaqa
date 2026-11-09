#!/usr/bin/env bash
# Full pipeline: voices (ar + en) -> render -> mix. Usage: bash run_all.sh
set -e
cd "$(dirname "$0")"
PY=/home/user/xtts-venv/bin/python
export COQUI_TOS_AGREED=1   # owner accepted the CPML (non-commercial) licence
while pgrep -f "python voice.py" >/dev/null; do sleep 20; done   # wait for any running voice job
$PY voice.py --only 02 outro --force 2>&1 | grep -E "^wrote|Error" || true
$PY voice.py 2>&1 | grep -E "^wrote|Error" || true
$PY voice.py --lang en 2>&1 | grep -E "^wrote|Error" || true
for L in ar en; do
  python3 -c "import json;print('\n'.join(v['id'] for v in json.load(open('tips.json'))['videos']))" \
    | xargs -P 4 -n 1 python3 render.py --lang $L --id
  python3 add_music.py --lang $L
done
echo PIPELINE_DONE
