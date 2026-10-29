"""
Build a lip-sync bust rig from a character's face-sheet cut-outs.

    .venv/bin/python tools/viseme_align.py <faces_dir> <out_dir> A=00,B=01,C=02,D=03,E=04,F=05,G=06,H=07,X=00 [laugh=08,angry=09,...]

Every face is aligned onto the base face (the "A" one) with OpenCV ECC on the
eyes/head area, so swapping faces never makes the head jump. Writes, on one
shared canvas:
  base.png            the bust for the closed mouth
  mouth-<S>.png       each Rhubarb shape (A–H, X) as a full aligned face
  <expression>.png    extra full faces (laugh, angry, …)
  rig.json            canvas size and the mouth box (where the mouth shapes differ)
The composition shows base.png and overlays the current mouth image only inside
the mouth box (soft mask), so eyes and outline stay rock steady.
"""

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

faces_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
mapping = dict(kv.split("=") for kv in ",".join(sys.argv[3:]).split(",") if kv)
out_dir.mkdir(parents=True, exist_ok=True)


def load(idx: str) -> np.ndarray:
    return np.asarray(Image.open(faces_dir / f"face-{int(idx):02d}.png").convert("RGBA"))


base = load(mapping["A"])
H, W = base.shape[:2]
pad = 40
canvas = (H + 2 * pad, W + 2 * pad)


def place(img: np.ndarray) -> np.ndarray:
    c = np.zeros((*canvas, 4), np.uint8)
    h, w = min(img.shape[0], H), min(img.shape[1], W)
    c[pad : pad + h, pad : pad + w] = img[:h, :w]
    return c


base_c = place(base)
gray_b = cv2.cvtColor(base_c[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32)
# Align on the upper face (hair, eyes, ears), not the mouth that changes.
weight = np.zeros(canvas, np.uint8)
weight[pad : pad + int(H * 0.5), pad : pad + W] = 255
weight &= (base_c[..., 3] > 128).astype(np.uint8) * 255


def align(img: np.ndarray) -> np.ndarray:
    c = place(img)
    g = cv2.cvtColor(c[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        _, warp = cv2.findTransformECC(gray_b, g, warp, cv2.MOTION_AFFINE,
                                       (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), weight, 5)
    except cv2.error:
        print("  ECC did not converge; using unaligned")
    return cv2.warpAffine(c, warp, (canvas[1], canvas[0]), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)


Image.fromarray(base_c).save(out_dir / "base.png")
aligned = {}
for name, idx in mapping.items():
    a = base_c if idx == mapping["A"] else align(load(idx))
    aligned[name] = a
    fname = f"mouth-{name}.png" if len(name) == 1 else f"{name}.png"
    Image.fromarray(a).save(out_dir / fname)

# Mouth box: where the mouth shapes differ most from each other.
keys = [k for k in aligned if len(k) == 1]
shapes = [aligned[k][..., :3].astype(np.float32) for k in keys]
inside = np.min(np.stack([aligned[k][..., 3] for k in keys]), axis=0) > 200  # on every face
diff = np.std(np.stack(shapes), axis=0).mean(axis=2) * inside
diff[: int(canvas[0] * 0.35)] = 0  # hair and eyes
diff[int(canvas[0] * 0.85) :] = 0  # bust edge
diff = cv2.GaussianBlur(diff, (0, 0), 8)
m = (diff > np.percentile(diff[diff > 0], 97)).astype(np.uint8) if (diff > 0).any() else diff.astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])) if n > 1 else 0
x, y, w, h = (int(v) for v in st[k, :4]) if k else (canvas[1] // 3, canvas[0] // 2, canvas[1] // 3, canvas[0] // 6)
grow = 0.25
box = {"x": max(0, int(x - w * grow)), "y": max(0, int(y - h * grow)), "w": int(w * (1 + 2 * grow)), "h": int(h * (1 + 2 * grow))}
rig = {"width": canvas[1], "height": canvas[0], "mouth": box, "shapes": sorted(k for k in aligned if len(k) == 1),
       "expressions": sorted(k for k in aligned if len(k) > 1)}
(out_dir / "rig.json").write_text(json.dumps(rig, indent=1))
print(f"{out_dir}: {len(aligned)} faces aligned, mouth box {box}")
