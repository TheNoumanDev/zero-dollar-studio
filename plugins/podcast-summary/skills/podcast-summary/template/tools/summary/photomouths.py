"""
Real mouth shapes for a photo cut-out: take the person's OWN mouth from nearby frames of the same camera shot. Every
frame within ±window s of the base still is aligned to it (YuNet 5 points, similarity transform), and only the lips +
chin are blended into the base. Frames are ranked by how open the mouth is, and `levels` of them become
mouth0…N.png (0 = closed … N-1 = wide), all with the base's own cut-out alpha (rembg), so only the mouth changes.
mouth0.png is also the source image for the AI talking face (aiface.py prep) and a clean thumbnail cut-out.

    .venv/bin/python tools/summary/photomouths.py <slug> <who> <source.mp4> <t> auto|<x0,y0,x1,y1> [--window 12] [--levels 4]

Pick a base time where the person is talking in their own close-up shot, eyes open, hands away from the chin.
→ public/summary/photos/<slug>/<who>/mouth0..N.png + sheet.jpg (check it), and prints the `photo` block for cast[who].look.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
YUNET = ROOT / "tools/models/yunet/face_detection_yunet_2023mar.onnx"


def size(src: str) -> tuple[int, int]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                         capture_output=True, text=True, check=True).stdout.strip().split(",")
    return int(out[0]), int(out[1])


W, H = 1920, 1080  # set from the source in main()


def frames(src: str, a: float, b: float, fps: int = 10):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", src, "-vf", f"fps={fps}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    i = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        yield a + i / fps, np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        i += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"), ap.add_argument("who"), ap.add_argument("src"), ap.add_argument("t", type=float), ap.add_argument("box")
    ap.add_argument("--window", type=float, default=12), ap.add_argument("--levels", type=int, default=4)
    o = ap.parse_args()
    global W, H
    W, H = size(o.src)
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (W, H), 0.7)

    def face(img):
        _, F = det.detect(img)
        return None if F is None else max(F, key=lambda r: r[2] * r[3])

    base = next(f for _, f in frames(o.src, o.t, o.t + 0.2))
    fb = face(base)
    pts_b = fb[4:14].reshape(5, 2).astype(np.float32)
    mc = pts_b[3:5]
    mx, my = float(mc[:, 0].mean()), float(mc[:, 1].mean())
    mw = float(np.linalg.norm(mc[0] - mc[1]))
    fh = float(fb[3])

    # Blend region: an ellipse over the lips and chin (feathered), so cheeks/eyes always stay the base's.
    mask = np.zeros((H, W), np.float32)
    cv2.ellipse(mask, (int(mx), int(my + 0.22 * mw)), (int(0.95 * mw), int(0.9 * mw)), 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), 0.18 * mw)[..., None]
    # Openness probe: dark pixels just below the lip line, between the corners.
    py0, py1 = int(my - 0.08 * mw), int(my + 0.32 * mw)
    px0, px1 = int(mx - 0.32 * mw), int(mx + 0.32 * mw)

    def openness(img):
        g = cv2.cvtColor(img[py0:py1, px0:px1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        return float((g < 0.55 * np.median(g)).mean())

    cands = []
    for t, img in frames(o.src, o.t - o.window, o.t + o.window):
        f = face(img)
        if f is None:
            continue
        pts = f[4:14].reshape(5, 2).astype(np.float32)
        M, _ = cv2.estimateAffinePartial2D(pts, pts_b)
        if M is None:
            continue
        s = float(np.hypot(M[0, 0], M[1, 0]))
        warped_pts = (np.c_[pts, np.ones(5)] @ M.T)
        err = float(np.abs(warped_pts - pts_b).max())
        if abs(s - 1) > 0.08 or err > 0.06 * fh:
            continue  # different shot, head turned, or too far moved: the patch would not line up
        al = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        cands.append((openness(al), err, t, al))
    if len(cands) < o.levels:
        raise SystemExit(f"only {len(cands)} usable frames near {o.t}s: try another base time or a wider --window")
    cands.sort(key=lambda c: c[0])
    lo, hi = cands[0][0], cands[-1][0]
    picks = []
    for k in range(o.levels):
        target = lo + (hi - lo) * (k / (o.levels - 1)) ** 0.8
        best = min(cands, key=lambda c: abs(c[0] - target) + 0.002 * c[1])
        picks.append(best)
    print("picked", [(round(c[0], 3), round(c[2], 1)) for c in picks])

    # Cut-out alpha from the base (the same for every mouth), cropped to the box.
    if o.box == "auto":  # head and shoulders around the base face
        cx, cy, fw = fb[0] + fb[2] / 2, fb[1] + fb[3] / 2, fb[2]
        x0, y0, x1, y1 = int(max(0, cx - 1.45 * fw)), int(max(0, cy - 1.3 * fh)), int(min(W, cx + 1.45 * fw)), int(min(H, cy + 1.85 * fh))
    else:
        x0, y0, x1, y1 = (int(v) for v in o.box.split(","))
    crop = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)).crop((x0, y0, x1, y1))
    cut = np.array(remove(crop, session=new_session("isnet-general-use")))
    a = cut[..., 3] > 40
    lab, n = ndimage.label(a)
    if n > 1:
        sizes = ndimage.sum(a, lab, range(1, n + 1))
        cut[..., 3] = np.where(lab == 1 + int(np.argmax(sizes)), cut[..., 3], 0)
    solid = ndimage.binary_fill_holes(cut[..., 3] > 40)
    alpha = np.where(solid & (cut[..., 3] < 200), 255, cut[..., 3]).astype(np.float32)
    h, w = alpha.shape
    fx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / (0.06 * w), 0, 1)
    fy = np.clip((h - 1 - np.arange(h)) / (0.08 * h), 0, 1)
    alpha *= fx[None, :] * fy[:, None]
    bb = Image.fromarray(alpha.astype(np.uint8)).point(lambda v: 255 if v > 60 else 0).getbbox()

    out = ROOT / "public/summary/photos" / o.slug / o.who
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for k, (_, _, t, al) in enumerate(picks):
        mixed = base.astype(np.float32) * (1 - mask) + al.astype(np.float32) * mask
        rgb = cv2.cvtColor(np.clip(mixed, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)[y0:y1, x0:x1]
        im = Image.fromarray(rgb).filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
        im.putalpha(Image.fromarray(alpha.astype(np.uint8)))
        im = im.crop(bb)
        im.save(out / f"mouth{k}.png")
        tiles.append(im.crop((int(mx - x0 - bb[0] - 1.6 * mw), int(my - y0 - bb[1] - 1.4 * mw),
                              int(mx - x0 - bb[0] + 1.6 * mw), int(my - y0 - bb[1] + 1.4 * mw))).resize((300, 262)))
    sheet = Image.new("RGB", (300 * len(tiles), 262), (40, 40, 40))
    for k, ti in enumerate(tiles):
        sheet.paste(ti, (300 * k, 0), ti)
    sheet.save(out / "sheet.jpg")
    iw, ih = bb[2] - bb[0], bb[3] - bb[1]
    print(json.dumps({"src": f"summary/photos/{o.slug}/{o.who}", "w": iw, "h": ih, "levels": o.levels}))


if __name__ == "__main__":
    main()
