#!/usr/bin/env bash
# Upscale every cut-out PNG 4× with Real-ESRGAN (BSD-3-Clause), keeping transparency.
# Optional: install it with WITH_UPSCALE=1 tools/setup_cartoon.sh.
#   tools/upscale_cuts.sh <src_dir> <out_dir>                 # flat 2D art (anime model)
#   MODEL=realesrgan-x4plus tools/upscale_cuts.sh <src> <out>  # painted or 3D-looking art
set -euo pipefail
SRC=${1:?usage: tools/upscale_cuts.sh <src_dir> <out_dir>}
OUT=${2:?usage: tools/upscale_cuts.sh <src_dir> <out_dir>}
R=tools/realesrgan/realesrgan-ncnn-vulkan
[ -x "$R" ] || { echo "❌ Real-ESRGAN not installed. Run: WITH_UPSCALE=1 tools/setup_cartoon.sh"; exit 1; }
MODEL=${MODEL:-realesrgan-x4plus-anime}
n=0
while IFS= read -r f; do
  mkdir -p "$OUT/$(dirname "$f")"
  # Skip files already done, so a re-run only upscales new cut-outs.
  [ -f "$OUT/$f" ] || "$R" -i "$SRC/$f" -o "$OUT/$f" -n "$MODEL" -m tools/realesrgan/models > /dev/null 2>&1
  n=$((n + 1))
done < <(cd "$SRC" && find . -name '*.png' | sort)
echo "Upscaled $n images → $OUT"
