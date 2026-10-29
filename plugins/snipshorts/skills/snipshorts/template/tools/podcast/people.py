"""Who is on screen in each shot, for name tags. Matches clothing colour, never faces.

  people.py <clip-id> --sheet out.jpg          # one tile per person per shot, labelled s<shot>.<slot>
  people.py <clip-id> --label s2.0=guest ...   # store those signatures as references in source.json
  people.py <clip-id>                          # assign names to every shot (writes clip.json "who")

source.json "people": [{"key": "guest", "name": "Jane Doe", "role": "Author", "refs": [[...]]}]
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MAX_DIST = 0.45  # Bhattacharyya distance; above this a person is left unnamed


def paths(clip_id):
    d = ROOT / "public/podcast-shorts" / clip_id
    folder = ROOT / "podcasts" / clip_id.rsplit("-", 1)[0]
    return d, folder / "source.json"


def dist(a, b):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    return float(cv2.compareHist(a, b, cv2.HISTCMP_BHATTACHARYYA))


def sheet(clip_id, out):
    d, _ = paths(clip_id)
    clip = json.loads((d / "clip.json").read_text())
    cap = cv2.VideoCapture(str(d / "source.mp4"))
    tiles = []
    for sh in clip["shots"]:
        t = (sh["start"] + sh["end"]) / 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * clip["fps"]))
        ok, frame = cap.read()
        if not ok:
            continue
        key = min(clip["crop"], key=lambda k: abs(k["t"] - t))
        faces = [key["a"], key["b"]] if sh["mode"] == "split" else [key]
        for slot, f in enumerate(faces):
            if sh["sigs"][slot] is None:
                continue
            x0, x1 = int(max(0, f["cx"] - f["fh"] * 1.6)), int(min(clip["width"], f["cx"] + f["fh"] * 1.6))
            y0, y1 = int(max(0, f["cy"] - f["fh"])), int(min(clip["height"], f["cy"] + f["fh"] * 3))
            tile = cv2.resize(frame[y0:y1, x0:x1], (240, 300))
            cv2.putText(tile, f"s{sh['shot']}.{slot}", (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
            tiles.append(tile)
    rows = [np.hstack(tiles[i:i + 6] + [np.zeros_like(tiles[0])] * (6 - len(tiles[i:i + 6]))) for i in range(0, len(tiles), 6)]
    cv2.imwrite(out, np.vstack(rows))
    print(f"{len(tiles)} tiles → {out}")


def label(clip_id, pairs):
    d, src = paths(clip_id)
    clip = json.loads((d / "clip.json").read_text())
    source = json.loads(src.read_text())
    people = {p["key"]: p for p in source.get("people", [])}
    for pair in pairs:
        ref, key = pair.split("=")
        shot, slot = ref[1:].split(".")
        sh = next(s for s in clip["shots"] if s["shot"] == int(shot))
        if key not in people:
            raise SystemExit(f"unknown person '{key}': add it to {src} people first")
        people[key].setdefault("refs", []).append(sh["sigs"][int(slot)])
    source["people"] = list(people.values())
    src.write_text(json.dumps(source, indent=2, ensure_ascii=False))
    print(f"stored {len(pairs)} reference(s) in {src}")


def assign(clip_id):
    d, src = paths(clip_id)
    clip = json.loads((d / "clip.json").read_text())
    people = [p for p in json.loads(src.read_text()).get("people", []) if p.get("refs")]
    for sh in clip["shots"]:
        who = []
        for sig in sh["sigs"]:
            best = min(((min(dist(sig, r) for r in p["refs"]), p) for p in people), default=(9, None), key=lambda x: x[0]) if sig else (9, None)
            who.append(best[1]["key"] if best[1] and best[0] < MAX_DIST else None)
        sh["who"] = who
    clip["people"] = {p["key"]: {"name": p["name"], "role": p.get("role", "")} for p in people}
    (d / "clip.json").write_text(json.dumps(clip, ensure_ascii=False))
    print(clip_id + ": " + ", ".join(f"s{s['shot']}={'+'.join(w or '?' for w in s['who'])}" for s in clip["shots"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("--sheet")
    ap.add_argument("--label", nargs="+")
    args = ap.parse_args()
    if args.sheet:
        sheet(args.clip_id, args.sheet)
    elif args.label:
        label(args.clip_id, args.label)
    else:
        assign(args.clip_id)
