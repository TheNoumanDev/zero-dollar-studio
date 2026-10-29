"""Word timings from YouTube auto-captions (.vtt with <c> word tags) → words.json.

Usage: .venv/bin/python tools/podcast/vtt_words.py <captions.vtt> podcasts/<slug>/words.json

Faster and, for Hindi, more accurate than Whisper small. Each rolling-caption cue that carries
<c> tags holds the new words: the first starts at the cue start, each tag gives the next word's
start, and a word ends where the next begins (capped at 1.2 s).
"""
import html
import json
import re
import sys

CUE = re.compile(r"(\d+:\d\d:\d\d\.\d+) --> (\d+:\d\d:\d\d\.\d+)[^\n]*\n(.*?)(?:\n\n|\Z)", re.S)
TAG = re.compile(r"<(\d+:\d\d:\d\d\.\d+)><c>(.*?)</c>")


def secs(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    segments = []
    for start, end, body in CUE.findall(text):
        line = next((ln for ln in body.split("\n") if "<c>" in ln), None)
        if not line:
            continue
        first = line.split("<", 1)[0].strip()
        words = [(secs(start), first)] if first else []
        words += [(secs(t), w.strip()) for t, w in TAG.findall(line) if w.strip()]
        # Decode entities and drop YouTube's ">>" speaker-change markers.
        words = [(t, html.unescape(w).replace(">>", "").strip()) for t, w in words]
        # Sound tags ("[snorts]", "[music]") are not speech.
        words = [(t, re.sub(r"\[[^\]]*\]", "", w).strip()) for t, w in words]
        words = [(t, w) for t, w in words if w]
        if not words:
            continue
        cue_end = secs(end)
        items = []
        for i, (s, w) in enumerate(words):
            e = words[i + 1][0] if i + 1 < len(words) else cue_end
            items.append({"w": w, "s": round(s, 2), "e": round(min(e, s + 1.2), 2)})
        segments.append({"start": items[0]["s"], "end": items[-1]["e"], "text": " ".join(x["w"] for x in items), "words": items})
    duration = segments[-1]["end"] if segments else 0
    json.dump({"duration": duration, "segments": segments, "source": "youtube-auto-captions"}, open(out, "w"), ensure_ascii=False)
    print(f"{sum(len(s['words']) for s in segments)} words in {len(segments)} segments, {duration / 60:.1f} min")


if __name__ == "__main__":
    main()
