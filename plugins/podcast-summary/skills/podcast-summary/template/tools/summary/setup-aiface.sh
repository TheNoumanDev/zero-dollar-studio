#!/usr/bin/env bash
# Optional: the AI talking face (JoyVASA + LivePortrait) for real-photo cut-outs (aiface.py). Safe to re-run.
#
# Installs JoyVASA at a pinned commit into tools/aiface/JoyVASA, applies joyvasa.patch (Apple GPU instead of CUDA,
# lips closed in pauses, AIFACE_CALM, and InsightFace switched off: its models are non-commercial, so they are
# never downloaded or loaded), makes a Python 3.10 venv with torch 2.3.1, and downloads only the weights it uses:
#   JoyVASA motion generator (jdh-algo/JoyVASA, MIT)            ~395 MB
#   chinese-hubert-base audio encoder (TencentGameMate)         ~360 MB
#   LivePortrait base + retargeting models (KwaiVGI, MIT)       ~610 MB
# About 1.4 GB of weights plus ~2 GB of Python packages. Slow but local: ~20 s of compute per second of speech on
# an M1 Max, so run it in the background.
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT=$(pwd)
JV=tools/aiface/JoyVASA
COMMIT=916a90f8de490e8648fee460c1200bd5d9a795af

command -v uv >/dev/null || { echo "❌ uv not found. Run tools/setup.sh (make-video) first."; exit 1; }
command -v git >/dev/null || { echo "❌ git not found."; exit 1; }

echo "▶ JoyVASA source (github.com/jdh-algo/JoyVASA @ ${COMMIT:0:7}, MIT)"
if [[ ! -d $JV/.git ]]; then
  mkdir -p tools/aiface
  git clone --quiet https://github.com/jdh-algo/JoyVASA.git "$JV"
fi
git -C "$JV" fetch --quiet origin "$COMMIT" 2>/dev/null || true
if ! git -C "$JV" diff --quiet; then
  echo "  already patched"
else
  git -C "$JV" checkout --quiet "$COMMIT"
  git -C "$JV" apply "$ROOT/tools/summary/joyvasa.patch"
  echo "  patched (InsightFace off, Apple GPU, speech gate, AIFACE_CALM)"
fi

echo "▶ Python 3.10 venv for JoyVASA"
[[ -d $JV/.venv ]] || uv venv --quiet --python 3.10 "$JV/.venv"
uv pip install --quiet --python "$JV/.venv/bin/python" torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 huggingface_hub
uv pip install --quiet --python "$JV/.venv/bin/python" -r tools/summary/requirements-aiface.txt

echo "▶ Weights (only the ones used; no InsightFace)"
"$JV/.venv/bin/python" - "$JV/pretrained_weights" <<'PY'
import sys
from huggingface_hub import snapshot_download
w = sys.argv[1]
snapshot_download("jdh-algo/JoyVASA", local_dir=f"{w}/JoyVASA",
                  allow_patterns=["config.json", "motion_template/*", "motion_generator/motion_generator_hubert_chinese.pt"])
snapshot_download("TencentGameMate/chinese-hubert-base", local_dir=f"{w}/TencentGameMate:chinese-hubert-base",
                  allow_patterns=["config.json", "preprocessor_config.json", "pytorch_model.bin"])
snapshot_download("KwaiVGI/LivePortrait", local_dir=w,
                  allow_patterns=["liveportrait/base_models/*", "liveportrait/retargeting_models/*", "liveportrait/landmark.onnx"])
print("weights ok")
PY
[[ -d $JV/pretrained_weights/insightface ]] && { echo "❌ insightface weights found in $JV/pretrained_weights: delete them (non-commercial)."; exit 1; }

echo "▶ .gitignore"
for line in "tools/aiface/" "work/"; do grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore; done
echo "✅ AI talking face ready: tools/summary/aiface.py"
