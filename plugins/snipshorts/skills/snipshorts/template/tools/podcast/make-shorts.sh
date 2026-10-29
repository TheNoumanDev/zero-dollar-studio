#!/usr/bin/env bash
# Long video -> vertical Shorts, end to end.
#   tools/podcast/make-shorts.sh podcasts/<slug> [count]
# Needs podcasts/<slug>/source.json and words.json (see the snipshorts skill).
# Env: SKIP_MOMENTS=1 reuse moments.json · ONLY=2 or ONLY=1,4,5 just those clips · SKIP_PLAN=1 reuse plan.json
#      RENDER_ONLY=1 just re-render (after composition changes) · SAMPLE=10 render only the first 10 s
#      POST=1 also write the ready-to-post folder (titles, captions, tags, thumbnail; nothing is uploaded)
set -euo pipefail
cd "$(dirname "$0")/../.."
FOLDER=${1:?usage: make-shorts.sh podcasts/<slug> [count]}
FOLDER=${FOLDER%/}
COUNT=${2:-3}
SLUG=$(basename "$FOLDER")
PY=.venv/bin/python
CLIPS=src/compositions/PodcastShort/clips.ts
OUT=out/podcast-shorts/$SLUG

step() { printf '\033[36m▶ %s\033[0m\n' "$1"; }

[[ $SLUG =~ ^[a-zA-Z0-9-]+$ ]] || { echo "❌ slug '$SLUG' must use only letters, digits and hyphens (it becomes a Remotion composition id)"; exit 1; }
[[ -f $FOLDER/source.json && -f $FOLDER/words.json ]] || { echo "❌ $FOLDER needs source.json and words.json"; exit 1; }
# Moment picking, edit planning and post copy use a logged-in agent CLI (no API key):
# Claude Code by default; SNIPSHORTS_LLM=codex|gemini|<command> picks another (see llm.py).
.venv/bin/python -c "import sys; sys.path.insert(0, 'tools/podcast'); import llm; llm.check()" || exit 1

if [[ -z ${SKIP_MOMENTS:-} || ! -f $FOLDER/moments.json ]]; then
  step "Claude picks $COUNT moments"
  $PY tools/podcast/moments.py "$FOLDER" --count "$COUNT"
fi

mkdir -p "$OUT"
DONE=()
for i in $(seq 1 "$COUNT"); do
  [[ -n ${ONLY:-} && ",$ONLY," != *",$i,"* ]] && continue
  ID=$SLUG-$i
  grep -q "\"$ID\"" $CLIPS || perl -pi -e "s/(PODCAST_SHORTS: string\[\] = \[)/\$1\"$ID\", /" $CLIPS
  if [[ -z ${RENDER_ONLY:-} ]]; then
    step "$ID: cut, jump-cut, track the speaker"
    $PY tools/podcast/prepare.py "$FOLDER" $((i - 1)) --id "$ID"
    # Name tags: match people by clothing once references exist (people.py --sheet / --label).
    if grep -q '"refs"' "$FOLDER/source.json"; then $PY tools/podcast/people.py "$ID"; fi
    # Non-English sources: captions in Latin script (the caption font has Latin glyphs only).
    if grep -q '"language": *"[a-z]*"' "$FOLDER/source.json" && ! grep -q '"language": *"en"' "$FOLDER/source.json"; then
      $PY tools/podcast/romanize.py "$ID"
    fi
    if [[ -z ${SKIP_PLAN:-} || ! -f public/podcast-shorts/$ID/plan.json ]]; then
      step "$ID: Claude writes the edit plan"
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
  # Contact sheet: 6 frames across the clip, for a quick look.
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$ID.mp4")
  ffmpeg -y -v error -i "$OUT/$ID.mp4" -vf "fps=6/$DUR,scale=270:-1,tile=6x1" -frames:v 1 "$OUT/$ID.sheet.png"
  step "$ID: done → $OUT/$ID.mp4"
  DONE+=("$ID")
done
if [[ -n ${POST:-} && ${#DONE[@]} -gt 0 ]]; then
  step "ready-to-post folder"
  $PY tools/podcast/post.py "$FOLDER" "${DONE[@]}"
fi
