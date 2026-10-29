"""Posting-copy rules for the ready-to-post kits (tools/podcast/post.py). Edit them to taste.

Defaults:
- YouTube title carries its hashtags at the end, and the whole title is at most 100 characters.
- No description for Shorts / Reels / TikTok: only long-form YouTube videos get a description.
- Never put the original video's link (or any URL) anywhere: title, description, caption, pinned comment.
- Instagram (and TikTok) caption: one hook line plus lots of hashtags, no description paragraph.

`prompt_rules(long)` is pasted into the copywriting prompt; `enforce(post, long)` makes the result obey
the rules whatever the model wrote.
"""
import re

TITLE_MAX = 100
URL = re.compile(r"(https?://\S+|www\.\S+|youtu\.be/\S+|\b\S+\.(com|in|be)/\S*)", re.I)


def prompt_rules(long: bool) -> str:
    short = "" if long else " and include #shorts"
    desc = (
        "- youtube_description: 3-5 short lines: a hook line, what happens in the video, a question to drive comments, "
        "then 5-8 hashtags. NO links or URLs at all, no 'full episode' pointers."
        if long
        else '- youtube_description: return an empty string "" (Shorts get no description).'
    )
    return f"""- youtube_title: the hook title, then 2-4 hashtags at the end{short}. The WHOLE title including hashtags and spaces must be at most {TITLE_MAX} characters. 0-1 emoji, no ALL CAPS, nothing the video doesn't show.
{desc}
- youtube_tags: 10-15 search tags (names, show, topics), lowercase.
- instagram_caption: ONE scroll-stopping line (max 90 characters), then a blank line, then 15-25 hashtags mixing big and niche. No description, no credit line, no links.
- pinned_comment: a question that sparks replies (no links).
- best_post_time: a weekday time window (with time zone) when this kind of content does well for its audience (one short phrase)."""


def _strip_urls(text: str) -> str:
    return re.sub(r"[ \t]+\n", "\n", URL.sub("", text)).strip()


def fit_title(title: str) -> str:
    """Drop trailing hashtags (then words) until the title fits in 100 characters."""
    title = " ".join(title.split())
    while len(title) > TITLE_MAX:
        words = title.split(" ")
        tags = [i for i, w in enumerate(words) if w.startswith("#") and w.lower() != "#shorts"]  # #shorts stays
        drop = tags[-1] if tags else max(i for i, w in enumerate(words) if not w.startswith("#"))
        title = " ".join(words[:drop] + words[drop + 1:])
    return title


def enforce(post: dict, long: bool) -> dict:
    post = dict(post)
    post["youtube_title"] = fit_title(_strip_urls(post.get("youtube_title", "")))
    post["youtube_description"] = _strip_urls(post.get("youtube_description", "")) if long else ""
    caption = _strip_urls(post.get("instagram_caption", ""))
    # Caption = first line + hashtags only.
    lines = [l for l in caption.splitlines() if l.strip()]
    hook = next((l for l in lines if not l.strip().startswith("#")), "")
    tags = " ".join(w for l in lines for w in l.split() if w.startswith("#"))
    post["instagram_caption"] = f"{hook.strip()}\n\n{tags}".strip()
    post["pinned_comment"] = _strip_urls(post.get("pinned_comment", ""))
    return post


def post_md(post: dict, long: bool, size: str) -> str:
    """The copy-paste sheet for one video."""
    yt = "YouTube (long-form)" if long else "YouTube Shorts"
    desc = f"\n**Description**\n\n```\n{post['youtube_description']}\n```\n" if long else "\n_No description (Short)._\n"
    return f"""# {post['youtube_title']}

`video.mp4` · {post.get('duration', '?')} s · {size} · thumbnail: `thumbnail.jpg` · best time: {post.get('best_post_time', '?')}

## {yt}

**Title** ({len(post['youtube_title'])}/100, hashtags included)

```
{post['youtube_title']}
```
{desc}
**Tags**

```
{', '.join(post['youtube_tags'])}
```

## Instagram Reels / TikTok

**Caption** (hook + hashtags)

```
{post['instagram_caption']}
```

## Pinned comment

```
{post['pinned_comment']}
```
"""
