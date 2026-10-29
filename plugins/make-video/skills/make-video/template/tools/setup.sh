#!/usr/bin/env bash
# One-time setup for the voice / captions / music pipeline (macOS, Apple Silicon).
# Safe to re-run: every step skips work that is already done.
#   tools/setup.sh                    # everything (~6 GB of downloads)
#   SKIP_TAKE_CHECK=1 tools/setup.sh  # skip the Whisper take checker (~1.6 GB)
set -euo pipefail
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null || { echo "❌ $1 not found. $2"; exit 1; }; }
need node "Install Node 20+ (https://nodejs.org or brew install node)."
need brew "Install Homebrew first: https://brew.sh"
command -v ffmpeg >/dev/null || brew install ffmpeg
command -v uv >/dev/null || brew install uv

echo "▶ Node packages"; npm install --loglevel=error
echo "▶ FluidSynth"; command -v fluidsynth >/dev/null || brew install fluid-synth
echo "▶ Python 3.11 env"
[ -d .venv ] || uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r tools/requirements.txt

echo "▶ Soundfont (GeneralUser GS, free for music you make, including commercial)"
SF=tools/soundfonts/GeneralUser-GS.sf2
[ -f "$SF" ] || { mkdir -p tools/soundfonts; curl -L --retry 3 -o "$SF" \
  https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/main/GeneralUser-GS.sf2; }

echo "▶ Chatterbox weights (~3 GB from Hugging Face; resumes if interrupted)"
.venv/bin/python - <<'EOF'
from huggingface_hub import snapshot_download
snapshot_download("ResembleAI/chatterbox", allow_patterns=[
    "ve.safetensors", "t3_cfg.safetensors", "s3gen.safetensors",
    "tokenizer.json", "conds.pt", "Cangjie5_TC.json"])
EOF

echo "▶ Whisper small.en for captions (Hugging Face copy of Remotion's model, ~590 MB)"
# tools/captions.mjs reads the ONNX files from tools/models/<hosted id>/ (the
# Transformers.js cache layout), so captions also work where remotion.media is blocked.
.venv/bin/python - <<'EOF'
from huggingface_hub import snapshot_download
snapshot_download("onnx-community/whisper-small.en_timestamped",
    local_dir="tools/models/whisper-small.en_timestamped-v1",
    allow_patterns=["*.json", "*.txt", "onnx/encoder_model.onnx", "onnx/decoder_model_merged_q4.onnx"])
EOF

if [ -z "${SKIP_TAKE_CHECK:-}" ]; then
  echo "▶ Take checker (Whisper large-v3-turbo on MLX): re-records lines it can't hear clearly"
  [ -d tools/whisper-mlx/.venv ] || uv venv --python 3.11 tools/whisper-mlx/.venv
  uv pip install --python tools/whisper-mlx/.venv/bin/python mlx-whisper
  tools/whisper-mlx/.venv/bin/python -c "from huggingface_hub import snapshot_download as s; s('mlx-community/whisper-large-v3-turbo')"
fi

echo "▶ Checks"
node tools/check-webgpu.mjs
.venv/bin/python -c "import perth, chatterbox, torch; assert perth.PerthImplicitWatermarker; print('chatterbox ok, mps:', torch.backends.mps.is_available())"
fluidsynth --version | head -1
echo "✅ Setup complete. Try: tools/make-story.sh stories/fridge-drama FridgeDrama"
