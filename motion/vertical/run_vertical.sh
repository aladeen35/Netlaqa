#!/usr/bin/env bash
# Render + mix all vertical videos (ar, en), then refresh the square ones.
set -e
cd "$(dirname "$0")/.."
IDS=$(python3 -c "import json;print(' '.join(v['id'] for v in json.load(open('tips.json'))['videos']))")
for L in ar en; do
  echo $IDS | tr ' ' '\n' | xargs -P 4 -n 1 python3 vertical/render_vertical.py --lang $L --id
  python3 vertical/mix.py --lang $L
done
echo VERTICAL_DONE
for L in ar en; do
  echo $IDS | tr ' ' '\n' | xargs -P 4 -n 1 python3 render.py --lang $L --id
  python3 add_music.py --lang $L
done
echo SQUARE_DONE
