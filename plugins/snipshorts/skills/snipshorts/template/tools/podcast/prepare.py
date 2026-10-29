"""Turn one picked moment into an edited source clip plus tracking data.

Usage: .venv/bin/python tools/podcast/prepare.py podcasts/<slug> <index> [--id <clip-id>]

Steps:
  1. Fetch the moment from YouTube at 1080p (just that section), falling back to the local file.
  2. Jump-cut dead air: gaps between words longer than MAX_GAP shrink to KEEP_GAP.
  3. Track faces (OpenCV YuNet detector, MIT) and the active speaker (lower-face motion) for a 9:16 crop.
     No face recognition: people are told apart by position, and across shots by clothing colour (people.py).
Writes public/podcast-shorts/<id>/source.mp4 and public/podcast-shorts/<id>/clip.json.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
YUNET = ROOT / "tools/models/yunet/face_detection_yunet_2023mar.onnx"
YTDLP = ROOT / ".venv/bin/yt-dlp"
FPS = 30
PAD = 0.25          # seconds kept before the first and after the last word
MAX_GAP = 0.45      # silences longer than this get cut...
KEEP_GAP = 0.12     # ...down to this
SAMPLE_EVERY = 3    # track every 3rd frame (10 Hz)


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def fetch(source, start, end, out: Path):
    """Section download at <=1080p (local fallback), normalised to 30 fps, with the source's grade if set."""
    if out.exists():
        return
    tmp = out.with_suffix(".dl.mp4")
    src, ss = None, 0.0
    # YouTube rate-limits bursts of section downloads; retry before settling for the 720p copy.
    # A source with no "url" (a local file only) goes straight to the local copy.
    for attempt in range(3 if source.get("url") else 0):
        try:
            run([str(YTDLP), "--js-runtimes", "node", "-q", "--force-keyframes-at-cuts",
                 "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]", "--merge-output-format", "mp4",
                 "--download-sections", f"*{start:.2f}-{end:.2f}", "-o", str(tmp), source["url"]])
            src = tmp
            break
        except subprocess.CalledProcessError as err:
            print(f"  1080p fetch failed (attempt {attempt + 1}/3): {err.stderr.decode()[-300:].strip()}")
            time.sleep(20 * (attempt + 1))
    if src is None:
        if source.get("url"):
            print("  WARNING: falling back to the local file; the crop will be softer")
        src, ss = Path(os.path.expanduser(source["local"])), start
    # Normalise: constant 30 fps, exact duration, 48 kHz audio.
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.3f}", "-i", str(src), "-t", f"{end - start:.3f}",
         # source.json "grade": an ffmpeg filter chain (subtle look) applied once, at the cut.
         "-vf", f"fps={FPS}" + (f",{source['grade']}" if source.get("grade") else ""), "-c:v", "libx264", "-crf", "16", "-preset", "fast",
         "-c:a", "aac", "-ar", "48000", "-b:a", "192k", str(out)])
    tmp.unlink(missing_ok=True)


def keep_ranges(words, t0, length):
    """Ranges (clip time) to keep, trimming long silences between words."""
    ranges, cur = [], [max(0.0, words[0]["s"] - t0 - PAD), None]
    for a, b in zip(words, words[1:]):
        gap = b["s"] - a["e"]
        if gap > MAX_GAP:
            cur[1] = a["e"] - t0 + KEEP_GAP / 2
            ranges.append(cur)
            cur = [b["s"] - t0 - KEEP_GAP / 2, None]
    cur[1] = min(length, words[-1]["e"] - t0 + PAD)
    ranges.append(cur)
    # Snap to frames so audio and video cut on the same sample.
    return [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in ranges if b - a > 0.05]


def jump_cut(src: Path, ranges, out: Path):
    parts, labels = [], []
    for i, (a, b) in enumerate(ranges):
        parts.append(f"[0:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.01,afade=t=out:st={max(0, b - a - 0.012):.4f}:d=0.012[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(ranges)}:v=1:a=1[v][a]"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-r", str(FPS),
         "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", str(out)])


def remap(t, ranges):
    """Clip time -> edited time, or None if t falls in a removed gap."""
    acc = 0.0
    for a, b in ranges:
        if a - 1e-3 <= t <= b + 1e-3:
            return acc + min(max(t, a), b) - a
        acc += b - a
    return None


def track(video: Path):
    """Per sample: crop centre, face size and the shot id, following the active speaker."""
    if not YUNET.exists():
        sys.exit(f"missing {YUNET}: run tools/podcast/setup.sh")
    cap = cv2.VideoCapture(str(video))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    det_w = 640
    det_h = round(h * det_w / w)
    k = w / det_w
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (det_w, det_h), score_threshold=0.6, nms_threshold=0.3, top_k=10)
    samples, prev_gray, prev_hist, shot = [], None, None, 0
    stable, pending = None, 0
    prev_tiny = None
    recent_diffs = []
    frame_i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_i % SAMPLE_EVERY:
            frame_i += 1
            continue
        small = cv2.resize(frame, (det_w, det_h))
        hist = cv2.calcHist([cv2.cvtColor(small, cv2.COLOR_BGR2HSV)], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        # Cut signals: a colour-histogram jump, or the whole picture changing at once (dark sets where
        # host and guest look alike in colour: real cuts change ~20 grey levels, movement 1-5).
        tiny = cv2.cvtColor(cv2.resize(small, (160, 90)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        # Adaptive: a cut must beat 4x the clip's recent normal change (footage with a constant drift or
        # zoom, as in re-uploads, changes ~15 grey levels per sample; still studio shots ~1).
        diff = float(np.mean(np.abs(tiny - prev_tiny))) if prev_tiny is not None else 0.0
        frame_jump = prev_tiny is not None and diff > max(12.0, 4.0 * float(np.median(recent_diffs[-20:] or [0.0])))
        recent_diffs.append(diff)
        prev_tiny = tiny
        if prev_hist is not None and (cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA) > 0.35 or frame_jump):
            shot += 1
        prev_hist = hist
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        _, faces = det.detect(small)
        found = []
        for f in faces if faces is not None else []:
            x, y, fw, fh = f[:4]
            if fh < det_h * 0.08:  # ignore tiny background faces
                continue
            # Lower-face motion: mouth area difference against the previous sample.
            mx0, mx1 = int(x + fw * 0.2), int(x + fw * 0.8)
            my0, my1 = int(y + fh * 0.6), int(min(det_h, y + fh * 1.05))
            # Upper face (eyes/forehead) moves with the head but not with speech:
            # subtracting it leaves mostly jaw/lip movement.
            ex0, ex1 = int(max(0, x + fw * 0.15)), int(x + fw * 0.85)
            ey0, ey1 = int(max(0, y + fh * 0.1)), int(y + fh * 0.45)
            motion = 0.0
            if prev_gray is not None and mx1 > mx0 and my1 > my0 and ex1 > ex0 and ey1 > ey0:
                mouth = float(np.mean(cv2.absdiff(gray[my0:my1, mx0:mx1], prev_gray[my0:my1, mx0:mx1])))
                head = float(np.mean(cv2.absdiff(gray[ey0:ey1, ex0:ex1], prev_gray[ey0:ey1, ex0:ex1])))
                motion = max(0.0, mouth - head) / max(1.0, fh / 100)
            # Clothing colour under the face identifies the person across shots (no face recognition).
            tx0, tx1 = int(max(0, x - fw * 0.4)), int(min(det_w, x + fw * 1.4))
            ty0, ty1 = int(min(det_h, y + fh * 1.3)), int(min(det_h, y + fh * 2.8))
            torso = None
            if tx1 - tx0 > 4 and ty1 - ty0 > 4:
                hsv = cv2.cvtColor(small[ty0:ty1, tx0:tx1], cv2.COLOR_BGR2HSV)
                hh = cv2.calcHist([hsv], [0, 1, 2], None, [12, 3, 3], [0, 180, 0, 256, 0, 256]).flatten()
                torso = (hh / max(hh.sum(), 1)).tolist()
            found.append({"cx": float((x + fw / 2) * k), "cy": float((y + fh / 2) * k), "fh": float(fh * k),
                          "motion": motion, "torso": torso, "score": float(f[-1])})
        # Same colours but a different framing (close-up <-> two-shot) is still a cut:
        # the biggest face jumps in size or the face count changes. Confirm on the next sample
        # so one missed detection doesn't split a shot.
        big = max((f["fh"] for f in found), default=0.0)
        big_cx = max(found, key=lambda f: f["fh"])["cx"] if found else 0.0
        if found:
            if stable is not None:
                sc, sb, scx = stable
                # Main-face size jump (close-up <-> wide on the same set). A face-count change alone is not
                # a cut: in crowd shots people walk in and out of frame all the time.
                changed = abs(big - sb) / max(sb, 1.0) > 0.35
                # A real cut holds: 3 changed samples in a row (0.3 s). A hand or mic briefly
                # read as a face changes for one sample only.
                if changed and pending >= 2 and len(samples) >= 2 and samples[-2]["shot"] == shot:
                    shot += 1
                    samples[-1]["shot"] = samples[-2]["shot"] = shot  # the new framing began 2 samples earlier
                    stable, pending = (len(found), big, big_cx), 0
                elif changed:
                    pending += 1
                else:
                    stable, pending = (len(found), big, big_cx), 0
            else:
                stable = (len(found), big, big_cx)
        prev_gray = gray
        samples.append({"t": frame_i / FPS, "shot": shot, "faces": found})
        frame_i += 1
    cap.release()
    return w, h, samples


def choose_speaker(samples, w):
    """Pick one face per sample: the one whose mouth moves most (smoothed), held for >= 1.2 s."""
    out, current, held = [], None, 0.0

    def baseline(f, shot):
        """Median mouth motion of this face (matched by x) across its shot."""
        vals = [g["motion"] for sm in samples if sm["shot"] == shot for g in sm["faces"] if abs(g["cx"] - f["cx"]) < w * 0.08]
        return max(0.3, float(np.median(vals))) if vals else 1.0
    for i, s in enumerate(samples):
        faces = s["faces"]
        if not faces:
            out.append(None)
            continue
        if len(faces) == 1:
            pick = faces[0]
        else:
            # Average motion over +-0.4 s for each face, matched by x position.
            def energy(f):
                vals = []
                for j in range(max(0, i - 4), min(len(samples), i + 5)):
                    if samples[j]["shot"] != s["shot"]:
                        continue
                    near = [g for g in samples[j]["faces"] if abs(g["cx"] - f["cx"]) < w * 0.08]
                    vals += [g["motion"] for g in near]
                return np.mean(vals) if vals else 0.0
            ranked = sorted(faces, key=lambda f: energy(f) / baseline(f, s["shot"]), reverse=True)
            pick = ranked[0]
            if current is not None and s["shot"] == current["shot"] and held < 1.2:
                same = [f for f in faces if abs(f["cx"] - current["cx"]) < w * 0.08]
                if same:
                    pick = same[0]
        if current is None or s["shot"] != current["shot"] or abs(pick["cx"] - current["cx"]) > w * 0.08:
            held = 0.0
        held += SAMPLE_EVERY / FPS
        current = {**pick, "shot": s["shot"]}
        out.append(current)
    return out


JUMPCUT = True  # source.json "jumpcut": false keeps segments whole
SPLIT = True  # source.json "split": false turns split screens off (over-the-shoulder studios)


def smooth_crop(samples, picks, w, h):
    """Crop keyframes in source px, eased within a shot and hard at cuts.

    A shot where two people are on screen most of the time becomes mode "split":
    both faces, left person on top, right person below. Other shots follow the speaker.
    """
    shots = {}
    for s in samples:
        shots.setdefault(s["shot"], []).append(s)
    split_shots = {}
    for shot, ss in shots.items():
        # Splits need two confident faces: edge artefacts and background shapes score low.
        sure = lambda s: [f for f in s["faces"] if f.get("score", 1) >= 0.85]
        two = [s for s in ss if len(sure(s)) >= 2]
        if SPLIT and len(ss) >= 8 and len(two) >= 0.6 * len(ss):  # at least 0.8 s, so no split flicker
            # Typical left/right face positions over the shot (median), so the halves stay steady.
            lefts = [min(sure(s), key=lambda f: f["cx"]) for s in two]
            rights = [max(sure(s), key=lambda f: f["cx"]) for s in two]
            med = lambda fs: {k: float(np.median([f[k] for f in fs])) for k in ("cx", "cy", "fh")}
            a, b = med(lefts), med(rights)
            # Two real people sit at similar distances; a background object read as a face is far smaller.
            if b["cx"] - a["cx"] > w * 0.15 and min(a["fh"], b["fh"]) >= 0.55 * max(a["fh"], b["fh"]):
                split_shots[shot] = (a, b)

    keys, last = [], {"cx": w / 2, "cy": h * 0.42, "fh": h * 0.3}
    for s, p in zip(samples, picks):
        target = p or last
        kf = {"t": round(s["t"], 3), "shot": s["shot"], "cx": target["cx"], "cy": target["cy"], "fh": target["fh"]}
        if s["shot"] in split_shots:
            a, b = split_shots[s["shot"]]
            kf["mode"] = "split"
            kf["a"] = {k: round(v, 1) for k, v in a.items()}
            kf["b"] = {k: round(v, 1) for k, v in b.items()}
        keys.append(kf)
        last = target
    for i in range(1, len(keys)):
        if keys[i]["shot"] == keys[i - 1]["shot"]:
            for f in ("cx", "cy", "fh"):
                keys[i][f] = keys[i - 1][f] + 0.25 * (keys[i][f] - keys[i - 1][f])
    for kf in keys:
        kf.update(cx=round(kf["cx"], 1), cy=round(kf["cy"], 1), fh=round(kf["fh"], 1))
    return keys


def shot_people(samples, keys, w):
    """Per shot: layout, start time, and the clothing signature of each visible person
    (single: the framed person; split: top/left then bottom/right)."""
    shots = []
    for shot in sorted({k["shot"] for k in keys}):
        ks = [k for k in keys if k["shot"] == shot]
        ss = [s for s in samples if s["shot"] == shot]
        mode = ks[0].get("mode", "single")
        targets = [ks[0]["a"], ks[0]["b"]] if mode == "split" else [None]
        sigs = []
        for target in targets:
            vecs = []
            for s, k in zip(ss, ks):
                ref = target or k
                near = [f for f in s["faces"] if f["torso"] is not None and abs(f["cx"] - ref["cx"]) < w * 0.08]
                if near:
                    vecs.append(min(near, key=lambda f: abs(f["cx"] - ref["cx"]))["torso"])
            sigs.append(np.round(np.median(vecs, axis=0), 4).tolist() if vecs else None)
        shots.append({"shot": shot, "mode": mode, "start": ks[0]["t"], "end": ks[-1]["t"] + SAMPLE_EVERY / FPS, "sigs": sigs})
    return shots


def branding(source):
    """Optional on-screen branding from source.json: "watermark" text and an "endCard" {title, handle}."""
    return {k: source[k] for k in ("watermark", "endCard") if source.get(k)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("index", type=int)
    ap.add_argument("--id")
    ap.add_argument("--retrack", action="store_true", help="redo face tracking on the existing source.mp4")
    args = ap.parse_args()
    folder = Path(args.folder)
    moment = json.loads((folder / "moments.json").read_text())[args.index]
    source = json.loads((folder / "source.json").read_text())
    global SPLIT, JUMPCUT
    SPLIT = source.get("split", True)
    JUMPCUT = source.get("jumpcut", True)
    words_all = [w for s in json.loads((folder / "words.json").read_text())["segments"] for w in s["words"]]
    clip_id = args.id or f"{folder.name}-{args.index + 1}"
    out_dir = ROOT / "public/podcast-shorts" / clip_id
    out_dir.mkdir(parents=True, exist_ok=True)

    t0, t1 = moment["start"] - 1.0, moment["end"] + 1.0
    if args.retrack:
        clip = json.loads((out_dir / "clip.json").read_text())
        w, h, samples = track(out_dir / "source.mp4")
        clip["crop"] = smooth_crop(samples, choose_speaker(samples, w), w, h)
        clip["shots"] = shot_people(samples, clip["crop"], w)
        clip.update(branding(source))
        (out_dir / "clip.json").write_text(json.dumps(clip, ensure_ascii=False))
        print(f"{clip_id}: re-tracked, {clip['crop'][-1]['shot'] + 1} shots")
        # New shots lose their names: re-assign them when people references exist.
        if any(p.get("refs") for p in source.get("people", [])):
            subprocess.run([sys.executable, str(Path(__file__).parent / "people.py"), clip_id], check=False)
        return
    raw = out_dir / "raw.mp4"
    fetch(source, t0, t1, raw)

    # A moment may be spliced from several segments (setup ... payoff, skipping the middle).
    segments = sorted(moment.get("segments") or [{"start": moment["start"], "end": moment["end"]}], key=lambda g: g["start"])
    # Cold open: the teaser line (from later in the moment) plays first, then the story from the top.
    teaser = moment.get("teaser")
    if teaser:
        segments = [{**teaser, "teaser": True}] + segments
    ranges, splice_at, clip_words = [], [], []
    teaser_end = None
    for seg in segments:
        seg_words = [w for w in words_all if w["s"] >= seg["start"] - 0.05 and w["e"] <= seg["end"] + 0.05]
        if not seg_words:
            continue
        if ranges:
            splice_at.append(len(ranges))
        # source.json "jumpcut": false keeps every frame of a segment (TV footage is already edited, and
        # in shouting matches the "silences" between transcribed words are speech Whisper missed).
        seg_ranges = keep_ranges(seg_words, t0, t1 - t0) if JUMPCUT else [
            (round((seg["start"] - t0) * FPS) / FPS, round((seg["end"] - t0) * FPS) / FPS)]
        # Remap within this segment only: a teaser repeats words that the story plays again later.
        offset = sum(b - a for a, b in ranges)
        for wd in seg_words:
            s0, e0 = remap(wd["s"] - t0, seg_ranges), remap(wd["e"] - t0, seg_ranges)
            if s0 is not None and e0 is not None and wd["w"]:
                clip_words.append({"w": wd["w"], "s": round(offset + s0, 3), "e": round(offset + max(e0, s0 + 0.05), 3)})
        ranges += seg_ranges
        if seg.get("teaser"):
            teaser_end = round(sum(b - a for a, b in ranges), 3)
    edited = out_dir / "source.mp4"
    jump_cut(raw, ranges, edited)

    duration = sum(b - a for a, b in ranges)
    cuts = []
    acc = 0.0
    for a, b in ranges[:-1]:
        acc += b - a
        cuts.append(round(acc, 3))

    w, h, samples = track(edited)
    picks = choose_speaker(samples, w)
    crop = smooth_crop(samples, picks, w, h)
    faces_seen = sum(1 for p in picks if p) / max(1, len(picks))

    # Edited times where spliced segments meet (they get a bigger transition than a jump cut).
    splices = [round(sum(b - a for a, b in ranges[:i]), 3) for i in splice_at]
    clip = {"id": clip_id, "fps": FPS, "width": w, "height": h, "duration": round(duration, 3),
            "moment": moment, "jumpCuts": cuts, "splices": splices, "teaserEnd": teaser_end,
            "words": clip_words, "crop": crop, "shots": shot_people(samples, crop, w), **branding(source)}
    (out_dir / "clip.json").write_text(json.dumps(clip, ensure_ascii=False))
    raw.unlink(missing_ok=True)
    print(f"{clip_id}: {w}x{h}, {duration:.1f}s (from {t1 - t0 - 2:.1f}s), {len(cuts)} jump cuts, "
          f"{len(clip_words)} words, faces in {faces_seen:.0%} of samples, {crop[-1]['shot'] + 1} shots")


if __name__ == "__main__":
    main()
