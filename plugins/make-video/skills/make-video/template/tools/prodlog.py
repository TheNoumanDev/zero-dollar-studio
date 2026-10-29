"""
Append one production record per pipeline run (reproducibility + rollback).

    .venv/bin/python tools/prodlog.py stories/<slug> <CompositionId> <out.mp4>

Writes a JSON line to stories/<slug>/production.jsonl with what produced the
video: script hash, per-line voice settings and cache files, voice reference
hashes, music tempo/beat fit, tool versions, the
output's hash and the QA verdict.
"""

import hashlib
import json
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

story, comp, video = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])


def sha(path: Path) -> str | None:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12] if path.exists() else None



def version(pkg: str) -> str | None:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


script = json.loads((story / "script.json").read_text())
tl = json.loads((story / "timeline.json").read_text())
qa_path = story / "qa" / "report.json"
pkg = json.loads(Path("package.json").read_text())

record = {
    "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "composition": comp,
    "output": {"file": str(video), "sha1": sha(video), "bytes": video.stat().st_size if video.exists() else None},
    "qa": json.loads(qa_path.read_text())["status"] if qa_path.exists() else None,
    "script_sha1": sha(story / "script.json"),
    "language": tl.get("language", "en"),
    "voices": {k: {"ref": c.get("refVoice"), "ref_sha1": sha(Path(c["refVoice"])) if c.get("refVoice") else None, "exaggeration": c.get("exaggeration")}
               for k, c in script["characters"].items()},
    "lines": [{"speaker": l["speaker"], "file": Path(l["file"]).name, "direction": l.get("direction", {}), "emphasis": l.get("emphasis", [])}
              for l in tl["lines"]],
    "music": {k: tl["music"][k] for k in ("bpm", "firstBeatMs")} | {"worstOffBeatMs": max(c["offBeatMs"] for c in tl["music"]["cuts"])} if "music" in tl else None,
    "versions": {"remotion": pkg["dependencies"].get("remotion"), "chatterbox": version("chatterbox-tts"),
                 "ffmpeg": subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0].split(" ")[2]},
}
with (story / "production.jsonl").open("a") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")
print(f"Logged run → {story / 'production.jsonl'} (QA {record['qa']})")
