"""
Glue between a series bible, an episode script and the _Episode composition.

    .venv/bin/python tools/episode_data.py sync stories/<slug>   # before voicing
    .venv/bin/python tools/episode_data.py pack stories/<slug>   # after voicing + lip sync

sync  Checks the script against series/<series>/series.json (every speaker, set,
      expression and pose exists) and copies each character's voice settings
      from the bible into script.json "characters", so tools/voice.py and
      tools/voice_parler.py voice them the same way in every episode.
      Edit voices in the bible, never in script.json.
pack  Writes public/<slug>/episode.json for the composition: the bible (with
      each character's rig.json and pose list) plus every line's timing, mouth
      cues and shot direction. tools/make-episode.sh runs both.
"""

import json
import sys
from pathlib import Path

VOICE_KEYS = ("name", "color", "exaggeration", "cfgWeight", "refVoice", "engine", "speaker", "style")

mode, story = sys.argv[1], Path(sys.argv[2])
script_path = story / "script.json"
script = json.loads(script_path.read_text())
series_id = script.get("series") or sys.exit(f"{script_path}: add \"series\": \"<id>\" (a folder in series/)")
bible = json.loads((Path("series") / series_id / "series.json").read_text())
cast_dir = Path("public") / series_id / "cast"
chars, sets = bible["characters"], bible["sets"]


def rig(cid: str) -> dict | None:
    f = cast_dir / cid / "bust" / "rig.json"
    return json.loads(f.read_text()) if f.exists() else None


def poses(cid: str) -> list[str]:
    return sorted(p.stem for p in (cast_dir / cid / "poses").glob("*.png"))


def used() -> list[str]:
    """Characters in this episode, in order of appearance."""
    out: list[str] = []
    for line in script["lines"]:
        shot = line.get("shot", {})
        for c in [line["speaker"], shot.get("with"), *shot.get("cast", []), *line.get("react", {})]:
            if c and c != "all" and c not in out:
                out.append(c)
    return out


def check() -> list[str]:
    problems = []
    for c in used():
        if c not in chars:
            problems.append(f"character {c!r} is not in series/{series_id}/series.json")
    for n, line in enumerate(script["lines"]):
        shot = line.get("shot", {})
        if shot.get("set") and shot["set"] not in sets:
            problems.append(f"line {n}: set {shot['set']!r} is not in the bible")
        if "pauseAfter" not in line:
            problems.append(f"line {n}: add \"pauseAfter\" (seconds)")
        faces = [(line["speaker"], line.get("expression"))] + list(line.get("react", {}).items())
        for who, expr in faces:
            r = rig(who) if who in chars else None
            if expr and r and expr not in r.get("expressions", []):
                problems.append(f"line {n}: {who} has no {expr!r} face (has {r.get('expressions', [])})")
        if shot.get("pose") and line["speaker"] in chars and shot["pose"] not in poses(line["speaker"]):
            problems.append(f"line {n}: {line['speaker']} has no pose {shot['pose']!r} (has {poses(line['speaker'])})")
    return problems


if mode == "sync":
    problems = check()
    if problems:
        sys.exit("❌ Episode script problems:\n  " + "\n  ".join(problems))
    want = {c: {k: chars[c][k] for k in VOICE_KEYS if k in chars[c]} for c in used()}
    if script.get("characters") != want:
        script["characters"] = want
        script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False) + "\n")
        print(f"Voices synced from series/{series_id}/series.json → {script_path}")
    missing = [c for c in used() if not rig(c)]
    if missing:
        print(f"⚠️  No bust rig yet for {', '.join(missing)} (tools/rig_character.sh); they'll show as a placeholder.")
elif mode == "pack":
    tl = json.loads((story / "timeline.json").read_text())
    fmt = script["format"]
    lines = []
    for src, t in zip(script["lines"], tl["lines"]):
        line = {k: t[k] for k in ("speaker", "caption", "startMs", "endMs", "envelope") if k in t}
        line["mouthCues"] = t.get("mouthCues")
        for k in ("shot", "expression", "react"):
            if k in src:
                line[k] = src[k]
        lines.append(line)
    data = {
        "slug": story.name,
        "title": script.get("title", ""),
        "language": tl.get("language", "en"),
        "fps": fmt["fps"],
        "width": fmt["width"],
        "height": fmt["height"],
        "durationInFrames": tl["durationInFrames"],
        "outroStartMs": tl["outroStartMs"],
        "outro": script.get("outro", {}),
        "events": tl.get("events", {}),
        "series": {
            "id": series_id,
            "title": bible.get("title", ""),
            "characters": {
                c: {"name": chars[c].get("name", c), "color": chars[c].get("color", "#ffffff"), "scale": chars[c].get("scale", 1),
                    "rig": rig(c), "poses": poses(c)}
                for c in chars
            },
            "sets": sets,
        },
        "lines": lines,
    }
    out = Path("public") / story.name / "episode.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False))
    print(f"Episode data → {out} ({len(lines)} lines, {data['durationInFrames']} frames)")
else:
    sys.exit("usage: tools/episode_data.py sync|pack stories/<slug>")
