"""Join and normalise the raw recording(s) into footage/<slug>/source.mp4.

Usage: .venv/bin/python tools/footage/ingest.py footage/<slug>

footage.json "local" is one file or a list (phone recordings are often one file per attempt); they are
joined in order. Output: constant 30 fps, upright (phone rotation applied), 48 kHz stereo, with the
optional "grade" filter chain. Every later step reads this file.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FPS = 30


def probe(path: Path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,color_transfer:stream_side_data=rotation", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    st = json.loads(out)["streams"][0]
    w, h = st["width"], st["height"]
    rot = next((abs(int(d.get("rotation", 0))) for d in st.get("side_data_list", []) if "rotation" in d), 0)
    return (h, w) if rot in (90, 270) else (w, h), st.get("color_transfer", "")


def main():
    folder = Path(sys.argv[1])
    cfg = json.loads((folder / "footage.json").read_text())
    files = cfg["local"] if isinstance(cfg["local"], list) else [cfg["local"]]
    files = [Path(f).expanduser() if Path(f).expanduser().is_absolute() else ROOT / f for f in files]
    for f in files:
        if not f.exists():
            sys.exit(f"missing {f}")
    (w, h), transfer = probe(files[0])
    if transfer in ("arib-std-b67", "smpte2084"):
        print("  WARNING: HDR video (iPhone 'HDR Video' is on): colours may look flat. Record in SDR next time "
              "(Settings → Camera → Record Video → HDR Video off), or add a \"grade\" in footage.json.")
    w, h = w - w % 2, h - h % 2
    # Every file scaled into the first one's frame, so differently sized takes still join.
    chains, labels = [], []
    for i in range(len(files)):
        chains.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:-1:-1,setsar=1,"
                      f"fps={FPS},format=yuv420p[v{i}];[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    graph = "".join(chains) + "".join(labels) + f"concat=n={len(files)}:v=1:a=1[v][a]"
    if cfg.get("grade"):
        graph += f";[v]{cfg['grade']}[vg]"
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for f in files:
        cmd += ["-i", str(f)]
    cmd += ["-filter_complex", graph, "-map", "[vg]" if cfg.get("grade") else "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
            "-movflags", "+faststart", str(folder / "source.mp4")]
    subprocess.run(cmd, check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(folder / "source.mp4")], check=True, capture_output=True, text=True).stdout)
    print(f"{folder.name}: {len(files)} file(s) → source.mp4, {w}x{h}, {dur:.1f} s")


if __name__ == "__main__":
    main()
