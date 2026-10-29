"""Have Claude write the edit plan (zooms, caption emphasis, motion graphics, caption fixes) for a clip.

Usage: .venv/bin/python tools/podcast/plan.py <clip-id>

Reads public/podcast-shorts/<id>/clip.json, writes public/podcast-shorts/<id>/plan.json.
Every beat is anchored to a word index, then converted to seconds here, so timing is word-accurate.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PROMPT = """You are the motion editor for viral podcast Shorts (think the punchy edits on top creator clips).
The clip is {duration:.1f} s, vertical 1080x1920. Speakers: {speakers}.
Moment: "{hook}" ({emotion}). Why it works: {why}

{teaser}
Words, one per line as "index | start-seconds | word":
{words}

Design the edit. Everything is anchored to a word index (the beat starts when that word is spoken).

1. hook: on-screen title for the first 2.5 s, 3-7 words, uppercase-friendly, a curiosity gap that matches what is said. You may reuse or improve: "{hook}".
2. emphasis: indices of the 8-16 most important words (punchline words, numbers, names, emotional words). Never filler.
3. zooms: 5-10 camera moves. kind "punch" (snap in on a punchline/key word, to 1.25-1.45, dur 0.6-1.5 s) or "push" (slow push during build-up or a vulnerable moment, to 1.15-1.25, dur 2-5 s). Do not overlap. Put a punch on the payoff.
4. graphics: 4-7 motion graphics, each tied to what is said at that word:
   - kinetic: 1-3 word slam of the key phrase (e.g. "LOVE AT FIRST SIGHT"), dur 1.2-2 s
   - stat: only for real numbers said aloud (value, optional prefix/suffix, short label), dur 1.8-2.5 s
   - emoji: one emoji that matches the emotion (laugh 😂, love ❤️, shock 😳, fire 🔥, cry 🥹...), dur 1.5-2 s
   - callout: short label with an icon emoji (e.g. "9 YEARS TOGETHER" with ⏳), dur 1.5-2.2 s
   - quote: the single most quotable sentence (max 12 words, exact words from the transcript), dur 2.5-4 s
   Never before 2.6 s (hook is on screen). Never two graphics at once. Leave 0.5 s between graphics.
5. Something must change on screen at least every 3 seconds across zooms and graphics combined.
6. fixes: the words come from speech recognition and some are misheard (e.g. "called" for "cool", wrong names,
   "B-com" for "B.Com"). Return {{index, word}} for each word that is clearly wrong in context, with the word that
   was actually said (keep its punctuation). Only fix real mistakes; keep the speaker's own grammar and slang.

Return ONLY JSON matching the schema."""

ANCHOR = {"type": "integer", "description": "word index where the beat starts"}
SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {"type": "string"},
        "emphasis": {"type": "array", "items": {"type": "integer"}},
        "zooms": {"type": "array", "items": {"type": "object", "properties": {
            "at": ANCHOR, "dur": {"type": "number"}, "to": {"type": "number"}, "kind": {"enum": ["punch", "push"]}},
            "required": ["at", "dur", "to", "kind"]}},
        "graphics": {"type": "array", "items": {"type": "object", "properties": {
            "at": ANCHOR, "dur": {"type": "number"}, "type": {"enum": ["kinetic", "stat", "emoji", "callout", "quote"]},
            "text": {"type": "string"}, "value": {"type": "number"}, "prefix": {"type": "string"}, "suffix": {"type": "string"},
            "label": {"type": "string"}, "emoji": {"type": "string"}, "icon": {"type": "string"}},
            "required": ["at", "dur", "type"]}},
        "fixes": {"type": "array", "items": {"type": "object", "properties": {
            "index": {"type": "integer"}, "word": {"type": "string"}}, "required": ["index", "word"]}},
    },
    "required": ["hook", "emphasis", "zooms", "graphics", "fixes"],
}


def main():
    clip_id = sys.argv[1]
    d = ROOT / "public/podcast-shorts" / clip_id
    clip = json.loads((d / "clip.json").read_text())
    words = clip["words"]
    m = clip["moment"]
    folder = ROOT / "podcasts" / clip_id.rsplit("-", 1)[0]
    speakers = json.loads((folder / "source.json").read_text()).get("speakers", "") if (folder / "source.json").exists() else ""
    prompt = PROMPT.format(
        duration=clip["duration"], speakers=speakers, hook=m["hook_title"], emotion=m["emotion"], why=m["why"],
        words="\n".join(f"{i} | {w['s']:.2f} | {w['w']}" for i, w in enumerate(words)),
        teaser=(f"COLD OPEN: 0-{clip['teaserEnd']:.1f} s is a teaser line repeated from later, then a rewind into the story. "
                f"Put no graphics before {clip['teaserEnd'] + 1.8:.1f} s; a punch zoom on the teaser's key word is welcome."
                if clip.get("teaserEnd") else ""),
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_"))}
    out = subprocess.run(["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(SCHEMA)],
                         input=prompt, capture_output=True, text=True, env=env, timeout=600)
    if out.returncode != 0:
        sys.exit(f"claude failed: {out.stderr[-2000:]}")
    env_json = json.loads(out.stdout)
    raw = env_json.get("structured_output") or json.loads(env_json["result"])

    n = len(words)
    # Nothing may cover the hook card, the cold open, or the rewind label after it.
    quiet = max(2.6, (clip.get("teaserEnd") or 0) + 1.8)
    # Caption fixes go straight into clip.json (keep the recogniser's word in "asr").
    fixed = []
    for f in raw.get("fixes", []):
        i, wd = f["index"], f["word"].strip()
        if 0 <= i < n and wd and wd != words[i]["w"]:
            words[i].setdefault("asr", words[i]["w"])
            fixed.append(f"{words[i]['w']}→{wd}")
            words[i]["w"] = wd
    (d / "clip.json").write_text(json.dumps(clip, ensure_ascii=False))
    at = lambda i: round(words[max(0, min(n - 1, int(i)))]["s"], 3)
    end = clip["duration"]

    def fit(t, dur):
        return max(0.0, min(dur, end - t - 0.05))

    zooms = []
    for z in sorted(raw["zooms"], key=lambda z: z["at"]):
        t = at(z["at"])
        if zooms and t < zooms[-1]["t"] + zooms[-1]["dur"] + 0.3:
            continue
        zooms.append({"t": t, "dur": round(fit(t, z["dur"]), 2), "to": max(1.05, min(1.5, z["to"])), "kind": z["kind"]})

    graphics, last_end = [], quiet
    for g in sorted(raw["graphics"], key=lambda g: g["at"]):
        t = max(at(g["at"]), quiet)
        if t < last_end + 0.5 or t > end - 1.0:
            continue
        g = {k: v for k, v in g.items() if k != "at" and v not in ("", None)}
        g["t"], g["dur"] = t, round(fit(t, g["dur"]), 2)
        if g["type"] == "stat" and "value" not in g:
            continue
        if g["type"] == "emoji" and "emoji" not in g:
            continue
        if g["type"] in ("kinetic", "callout", "quote") and "text" not in g:
            continue
        graphics.append(g)
        last_end = t + g["dur"]

    plan = {"hook": raw["hook"], "emphasis": sorted({i for i in raw["emphasis"] if 0 <= i < n}),
            "zooms": zooms, "graphics": graphics}
    (d / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    print(f"{clip_id}: hook '{plan['hook']}', {len(zooms)} zooms, {len(graphics)} graphics "
          f"({', '.join(g['type'] for g in graphics)}), {len(plan['emphasis'])} emphasised words, "
          f"caption fixes: {', '.join(fixed) or 'none'}")


if __name__ == "__main__":
    main()
