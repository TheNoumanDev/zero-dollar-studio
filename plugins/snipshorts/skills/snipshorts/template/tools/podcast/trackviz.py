"""QA sheet for speaker tracking: the 9:16 crop window on source frames.
Usage: .venv/bin/python tools/podcast/trackviz.py <clip-id> <out.jpg> [n]"""
import json, sys
import cv2, numpy as np
d = f"public/podcast-shorts/{sys.argv[1]}/"
c = json.load(open(d + "clip.json")); cap = cv2.VideoCapture(d + "source.mp4")
n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
W, H = c["width"], c["height"]; cw = H * 9 / 16
tiles = []
for t in np.linspace(0.5, c["duration"] - 0.5, n):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * c["fps"])); ok, f = cap.read()
    k = min(c["crop"], key=lambda k: abs(k["t"] - t))
    x0 = int(max(0, min(W - cw, k["cx"] - cw / 2)))
    cv2.rectangle(f, (x0, 0), (x0 + int(cw), H - 1), (0, 255, 255), 8)
    words = " ".join(w["w"] for w in c["words"] if t - 0.8 <= w["s"] <= t + 0.4)
    cv2.putText(f, f"{t:.1f}s {words[:38]}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)
    tiles.append(cv2.resize(f, (480, 270)))
while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(sys.argv[2], np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]))
