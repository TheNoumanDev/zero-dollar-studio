"""
Generate character voices for a story with Chatterbox (MIT, runs locally).

    .venv/bin/python tools/voice.py stories/<slug>

Reads <story>/script.json and writes:
  public/<slug>/lines/<speaker>-<hash>.wav  one file per line (cached by text + voice settings)
  public/<slug>/voice.wav                all lines placed on the timeline
  <story>/timeline.json                  timings, events, mouth envelopes
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).parent))
import voice_key  # noqa: E402

DIRECTION_KEYS = voice_key.DIRECTION_KEYS

story = Path(sys.argv[1])
script = json.loads((story / "script.json").read_text())
slug = story.name
out = Path("public") / slug
(out / "lines").mkdir(parents=True, exist_ok=True)
FPS = script["format"]["fps"]
# "en" uses the English model; any other code (e.g. "hi") uses the multilingual model.
LANG = script.get("language", "en")
LEAD_IN = 0.25  # seconds of silence before the first line

device = "mps" if torch.backends.mps.is_available() else "cpu"
t_load = time.time()

_model = None
SR = 24000  # Chatterbox output sample rate


def get_model():
    """Load lazily, so a fully cached run never pays the model load."""
    global _model
    if _model is None:
        if LANG == "en":
            from chatterbox.tts import ChatterboxTTS

            _model = ChatterboxTTS.from_pretrained(device=device)
        else:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            _model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        print(f"Loaded Chatterbox on {device} in {time.time() - t_load:.1f}s")
    return _model


def trim_tail(audio: np.ndarray) -> np.ndarray:
    """Trim edges, and drop anything after a long silence at the end.

    The multilingual model sometimes keeps going after the sentence: seconds of
    near-silence, then a burst of garbage. Real speech has no gaps > ~0.8 s
    inside one sentence (comma pauses run ~0.5 s), so everything after such a gap is cut.
    """
    hop = SR // 100  # 10 ms frames
    rms = np.array([np.sqrt(np.mean(audio[i : i + hop] ** 2)) for i in range(0, len(audio), hop)])
    if not len(rms) or rms.max() == 0:
        return audio
    voiced = rms > rms.max() * 0.06
    idx = np.where(voiced)[0]
    if not len(idx):
        return audio
    start, end = idx[0], idx[0]
    for i in idx[1:]:
        if i - end > 80:  # > 0.8 s gap: the rest is a tail (comma pauses stay)
            break
        end = i
    return audio[max(0, start * hop - int(0.03 * SR)) : min(len(audio), (end + 1) * hop + int(0.08 * SR))]


def cut_mumble(audio: np.ndarray, n_words: int) -> np.ndarray:
    """Cut a quiet mumbling tail after the sentence (non-English model).

    The multilingual model can trail on for seconds at low volume (never silent,
    so trim_tail's gap rule misses it). After 70% of the expected length
    (~0.38 s per word), the first 300 ms stretch whose loudness stays under 18%
    of the line's peak marks the end of the real sentence.
    """
    hop = SR // 100
    rms = np.array([np.sqrt(np.mean(audio[i : i + hop] ** 2)) for i in range(0, len(audio), hop)])
    if not len(rms) or rms.max() == 0:
        return audio
    quiet = rms < rms.max() * 0.18
    first = int(0.7 * 0.38 * n_words * 100)
    run = 0
    for i in range(max(0, first), len(quiet)):
        run = run + 1 if quiet[i] else 0
        if run >= 30:  # 300 ms of quiet
            end = i - run + 1
            return audio[: min(len(audio), end * hop + int(0.08 * SR))]
    return audio


def has_growl(audio: np.ndarray) -> bool:
    """A breakdown growl: over 1.1 s that stays loud with no syllable dips (speech dips every ~0.2 s).

    The multilingual model sometimes buzzes mid-line and then carries on; Whisper doesn't notice
    because no words go missing. 20 ms frames; a 0.5 s window counts as steady when every frame is
    above -30 dB and they all sit within 14 dB of each other.
    """
    hop = SR // 50
    db = np.array([20 * np.log10(np.sqrt(np.mean(audio[i : i + hop] ** 2)) + 1e-9) for i in range(0, len(audio) - hop, hop)])
    win, run = 25, 0
    for i in range(len(db) - win):
        w = db[i : i + win]
        run = run + 1 if w.min() > -30 and w.max() - w.min() < 14 else 0
        if run * 0.02 + 0.5 > 1.1:
            return True
    return False


def generate_once(text: str, char: dict) -> np.ndarray:
    extra = {} if LANG == "en" else {"language_id": LANG}
    wav = get_model().generate(
        text,
        audio_prompt_path=char.get("refVoice") or None,  # no reference → Chatterbox's built-in voice
        exaggeration=char.get("exaggeration", 0.5),
        cfg_weight=char.get("cfgWeight", 0.5),
        **extra,
    )
    return trim_tail(wav.squeeze(0).cpu().numpy().astype(np.float32))


# Take checking: Whisper transcribes each sentence's take; if it hears a skipped or garbled word, up to
# VOICE_TAKES takes are made and the one whose words match the script best wins. VOICE_TAKES=1 turns it off.
TAKES = int(os.environ.get("VOICE_TAKES", "3"))
CHECKER = Path(__file__).parent / "whisper-mlx/.venv/bin/python"


def score_takes(takes: list[np.ndarray], sentence: str) -> list[float]:
    """Word error rate of each take against the sentence (lower is better); [] if the checker isn't available."""
    if not CHECKER.exists():
        return []
    with tempfile.TemporaryDirectory() as d:
        items = []
        for i, a in enumerate(takes):
            path = str(Path(d) / f"take{i}.wav")
            sf.write(path, a, SR)
            items.append({"path": path, "text": sentence})
        r = subprocess.run([str(CHECKER), str(Path(__file__).parent / "take_check.py")],
                           input=json.dumps({"lang": LANG, "items": items}), capture_output=True, text=True)
        if r.returncode != 0:
            print(f"   take check failed: {r.stderr.strip()[-300:]}")
            return []
        return [x["wer"] for x in json.loads(r.stdout)]


def speak(text: str, char: dict) -> np.ndarray:
    """Generate sentence by sentence (more stable): several takes each, drop runaways, keep the clearest."""
    sentences = [x.strip() for x in re.split(r"(?<=[.!?।])\s+", text) if x.strip()]
    parts = []
    for sentence in sentences:
        # ~0.6 s per word + slack; anything far longer is a runaway take.
        limit = 0.6 * len(sentence.split()) + 1.2
        def fresh(seed: int) -> np.ndarray | None:
            torch.manual_seed(seed)
            a = generate_once(sentence, char)
            if LANG != "en":
                a = cut_mumble(a, len(sentence.split()))
            if len(a) / SR > limit:
                print(f"   runaway take: {len(a) / SR:.1f}s > {limit:.1f}s for: {sentence}")
                return None
            if has_growl(a):
                print(f"   growl in take, retrying: {sentence}")
                return None
            return a

        # First take; only if Whisper hears a mistake do we pay for more takes.
        takes, seed, last = [], 1234, None
        while not takes and seed < 1237:
            last = fresh(seed)
            seed += 1
            if last is not None:
                takes.append(last)
        if not takes:  # every take ran away: keep the last one rather than nothing
            takes = [generate_once(sentence, char)]
        scores = score_takes(takes, sentence) if TAKES > 1 else []
        if scores and scores[0] > 0:
            while len(takes) < TAKES and seed < 1234 + TAKES + 3:
                a = fresh(seed)
                seed += 1
                if a is not None:
                    takes.append(a)
            scores = score_takes(takes, sentence) or scores + [1.0] * (len(takes) - len(scores))
        best = 0
        if len(scores) > 1:
            # Lowest word error rate; ties go to the shorter take (less trailing noise).
            best = min(range(len(takes)), key=lambda i: (scores[i], len(takes[i])))
            print(f"   takes {[round(x, 2) for x in scores]} -> #{best + 1} for: {sentence[:60]}")
        elif scores:
            print(f"   take 1 clean (wer {scores[0]}) for: {sentence[:60]}")
        parts.append(takes[best])
    gap = np.zeros(int(0.12 * SR), dtype=np.float32)
    return np.concatenate([p for a in parts for p in (a, gap)][:-1])


def envelope(audio: np.ndarray) -> list[float]:
    """Per-frame loudness 0..1, used to animate mouths."""
    hop = SR // FPS
    rms = [float(np.sqrt(np.mean(audio[i : i + hop] ** 2))) for i in range(0, len(audio), hop)]
    peak = max(rms) or 1.0
    return [round(min(1.0, r / peak * 1.2), 3) for r in rms]


# ---------- Voice direction (per line, optional) ----------
# "emotion" → Chatterbox exaggeration; "pace" → cfg_weight (lower = slower, more
# deliberate) plus a gentle time-stretch for "fast"; "emphasis" words are sent in
# CAPS (Chatterbox stresses them) and highlighted in captions; "pauseBefore" adds
# silence before the line.
EMOTION = {"calm": 0.35, "neutral": 0.5, "warm": 0.55, "excited": 0.75, "dramatic": 0.9, "whisper": 0.3}
PACE = {"slow": (0.3, 1.0), "normal": (0.5, 1.0), "fast": (0.55, 1.08)}  # (cfg_weight, tempo)


def directed(line: dict, char: dict) -> tuple[str, dict, float]:
    """Spoken text, voice settings and tempo for a line after applying its direction."""
    text, settings = line["text"], dict(char)
    if line.get("emotion"):
        settings["exaggeration"] = EMOTION[line["emotion"]]
    tempo = 1.0
    if line.get("pace"):
        settings["cfgWeight"], tempo = PACE[line["pace"]]
    for w in line.get("emphasis", []):
        text = re.sub(rf"\b{re.escape(w)}\b", w.upper(), text, flags=re.IGNORECASE)
    return text, settings, tempo


def stretch(audio: np.ndarray, tempo: float) -> np.ndarray:
    if tempo == 1.0:
        return audio
    import subprocess as sp
    raw = sp.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                  "-af", f"atempo={tempo}", "-f", "f32le", "-"], input=audio.tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def cache_key(line: dict) -> str:
    return voice_key.cache_key(line, script["characters"], LANG)


lines, cursor, gen_seconds, cached = [], LEAD_IN, 0.0, 0
events = {}
for n, line in enumerate(script["lines"]):
    t = time.time()
    cursor += line.get("pauseBefore", 0)
    f = out / "lines" / f"{line['speaker']}-{cache_key(line)}.wav"
    if f.exists():
        audio, _ = sf.read(f, dtype="float32")
        cached += 1
    elif line["speaker"] == "all":
        # Everyone shouts together: mix all character takes.
        takes = [speak(*directed(line, c)[:2]) for c in script["characters"].values()]
        audio = np.zeros(max(len(a) for a in takes), dtype=np.float32)
        for a in takes:
            audio[: len(a)] += a / len(takes) * 1.6
    elif script["characters"][line["speaker"]].get("engine"):
        sys.exit(f"Character {line['speaker']} uses engine {script['characters'][line['speaker']]['engine']!r}; this template only ships Chatterbox")
    else:
        spoken, settings, tempo = directed(line, script["characters"][line["speaker"]])
        audio = stretch(speak(spoken, settings), tempo)
    took = time.time() - t
    gen_seconds += took
    if not f.exists():
        sf.write(f, audio, SR)
    dur = len(audio) / SR
    print(f"[{n:02d} {line['speaker']:>8}] {dur:4.1f}s audio in {took:4.1f}s  {line['text']}")
    lines.append({
        "speaker": line["speaker"],
        "text": line["text"],
        # What viewers read; defaults to the spoken text (e.g. Roman Hinglish over Devanagari speech).
        "caption": line.get("caption", line["text"]),
        "file": str(f),
        "src": f"{slug}/lines/{f.name}",
        "startMs": round(cursor * 1000),
        "durationMs": round(dur * 1000),
        "endMs": round((cursor + dur) * 1000),
        "envelope": envelope(audio),
        "emphasis": line.get("emphasis", []),
        "direction": {k: line[k] for k in ("emotion", "pace", "pauseBefore") if k in line},
    })
    if "event" in line:
        # "start": when the line begins; default: in the pause after it.
        at = cursor if line.get("eventAt") == "start" else cursor + dur + line["pauseAfter"] / 2
        at += line.get("eventOffset", 0)  # e.g. land the CLANG on the frame where the AI clip's shield moves
        events[line["event"]] = round(at * 1000)
    cursor += dur + line["pauseAfter"]

voice_end = cursor
total = voice_end + script["outro"]["seconds"]
track = np.zeros(int(total * SR) + SR, dtype=np.float32)
for l in lines:
    a, _ = sf.read(l["file"], dtype="float32")
    s = int(l["startMs"] / 1000 * SR)
    track[s : s + len(a)] += a
sf.write(out / "voice.wav", track[: int(total * SR)], SR)

timeline = {
    "slug": slug,
    "language": LANG,
    "fps": FPS,
    "lines": lines,
    "events": events,
    "outroStartMs": round(voice_end * 1000),
    "totalMs": round(total * 1000),
    "durationInFrames": int(np.ceil(total * FPS)),
    "stats": {"device": device, "generationSeconds": round(gen_seconds, 1), "cachedLines": cached, "audioSeconds": round(sum(l["durationMs"] for l in lines) / 1000, 1)},
}
(story / "timeline.json").write_text(json.dumps(timeline, indent=1))
print(f"Total {total:.1f}s video, voice generated in {gen_seconds:.1f}s ({cached} lines from cache)")
