"""
Final review gate for a rendered video: PASS / FIX / FAIL with evidence.

    .venv/bin/python tools/qa.py stories/<slug> out/<Comp>.mp4 [--layout <CompositionId>]

Checks (each reports value, limit and verdict):
  probe     resolution, fps, duration vs timeline, audio present
  loudness  integrated -14 ±1 LUFS, true peak ≤ -1 dBFS
  captions  word error rate of the voice vs the script (from captions-report.json)
  beats     every visual cut within 120 ms of a music beat (timeline.music)
  frozen    longest stretch with almost no on-screen change (≤ 3 s)
  variety   distinct visuals per second of video, longest same-looking run (≤ 5 s)
  layout    (with --layout) captions vs platform dead zones (incl. the Reels right-side button rail) and vs the face:
            renders a ¼-scale preview of the composition with qa=true, in which
            captions are outlined pure magenta and the face pure cyan
  duplicate captions that only repeat text already on screen (script "onScreenText")
Writes stories/<slug>/qa/report.json, report.md and contact.png.
FAIL = a hard problem (wrong format, loudness, unsafe layout); FIX = worth fixing.
"""

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

story, video = Path(sys.argv[1]), Path(sys.argv[2])
layout_comp = sys.argv[sys.argv.index("--layout") + 1] if "--layout" in sys.argv else None
qa_dir = story / "qa"
qa_dir.mkdir(exist_ok=True)
tl = json.loads((story / "timeline.json").read_text())
script = json.loads((story / "script.json").read_text())
results = []
t0 = time.time()


def check(name: str, ok: bool, value, limit: str, severity: str = "FIX", note: str = ""):
    results.append({"check": name, "status": "PASS" if ok else severity, "value": value, "limit": limit, "note": note})


def run(*cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


# ---------- probe ----------
info = json.loads(run("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", str(video)))
vs = next(s for s in info["streams"] if s["codec_type"] == "video")
has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
dur = float(info["format"]["duration"])
fmt = script.get("format", {"width": 1080, "height": 1920, "fps": 30})
check("probe: resolution", (vs["width"], vs["height"]) == (fmt["width"], fmt["height"]), f'{vs["width"]}×{vs["height"]}', f'{fmt["width"]}×{fmt["height"]}', "FAIL")
check("probe: fps", vs["r_frame_rate"] == f'{fmt["fps"]}/1', vs["r_frame_rate"], f'{fmt["fps"]}/1', "FAIL")
check("probe: duration", abs(dur - tl["totalMs"] / 1000) < 0.3, f"{dur:.2f}s", f'{tl["totalMs"] / 1000:.2f}s ±0.3', "FAIL")
check("probe: audio track", has_audio, has_audio, "present", "FAIL")

# ---------- loudness ----------
ebu = subprocess.run(["ffmpeg", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
summary = ebu[ebu.rfind("Summary:"):]
lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))
check("loudness: integrated", abs(lufs + 14) <= 1, f"{lufs} LUFS", "-14 ±1", "FAIL")
check("loudness: true peak", peak <= -1.0, f"{peak} dBFS", "≤ -1.0", "FAIL")

# ---------- captions ----------
rep_path = story / "captions-report.json"
if rep_path.exists():
    rep = json.loads(rep_path.read_text())
    bad = [l["script"] for l in rep["lines"] if l["wer"] > 0.2]
    lang = tl.get("language", "en")
    # Whisper small can't judge accented Hindi TTS (see skill lessons), so only English is gated.
    check("captions: word error rate", lang != "en" or rep["averageWer"] <= 0.1, f'{rep["averageWer"]:.1%}', "≤ 10% (English)",
          note=("lines to re-record: " + " | ".join(bad)) if bad else "")

# ---------- beats ----------
if "music" in tl:
    worst = max((c["offBeatMs"] for c in tl["music"]["cuts"]), default=0)
    check("beats: cuts on the beat", worst <= 120, f"worst {worst} ms at {tl['music']['bpm']} BPM", "≤ 120 ms")

# ---------- frozen + variety (pixels) ----------
cap = cv2.VideoCapture(str(video))
fps = cap.get(cv2.CAP_PROP_FPS) or 30
step = max(1, round(fps / 4))  # 4 samples per second
prev, diffs, hashes, frames, idx = None, [], [], [], 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if idx % step == 0:
        g = cv2.cvtColor(cv2.resize(frame, (135, 240)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.mean(np.abs(g - prev))))
        prev = g
        small = cv2.resize(g, (9, 8))
        hashes.append((small[:, 1:] > small[:, :-1]).flatten())  # dHash
        frames.append(frame)
    idx += 1
cap.release()
sample_dt = step / fps
static = [d < 0.6 for d in diffs]
longest, run_len = 0, 0
for s in static:
    run_len = run_len + 1 if s else 0
    longest = max(longest, run_len)
frozen_s = longest * sample_dt
check("frozen: longest still stretch", frozen_s <= 3.0, f"{frozen_s:.1f}s", "≤ 3.0s")

per_sec = hashes[:: max(1, round(1 / sample_dt))]
distinct = []
for h in per_sec:
    if all(np.count_nonzero(h != d) > 8 for d in distinct):
        distinct.append(h)
same_run, longest_same = 0, 0
for a, b in zip(per_sec, per_sec[1:]):
    same_run = same_run + 1 if np.count_nonzero(a != b) <= 4 else 0
    longest_same = max(longest_same, same_run)
check("variety: distinct visuals", len(distinct) / max(1, len(per_sec)) >= 0.2, f"{len(distinct)} distinct in {len(per_sec)} s", "≥ 20% of seconds")
check("variety: longest same-looking run", longest_same <= 5, f"{longest_same}s", "≤ 5s")

# ---------- duplicate caption vs on-screen text ----------
on_screen = [re.sub(r"[^a-z0-9 ]", "", t.lower()) for t in script.get("onScreenText", [])]
cap_path = Path("public") / tl["slug"] / "captions.json"
if on_screen and cap_path.exists():
    words = [re.sub(r"[^a-z0-9]", "", w["text"].lower()) for w in json.loads(cap_path.read_text())]
    pages = [" ".join(words[i : i + 3]) for i in range(0, len(words), 3)]
    dupes = [p for p in pages if len(p) > 6 and any(p in s for s in on_screen)]
    check("duplicate: captions repeating on-screen text", not dupes, len(dupes), "0", note=" | ".join(dupes))

# ---------- layout (caption safe zones + face) ----------
if layout_comp:
    with tempfile.TemporaryDirectory() as tmp:
        props = json.dumps({"lang": tl.get("language", "en"), "qa": True})
        subprocess.run(["npx", "remotion", "render", layout_comp, tmp, "--sequence", "--image-format=png", "--scale=0.25",
                        f"--props={props}", "--log=error", "--timeout=180000", "--concurrency=2"], check=True)
        pngs = sorted(Path(tmp).glob("*.png"))
        dead, overlap = [], []
        for i, p in enumerate(pngs[::3]):
            im = cv2.imread(str(p))
            h, w = im.shape[:2]
            b, g, r = im[..., 0].astype(int), im[..., 1].astype(int), im[..., 2].astype(int)
            mag = (r > 220) & (g < 40) & (b > 220)
            cyan = (r < 40) & (g > 220) & (b > 220)
            if mag.sum() < 20:
                continue
            ys, xs = np.where(mag)
            t_s = i * 3 / fps
            if w > h:  # 16:9 long-form: only the player's controls/progress bar (bottom ~7%) and the top edge get in the way
                top, bottom = ys.min() / h * 1080, ys.max() / h * 1080
                bad = top < 30 or bottom > 1005
            else:  # 9:16 Shorts/Reels: platform UI above y 220 and below y 1540, plus the like/comment/share column on the right
                top, bottom = ys.min() / h * 1920, ys.max() / h * 1920
                right = xs.max() / w * 1080
                bad = top < 220 or bottom > 1540 or (right > 940 and bottom > 1000)
            if bad:
                dead.append(f"{t_s:.1f}s ({top:.0f}–{bottom:.0f}px" + (f", right {right:.0f}px)" if w < h else ")"))
            if cyan.sum() > 20:
                cy_, cx_ = np.where(cyan)
                if not (xs.max() < cx_.min() or xs.min() > cx_.max() or ys.max() < cy_.min() or ys.min() > cy_.max()):
                    overlap.append(f"{t_s:.1f}s")
        check("layout: captions inside safe zone (9:16 y 220–1540, clear of the right rail x>940 below y 1000 · 16:9 y 30–1005)", not dead, len(dead), "0 frames", "FAIL", ", ".join(dead[:6]))
        check("layout: captions never cover the face", not overlap, len(overlap), "0 frames", "FAIL", ", ".join(overlap[:6]))

# ---------- contact sheet + verdict ----------
pick = [frames[int(i * (len(frames) - 1) / 5)] for i in range(6)]
sheet = np.hstack([cv2.resize(f, (384, 216) if f.shape[1] > f.shape[0] else (216, 384)) for f in pick])
cv2.imwrite(str(qa_dir / "contact.png"), sheet)

status = "FAIL" if any(r["status"] == "FAIL" for r in results) else "FIX" if any(r["status"] == "FIX" for r in results) else "PASS"
report = {"video": str(video), "status": status, "seconds": round(time.time() - t0, 1), "checks": results}
(qa_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
icon = {"PASS": "✅", "FIX": "🟡", "FAIL": "❌"}
md = [f"# QA {icon[status]} {status}: {video.name}", "", "| | Check | Value | Limit | Note |", "|---|---|---|---|---|"]
md += [f"| {icon[r['status']]} | {r['check']} | {r['value']} | {r['limit']} | {r['note']} |" for r in results]
(qa_dir / "report.md").write_text("\n".join(md) + "\n\n![contact](contact.png)\n")
print("\n".join(md))
print(f"\nQA {status} in {report['seconds']}s → {qa_dir / 'report.md'}")
sys.exit(1 if status == "FAIL" else 0)
