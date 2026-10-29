"""Pick short-form "viral moments" from a podcast transcript with Claude.

Usage: .venv/bin/python tools/podcast/moments.py podcasts/<slug> [--count 3]

Reads podcasts/<slug>/words.json (Whisper word timestamps), asks the logged-in
`claude` CLI (subscription, no API key) for self-contained 20-45 s moments that
open on a hook, then snaps each to word boundaries.
Writes podcasts/<slug>/moments.json.
"""
import argparse
import json
from pathlib import Path
import llm

PROMPT = """You are a senior short-form video editor who cuts viral YouTube Shorts and Instagram Reels from long podcasts.

Below is a timestamped transcript of a podcast ({minutes} min). Each line is "[start-end] text" in seconds.
Context: {context}

Pick the {count} BEST moments to post as standalone Shorts. Rank by how likely each is to stop the scroll and get shared.

A great moment:
- Opens on a HOOK: the first sentence alone makes someone stop scrolling (a bold claim, a confession, a surprising fact, a funny line, a question that demands an answer). Never open on filler ("so", "yeah", "you know", "I think").
- Is self-contained: a stranger with zero context understands it.
- Has a payoff: ends on the punchline, the reveal, the lesson, or a laugh. Do not cut mid-thought.
- Is 20-45 seconds long (hard limits: 15 s min, 55 s max).
- Is emotional, funny, controversial, vulnerable, or quotable.

Never pick: the intro or welcome, subscribe/like requests, sponsor reads, outro thank-yous, small talk, or long setup that only pays off minutes later.

THE ENDING IS EVERYTHING. Read past your planned end: if the story's real payoff, lesson or punchline comes a little later, the clip must include it. Never end on a setup line or mid-story.
If keeping everything continuous would exceed 55 s, SPLICE like an editor: give "segments" (2-3 pieces, in order) that keep the hook/setup and jump to the payoff, skipping the rambling middle. Each segment needs its own exact first_words/last_words. The spliced result must read naturally as one story (total 20-55 s).
Moments must not overlap. Prefer variety (different topics/emotions).
{taken}

Timestamps must come from the transcript lines: start = the start time of the line where the hook begins, end = the end time of the line where the payoff lands. You may start or end mid-line only by quoting the exact first/last words.

Return ONLY JSON matching the schema. For each moment:
- start, end: seconds
- first_words: the exact first 3-6 words spoken in the clip
- last_words: the exact last 3-6 words spoken in the clip
- hook_title: 3-7 word on-screen title for the first 2 seconds (curiosity gap, no clickbait lies, no emojis)
- why: one sentence on why this will perform
- emotion: one of funny, vulnerable, inspiring, controversial, surprising, romantic, wholesome
- score: 1-100 predicted virality
- segments: optional, only when splicing; list of {{start, end, first_words, last_words}}. Then start/end/first_words/last_words describe the whole span (first segment start to last segment end).

TRANSCRIPT:
{transcript}
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "moments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "first_words": {"type": "string"},
                    "last_words": {"type": "string"},
                    "hook_title": {"type": "string"},
                    "why": {"type": "string"},
                    "emotion": {"type": "string"},
                    "score": {"type": "number"},
                    "segments": {"type": "array", "items": {"type": "object", "properties": {
                        "start": {"type": "number"}, "end": {"type": "number"},
                        "first_words": {"type": "string"}, "last_words": {"type": "string"}},
                        "required": ["start", "end", "first_words", "last_words"]}},
                },
                "required": ["start", "end", "first_words", "last_words", "hook_title", "why", "emotion", "score"],
            },
        }
    },
    "required": ["moments"],
}


def norm(w: str) -> str:
    return "".join(c for c in w.lower() if c.isalnum() or c == "'")


def find_phrase(words, phrase, near, window=20.0, want="start"):
    """Index of the word where `phrase` starts (or ends), closest to `near` seconds."""
    target = [norm(w) for w in phrase.split() if norm(w)]
    if not target:
        return None
    best = None
    for i in range(len(words) - len(target) + 1):
        if abs(words[i]["s"] - near) > window:
            continue
        if all(norm(words[i + k]["w"]) == target[k] for k in range(len(target))):
            j = i if want == "start" else i + len(target) - 1
            d = abs(words[j]["s"] - near)
            if best is None or d < best[0]:
                best = (d, j)
    return best[1] if best else None


TEASER_PROMPT = """You cut viral Shorts. This clip will use a COLD OPEN: a 2-5 second line from INSIDE the clip plays first,
then a quick rewind, then the story from the top. The cold open must make a scroller desperate to know the context.

Pick the line: funny, shocking or intriguing ON ITS OWN, but not the full payoff (don't spoil the ending), and never from
the first 5 seconds (that would just repeat the start). Whole sentence or clause, 2-5 seconds.
It must keep the speaker's meaning: never a half-sentence that out of context says the opposite of what they meant
(e.g. "maybe I'm not made for this" taken from "it's NOT heartbreaking where I'm like maybe I'm not made for this").

Clip: "{hook}". Lines as "[start-end] text":
{lines}

Return JSON: start, end (seconds, from the lines), first_words, last_words (exact words), why (one sentence),
label (2-4 word rewind label shown after the teaser, e.g. "HOW IT STARTED", "LET HIM COOK", "WAIT FOR IT")."""

TEASER_SCHEMA = {"type": "object", "properties": {
    "start": {"type": "number"}, "end": {"type": "number"}, "first_words": {"type": "string"},
    "last_words": {"type": "string"}, "why": {"type": "string"}, "label": {"type": "string"}},
    "required": ["start", "end", "first_words", "last_words", "why", "label"]}


def ask_claude(prompt, schema):
    return llm.ask(prompt, schema, timeout=900)


def add_teaser(folder: Path, index: int, data):
    moments = json.loads((folder / "moments.json").read_text())
    m = moments[index]
    segs = data["segments"]
    spans = m.get("segments") or [{"start": m["start"], "end": m["end"]}]
    lines = "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segs
                      if any(sp["start"] - 1 <= s["start"] <= sp["end"] for sp in spans))
    t = ask_claude(TEASER_PROMPT.format(hook=m["hook_title"], lines=lines), TEASER_SCHEMA)
    words = [w for s in segs for w in s["words"]]
    a = find_phrase(words, t["first_words"], t["start"], want="start")
    b = find_phrase(words, t["last_words"], t["end"], want="end")
    t["start"] = round(words[a]["s"], 2) if a is not None else t["start"]
    t["end"] = round(words[b]["e"], 2) if b is not None else t["end"]
    m["teaser"] = t
    (folder / "moments.json").write_text(json.dumps(moments, indent=2, ensure_ascii=False))
    print(f"teaser {t['start']:.1f}-{t['end']:.1f} ({t['end'] - t['start']:.1f}s) "
          f"{'snapped' if a is not None and b is not None else 'UNSNAPPED'}: "
          f"{' '.join(w['w'] for w in words if t['start'] - 0.05 <= w['s'] <= t['end'])} | {t['label']} | {t['why']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--context", default="")
    ap.add_argument("--teaser", type=int, help="only add a cold-open teaser to moment N (0-based) in moments.json")
    ap.add_argument("--no-teasers", action="store_true", help="skip cold-open teasers")
    ap.add_argument("--append", action="store_true", help="keep moments.json and add new, non-overlapping moments")
    args = ap.parse_args()
    folder = Path(args.folder)
    data = json.loads((folder / "words.json").read_text())
    if args.teaser is not None:
        add_teaser(folder, args.teaser, data)
        return
    words = [w for s in data["segments"] for w in s["words"]]
    lines = "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in data["segments"])
    # Context for the picker: --context, else podcasts/<slug>/README.md, else the source's title and speakers.
    source = json.loads((folder / "source.json").read_text()) if (folder / "source.json").exists() else {}
    context = args.context or ((folder / "README.md").read_text().strip() if (folder / "README.md").exists() else
                               f"{source.get('title', '')}. {source.get('speakers', '')}".strip(". "))
    existing = json.loads((folder / "moments.json").read_text()) if args.append and (folder / "moments.json").exists() else []
    taken = ("Already clipped, do NOT pick these or anything overlapping them:\n" + "\n".join(
        f"- {m['start']:.0f}-{m['end']:.0f} s: {m['hook_title']}" for m in existing)) if existing else ""
    prompt = PROMPT.format(minutes=round(data["duration"] / 60), count=args.count, context=context, transcript=lines, taken=taken)

    result = ask_claude(prompt, SCHEMA)

    moments = []
    for m in sorted(result["moments"], key=lambda m: -m["score"]):
        if any(m["start"] < e["end"] and e["start"] < m["end"] for e in existing):
            print(f"skip overlapping pick: {m['hook_title']}")
            continue
        a = find_phrase(words, m["first_words"], m["start"], want="start")
        b = find_phrase(words, m["last_words"], m["end"], want="end")
        start = words[a]["s"] if a is not None else m["start"]
        end = words[b]["e"] if b is not None else m["end"]
        snapped = a is not None and b is not None
        if m.get("segments"):
            for seg in m["segments"]:
                sa = find_phrase(words, seg["first_words"], seg["start"], want="start")
                sb = find_phrase(words, seg["last_words"], seg["end"], want="end")
                seg["start"] = round(words[sa]["s"], 2) if sa is not None else seg["start"]
                seg["end"] = round(words[sb]["e"], 2) if sb is not None else seg["end"]
                snapped = snapped and sa is not None and sb is not None
            start, end = m["segments"][0]["start"], m["segments"][-1]["end"]
        m.update(start=round(start, 2), end=round(end, 2), snapped=snapped,
                 duration=round(sum(g["end"] - g["start"] for g in m["segments"]) if m.get("segments") else end - start, 1))
        moments.append(m)
        print(f"{m['score']:>3} {m['start']:7.1f}-{m['end']:7.1f} ({m['duration']:4.1f}s) "
              f"{'snapped' if m['snapped'] else 'UNSNAPPED'} | {m['hook_title']} | {m['why']}")
    (folder / "moments.json").write_text(json.dumps(existing + moments, indent=2, ensure_ascii=False))
    if not args.no_teasers:
        for i in range(len(existing), len(existing) + len(moments)):
            add_teaser(folder, i, data)


if __name__ == "__main__":
    main()
