"""Non-Latin caption words → Latin script, one word for one word, keeping timings.

Usage: .venv/bin/python tools/podcast/romanize.py <clip-id>
Rewrites public/podcast-shorts/<id>/clip.json words in place (original kept as "orig").
make-shorts.sh runs it when source.json has a "language" other than "en". The caption font
(Montserrat) only has Latin glyphs, so Devanagari, Arabic, Cyrillic etc. would render as boxes.
English words written in another script come back as normal English spelling.
Uses the logged-in `claude` CLI (no API key).
"""
import json
import sys
from pathlib import Path
import llm

ROOT = Path(__file__).resolve().parents[2]

PROMPT = """Transliterate these caption words into natural Latin script, the way native speakers type them in social media comments.
Rules: exactly one output word per input word, same order and count, keep punctuation attached.
English words written in another script become normal English spelling. Words already in Latin script stay as they are.
{names}

Words (index | word):
{words}

Return JSON {{"words": [...]}} with exactly {n} strings."""


def main():
    clip_id = sys.argv[1]
    path = ROOT / "public/podcast-shorts" / clip_id / "clip.json"
    clip = json.loads(path.read_text())
    words = clip["words"]
    if all(w.get("orig") for w in words) or all(ch.isascii() or not ch.isalpha() or "\u00c0" <= ch <= "\u024f" for w in words for ch in w["w"]):
        print(f"{clip_id}: already Latin script")
        return
    source = ROOT / "podcasts" / clip_id.rsplit("-", 1)[0] / "source.json"
    people = json.loads(source.read_text()).get("people", []) if source.exists() else []
    names = ("Names in this source: " + ", ".join(p["name"] for p in people if p.get("name")) + ".") if people else ""
    n = len(words)
    schema = {"type": "object", "properties": {"words": {"type": "array", "items": {"type": "string"}, "minItems": n, "maxItems": n}}, "required": ["words"]}
    roman = llm.ask(PROMPT.format(words="\n".join(f"{i} | {w['w']}" for i, w in enumerate(words)), n=n, names=names),
                    schema, timeout=600)["words"]
    if len(roman) != n:
        sys.exit(f"{clip_id}: got {len(roman)} words for {n}")
    for w, r in zip(words, roman):
        w["orig"], w["w"] = w["w"], r.strip() or w["w"]
    path.write_text(json.dumps(clip, ensure_ascii=False))
    print(f"{clip_id}: {n} words → Latin script: {' '.join(roman[:16])} …")


if __name__ == "__main__":
    main()
