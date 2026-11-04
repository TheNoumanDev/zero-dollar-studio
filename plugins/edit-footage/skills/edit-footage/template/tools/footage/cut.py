"""Cut the kept takes into one clip and write it in snipshorts' PodcastShort format.

Usage: .venv/bin/python tools/footage/cut.py footage/<slug> [--id <clip-id>]

Reads footage/<slug>/source.mp4, words.json and takes.json (takes.py). Uses snipshorts' prepare.py for the
cut (with "denoise"), face tracking and framing, so plan.py, sfx.py and the PodcastShort composition work
unchanged. Writes public/podcast-shorts/<id>/source.mp4 and clip.json (id defaults to the slug).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/podcast"))
sys.path.insert(0, str(Path(__file__).parent))
import prepare  # noqa: E402  (snipshorts)
import takes  # noqa: E402


def to_edited(t, ranges):
    """Source time -> edited time, clamped into the nearest kept range."""
    acc = 0.0
    for a, b in ranges:
        if t < b + 1e-3:
            return acc + max(0.0, min(t, b) - a)
        acc += b - a
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--id")
    args = ap.parse_args()
    folder = Path(args.folder)
    cfg = json.loads((folder / "footage.json").read_text())
    clip_id = args.id or folder.name
    out_dir = ROOT / "public/podcast-shorts" / clip_id
    out_dir.mkdir(parents=True, exist_ok=True)
    # One person talking to camera: no split screens unless asked; screen recordings still get the wide view.
    prepare.SPLIT = cfg.get("split", False)
    prepare.SCREEN = cfg.get("screen", True)
    prepare.DENOISE = cfg.get("denoise", False)

    words = takes.flat_words(folder)
    lines = json.loads((folder / "takes.json").read_text())["lines"]
    src = folder / "source.mp4"
    length = float(json.loads((folder / "words.json").read_text())["duration"])
    ranges, kept = takes.edit_ranges(lines, words, length)
    if not ranges:
        sys.exit("takes.json keeps nothing")
    prepare.jump_cut(src, ranges, out_dir / "source.mp4")

    duration = sum(b - a for a, b in ranges)
    cuts, acc = [], 0.0
    for a, b in ranges[:-1]:
        acc += b - a
        cuts.append(round(acc, 3))
    clip_words = []
    for i in kept:
        wd = words[i]
        s = to_edited(wd["s"], ranges)
        # Whisper splits hyphenated words ("to" + "-do"): glue them back for the captions.
        if clip_words and wd["w"].startswith("-"):
            clip_words[-1].update(w=clip_words[-1]["w"] + wd["w"], e=round(max(to_edited(wd["e"], ranges), s + 0.05), 3))
            continue
        clip_words.append({"w": wd["w"], "s": round(s, 3), "e": round(max(to_edited(wd["e"], ranges), s + 0.05), 3)})

    w, h, samples = prepare.track(out_dir / "source.mp4")
    picks = prepare.choose_speaker(samples, w)
    crop = prepare.smooth_crop(samples, picks, w, h)
    faces_seen = sum(1 for p in picks if p) / max(1, len(picks))
    first = next(ln for ln in lines if ln["keep"])
    # plan.py reads the moment for context; the hook card text comes from footage.json "hook" or the first line.
    moment = {"hook_title": cfg.get("hook") or " ".join(first["text"].split()[:8]),
              "emotion": cfg.get("emotion", "talking to camera"),
              "why": cfg.get("about") or cfg.get("title", "A creator talking straight to camera.")}
    clip = {"id": clip_id, "fps": prepare.FPS, "width": w, "height": h, "duration": round(duration, 3),
            "moment": moment, "jumpCuts": cuts, "splices": [], "teaserEnd": None, "words": clip_words,
            "crop": crop, "shots": prepare.shot_people(samples, crop, w), **prepare.branding(cfg)}
    (out_dir / "clip.json").write_text(json.dumps(clip, ensure_ascii=False))
    print(f"{clip_id}: {w}x{h}, {duration:.1f}s (from {length:.1f}s raw), {len(cuts)} cuts, "
          f"{len(clip_words)} words, face in {faces_seen:.0%} of samples")


if __name__ == "__main__":
    main()
