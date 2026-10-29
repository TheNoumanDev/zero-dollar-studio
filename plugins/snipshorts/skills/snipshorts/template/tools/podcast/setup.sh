#!/usr/bin/env bash
# One-time setup for snipshorts, on top of a make-video project (run tools/setup.sh first).
# Safe to re-run: every step skips work that is already done.
set -euo pipefail
cd "$(dirname "$0")/../.."

[[ -f tools/make-story.sh ]] || { echo "❌ Not a make-video project. Set one up with the make-video skill first."; exit 1; }
command -v uv >/dev/null || { echo "❌ uv not found. Run tools/setup.sh (make-video) first."; exit 1; }
command -v ffmpeg >/dev/null || { echo "❌ ffmpeg not found. Run tools/setup.sh (make-video) first."; exit 1; }
[[ -d .venv ]] || uv venv --python 3.11 .venv

echo "▶ Python packages (faster-whisper, yt-dlp, OpenCV)"
uv pip install --python .venv/bin/python -r tools/podcast/requirements.txt

echo "▶ YuNet face detector (OpenCV Zoo, MIT, 230 KB)"
YUNET=tools/models/yunet/face_detection_yunet_2023mar.onnx
[[ -f $YUNET ]] || { mkdir -p "$(dirname "$YUNET")"; curl -L --retry 3 -o "$YUNET" \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx; }

echo "▶ Register the PodcastShort compositions in src/Root.tsx"
.venv/bin/python tools/podcast/register_root.py

echo "▶ .gitignore"
for line in "public/podcast-shorts/" "podcasts/*/*.mp4" "podcasts/*/*.mkv" "podcasts/*/*.webm" "podcasts/*/*.vtt"; do
  grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
done

echo "▶ Checks"
# Separate processes: PyAV (faster-whisper) and OpenCV each bundle FFmpeg and warn when loaded together.
.venv/bin/python -c "import faster_whisper; print('faster-whisper ok')"
.venv/bin/python -c "import cv2; cv2.FaceDetectorYN.create('$YUNET', '', (320, 240)); print('YuNet ok')"
.venv/bin/yt-dlp --version | sed 's/^/yt-dlp /'
if command -v claude >/dev/null; then claude --version; else
  echo "⚠️  claude CLI not on PATH. Moment picking, edit plans and post copy need the logged-in Claude Code CLI."; fi
echo "✅ snipshorts ready. Next: write podcasts/<slug>/source.json (see podcasts/example/source.json)."
