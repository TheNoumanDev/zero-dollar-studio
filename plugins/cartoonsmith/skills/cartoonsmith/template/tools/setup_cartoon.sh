#!/usr/bin/env bash
# One-time setup for cartoonsmith, on top of a make-video project (run tools/setup.sh first).
# Safe to re-run: every step skips work that is already done.
#   tools/setup_cartoon.sh                  # Pillow + Rhubarb Lip Sync (~10 MB)
#   WITH_UPSCALE=1 tools/setup_cartoon.sh   # + Real-ESRGAN 4× upscaler (~45 MB)
#   WITH_PARLER=1 tools/setup_cartoon.sh    # + Indic Parler-TTS voice engine (~5 GB, gated on Hugging Face)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -x .venv/bin/python ] || { echo "❌ No .venv. Run make-video's tools/setup.sh first."; exit 1; }

echo "▶ Python extras (Pillow)"
uv pip install --python .venv/bin/python -r tools/requirements-cartoon.txt

fetch() { # fetch <url> <dest dir>: download a release zip and unpack it flat into <dest dir>
  local tmp; tmp=$(mktemp -d)
  curl -L --retry 3 -o "$tmp/a.zip" "$1"
  unzip -q "$tmp/a.zip" -d "$tmp/x"
  local inner; inner=$(find "$tmp/x" -mindepth 1 -maxdepth 1)
  # Some zips hold one folder, others hold the files directly.
  if [ "$(echo "$inner" | wc -l | tr -d ' ')" = 1 ] && [ -d "$inner" ]; then mv "$inner" "$2"; else mv "$tmp/x" "$2"; fi
  xattr -dr com.apple.quarantine "$2" 2>/dev/null || true
  rm -rf "$tmp"
}

echo "▶ Rhubarb Lip Sync 1.14.0 (MIT): phoneme-timed mouth shapes"
if [ ! -x tools/rhubarb/rhubarb ]; then
  case "$(uname -s)" in
    Darwin) fetch https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-macOS.zip tools/rhubarb ;;
    Linux) fetch https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip tools/rhubarb ;;
    *) echo "⚠️  Install Rhubarb into tools/rhubarb/ by hand (https://github.com/DanielSWolf/rhubarb-lip-sync/releases)" ;;
  esac
fi
# The macOS build is Intel-only: Apple Silicon runs it through Rosetta 2.
if ! tools/rhubarb/rhubarb --version >/dev/null 2>&1; then
  echo "⚠️  Rhubarb won't start. On Apple Silicon install Rosetta 2: softwareupdate --install-rosetta"
  echo "    Without it, mouths follow loudness only."
fi

if [ -n "${WITH_UPSCALE:-}" ]; then
  echo "▶ Real-ESRGAN ncnn (BSD-3-Clause): 4× upscaler for small character sheets"
  [ -x tools/realesrgan/realesrgan-ncnn-vulkan ] || {
    case "$(uname -s)" in
      Darwin) fetch https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip tools/realesrgan ;;
      Linux) fetch https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip tools/realesrgan ;;
    esac
    chmod +x tools/realesrgan/realesrgan-ncnn-vulkan
  }
fi

if [ -n "${WITH_PARLER:-}" ]; then
  echo "▶ Indic Parler-TTS (Apache-2.0) in tools/parler-venv"
  echo "  The model is gated: accept its terms at https://huggingface.co/ai4bharat/indic-parler-tts and run 'hf auth login' first."
  [ -d tools/parler-venv ] || uv venv --python 3.11 tools/parler-venv
  uv pip install --python tools/parler-venv/bin/python -r tools/requirements-parler.txt
  tools/parler-venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("ai4bharat/indic-parler-tts")
snapshot_download("google/flan-t5-large", allow_patterns=["*.json", "*.model"])  # its description tokenizer
PY
fi

echo "▶ Git-ignore the downloaded tools and intermediate cut-outs"
for p in tools/rhubarb tools/realesrgan tools/parler-venv 'art/*/*/cuts/'; do
  grep -qxF "$p" .gitignore 2>/dev/null || echo "$p" >> .gitignore
done

echo "▶ Checks"
.venv/bin/python -c "import PIL, cv2; print('pillow', PIL.__version__, 'opencv', cv2.__version__)"
tools/rhubarb/rhubarb --version 2>/dev/null | grep -i version || true
echo "✅ cartoonsmith ready. Try: .venv/bin/python tools/make_placeholder_cast.py"
