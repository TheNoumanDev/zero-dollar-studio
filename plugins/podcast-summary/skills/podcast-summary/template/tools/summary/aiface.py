"""
AI talking face for a real-photo cut-out: JoyVASA turns the person's own voice into face motion and LivePortrait
renders it onto their still, so lips, blinks and small head moves come from the model, not from pasted patches.
Set it up once with tools/summary/setup-aiface.sh (patched so InsightFace is never loaded). Runs locally.

    W=work/aiface/<slug>/<who>
    .venv/bin/python tools/summary/aiface.py prep   public/summary/photos/<slug>/<who>/mouth0.png $W   # grey-backed image + 512 px face crop
    .venv/bin/python tools/summary/aiface.py voice  <slug> <who> $W          # their lines back to back → $W/voice.wav + segs.json
    AIFACE_CALM=0.3 .venv/bin/python tools/summary/aiface.py run $W $W/voice.wav   # JoyVASA → $W/out/*.mp4 (slow)
    .venv/bin/python tools/summary/aiface.py frames $W $W/out/<file>.mp4 <slug> <who>   # → public/summary/photos/<slug>/<who>/ai/
    .venv/bin/python tools/summary/aiface.py block  <slug> <who> $W          # prints the photo.ai block for script.json
    .venv/bin/python tools/summary/aiface.py incr   <slug> <old script.json> <old manifest.json> <tag>   # after a re-cut

The cut-out is put on flat grey so a colour key can take the background off again per frame (it follows the head
when it moves, unlike a fixed alpha). AIFACE_CALM (0-1) scales the generated eye/brow motion; 0.3 keeps real faces
from going wide-eyed, lips keep full motion.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
YUNET = ROOT / "tools/models/yunet/face_detection_yunet_2023mar.onnx"
JV = ROOT / "tools/aiface/JoyVASA"
GREY = (128, 128, 128)
FEATHER = 40


def key_out(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    bg = np.array(GREY, np.float32)
    dist = np.linalg.norm(rgb.astype(np.float32) - bg, axis=2)
    fill = (dist < 14).astype(np.uint8)
    conn = np.zeros((h + 2, w + 2), np.uint8)
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0)):
        if fill[seed[1], seed[0]] == 1:
            cv2.floodFill(fill, conn, seed, 2)
    is_bg = fill == 2
    alpha = np.where(is_bg, 0.0, 1.0).astype(np.float32)
    soft = np.clip((dist - 8) / 24, 0, 1)
    edge = cv2.dilate(is_bg.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~is_bg
    alpha[edge] = soft[edge]
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    return np.dstack([rgb, (alpha * 255).astype(np.uint8)])


def prep(cut: str, work: str) -> None:
    w_ = Path(work)
    w_.mkdir(parents=True, exist_ok=True)
    im = Image.open(cut).convert("RGBA")
    # pad so the face crop never leaves the image
    pad = im.width // 2
    full = Image.new("RGB", (im.width + 2 * pad, im.height + pad), GREY)
    full.paste(im, (pad, pad), im)
    full.save(w_ / "full.png")
    bgr = cv2.cvtColor(np.asarray(full), cv2.COLOR_RGB2BGR)
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (bgr.shape[1], bgr.shape[0]), 0.6)
    _, F = det.detect(bgr)
    f = max(F, key=lambda r: r[2] * r[3])
    cx, cy, fh = f[0] + f[2] / 2, f[1] + f[3] / 2, f[3]
    size = int(2.3 * fh)
    x0, y0 = int(cx - size / 2), int(cy - 0.5 * size)
    json.dump({"x0": x0, "y0": y0, "size": size, "pad": pad, "w": im.width, "h": im.height}, open(w_ / "crop.json", "w"))
    full.crop((x0, y0, x0 + size, y0 + size)).resize((512, 512), Image.LANCZOS).save(w_ / "source.png")
    print(w_ / "source.png", size)


def run(work: str, wav: str) -> None:
    w_ = Path(work).resolve()
    src = w_ / "source.png"
    while not src.exists():
        src = src.parent.parent / "source.png"
    env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK="1")
    subprocess.run([str(JV / ".venv/bin/python"), "inference.py", "-r", str(src), "-a", str(Path(wav).resolve()),
                    "-o", str(w_ / "out"), "--animation_mode", "human", "--cfg_scale", "2.0"], cwd=JV, env=env, check=True)


GAP = 0.5  # silence between one person's lines in their voice track (the speech gate closes the mouth there)


def voice(slug: str, who: str, work: str) -> None:
    """One voice track per person: their lines from public/summary/<slug>/audio.wav back to back, plus segs.json
    mapping each composition line (start/end) to its offset in the track."""
    m = json.load(open(ROOT / f"public/summary/{slug}/manifest.json"))
    w_ = Path(work)
    w_.mkdir(parents=True, exist_ok=True)
    segs, parts, off = [], [], GAP
    for l in m["lines"]:
        if l["who"] != who:
            continue
        a, b = l["start"] - 0.1, l["end"] + 0.1
        segs.append({"start": round(a, 3), "end": round(b, 3), "off": round(off, 3)})
        parts.append((a, b))
        off += (b - a) + GAP
    flt = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,apad=pad_dur={GAP}[s{i}];" for i, (a, b) in enumerate(parts))
    flt = f"anullsrc=r=16000:cl=mono,atrim=0:{GAP}[lead];" + flt.replace("[0:a]", "[0:a]aresample=16000,aformat=channel_layouts=mono,")
    flt += "[lead]" + "".join(f"[s{i}]" for i in range(len(parts))) + f"concat=n={len(parts) + 1}:v=0:a=1[o]"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(ROOT / f"public/summary/{slug}/audio.wav"), "-filter_complex", flt,
                    "-map", "[o]", "-ar", "16000", "-ac", "1", str(w_ / "voice.wav")], check=True)
    json.dump(segs, open(w_ / "segs.json", "w"))
    print(who, len(segs), "lines", round(off, 1), "s")


def frames(work: str, src: str, slug: str, who: str, dest: str = "ai") -> None:
    """Paste back + key every frame and write them as WebP (alpha) to public/summary/photos/<slug>/<who>/ai/,
    for MascotKit's photo.ai (frame-accurate <Img>, no video seeking)."""
    w_ = Path(work)
    while not (w_ / "crop.json").exists():  # a sub-run dir (incr) uses its person's crop
        w_ = w_.parent
    c = json.load(open(w_ / "crop.json"))
    full = Image.open(w_ / "full.png").convert("RGB")
    size, x0, y0 = c["size"], c["x0"], c["y0"]
    mask = Image.new("L", (size, size), 0)
    mask.paste(Image.new("L", (size - 2 * FEATHER, size - 2 * FEATHER), 255), (FEATHER, FEATHER))
    mask = mask.filter(ImageFilter.GaussianBlur(FEATHER / 2))
    box = (c["pad"], c["pad"], c["pad"] + c["w"], c["pad"] + c["h"])
    out = ROOT / "public/summary/photos" / slug / who / dest
    out.mkdir(parents=True, exist_ok=True)
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src],
                         capture_output=True, text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        fi = Path(tmp)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", src, str(fi / "%05d.png")], check=True)
        files = sorted(fi.glob("*.png"))
        for i, f in enumerate(files):
            face = Image.open(f).convert("RGB").resize((size, size), Image.LANCZOS)
            fr = full.copy()
            fr.paste(face, (x0, y0), mask)
            rgba = key_out(np.asarray(fr.crop(box)))
            rgba[..., 3] = np.minimum(rgba[..., 3], cv2.erode(rgba[..., 3], np.ones((3, 3), np.uint8)))  # choke the grey fringe
            Image.fromarray(rgba).save(out / f"{i:05d}.webp", quality=88, method=4)
    n, (num, den) = len(files), fps.split("/")
    json.dump({"fps": int(num) / int(den), "n": n}, open(out / "info.json", "w"))
    print(out, n, "frames", fps)


def _flat(script: dict) -> list:
    return [(l[0], l[1], l[2]) for sc in script["scenes"] for l in sc["lines"]]


def incr(slug: str, old_script: str, old_manifest: str, tag: str) -> None:
    """After re-cutting: reuse the AI frames of every line whose source in/out didn't change, and write a voice
    track of only the new/changed lines per person (<work>/<tag>/voice.wav + pending.json) to run and add as
    frames dir ai-<tag>. Manifest lines follow script lines one to one, in order."""
    new_s = json.load(open(ROOT / f"summaries/{slug}/script.json"))
    new_m = json.load(open(ROOT / f"public/summary/{slug}/manifest.json"))
    old_s, old_m = json.load(open(old_script)), json.load(open(old_manifest))
    old_look = {w: c["look"]["photo"]["ai"] for w, c in old_s["cast"].items()}
    old_seg = {}  # (who, in, out) → (seg, dir)
    count: dict = {}
    for (who, a, b), l in zip(_flat(old_s), old_m["lines"]):
        k = count.get(who, 0)
        count[who] = k + 1
        ai = old_look[who]
        old_seg[(who, a, b)] = (ai["segs"][k], ai["dir"], ai["n"])
    for who in new_s["cast"]:
        segs, todo = [], []
        for (w, a, b), l in zip(_flat(new_s), new_m["lines"]):
            if w != who:
                continue
            st, en = round(l["start"] - 0.1, 3), round(l["end"] + 0.1, 3)
            if (w, a, b) in old_seg:
                g, d, n = old_seg[(w, a, b)]
                assert abs((g["end"] - g["start"]) - (en - st)) < 0.02, (w, a, b)
                segs.append({"start": st, "end": en, "off": g["off"], "dir": d, "n": n})
            else:
                todo.append((st, en))
                segs.append({"start": st, "end": en, "todo": len(todo) - 1})
        work = ROOT / f"work/aiface/{slug}/{who}/{tag}"
        work.mkdir(parents=True, exist_ok=True)
        off, offs = GAP, []
        for a, b in todo:
            offs.append(round(off, 3))
            off += (b - a) + GAP
        for g in segs:
            if "todo" in g:
                g["off"], g["dir"] = offs[g.pop("todo")], f"summary/photos/{slug}/{who}/ai-{tag}"
        json.dump(segs, open(work / "pending.json", "w"))
        if todo:
            flt = "".join(f"[0:a]aresample=16000,aformat=channel_layouts=mono,atrim={a}:{b},asetpts=PTS-STARTPTS,apad=pad_dur={GAP}[s{i}];"
                          for i, (a, b) in enumerate(todo))
            flt = f"anullsrc=r=16000:cl=mono,atrim=0:{GAP}[lead];" + flt + "[lead]" + "".join(f"[s{i}]" for i in range(len(todo))) + \
                f"concat=n={len(todo) + 1}:v=0:a=1[o]"
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(ROOT / f"public/summary/{slug}/audio.wav"), "-filter_complex", flt,
                            "-map", "[o]", "-ar", "16000", "-ac", "1", str(work / "voice.wav")], check=True)
        print(who, f"{len(segs) - len(todo)} reused, {len(todo)} new ({off - GAP:.1f}s)")


def block(slug: str, who: str, work: str, dest: str = "ai") -> None:
    """The `photo.ai` block for cast[who].look in script.json, from frames' info.json and voice's segs.json."""
    info = json.load(open(ROOT / "public/summary/photos" / slug / who / dest / "info.json"))
    segs = json.load(open(Path(work) / "segs.json"))
    print(json.dumps({"ai": {"dir": f"summary/photos/{slug}/{who}/{dest}", "fps": info["fps"], "n": info["n"], "segs": segs}}))


if __name__ == "__main__":
    {"prep": prep, "run": run, "voice": voice, "frames": frames, "block": block, "incr": incr}[sys.argv[1]](*sys.argv[2:])
