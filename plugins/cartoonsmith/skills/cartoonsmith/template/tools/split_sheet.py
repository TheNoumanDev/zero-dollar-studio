"""
Split a character sheet (drawings on a plain white page) into separate transparent PNGs.

    .venv/bin/python tools/split_sheet.py <sheet.png|jpg> <out_dir> [--prefix pose] [--min-area 0.004]
    .venv/bin/python tools/split_sheet.py faces.png <out_dir> --prefix face --grid 4x3   # face sheets

Each drawing = one blob of non-white pixels (blobs closer than a few px are merged,
so a held prop stays with its owner). Small blobs (text labels, sweat drops
far from a body) are dropped. Output is sorted in reading order (rows, then left to
right), keyed out from the white page with holes inside the outline kept opaque,
and saved as <prefix>-NN.png.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("sheet")
ap.add_argument("out")
ap.add_argument("--prefix", default="pose")
ap.add_argument("--min-area", type=float, default=0.004, help="fraction of the sheet's area")
ap.add_argument("--join", type=int, default=15, help="px gap still treated as one drawing")
ap.add_argument("--rembg", action="store_true", help="AI matte + hole fill (white clothes on a white page; needs rembg)")
ap.add_argument("--grid", help="COLSxROWS: cut equal cells instead (face sheets, where busts touch)")
args = ap.parse_args()

rgb = np.asarray(Image.open(args.sheet).convert("RGB"))
H, W = rgb.shape[:2]
ink = (rgb.min(axis=2) < 232).astype(np.uint8)
# Merge the parts of one drawing (detached props, sparkles) but keep neighbours apart.
merged = cv2.dilate(ink, np.ones((args.join, args.join), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(merged)
boxes = []
for k in range(1, n):
    x, y, w, h, area = stats[k]
    if w * h < args.min_area * W * H or h < 0.06 * H:
        continue  # text labels and specks
    boxes.append((x, y, w, h, k))

# Reading order: group into rows by vertical centre.
boxes.sort(key=lambda b: b[1] + b[3] / 2)
rows: list[list[tuple]] = []
for b in boxes:
    cy = b[1] + b[3] / 2
    if rows and abs(cy - np.mean([r[1] + r[3] / 2 for r in rows[-1]])) < 0.5 * b[3]:
        rows[-1].append(b)
    else:
        rows.append([b])
ordered = [b for r in rows for b in sorted(r, key=lambda b: b[0])]
if args.grid:
    # Equal cells; inside each cell keep the biggest blob (the bust, not a stray label).
    cols, nrows = (int(v) for v in args.grid.split("x"))
    cell = np.zeros_like(lab)
    ordered, rows = [], [None] * nrows
    for r in range(nrows):
        for c in range(cols):
            y0, y1, x0, x1 = r * H // nrows, (r + 1) * H // nrows, c * W // cols, (c + 1) * W // cols
            m, l2, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(ink[y0:y1, x0:x1], np.ones((5, 5), np.uint8)))
            if m < 2:
                continue
            j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            k = len(ordered) + 1
            cell[y0:y1, x0:x1][l2 == j] = k
            x, y, w, h = st[j, :4]
            # The bust's bottom edge has no outline: stop at the last row with dark
            # ink so the white page below can't flood into white clothes.
            dark = (rgb[y0 + y : y0 + y + h, x0 + x : x0 + x + w].min(axis=2) < 120).sum(axis=1)
            inked = np.where(dark >= 2)[0]
            if len(inked):
                h = int(inked[-1]) + 1
            ordered.append((x0 + x, y0 + y, w, h, k))
    lab = cell

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
for i, (x, y, w, h, k) in enumerate(ordered):
    pad = 6
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + (0 if args.grid else pad))
    crop = rgb[y0:y1, x0:x1]
    mine = (lab[y0:y1, x0:x1] == k)  # only this drawing's blob, not a neighbour's
    # Background = near-white connected to the crop border; everything enclosed stays.
    white = ((crop.min(axis=2) > 235) & mine | ~mine).astype(np.uint8)
    flood = white.copy()
    mask = np.zeros((flood.shape[0] + 2, flood.shape[1] + 2), np.uint8)
    for sx in range(0, flood.shape[1], 4):
        for sy in (0,) if args.grid else (0, flood.shape[0] - 1):  # busts are open at the bottom
            if flood[sy, sx] == 1:
                cv2.floodFill(flood, mask, (sx, sy), 2)
    # Busts: white clothes run off the cell's lower sides with no outline, so only
    # seed the sides above the shoulders.
    for sy in range(0, int(flood.shape[0] * (0.45 if args.grid else 1)), 4):
        for sx in (0, flood.shape[1] - 1):
            if flood[sy, sx] == 1:
                cv2.floodFill(flood, mask, (sx, sy), 2)
    alpha = np.where(flood == 2, 0, 255).astype(np.uint8)
    # Soft edge: semi-transparent where the anti-aliased outline meets white.
    edge = cv2.dilate((alpha == 0).astype(np.uint8), np.ones((3, 3), np.uint8)) & (alpha == 255)
    lum = crop.min(axis=2).astype(np.float32)
    alpha = np.where(edge > 0, np.clip((255 - lum) * 3, 0, 255), alpha).astype(np.uint8)
    if args.rembg:
        from rembg import new_session, remove

        global _session
        _session = globals().get("_session") or new_session("isnet-general-use")
        a = np.asarray(remove(Image.fromarray(crop), session=_session))[..., 3]
        # Union with the white-key matte (it keeps white clothes the AI matte drops),
        # then close small gaps so speckles in the clothes become solid.
        solid = ((a > 24) | (alpha > 128)).astype(np.uint8)
        solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        a = np.maximum(a, alpha)
        # The shirt runs off the cell sides with no outline. Its shape is the convex
        # hull of the drawn ink (shoulder lines slope down to the edges): fill the
        # hull in the bottom third so the shoulders are solid and keep their slope.
        dark = np.argwhere(crop.min(axis=2) < 110)[:, ::-1].astype(np.int32)
        if len(dark) > 3:
            hull = np.zeros_like(solid)
            cv2.fillConvexPoly(hull, cv2.convexHull(dark), 1)
            # start where the shoulder line reaches a side edge (below the ears)
            dk = crop.min(axis=2) < 110
            edge_rows = np.where(dk[:, :8].any(axis=1) | dk[:, -8:].any(axis=1))[0]
            edge_rows = edge_rows[edge_rows > solid.shape[0] * 0.55]
            y_cut = int(edge_rows[0]) if len(edge_rows) else solid.shape[0]
            solid[y_cut:] |= hull[y_cut:]
        bottom = np.where(solid[-1] > 0)[0]
        if len(bottom):  # close the open bottom of a bust before filling holes
            solid[-1, bottom.min() : bottom.max() + 1] = 1
        holes = solid.copy()
        cv2.floodFill(holes, np.zeros((holes.shape[0] + 2, holes.shape[1] + 2), np.uint8), (0, 0), 1)
        inside = solid | (1 - holes)
        core = cv2.erode(inside, np.ones((3, 3), np.uint8))
        alpha = np.where(core > 0, 255, np.where(inside > 0, np.maximum(a, 128), 0)).astype(np.uint8)
    Image.fromarray(np.dstack([crop, alpha]), "RGBA").save(out / f"{args.prefix}-{i:02d}.png")
print(f"{args.sheet}: {len(ordered)} drawings in {len(rows)} rows → {out}/{args.prefix}-NN.png")
