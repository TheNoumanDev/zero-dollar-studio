#!/usr/bin/env bash
# Your own raw talking-head recording -> a finished vertical reel.
#   tools/footage/make-reel.sh footage/<slug>          # join, transcribe, pick takes, print the script, stop
#   GO=1 tools/footage/make-reel.sh footage/<slug>     # cut, plan, render the approved script
# Needs footage/<slug>/footage.json (see footage/example/footage.json) and the snipshorts tools.
# Env: GO=1 render the script in takes.json · RETAKE=1 pick takes again (discards hand edits)
#      SKIP_PLAN=1 reuse plan.json · RENDER_ONLY=1 just re-render · SAMPLE=10 render only the first 10 s
#      PLATFORMS="yt ig tiktok" also write <id>.yt.mp4 etc. with each platform's encode settings
set -euo pipefail
cd "$(dirname "$0")/../.."
FOLDER=${1:?usage: make-reel.sh footage/<slug>}
FOLDER=${FOLDER%/}
SLUG=$(basename "$FOLDER")
ID=$SLUG
PY=.venv/bin/python
CLIPS=src/compositions/PodcastShort/clips.ts
OUT=out/reels

step() { printf '\033[36m▶ %s\033[0m\n' "$1"; }

[[ $SLUG =~ ^[a-zA-Z0-9-]+$ ]] || { echo "❌ slug '$SLUG' must use only letters, digits and hyphens (it becomes a Remotion composition id)"; exit 1; }
[[ -f $FOLDER/footage.json ]] || { echo "❌ $FOLDER needs footage.json (copy footage/example/footage.json)"; exit 1; }
[[ -f tools/podcast/prepare.py && -f $CLIPS ]] || { echo "❌ snipshorts tools missing: set them up first (snipshorts skill §0)"; exit 1; }
LANG_CODE=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('language', 'en'))" "$FOLDER/footage.json")

if [[ -z ${RENDER_ONLY:-} ]]; then
  if [[ ! -f $FOLDER/source.mp4 ]]; then
    step "join and normalise the recording"
    $PY tools/footage/ingest.py "$FOLDER"
  fi
  if [[ ! -f $FOLDER/words.json ]]; then
    step "transcribe, keeping fillers and false starts"
    $PY tools/podcast/transcribe.py "$FOLDER/source.mp4" "$FOLDER/words.json" --lang "$LANG_CODE" --verbatim
  fi
  if [[ -n ${RETAKE:-} || ! -f $FOLDER/takes.json ]]; then
    step "best take of each line"
    $PY tools/footage/takes.py "$FOLDER"
  else
    $PY tools/footage/takes.py "$FOLDER" --show
  fi
  if [[ -z ${GO:-} ]]; then
    echo "Check the script above (✓ kept, ✗ dropped). Flip lines with: $PY tools/footage/takes.py $FOLDER --keep 4 --drop 7"
    echo "Then render: GO=1 $0 $FOLDER"
    exit 0
  fi
fi

# The edit plan calls the agent CLI (Claude Code by default; SNIPSHORTS_LLM picks another).
$PY -c "import sys; sys.path.insert(0, 'tools/podcast'); import llm; llm.check()" || exit 1
mkdir -p "$OUT"
grep -q "\"$ID\"" $CLIPS || perl -pi -e "s/(PODCAST_SHORTS: string\[\] = \[)/\$1\"$ID\", /" $CLIPS
if [[ -z ${RENDER_ONLY:-} ]]; then
  step "$ID: cut the takes, jump-cut pauses, frame the face"
  $PY tools/footage/cut.py "$FOLDER" --id "$ID"
  # Non-English: captions in Latin script (the caption font has Latin glyphs only).
  [[ $LANG_CODE == en ]] || $PY tools/podcast/romanize.py "$ID"
  if [[ -z ${SKIP_PLAN:-} || ! -f public/podcast-shorts/$ID/plan.json ]]; then
    step "$ID: the agent writes the edit plan"
    $PY tools/podcast/plan.py "$ID"
  fi
  $PY tools/podcast/sfx.py "$ID"
fi
step "$ID: render"
FRAMES=()
[[ -n ${SAMPLE:-} ]] && FRAMES=(--frames=0-$((SAMPLE * 30 - 1)))
npx remotion render "$ID" "$OUT/$ID.raw.mp4" --log=warn --timeout=180000 --concurrency=2 ${FRAMES[@]+"${FRAMES[@]}"}
# Master to -14 LUFS for Shorts/Reels.
ffmpeg -y -v error -i "$OUT/$ID.raw.mp4" -c:v copy \
  -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 192k "$OUT/$ID.mp4"
rm "${OUT:?}/${ID:?}.raw.mp4"
for P in ${PLATFORMS:-}; do
  case $P in
    yt) V=(-b:v 12M -maxrate 15M -bufsize 24M); AB=192k ;;
    ig) V=(-b:v 4500k -maxrate 5000k -bufsize 10000k); AB=128k ;;
    tiktok) V=(-crf 18 -preset slow); AB=128k ;;
    *) echo "unknown platform $P (yt, ig, tiktok)"; continue ;;
  esac
  ffmpeg -y -v error -i "$OUT/$ID.mp4" -c:v libx264 -profile:v high -level 4.2 -pix_fmt yuv420p "${V[@]}" \
    -c:a aac -b:a $AB -ar 48000 -movflags +faststart "$OUT/$ID.$P.mp4"
done
# Contact sheet: 6 frames across the reel, for a quick look.
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$ID.mp4")
ffmpeg -y -v error -i "$OUT/$ID.mp4" -vf "fps=6/$DUR,scale=270:-1,tile=6x1" -frames:v 1 "$OUT/$ID.sheet.png"
step "$ID: done → $OUT/$ID.mp4"
