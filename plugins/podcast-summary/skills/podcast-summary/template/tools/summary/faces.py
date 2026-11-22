"""
Head-and-shoulders portraits for the cast intro and the speaker bubble: one 600×800 JPEG per person, cropped around
the biggest face YuNet finds in a frame of the episode.

    .venv/bin/python tools/summary/faces.py <slug> <who> <source.mp4> <t> [<who> <t> …]

→ public/summary/faces/<slug>/<who>.jpg  (set "faces": "summary/faces/<slug>" in script.json). Look at each one: pick
a time where the person faces the camera in their own shot, eyes open, nothing over the face.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
YUNET = ROOT / "tools/models/yunet/face_detection_yunet_2023mar.onnx"


def grab(src: str, t: float) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True).stdout
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)


def main() -> None:
    slug, src, pairs = sys.argv[1], sys.argv[3], sys.argv[2:3] + sys.argv[4:]
    if len(pairs) % 2:
        sys.exit("usage: faces.py <slug> <who> <source.mp4> <t> [<who> <t> …]")
    out = ROOT / "public/summary/faces" / slug
    out.mkdir(parents=True, exist_ok=True)
    for who, t in zip(pairs[0::2], pairs[1::2]):
        img = grab(src, float(t))
        h, w = img.shape[:2]
        det = cv2.FaceDetectorYN.create(str(YUNET), "", (w, h), 0.7)
        _, found = det.detect(img)
        if found is None:
            sys.exit(f"{who}: no face at {t}s, try another time")
        x, y, fw, fh = max(found, key=lambda r: r[2] * r[3])[:4]
        cx, cy = x + fw / 2, y + fh / 2
        ch = min(h, 3.2 * fh)
        cw = ch * 0.75
        x0 = int(np.clip(cx - cw / 2, 0, w - cw))
        y0 = int(np.clip(cy - 0.42 * ch, 0, h - ch))
        crop = cv2.resize(img[y0:y0 + int(ch), x0:x0 + int(cw)], (600, 800), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(out / f"{who}.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"✅ {out / f'{who}.jpg'}")


if __name__ == "__main__":
    main()
