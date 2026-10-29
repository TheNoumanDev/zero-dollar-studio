#!/usr/bin/env bash
# One command for a cartoon episode: check → voice → lip sync → episode data, then
# make-video's tools/make-story.sh for captions → music/SFX → lint → render → master → QA.
#
#   tools/make-episode.sh stories/<slug> <CompositionId>
#
# Same switches as make-story.sh: SKIP_VOICE=1 (also skips lip sync), SKIP_CAPTIONS=1,
# SKIP_MUSIC=1, SAMPLE=15, LAYOUT=<Id>.
set -euo pipefail
STORY=${1:?usage: tools/make-episode.sh stories/<slug> <CompositionId>}
COMP=${2:?usage: tools/make-episode.sh stories/<slug> <CompositionId>}
SLUG=$(basename "$STORY")
LOG="$STORY/timing.csv"
PY=.venv/bin/python
[ -x tools/make-story.sh ] || { echo "❌ Not a make-video project (no tools/make-story.sh). Set one up with the make-video skill first."; exit 1; }
[ -f "$LOG" ] || echo "step,seconds" > "$LOG"

step() { # step <name> <command...>: time it, keep its exit code
  local name=$1; shift
  local t0=$(date +%s) rc=0
  echo "▶ $name"
  "$@" || rc=$?
  echo "$name,$(( $(date +%s) - t0 ))" >> "$LOG"
  return $rc
}

# Bible → script.json voices, and catch missing characters, sets, faces and poses early.
step check $PY tools/episode_data.py sync "$STORY"
if [ -z "${SKIP_VOICE:-}" ]; then
  # Characters with "engine": "parler" are voiced first in their own venv;
  # voice.py then builds the timeline from those cached lines.
  if grep -q '"engine": *"parler"' "$STORY/script.json"; then
    [ -x tools/parler-venv/bin/python ] || { echo "❌ Parler isn't installed: WITH_PARLER=1 tools/setup_cartoon.sh"; exit 1; }
    step voice-parler tools/parler-venv/bin/python tools/voice_parler.py "$STORY"
  fi
  step voice $PY tools/voice.py "$STORY"
  step voice-loudness ffmpeg -y -v error -i "public/$SLUG/voice.wav" -af loudnorm=I=-16:TP=-1.5 -ar 48000 "public/$SLUG/voice.norm.wav"
  mv "public/$SLUG/voice.norm.wav" "public/$SLUG/voice.wav"
  step lipsync node tools/lipsync.mjs "$STORY"
fi
step episode-data $PY tools/episode_data.py pack "$STORY"
# The rest is make-video's pipeline, with voice already done.
SKIP_VOICE=1 tools/make-story.sh "$STORY" "$COMP"
