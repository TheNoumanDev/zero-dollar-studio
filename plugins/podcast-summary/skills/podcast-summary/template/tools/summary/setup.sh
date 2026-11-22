#!/usr/bin/env bash
# One-time setup for podcast-summary, on top of a make-video project with the snipshorts tools.
# Safe to re-run. The optional AI talking face has its own script: tools/summary/setup-aiface.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."

[[ -f tools/make-story.sh ]] || { echo "❌ Not a make-video project. Set one up with the make-video skill first."; exit 1; }
[[ -f tools/podcast/setup.sh ]] || { echo "❌ No snipshorts tools (tools/podcast/). Add them with the snipshorts skill first."; exit 1; }

echo "▶ snipshorts tools (faster-whisper, yt-dlp, OpenCV, YuNet)"
tools/podcast/setup.sh

echo "▶ Python packages (rembg, onnxruntime, scipy)"
uv pip install --python .venv/bin/python -r tools/summary/requirements.txt

echo "▶ Register the PodcastSummary compositions in src/Root.tsx"
.venv/bin/python tools/summary/register_root.py

echo "▶ .gitignore"
for line in "public/summary/" "public/summary-thumbs/" "work/" "out/" "summaries/*/*.mp4" "summaries/*/roman.json" "podcasts/*/*.m4a"; do
  grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
done

echo "▶ Checks"
.venv/bin/python -c "import rembg, scipy, soundfile; print('rembg ok')"
[[ -x tools/whisper-mlx/.venv/bin/python ]] && echo "whisper-mlx ok (build.py --check)" || echo "⚠️  no tools/whisper-mlx: build.py --check needs make-video's setup (tools/setup.sh)"
echo "✅ podcast-summary ready. Optional AI talking faces: tools/summary/setup-aiface.sh"
