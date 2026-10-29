"""Word-level transcript with faster-whisper (free, local, CPU).

Usage: .venv/bin/python tools/podcast/transcribe.py <video> podcasts/<slug>/words.json [--lang en] [--model small]

The first run downloads the model from Hugging Face (small: ~460 MB). About 10 min for a 65 min
episode on an M1 Max. "--model large-v3" is slower but better on accents and noisy audio.
For sources that already have word-level auto-captions, tools/podcast/vtt_words.py is instant.
Writes {"duration", "segments": [{start, end, text, words: [{w, s, e}]}]}.
"""
import argparse
import json
import os

from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("out")
ap.add_argument("--lang", default="en")
ap.add_argument("--model", default="small")
args = ap.parse_args()

m = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
segs, info = m.transcribe(args.video, language=args.lang, vad_filter=True, beam_size=5,
                          word_timestamps=True, condition_on_previous_text=False)
res = []
for s in segs:
    res.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "words": [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for w in s.words]})
    if len(res) % 100 == 0:
        print(f"{s.end / info.duration * 100:.0f}%", flush=True)
json.dump({"duration": info.duration, "segments": res}, open(args.out, "w"), ensure_ascii=False)
print(f"done: {sum(len(s['words']) for s in res)} words, {info.duration / 60:.1f} min", flush=True)
