"""Speech loudness checks that Whisper's word timestamps miss, for takes.py.

Whisper stretches a word over the pause before (or after) it: "go" lasting 2.2 s is a 1.9 s pause plus "go".
That hides hesitations and restarts. Word ends also come early (a median 0.14 s), which clips last syllables
at a cut. refine() fixes both from a 10 ms loudness envelope. untranscribed() finds stretches of speech
with no words, e.g. a part in another language.
"""
import subprocess
from pathlib import Path

import numpy as np

HOP = 0.01          # envelope step, seconds
LONG_WORD = 0.4     # only words longer than this are checked for a swallowed pause
MIN_SILENCE = 0.25  # a quiet run this long inside a word is a pause
TAIL = 0.35         # how far a word's end may move out to where the voice stops
VERSION = 2         # words.json "refined": bump when refine() changes, so old transcripts are redone


def envelope(media: Path):
    """Per 10 ms: True where someone is speaking (loudness well above the recording's noise floor)."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(media), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    n = int(16000 * HOP)
    frames = x[: len(x) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)
    floor, loud = np.percentile(db, 10), np.percentile(db, 95)
    return db > floor + max(10.0, 0.35 * (loud - floor))


def _runs(mask, value):
    """(start, end) frame index pairs of runs equal to value."""
    d = np.diff(np.r_[False, mask == value, False].astype(int))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def refine(words, voiced):
    """Trim the pause out of stretched words. A long quiet run inside a word means the word sits on one side
    of it: after it when the word comes after a silence (the usual case), else before it."""
    moved = 0
    for w in words:
        if w["e"] - w["s"] <= LONG_WORD:
            continue
        a, b = int(w["s"] / HOP), min(len(voiced), int(w["e"] / HOP))
        quiet = [(s, e) for s, e in _runs(voiced[a:b], False) if (e - s) * HOP >= MIN_SILENCE]
        if not quiet:
            continue
        last_quiet_end = (a + quiet[-1][1]) * HOP
        first_quiet_start = (a + quiet[0][0]) * HOP
        if w["e"] - last_quiet_end >= 0.08:
            w["s"] = round(last_quiet_end - 0.03, 2)
        elif first_quiet_start - w["s"] >= 0.08:
            w["e"] = round(first_quiet_start + 0.05, 2)
        else:
            continue
        moved += 1
    # Late ends: follow the voice past the word end, up to TAIL and never into the next word.
    for w, nxt in zip(words, words[1:] + [None]):
        k, stop = int(w["e"] / HOP), min(len(voiced), int((w["e"] + TAIL) / HOP))
        if nxt is not None:
            stop = min(stop, int((nxt["s"] - 0.02) / HOP))
        while k < stop and voiced[k]:
            k += 1
        w["e"] = max(w["e"], round(k * HOP, 2))
    return moved


def untranscribed(words, voiced, min_len=3.0):
    """Stretches of speech (seconds) with no transcribed word, at least min_len long."""
    covered = np.zeros(len(voiced), bool)
    for w in words:
        covered[max(0, int(w["s"] / HOP) - 50): int(w["e"] / HOP) + 50] = True  # 0.5 s slack each side
    spans, start, last = [], None, None
    for i in np.flatnonzero(voiced & ~covered):
        if start is None or i - last > 100:  # a 1 s gap starts a new stretch
            if start is not None:
                spans.append((start * HOP, last * HOP))
            start = i
        last = i
    if start is not None:
        spans.append((start * HOP, last * HOP))
    return [(round(a, 1), round(b, 1)) for a, b in spans if b - a >= min_len]
