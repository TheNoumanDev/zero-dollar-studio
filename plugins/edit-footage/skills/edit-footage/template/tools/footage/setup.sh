#!/usr/bin/env bash
# One-time setup for edit-footage, on top of a make-video project with the snipshorts tools.
# Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/../.."

[[ -f tools/make-story.sh ]] || { echo "❌ Not a make-video project. Set one up with the make-video skill first."; exit 1; }
[[ -f tools/podcast/setup.sh ]] || { echo "❌ snipshorts tools missing. Add them with the snipshorts skill (§0) first."; exit 1; }
grep -q -- "--verbatim" tools/podcast/transcribe.py || {
  echo "❌ tools/podcast/transcribe.py is older than snipshorts 0.2.1 (no --verbatim). Copy the snipshorts template again."; exit 1; }

echo "▶ snipshorts packages, face detector, PodcastShorts in Root.tsx"
tools/podcast/setup.sh

echo "▶ .gitignore"
for line in "footage/*/*.mp4" "footage/*/*.mov" "footage/*/*.MOV" "footage/*/*.m4v" "footage/*/*.webm"; do
  grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
done
chmod +x tools/footage/make-reel.sh
echo "✅ edit-footage ready. Next: put your recording in footage/<slug>/ and write footage.json (see footage/example/footage.json)."
