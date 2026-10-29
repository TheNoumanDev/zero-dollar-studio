"""
Voice lines with Indic Parler-TTS (AI4Bharat, Apache-2.0) for characters with "engine": "parler".
Optional engine for Hindi and other Indian languages (it also speaks Indian-accented English).

    tools/parler-venv/bin/python tools/voice_parler.py stories/<slug> [--takes 3]

Install: accept the model's terms on https://huggingface.co/ai4bharat/indic-parler-tts
(it's gated), `hf auth login`, then WITH_PARLER=1 tools/setup_cartoon.sh.
tools/make-episode.sh runs this before tools/voice.py automatically.

For each missing line it renders several takes and keeps the cleanest one (least
breathy hiss, plausible length), then cleans it up: trim silence, DeepFilterNet
denoise (MIT/Apache-2.0), 8 kHz low-pass, level-match. Files land where voice.py
expects them (public/<slug>/lines/<speaker>-<key>.wav, 24 kHz), so running
tools/voice.py afterwards builds the timeline from cache.

Character fields (series bible): "engine": "parler", "speaker": a Parler speaker
name from the model card, "style": a sentence about the voice. Line
"emotion"/"pace" become words in the description Parler reads.
"""

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from scipy.signal import resample_poly, stft  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import voice_key  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("story")
ap.add_argument("--takes", type=int, default=3)
args = ap.parse_args()
story = Path(args.story)
script = json.loads((story / "script.json").read_text())
LANG, chars = script.get("language", "en"), script["characters"]
out = Path("public") / story.name / "lines"
out.mkdir(parents=True, exist_ok=True)
SR_OUT = 24000

EMOTION = {"calm": "calm, gentle", "neutral": "natural", "warm": "warm, friendly", "excited": "excited, energetic, very expressive",
           "dramatic": "dramatic, very expressive", "whisper": "soft, hushed, secretive"}
PACE = {"slow": "at a slow pace", "normal": "at a moderate pace", "fast": "at a fast pace"}
QUALITY = "The recording is of very high quality, with the speaker's voice sounding clear and very close up."


def description(line: dict, c: dict) -> str:
    tone = EMOTION.get(line.get("emotion", "neutral"), "natural")
    pace = PACE.get(line.get("pace", "normal"))
    return f"{c['speaker']} speaks in a {tone} tone {pace}. {c.get('style', '')} {QUALITY}"


def hiss(a: np.ndarray, sr: int) -> float:
    """Breathy-noise score: energy 7–16 kHz vs 0.1–4 kHz while speaking (dB, lower = cleaner)."""
    fr, _, z = stft(a, sr, nperseg=2048)
    p = np.abs(z) ** 2
    tot = p.sum(0)
    s = tot > np.percentile(tot, 40)
    return float(10 * np.log10(p[(fr > 7000) & (fr < 16000)][:, s].sum() / (p[(fr > 100) & (fr < 4000)][:, s].sum() + 1e-12) + 1e-12))


def trim(a: np.ndarray, sr: int) -> np.ndarray:
    hop = sr // 100
    rms = np.array([np.sqrt(np.mean(a[i : i + hop] ** 2)) for i in range(0, len(a), hop)])
    idx = np.where(rms > rms.max() * 0.05)[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] * hop - int(0.03 * sr)) : min(len(a), (idx[-1] + 1) * hop + int(0.1 * sr))]


todo = []
for line in script["lines"]:
    c = chars.get(line["speaker"], {})
    if c.get("engine") != "parler":
        continue
    f = out / f"{line['speaker']}-{voice_key.cache_key(line, chars, LANG)}.wav"
    if not f.exists():
        todo.append((line, c, f))
print(f"{len(todo)} line(s) to voice with Parler")
if not todo:
    sys.exit(0)

from df.enhance import enhance, init_df  # noqa: E402
from parler_tts import ParlerTTSForConditionalGeneration  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

dev = "mps" if torch.backends.mps.is_available() else "cpu"
model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts").to(dev)
tok = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
dtok = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
SR = model.config.sampling_rate
df_model, df_state, _ = init_df(log_level="ERROR")

for n, (line, c, f) in enumerate(todo):
    t0 = time.time()
    words = len(line["text"].split())
    lo, hi = 0.2 * words, 0.75 * words + 1.5  # seconds: outside this is a broken take
    d = dtok(description(line, c), return_tensors="pt").to(dev)
    p = tok(line["text"], return_tensors="pt").to(dev)
    takes = []
    for seed in range(args.takes):
        torch.manual_seed(seed)
        a = model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask,
                           prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask).cpu().float().numpy().squeeze()
        a = trim(a, SR)
        dur = len(a) / SR
        score = hiss(a, SR) + (0 if lo <= dur <= hi else 100)
        takes.append((score, seed, dur, a))
    score, seed, dur, best = min(takes, key=lambda t: t[0])
    # Clean: DeepFilterNet at 48 kHz, 8 kHz low-pass, then 24 kHz for voice.py.
    x = resample_poly(best, 48000, SR).astype(np.float32)
    x = enhance(df_model, df_state, torch.from_numpy(x)[None], atten_lim_db=30).squeeze().numpy()
    fr = np.fft.rfftfreq(len(x), 1 / 48000)
    spec = np.fft.rfft(x)
    spec *= 1 / np.sqrt(1 + (fr / 8000) ** 8)  # gentle 4th-order low-pass
    x = np.fft.irfft(spec, len(x))
    x = resample_poly(x, SR_OUT, 48000).astype(np.float32)
    rms = np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) if np.any(np.abs(x) > 0.01) else 1
    x = np.clip(x * (0.1 / rms), -0.98, 0.98).astype(np.float32)  # every speaker at the same level
    sf.write(f, x, SR_OUT)
    print(f"[{n + 1}/{len(todo)} {line['speaker']:>7}] take {seed} (hiss {score:.1f} dB) {dur:.1f}s in {time.time() - t0:.0f}s  {line['text']}", flush=True)
