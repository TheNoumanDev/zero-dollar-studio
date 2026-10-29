"""Sound effects for a podcast Short, keyed to its plan: whoosh on zooms and slides, pop on graphics.

Usage: .venv/bin/python tools/podcast/sfx.py <clip-id>
Writes public/podcast-shorts/<id>/sfx.wav (48 kHz stereo, peaks around -6 dBFS).
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SR = 48000
rng = np.random.default_rng(7)


def whoosh(dur=0.45, up=True):
    n = int(dur * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    # Cheap band sweep: blend low-passed and raw noise along the sweep.
    lp = np.convolve(noise, np.ones(24) / 24, mode="same")
    sweep = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    return ((lp * (1 - sweep) + noise * 0.35 * sweep) * env * 0.9).astype(np.float32)


def pop(freq=900, dur=0.09):
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    f = freq * (1 + 2 * np.exp(-tt * 60))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40)).astype(np.float32)


def boom(dur=0.5):
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    return (np.sin(2 * np.pi * 55 * tt * (1 - tt * 0.6)) * np.exp(-tt * 8) * 1.2).astype(np.float32)


def ding(dur=0.6):
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    return ((np.sin(2 * np.pi * 1320 * tt) + 0.5 * np.sin(2 * np.pi * 1980 * tt)) * np.exp(-tt * 7) * 0.5).astype(np.float32)


def rewind(dur=0.75):
    """Tape rewind: fast chirps falling in pitch over noise."""
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    f = 2400 * np.exp(-tt * 2.2) * (1 + 0.35 * np.sign(np.sin(2 * np.pi * 38 * tt)))
    chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    hiss = rng.standard_normal(len(tt)) * 0.12
    env = np.minimum(1, tt * 20) * np.exp(-np.maximum(0, tt - dur * 0.7) * 12)
    return ((chirp + hiss) * env).astype(np.float32)


def main():
    d = ROOT / "public/podcast-shorts" / sys.argv[1]
    clip = json.loads((d / "clip.json").read_text())
    plan = json.loads((d / "plan.json").read_text())
    # Optional end screen (source.json "endCard", EndCard.tsx END_SECONDS).
    END = 3.5 if clip.get("endCard") else 0.0
    out = np.zeros(int((clip["duration"] + END + 0.5) * SR), np.float32)

    def place(sig, at, gain):
        s = max(0, int(at * SR))
        e = min(len(out), s + len(sig))
        out[s:e] += sig[: e - s] * gain

    place(whoosh(0.35), 0.0, 0.8)          # hook card
    place(pop(700), 0.12, 0.7)
    for z in plan["zooms"]:
        if z["kind"] == "punch":
            place(whoosh(0.25), z["t"] - 0.15, 0.7)
            place(boom(), z["t"], 0.5)
    for g in plan["graphics"]:
        if g["type"] == "kinetic":
            place(boom(), g["t"], 0.7)
            place(whoosh(0.3), g["t"] - 0.12, 0.6)
        elif g["type"] == "stat":
            place(ding(), g["t"] + 0.5, 0.6)
            place(pop(800), g["t"], 0.6)
        elif g["type"] == "emoji":
            for i in range(4):
                place(pop(900 + i * 150), g["t"] + i * 0.09, 0.45)
        else:
            place(whoosh(0.4), g["t"] - 0.1, 0.6)
    if clip.get("teaserEnd"):
        place(rewind(), clip["teaserEnd"] - 0.35, 0.9)
    for t in [x for x in clip.get("splices", []) if abs(x - (clip.get("teaserEnd") or -9)) > 0.1]:
        place(whoosh(0.4), t - 0.2, 0.8)

    if END:
        # End screen: whoosh in, pop for the title, ding for the handle.
        place(whoosh(0.45), clip["duration"] - 0.35, 0.8)
        place(pop(700), clip["duration"] + 0.1, 0.7)
        place(ding(), clip["duration"] + 0.35, 0.6)

    peak = np.max(np.abs(out)) or 1.0
    out = out / peak * 0.5
    stereo = np.repeat((out * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(str(d / "sfx.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())
    print(f"{sys.argv[1]}: sfx.wav ({len(plan['zooms'])} zooms, {len(plan['graphics'])} graphics)")


if __name__ == "__main__":
    main()
