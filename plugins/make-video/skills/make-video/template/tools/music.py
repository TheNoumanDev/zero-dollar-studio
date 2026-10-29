"""
Compose music and sound effects that follow a story's timeline. Free and
offline: MIDI via mido, rendered with FluidSynth + GeneralUser GS soundfont,
SFX synthesised with numpy.

    .venv/bin/python tools/music.py stories/<slug>

Writes public/<slug>/music.wav and public/<slug>/sfx.wav (full length), and
adds a `music` block (bpm, beat grid, cut-to-beat errors) to timeline.json.

On-beat editing: the visual cut points (story events + outro) come from the
speech timing, so instead of moving the cuts we fit the music to them. The
tempo (100–124 BPM) and first-beat offset are searched so beats land as close
as possible to every cut; tools/qa.py then checks each cut is within 120 ms.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

t0 = time.time()
story = Path(sys.argv[1])
tl = json.loads((story / "timeline.json").read_text())
out = Path("public") / tl["slug"]
SF2 = "tools/soundfonts/GeneralUser-GS.sf2"
SR = 48000
total = tl["totalMs"] / 1000
stop_at = tl["events"].get("fridgeOpens", tl["outroStartMs"]) / 1000
sting_at = tl["events"].get("hide", tl["events"].get("fridgeOpens", tl["outroStartMs"])) / 1000
outro_at = tl["outroStartMs"] / 1000
# Music style from script.json ("music": {"style": "lofi"}); default = playful pizzicato.
STYLE = json.loads((story / "script.json").read_text()).get("music", {}).get("style", "playful")
LOFI = STYLE == "lofi"
if LOFI:  # the score runs under the whole video; no stop or sting
    stop_at = outro_at

# ---------- Fit tempo + offset so beats land on the cuts ----------
cuts = sorted({v / 1000 for v in tl["events"].values()} | {outro_at})


def fit_error(bpm: float, offset: float) -> float:
    b = 60 / bpm
    return max(abs(((c - offset) / b - round((c - offset) / b)) * b) for c in cuts)


best = (1e9, 112.0, 0.0)
BPM_RANGE = (76, 100) if LOFI else (100, 124)
for bpm in np.arange(BPM_RANGE[0], BPM_RANGE[1] + 0.01, 0.25):
    b = 60 / bpm
    for offset in np.arange(0, b, 0.005):
        err = fit_error(bpm, offset)
        if err < best[0]:
            best = (err, float(bpm), float(offset))
_, BPM, OFFSET = best

# ---------- Music (MIDI) ----------
TPB = 480
beat = 60 / BPM
mid = mido.MidiFile(ticks_per_beat=TPB)
events: list[tuple[float, mido.Message]] = []


def note(ch: int, pitch: int, start: float, length: float, vel: int):
    events.append((start, mido.Message("note_on", channel=ch, note=pitch, velocity=vel)))
    events.append((start + length, mido.Message("note_off", channel=ch, note=pitch, velocity=0)))


if LOFI:
    # Lo-fi tech bed (news/explainer Shorts): Rhodes 7th chords, warm pad, soft bass,
    # lazy swung boom-bap kit. Channels: 0 Rhodes, 1 bass, 2 pad, 9 drums.
    programs = {0: 4, 1: 33, 2: 89}
    CHORDS = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]  # Fmaj7 Em7 Dm7 Cmaj7
    MOTIF = [76, 74, 72, 69, 72, 74]  # pentatonic Rhodes fill, every 4th bar
    react_at = tl["events"].get("react")
    swing = beat * 0.12
    t, bar = OFFSET, 0
    while t < outro_at - 0.05:
        chord = CHORDS[bar % 4]
        # Drums drop out for the beat before the reaction, then come back on it.
        drums = not (react_at and react_at / 1000 - beat * 1.05 <= t + 3 * beat < react_at / 1000)
        for i, p in enumerate(chord):  # lazy strum
            note(0, p + 12, t + i * 0.025, beat * 3.6, 46)
        note(2, chord[0], t, beat * 4, 34)
        note(2, chord[2], t, beat * 4, 30)
        for bt, ln in ((0, 1.4), (1.5, 0.4), (2.5, 1.2)):
            note(1, chord[0] - 12, t + bt * beat, beat * ln, 72)
        for k in range(8):  # swung eighth hats
            s_ = t + k * beat / 2 + (swing if k % 2 else 0)
            if s_ < outro_at - 0.05:
                note(9, 42, s_, 0.08, 26 if k % 2 else 34)
        for bt in range(4):
            s_ = t + bt * beat
            if s_ >= outro_at - 0.05:
                break
            if bt == 3 and not drums:
                continue
            if bt in (0,) or (bt == 2 and bar % 2):
                note(9, 36, s_, 0.2, 70)
            if bt in (1, 3):
                note(9, 38, s_ + 0.015, 0.2, 44)
        if bar % 4 == 3:
            for i, p in enumerate(MOTIF):
                s_ = t + 2 * beat + i * beat / 3
                if s_ < outro_at - 0.05:
                    note(0, p, s_, beat / 3, 40)
        t += 4 * beat
        bar += 1
    if react_at:  # soft impact on the reaction
        note(9, 36, react_at / 1000, 0.3, 96)
        note(9, 49, react_at / 1000, 0.8, 50)
    # Outro: ringing Cmaj9.
    for p in (48, 55, 59, 62, 64, 67):
        note(0, p + 12, outro_at + 0.05, 2.0, 50)
    note(2, 48, outro_at, 2.0, 36)
    note(1, 36, outro_at + 0.05, 1.5, 70)
else:
    # Channels: 0 pizzicato strings, 1 bassoon, 2 glockenspiel, 3 orchestra hit, 9 drums
    programs = {0: 45, 1: 70, 2: 9, 3: 55}
    CHORDS = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]  # C Am F G

    t, bar = OFFSET, 0
    while t < stop_at - 0.05:
        chord = CHORDS[bar % 4]
        for i in range(8):  # eighth-note arpeggio
            s = t + i * beat / 2
            if s >= stop_at - 0.05:
                break
            p = chord[[0, 1, 2, 1, 0, 2, 1, 2][i]] + (12 if i in (2, 5) else 0)
            note(0, p, s, beat / 2.5, 62 if i % 2 == 0 else 48)
        for b in (0, 2):  # bouncy bassoon on 1 and 3
            s = t + b * beat
            if s < stop_at - 0.05:
                note(1, chord[0] - 24, s, beat * 0.8, 70)
        for b in range(4):  # soft shaker-ish hi-hat
            s = t + b * beat + beat / 2
            if s < stop_at - 0.05:
                note(9, 42, s, 0.1, 30)
        t += 4 * beat
        bar += 1

    # Sting on "Hide!": orchestra hit + timpani-ish low hit.
    note(3, 48, sting_at, 0.6, 110)
    note(3, 55, sting_at, 0.6, 100)
    note(9, 49, sting_at, 0.8, 100)  # crash

    # Outro: cheerful glockenspiel arpeggio resolving to C.
    for i, p in enumerate([72, 76, 79, 84, 79, 84]):
        note(2, p, outro_at + 0.2 + i * 0.16, 0.5 if i < 5 else 1.2, 80)
    note(1, 36, outro_at + 0.2, 1.5, 70)

events.sort(key=lambda e: (e[0], e[1].type == "note_on"))
track = mido.MidiTrack()
mid.tracks.append(track)
track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM)))
for ch, prog in programs.items():
    track.append(mido.Message("program_change", channel=ch, program=prog))
last = 0
for s, msg in events:
    tick = int(round(s / beat * TPB))  # MIDI time 0 = audio time 0, so beats stay where we fitted them
    track.append(msg.copy(time=max(0, tick - last)))
    last = max(last, tick)
midi_path = out / "music.mid"
mid.save(midi_path)

raw = out / "music-raw.wav"
subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.8", "-r", str(SR), "-F", str(raw), SF2, str(midi_path)], check=True)
# Music bed sits well under the voices.
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                f"loudnorm=I=-24:TP=-3,apad,atrim=0:{total}", "-ar", str(SR), "-ac", "2", str(out / "music.wav")], check=True)
raw.unlink()

# ---------- SFX (numpy) ----------
rng = np.random.default_rng(7)
sfx = np.zeros(int(total * SR) + SR, dtype=np.float32)


def place(sig: np.ndarray, at: float, gain=1.0):
    s = int(at * SR)
    e = min(len(sfx), s + len(sig))
    sfx[s:e] += sig[: e - s] * gain


def whoosh(dur=0.6):
    n = int(dur * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    # Sweep a one-pole low-pass cutoff up then down.
    cut = np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.35 + 0.02
    y, prev = np.zeros(n, np.float32), 0.0
    for i in range(n):
        prev += cut[i] * (noise[i] - prev)
        y[i] = prev
    return y * np.sin(np.linspace(0, np.pi, n)) * 0.9


def thunk(freq=70, dur=0.35):
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    return (np.sin(2 * np.pi * freq * tt * (1 - tt)) * np.exp(-tt * 14)).astype(np.float32)


def pop(freq=900, dur=0.09):
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    f = freq * (1 + 2 * np.exp(-tt * 60))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40)).astype(np.float32)


if "fridgeOpens" in tl["events"]:
    # Fridge hum under everything until the door opens.
    tt = np.arange(int(stop_at * SR)) / SR
    hum = (np.sin(2 * np.pi * 55 * tt) + 0.4 * np.sin(2 * np.pi * 110 * tt)) * 0.02
    sfx[: len(hum)] += hum.astype(np.float32)
    # Door opens: latch thunk + air whoosh.
    place(thunk(), stop_at, 0.9)
    place(whoosh(0.7), stop_at + 0.05, 0.6)
# Motion cues: a whoosh on every camera/avatar move event.
for name, ms in tl["events"].items():
    if name in ("fly", "flash", "pose", "center", "lift", "flex"):
        place(whoosh(0.45), ms / 1000 - 0.1, 0.5)
    if name in ("flash", "lift"):
        place(thunk(110, 0.25), ms / 1000, 0.6)
    if name == "crash":  # metal crash: noise burst + low thunk
        n = int(0.5 * SR)
        place(rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 9, n)).astype(np.float32) * 0.8, ms / 1000)
        place(thunk(55, 0.5), ms / 1000, 1.0)


def clang(dur=1.2):
    """Steel plate hit: inharmonic partials with a fast attack and long ring."""
    tt = np.linspace(0, dur, int(dur * SR), endpoint=False)
    parts = [(523, 1.0), (1311, 0.6), (2087, 0.45), (3460, 0.3), (4720, 0.2)]
    y = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * (3 + f / 900)) for f, a in parts)
    click = rng.standard_normal(len(tt)) * np.exp(-tt * 120) * 0.6
    return ((y + click) * 0.5).astype(np.float32)


def shimmer(dur=1.2, rising=True):
    """Magic: a fast arpeggio of soft bells, up (appear) or down (vanish)."""
    y = np.zeros(int(dur * SR), np.float32)
    notes = [72, 76, 79, 84, 88, 91, 96]
    notes = notes if rising else notes[::-1]
    for i, n in enumerate(notes):
        f = 440 * 2 ** ((n - 69) / 12)
        t0 = i * dur / (len(notes) + 2)
        tt = np.linspace(0, dur - t0, int((dur - t0) * SR), endpoint=False)
        bell = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.01 * f * tt)) * np.exp(-tt * 5)
        s0 = int(t0 * SR)
        y[s0 : s0 + len(bell)] += bell.astype(np.float32) * 0.35
    return y


def crackle(dur=1.0):
    """Fire: low rumble plus random pops."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    rumble = np.sin(2 * np.pi * 48 * tt) * 0.4 * np.sin(np.pi * tt / dur)
    pops = (rng.random(n) > 0.9985) * rng.standard_normal(n) * 3
    pops = np.convolve(pops, np.exp(-np.arange(200) / 30), mode="same")
    return ((rumble + pops * 0.3) * 0.8).astype(np.float32)


# Story events → sound.
for name, ms in tl["events"].items():
    at = ms / 1000
    if name == "scream":
        place(thunk(50, 0.6), at, 1.0)
        place(thunk(45, 0.7), at + 0.45, 1.0)
    elif name in ("chappalFloat",):
        place(shimmer(1.4), at, 0.7)
    elif name == "thaliBlock":
        place(whoosh(0.4), at - 0.35, 0.6)
        place(clang(), at + 0.05, 1.0)
    elif name == "chhotuFade":
        place(shimmer(1.2, rising=False), at, 0.7)
    elif name in ("chhotuFadeIn", "lesson"):
        place(shimmer(1.3), at, 0.7)
    elif name == "eyesFlash":
        place(crackle(1.1), at, 0.9)
    elif name in ("turnToPapa", "papaRun", "kitchen", "living", "underTable", "sheruSniff"):
        place(whoosh(0.5), at - 0.15, 0.55)
if LOFI:
    # A whoosh + UI blip on every beat. No vinyl crackle/hiss: any hiss under the voice reads as noise.
    for name, ms in tl["events"].items():
        place(whoosh(0.4), ms / 1000 - 0.12, 0.45)
        place(pop(1500 if name != "react" else 500, 0.07), ms / 1000 + 0.02, 0.35)
        if name == "react":
            place(thunk(58, 0.5), ms / 1000, 0.9)
# Small pop as each character starts talking.
for l in ([] if LOFI else tl["lines"]):
    place(pop(700 if l["speaker"] == "carrot" else 1000), l["startMs"] / 1000 - 0.04, 0.25)
# Outro card pops.
place(pop(1200), outro_at + 0.15, 0.4)

sfx = sfx[: int(total * SR)]
sfx = sfx / max(1e-6, np.abs(sfx).max()) * 0.7
sf.write(out / "sfx.wav", np.stack([sfx, sfx], axis=1), SR)
beats = [round((OFFSET + k * beat) * 1000) for k in range(int((total - OFFSET) / beat) + 1)]
tl["music"] = {
    "bpm": BPM,
    "firstBeatMs": round(OFFSET * 1000),
    "beatsMs": beats,
    "cuts": [{"ms": round(c * 1000), "offBeatMs": round(min(abs(c * 1000 - b) for b in beats))} for c in cuts],
}
(story / "timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False))
worst = max(c["offBeatMs"] for c in tl["music"]["cuts"])
print(f"Music + SFX for {total:.1f}s in {time.time() - t0:.1f}s · {BPM} BPM, {len(cuts)} cuts, worst {worst} ms off-beat")
