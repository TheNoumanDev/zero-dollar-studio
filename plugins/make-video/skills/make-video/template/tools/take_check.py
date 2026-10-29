"""Score voice takes against their script text with Whisper (MLX, on the Apple GPU), for tools/voice.py.

Run with the whisper-mlx venv:
  echo '{"lang": "en", "items": [{"path": "a.wav", "text": "Hello there."}]}' | \
    tools/whisper-mlx/.venv/bin/python tools/take_check.py
Prints JSON: [{"path", "heard", "wer"}] with wer = word error rate (0 = every word said, in order).
"""
import json
import re
import sys

import mlx_whisper

MODEL = "mlx-community/whisper-large-v3-turbo"


def words(text: str) -> list[str]:
    # Lowercase, drop punctuation (Latin + Devanagari danda), keep letters/digits of any script.
    text = re.sub(r"[^\w\s]|_", " ", text.lower().replace("।", " "))
    return text.split()


def wer(ref: list[str], hyp: list[str]) -> float:
    if not ref:
        return 0.0 if not hyp else 1.0
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i] + [0] * len(hyp)
        for j, h in enumerate(hyp, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h))
        prev = cur
    return prev[-1] / len(ref)


def main():
    job = json.load(sys.stdin)
    lang = job.get("lang", "en")
    out = []
    for item in job["items"]:
        heard = mlx_whisper.transcribe(item["path"], path_or_hf_repo=MODEL, language=lang,
                                       condition_on_previous_text=False, verbose=None)["text"].strip()
        out.append({"path": item["path"], "heard": heard, "wer": round(wer(words(item["text"]), words(heard)), 3)})
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
