#!/usr/bin/env bash
# Character sheets → a talking bust rig (and pose cut-outs) for the _Episode composition.
#
#   tools/rig_character.sh <series> <character> <face-sheet.png> [pose-sheet.png]
#
# The face sheet is a 4×3 grid of the same bust on white (see the cartoonsmith skill):
#   row 1: closed (A/X) · slightly open (B) · open (C) · wide open (D)
#   row 2: round O (E) · pucker OO (F) · teeth on lip F/V (G) · tongue L (H)
#   row 3: laugh · angry · shocked · sad
# Writes public/<series>/cast/<character>/bust/{base,mouth-*,<expression>}.png + rig.json,
# and public/<series>/cast/<character>/poses/<name>.png.
#   UPSCALE=1      4× Real-ESRGAN before aligning (small sheets; WITH_UPSCALE=1 tools/setup_cartoon.sh)
#   REMBG=1        AI matte for white clothes on the white page (needs rembg)
#   MAP=...        another face order, e.g. MAP=A=00,B=01,...,X=00,laugh=08
#   POSES="apose wave sit"   names for the pose cut-outs, in reading order
set -euo pipefail
SERIES=${1:?usage: tools/rig_character.sh <series> <character> <face-sheet> [pose-sheet]}
WHO=${2:?usage: tools/rig_character.sh <series> <character> <face-sheet> [pose-sheet]}
FACES=${3:?usage: tools/rig_character.sh <series> <character> <face-sheet> [pose-sheet]}
POSE_SHEET=${4:-}
PY=.venv/bin/python
DEST=public/$SERIES/cast/$WHO
WORK=art/$SERIES/$WHO/cuts
MAP=${MAP:-A=00,B=01,C=02,D=03,E=04,F=05,G=06,H=07,X=00,laugh=08,angry=09,shocked=10,sad=11}
REMBG_FLAG=${REMBG:+--rembg}

rm -rf "$WORK/faces" "$WORK/faces-hd"
$PY tools/split_sheet.py "$FACES" "$WORK/faces" --prefix face --grid 4x3 $REMBG_FLAG
n=$(ls "$WORK/faces" | wc -l | tr -d ' ')
[ "$n" -eq 12 ] || echo "⚠️  Found $n faces, expected 12. Check $WORK/faces and the sheet layout."
SRC=$WORK/faces
if [ -n "${UPSCALE:-}" ]; then tools/upscale_cuts.sh "$WORK/faces" "$WORK/faces-hd"; SRC=$WORK/faces-hd; fi
rm -rf "$DEST/bust"
$PY tools/viseme_align.py "$SRC" "$DEST/bust" "$MAP"

if [ -n "$POSE_SHEET" ]; then
  rm -rf "$WORK/poses" "$DEST/poses"
  $PY tools/split_sheet.py "$POSE_SHEET" "$WORK/poses" --prefix pose $REMBG_FLAG
  mkdir -p "$DEST/poses"
  i=0
  for f in "$WORK"/poses/pose-*.png; do
    name=$(echo "${POSES:-}" | awk -v k=$((i + 1)) '{print $k}')
    cp "$f" "$DEST/poses/${name:-$(basename "$f" .png)}.png"
    i=$((i + 1))
  done
  echo "Poses → $DEST/poses: $(ls "$DEST/poses" | tr '\n' ' ')"
fi
echo "✅ $WHO rigged. Look at $DEST/bust/base.png and a mouth-D.png before using it."
