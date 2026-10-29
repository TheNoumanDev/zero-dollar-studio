"""Posting kit for finished podcast Shorts: title with hashtags, tags, hook+hashtags caption, thumbnail (rules: tools/podcast/postrules.py).

Usage: .venv/bin/python tools/podcast/post.py podcasts/<slug> <clip-id> [<clip-id> ...]

Writes out/podcast-shorts/<slug>/ready-to-post/<NN>-<name>/ with video.mp4, thumbnail.jpg,
post.md (copy-paste ready) and post.json, plus an index ready-to-post/README.md.
Nothing is uploaded: posting stays a manual, approved step.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from postrules import enforce, post_md, prompt_rules  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

PROMPT = """You write the post copy for a viral YouTube Short / Instagram Reel cut from a podcast.

Source: "{title}" by {channel}. People: {speakers}.
Clip hook: "{hook}". On-screen hook card: "{card}". Emotion: {emotion}. Why it works: {why}
Clip transcript ({duration:.0f} s):
{transcript}

Write:
{rules}

Return ONLY JSON matching the schema."""

SCHEMA = {"type": "object", "properties": {
    "youtube_title": {"type": "string"}, "youtube_description": {"type": "string"},
    "youtube_tags": {"type": "array", "items": {"type": "string"}},
    "instagram_caption": {"type": "string"}, "pinned_comment": {"type": "string"},
    "best_post_time": {"type": "string"}},
    "required": ["youtube_title", "youtube_description", "youtube_tags", "instagram_caption", "pinned_comment", "best_post_time"]}


def ask(prompt):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_"))}
    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude CLI not found on PATH: install Claude Code and log in (https://claude.com/claude-code)")
    out = subprocess.run([claude, "-p", "--output-format", "json", "--json-schema", json.dumps(SCHEMA)],
                         input=prompt, capture_output=True, text=True, env=env, timeout=600)
    if out.returncode != 0:
        sys.exit(f"claude failed: {out.stderr[-2000:]}")
    env_json = json.loads(out.stdout)
    return env_json.get("structured_output") or json.loads(env_json["result"])


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


def main():
    folder = Path(sys.argv[1])
    source = json.loads((folder / "source.json").read_text())
    out_root = ROOT / "out/podcast-shorts" / folder.name / "ready-to-post"
    out_root.mkdir(parents=True, exist_ok=True)
    for clip_id in sys.argv[2:]:
        d = ROOT / "public/podcast-shorts" / clip_id
        clip = json.loads((d / "clip.json").read_text())
        plan = json.loads((d / "plan.json").read_text())
        m = clip["moment"]
        video = ROOT / "out/podcast-shorts" / folder.name / f"{clip_id}.mp4"
        post = ask(PROMPT.format(
            title=source.get("title", folder.name), channel=source.get("channel", ""), speakers=source.get("speakers", ""),
            rules=prompt_rules(False),
            hook=m["hook_title"], card=plan["hook"], emotion=m["emotion"], why=m["why"], duration=clip["duration"],
            transcript=" ".join(w["w"] for w in clip["words"])))
        n = clip_id.rsplit("-", 1)[1]
        target = out_root / f"{int(n):02d}-{slugify(m['hook_title'])}"
        if target.exists():
            shutil.rmtree(target)
        target.mkdir()
        shutil.copy(video, target / "video.mp4")
        # Thumbnail: a designed cover kept outside the kit (out/podcast-shorts/<slug>/covers/<NN>.jpg, survives
        # regeneration), else the frame with the hook card up (Shorts pick a cover frame; Reels take an upload).
        cover = out_root.parent / "covers" / f"{int(n):02d}.jpg"
        if cover.exists():
            shutil.copy(cover, target / "thumbnail.jpg")
        else:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.2", "-i", str(video), "-frames:v", "1", "-q:v", "2",
                            str(target / "thumbnail.jpg")], check=True)
        post = enforce(post, long=False)  # Shorts: hashtags in the title (≤100), no description, no links
        post.update(clip_id=clip_id, duration=round(clip["duration"], 1), source=source.get("url", source.get("local", "")))
        (target / "post.json").write_text(json.dumps(post, indent=2, ensure_ascii=False))
        (target / "post.md").write_text(post_md(post, False, "1080×1920"))
        print(f"{target.name}: {post['youtube_title']}")

    # Index of everything in the folder.
    rows = []
    for t in sorted(p for p in out_root.iterdir() if p.is_dir()):
        pj = json.loads((t / "post.json").read_text())
        rows.append(f"| {t.name[:2]} | [{pj['youtube_title']}]({t.name}/post.md) | {pj['duration']} s | {pj.get('best_post_time', '?')} |")
    (out_root / "README.md").write_text(
        f"# Ready to post: {source.get('title', folder.name)}\n\nSource: {source.get('url') or 'local file'} ({source.get('channel', '')}). "
        "Each folder has `video.mp4`, `thumbnail.jpg` and `post.md` (copy-paste title, description, tags, caption).\n\n"
        "| # | Title | Length | Best time |\n|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "Rights: only post clips of footage you own or have permission (or a solid fair-use case) to use. "
        "Reused footage can draw copyright claims.\n")


if __name__ == "__main__":
    main()
