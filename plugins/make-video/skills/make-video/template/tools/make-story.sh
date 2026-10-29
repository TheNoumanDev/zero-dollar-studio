#!/usr/bin/env bash
# One-command story pipeline: voice → captions → music/SFX → render → loudness.
#
#   tools/make-story.sh stories/<slug> <CompositionId>
#
# Steps can be skipped with SKIP_VOICE=1 / SKIP_CAPTIONS=1 / SKIP_MUSIC=1 to
# iterate on visuals without regenerating audio.
#   SAMPLE=15   render only the first 15 s to out/<Comp>.sample.mp4 for approval, then stop
#   LAYOUT=<Id> run the QA caption-layout check against this composition (needs a `qa` prop)
set -euo pipefail
STORY=${1:?usage: tools/make-story.sh stories/<slug> <CompositionId>}
COMP=${2:?usage: tools/make-story.sh stories/<slug> <CompositionId>}
SLUG=$(basename "$STORY")
LOG="$STORY/timing.csv"
PY=.venv/bin/python
[ -f "$LOG" ] || echo "step,seconds" > "$LOG"

step() { # step <name> <command...>
  local name=$1; shift
  local t0=$(date +%s)
  echo "▶ $name"
  local rc=0
  "$@" || rc=$?
  echo "$name,$(( $(date +%s) - t0 ))" >> "$LOG"
  return $rc  # keep the command's exit code (it used to return echo's 0)
}

[ "${SKIP_VOICE:-}" ] || step voice $PY tools/voice.py "$STORY"
# Normalise dialogue so every video has the same voice level.
[ "${SKIP_VOICE:-}" ] || step voice-loudness ffmpeg -y -v error -i "public/$SLUG/voice.wav" \
  -af loudnorm=I=-16:TP=-1.5 -ar 48000 "public/$SLUG/voice.norm.wav"
[ "${SKIP_VOICE:-}" ] || mv "public/$SLUG/voice.norm.wav" "public/$SLUG/voice.wav"
[ "${SKIP_CAPTIONS:-}" ] || step captions node tools/captions.mjs "$STORY"
[ "${SKIP_MUSIC:-}" ] || step music $PY tools/music.py "$STORY"
step lint npm run -s lint
if [ "${SAMPLE:-}" ]; then
  FPS=$(python3 -c "import json;print(json.load(open('$STORY/script.json'))['format']['fps'])")
  step sample npx remotion render "$COMP" "out/$COMP.sample.mp4" --frames=0-$(( SAMPLE * FPS - 1 )) --timeout=180000 --concurrency=2 --log=error
  echo "✅ sample: out/$COMP.sample.mp4 (first ${SAMPLE}s). Approve it, then run again without SAMPLE."
  exit 0
fi
# --timeout/--concurrency: a render once hung for 23 h at 0% CPU without them.
step render npx remotion render "$COMP" "out/$COMP.raw.mp4" --timeout=180000 --concurrency=2 --log=error
# Final master at -14 LUFS (YouTube / Instagram normalisation target).
# Two-pass: measure, then normalise with the measured values (one-pass loudnorm
# under-shoots videos with long quiet stretches, e.g. dramatic pauses).
master() {
  local m; m=$(ffmpeg -hide_banner -i "out/$COMP.raw.mp4" -af loudnorm=I=-14:TP=-1.5:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  local mi mtp mlra mth off
  mi=$(echo "$m" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["input_i"],d["input_tp"],d["input_lra"],d["input_thresh"],d["target_offset"])')
  read -r mi mtp mlra mth off <<<"$mi"
  ffmpeg -y -v error -i "out/$COMP.raw.mp4" -c:v copy -c:a aac -b:a 192k \
    -af "loudnorm=I=-14:TP=-1.5:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:offset=$off:linear=true" \
    "out/$COMP.mp4"
}
step master master
rm "out/$COMP.raw.mp4"
# Final review gate + production log (QA FAIL stops the run with a non-zero exit).
QA_OK=0
step qa $PY tools/qa.py "$STORY" "out/$COMP.mp4" ${LAYOUT:+--layout "$LAYOUT"} || QA_OK=$?
$PY tools/prodlog.py "$STORY" "$COMP" "out/$COMP.mp4"
[ "$QA_OK" -eq 0 ] || { echo "❌ QA failed: see $STORY/qa/report.md"; exit 1; }
echo "✅ out/$COMP.mp4"
column -s, -t "$LOG"
