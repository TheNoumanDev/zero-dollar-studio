"""
Ready-to-post kits for a summary: the mastered video, a thumbnail still and the posting copy, checked against
snipshorts' tools/podcast/postrules.py (no links, title ≤ 100 characters).

    .venv/bin/python tools/summary/kit.py <slug>

Reads summaries/<slug>/script.json: `post` (16:9 cut) and `short_post` (9:16 cut), each with youtube_title,
youtube_description, youtube_tags, instagram_caption, pinned_comment. Videos: out/summary/<slug>/final.mp4 and
final-short.mp4 (whichever exist). Thumbnails: the compositions named in script.json "thumb" / "shortThumb".
→ out/summary/<slug>/ready-to-post/wide/ and short/ (video.mp4, thumbnail.jpg, post.json, post.md).
Nothing is uploaded: you post it yourself.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "tools/podcast"))
import postrules  # noqa: E402


def duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return round(float(out.stdout), 1)


def main() -> None:
    slug = sys.argv[1]
    script = json.loads((PROJECT / f"summaries/{slug}/script.json").read_text())
    root = PROJECT / f"out/summary/{slug}/ready-to-post"
    for name, video, thumb, key, long in [("short", "final-short.mp4", script.get("shortThumb"), "short_post", False),
                                          ("wide", "final.mp4", script.get("thumb"), "post", True)]:
        src = PROJECT / f"out/summary/{slug}/{video}"
        if not src.exists():
            print(f"– skip {name}: no {src.name}")
            continue
        if key not in script:
            sys.exit(f"summaries/{slug}/script.json has no '{key}' (posting copy for the {name} cut)")
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, d / "video.mp4")
        if thumb:
            subprocess.run(["npx", "remotion", "still", thumb, str((d / "thumbnail.jpg").resolve()), "--image-format=jpeg", "--jpeg-quality=92", "--log=error"],
                           cwd=PROJECT, check=True)
        post = postrules.enforce(dict(script[key]), long)
        post.update({"duration": duration(src), "long_form": long})
        # Real faces animated by AI must be disclosed: YouTube Studio → "Altered or synthetic content" = Yes.
        if script.get("synthetic") or script[key].get("synthetic"):
            post["synthetic"] = True
        (d / "post.json").write_text(json.dumps(post, ensure_ascii=False, indent=2))
        md = postrules.post_md(post, long, f"{(src.stat().st_size / 1e6):.0f} MB")
        if post.get("synthetic"):
            md = "> ⚠️ AI-animated real faces: in YouTube Studio set **Altered or synthetic content** to **Yes** (Instagram/TikTok: add the AI label).\n\n" + md
        (d / "post.md").write_text(md)
        print(f"✅ {d}")


if __name__ == "__main__":
    main()
