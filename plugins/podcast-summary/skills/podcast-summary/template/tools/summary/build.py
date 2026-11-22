"""
Podcast summary builder: the speakers' real voices, cut into short whole-sentence clips, played over an animated
stand-in for each person (src/compositions/PodcastSummary). Your own commentary is text only (topic titles, cards,
context lines, reaction bubbles); a real still from the episode flashes at the start of each scene.

    .venv/bin/python tools/summary/build.py summaries/<slug> [--short] [--check]

summaries/<slug>/script.json: scenes, each with lines [[who, in, out], …] in source seconds (rough is fine).
Every line is snapped to whole words and then to silence on the real audio, so no sentence is cut mid-word.
The audio is never pitch-shifted, sped up or otherwise altered. --check re-transcribes every cut clip with
Whisper (make-video's tools/take_check.py) and prints what is heard next to the caption text.

→ public/summary/<slug>[-short]/ audio.wav, s<N>.jpg stills, manifest.json (read by the PodcastSummary composition).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "tools/podcast"))
SR = 48000
FPS = 30
LINE_GAP = 0.25   # silence between two lines of one scene
SCENE_GAP = 0.5   # between scenes (Shorts); long cuts get SCENE_GAP_LONG with a soft whoosh under the still wiping in
SCENE_GAP_LONG = 0.8
END_CARD = 4.5
FADE = 0.03


def load_audio(src: Path) -> np.ndarray:
    cache = src.with_name("audio-48k.wav")
    if not cache.exists():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", str(SR), str(cache)], check=True)
    a, _ = sf.read(cache, dtype="float32")
    return a


def db(x: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def quiet(audio: np.ndarray, t: float, win: float = 0.06) -> bool:
    a = audio[int(t * SR): int((t + win) * SR)]
    return len(a) == 0 or db(a) < -40


def snap(words: list[dict], audio: np.ndarray, rough_in: float, rough_out: float) -> tuple[float, float, list[dict]]:
    """Whole words inside the rough span, then the cut points moved into silence (never into a neighbour word)."""
    inside = [i for i, w in enumerate(words) if w["s"] >= rough_in - 0.15 and w["s"] < rough_out]
    i0, i1 = inside[0], inside[-1]
    prev_e = words[i0 - 1]["e"] if i0 > 0 else 0.0
    next_s = words[i1 + 1]["s"] if i1 + 1 < len(words) else len(audio) / SR
    # End: walk forward from the last word's end until 80 ms of quiet, stopping short of the next word.
    limit = min(next_s - 0.03, words[i1]["e"] + 0.8)
    end, t = limit, words[i1]["e"]
    while t < limit:
        if quiet(audio, t) and quiet(audio, t + 0.04):
            end = t + 0.06
            break
        t += 0.01
    # Start: walk back from the first word's start to the last quiet point after the previous word.
    floor = max(prev_e + 0.02, words[i0]["s"] - 0.5)
    start, t = floor, words[i0]["s"]
    while t > floor:
        if quiet(audio, t - 0.06) and quiet(audio, t - 0.1):
            start = t - 0.05
            break
        t -= 0.01
    return max(start, floor), min(end, limit), words[i0: i1 + 1]


ROMAN_PROMPT = """Transliterate these Hindi caption lines into natural Roman Hinglish, the way Indians type on Instagram.
Rules: for every line, exactly one output word per input word, same order and count; keep punctuation attached (। becomes .).
English words written in Devanagari become normal English spelling ("बिकॉज़" → "because", "स्प्लिट्स" → "Splits").
Names: {names}. Common Hinglish spellings: hai, nahi, kya, yaar, mein, ke, ki, toh.

{lines}

Return JSON {{"lines": [[...], ...]}}: {n} lines, each with exactly the word count shown."""


def romanize(lines: list[list[str]], cache: Path, names: str) -> list[list[str]]:
    """Devanagari caption words → Roman Hinglish, word for word (the caption font has no Devanagari). Cached per line,
    in one call to your agent CLI (snipshorts' llm.py)."""
    done = json.loads(cache.read_text()) if cache.exists() else {}
    todo = [ws for ws in lines if " ".join(ws) not in done and any("ऀ" <= ch <= "ॿ" for w in ws for ch in w)]
    if todo:
        listing = "\n".join(f"Line {i} ({len(ws)} words): " + " | ".join(ws) for i, ws in enumerate(todo))
        schema = {"type": "object", "properties": {"lines": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}}, "required": ["lines"]}
        import llm  # snipshorts' tools/podcast/llm.py: Claude Code by default, or SNIPSHORTS_LLM
        got = llm.ask(ROMAN_PROMPT.format(names=names, lines=listing, n=len(todo)), schema)["lines"]
        for ws, r in zip(todo, got):
            if len(r) == len(ws):
                done[" ".join(ws)] = [x.strip() or w for x, w in zip(r, ws)]
            else:
                print(f"  ⚠️  romanize count mismatch ({len(r)} for {len(ws)}): {' '.join(ws)[:60]}")
        cache.write_text(json.dumps(done, ensure_ascii=False, indent=0))
    return [done.get(" ".join(ws), ws) for ws in lines]


def pop(gain: float = 0.22, base: float = 520) -> np.ndarray:
    """A short rising blip for each face in the cast intro (and a higher one as its card flips over)."""
    n = int(0.12 * SR)
    x = np.arange(n) / SR
    f = base + 900 * x / x[-1]
    return (gain * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 34)).astype(np.float32)


def whoosh(gain: float = 0.05) -> np.ndarray:
    """A soft airy swell for scene changes: band-limited noise, rising then falling (peak in the middle)."""
    n = int(0.5 * SR)
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n).astype(np.float32)
    x = np.convolve(x, np.ones(24) / 24, mode="same") - np.convolve(x, np.ones(240) / 240, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (gain * x / (np.abs(x).max() + 1e-9) * env).astype(np.float32)


def align(toks: list[str], ws: list[dict]) -> list[dict]:
    """Hand-written caption words on Whisper's real word times. Tokens that match a Whisper word take its times;
    the rest are spread (by length) between their matched neighbours, so the lit word follows the voice through pauses."""
    from difflib import SequenceMatcher
    norm = lambda w: "".join(ch for ch in w.lower() if ch.isalnum())
    times: list[tuple[float, float] | None] = [None] * len(toks)
    sm = SequenceMatcher(None, [norm(x) for x in toks], [norm(w["w"]) for w in ws], autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = ws[blk.b + k]
            times[blk.a + k] = (w["s"], w["e"])
    i = 0
    while i < len(toks):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(toks) and times[j] is None:
            j += 1
        a0 = times[i - 1][1] if i > 0 else ws[0]["s"]
        a1 = times[j][0] if j < len(toks) else ws[-1]["e"]
        if a1 - a0 < 0.05 * (j - i):  # no room between neighbours: share the neighbour's slot instead
            a0, a1 = (times[i - 1][0] if i > 0 else a0), max(a1, a0 + 0.12 * (j - i))
        wt = np.cumsum([0] + [len(x) + 1 for x in toks[i:j]])
        k = (a1 - a0) / wt[-1]
        for q in range(i, j):
            times[q] = (a0 + wt[q - i] * k, a0 + wt[q - i + 1] * k - 0.02)
        i = j
    return [{"w": x, "s": s0, "e": e0} for x, (s0, e0) in zip(toks, times)]


def fade(a: np.ndarray) -> np.ndarray:
    n = min(int(FADE * SR), len(a) // 2)
    ramp = np.linspace(0, 1, n, dtype=np.float32)
    a = a.copy()
    a[:n] *= ramp
    a[-n:] *= ramp[::-1]
    return a


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    short, check = "--short" in sys.argv, "--check" in sys.argv
    story = PROJECT / args[0]
    script = json.loads((story / "script.json").read_text())
    slug = story.name + ("-short" if short else "")
    out = PROJECT / "public/summary" / slug
    out.mkdir(parents=True, exist_ok=True)
    src = PROJECT / script["source"]
    audio = load_audio(src)
    words = [w for s in json.loads((PROJECT / script["words"]).read_text())["segments"] for w in s["words"]]
    fixes = script.get("fix", [])

    def fix(w: str) -> str:
        for a, b in fixes:
            if w == a:
                return b
        return w

    lang = script.get("lang", "en")
    picked = [sc for sc in script["scenes"] if not short or sc.get("short")]
    if lang == "hi":
        # One batched transliteration for every line that has no hand-written caption (4th field).
        need = []
        for sc in picked:
            for ln in sc["lines"]:
                if len(ln) < 4:
                    s0, s1, ws = snap(words, audio, ln[1], ln[2])
                    need.append([w["w"] for w in ws if w["s"] < s1 - 0.05 and w["e"] > s0 + 0.05])
        romanize(need, story / "roman.json", script.get("names", ""))
    roman_cache = json.loads((story / "roman.json").read_text()) if (story / "roman.json").exists() else {}

    # Cast intro ("meet the cast": each real face, then its animated card and name) before the first clip, if the script asks.
    cast_keys = list((script.get("cast") or {}).keys())
    who_in = {ln[0] for sc in picked for li, ln in enumerate(sc["lines"]) if not short or not sc.get("shortLines") or li in sc["shortLines"]}
    intro_cast = [w for w in cast_keys if w in who_in or w == script.get("listener")]
    intro_len = script.get("introShort" if short else "intro", 0) if script.get("faces") else 0
    intro = None
    if intro_len:
        gap = min(0.5, (intro_len - 1.6) / max(1, len(intro_cast)))
        at = [round(0.4 + i * gap, 2) for i in range(len(intro_cast))]
        # Each real-photo card flips over `flip` s after it pops in; the last flip settles ~0.9 s before the end.
        flip = round(float(np.clip(intro_len - 1.35 - at[-1], 0.6, 1.3)), 2) if at else 0
        intro = {"dur": intro_len, "cast": intro_cast, "at": at, "flip": flip, "faces": script["faces"]}
    t, pieces, scenes, lines_out, caps, clips, fx = float(intro_len), [], [], [], [], [], []
    if intro_len:
        lead = np.zeros(int(intro_len * SR), np.float32)
        for a in intro["at"]:
            for when, b in ((a, pop()), (a + intro["flip"], pop(0.16, 900))):
                lead[int(when * SR): int(when * SR) + len(b)] += b
        pieces.append(lead)
    for n, sc in enumerate(picked):
        keep = sc.get("shortLines") if short and sc.get("shortLines") else list(range(len(sc["lines"])))
        start_scene, starts = t, {}
        for li in keep:
            who, a, b, *override = sc["lines"][li]
            s0, s1, ws = snap(words, audio, a, b)
            # Captions: only words the cut actually contains; a line's 4th field replaces Whisper's text (aligned to its word times).
            ws = [w for w in ws if w["s"] < s1 - 0.05 and w["e"] > s0 + 0.05]
            dev_text = " ".join(w["w"] for w in ws)
            if not override and dev_text in roman_cache:
                ws = [{**w, "w": r} for w, r in zip(ws, roman_cache[dev_text])]
            if override:
                ws = align(override[0].split(), ws)
            clip = fade(audio[int(s0 * SR): int(s1 * SR)])
            pieces += [clip, np.zeros(int(LINE_GAP * SR), np.float32)]
            starts[li] = t
            lines_out.append({"who": who, "start": round(t, 3), "end": round(t + len(clip) / SR, 3)})
            caps += [{"w": fix(w["w"]), "s": round(t + w["s"] - s0, 3), "e": round(t + w["e"] - s0, 3), "who": who, "line": len(lines_out) - 1} for w in ws if not override] + \
                    [{"w": w["w"], "s": round(t + w["s"] - s0, 3), "e": round(t + w["e"] - s0, 3), "who": who, "line": len(lines_out) - 1} for w in ws if override]
            text = " ".join(fix(w["w"]) for w in ws)
            clips.append((clip, dev_text if lang == "hi" else text))
            print(f"  {who:3} {s0:8.2f}-{s1:8.2f} ({s1 - s0:4.1f}s)  {text}")
            t += len(clip) / SR + LINE_GAP
        end_scene = t - LINE_GAP
        first = sc["lines"][keep[0]]
        still = f"s{n}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(sc.get("stillAt", first[1] + 1.2)), "-i", str(src), "-frames:v", "1",
                        "-vf", "scale=1280:-2", "-q:v", "3", str(out / still)], check=True)
        card = dict(sc["card"]) if sc.get("card") else None
        if card:
            line = card.pop("line", 0)
            card["at"] = round(starts.get(line, start_scene) + card.get("at", 0), 2)
        cues = [{"at": round(starts.get(li, start_scene) + off, 2), "react": r, "comment": c} for li, off, r, c in sc.get("cues", []) if li in starts]
        scenes.append({"id": sc["id"], "start": round(start_scene, 3), "end": round(end_scene, 3), "still": still,
                       "card": card, "react": sc.get("react"), "comment": sc.get("comment"), "context": sc.get("context"), "topic": sc.get("topic"), "cues": cues})
        print(f"── {sc['id']}: {start_scene:.1f}-{end_scene:.1f}s")
        gap = (SCENE_GAP - 0.1 if short else SCENE_GAP_LONG) - LINE_GAP
        pad = np.zeros(int(gap * SR), np.float32)
        if not short and n + 1 < len(picked):
            # Whoosh swells while the next scene's still wipes in (PodcastSummary Still), so the change is felt, not a jump.
            w = whoosh()[: len(pad)]
            fx.append((int((t + gap) * SR) - len(w), w))
        pieces.append(pad)
        t += gap

    end_at = t + 0.2
    total = end_at + (2.6 if short else END_CARD)
    mix = np.concatenate(pieces)
    mix = np.pad(mix, (0, max(0, int(total * SR) - len(mix))))
    # Mouth opening per frame: loudness of the voice in that frame, 0 (closed) … 1 (wide). Whooshes go in after.
    hop = SR // FPS
    mouth = []
    for f in range(int(total * FPS)):
        d = db(mix[f * hop: (f + 1) * hop])
        mouth.append(round(float(np.clip((d + 42) / 26, 0, 1)), 2))
    for at, w in fx:
        mix[at: at + len(w)] += w[: len(mix) - at]
    sf.write(out / "audio.wav", mix, SR)
    manifest = {"slug": slug, "cast": script.get("cast"), "stillLabel": script.get("stillLabel", "📸 REAL MOMENT"),
                "host": script.get("host"), "handle": script.get("handle"), "intro": intro, "listener": script.get("listener"),
                "duration": round(total, 2), "endAt": round(end_at, 2), "title": script["title"] if not short else script.get("shortTitle", script["title"]),
                "subtitle": script["subtitle"] if not short else script.get("shortSubtitle", script["subtitle"]),
                "endNote": script["endNote"], "scenes": scenes, "lines": lines_out, "words": caps, "mouth": mouth}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False))
    print(f"✅ {out}/manifest.json  {total:.1f}s, {len(lines_out)} lines")

    if check:
        tmp = out / "check"
        tmp.mkdir(exist_ok=True)
        items = []
        for i, (clip, text) in enumerate(clips):
            p = tmp / f"{i:02}.wav"
            sf.write(p, clip, SR)
            items.append({"path": str(p), "text": text})
        res = subprocess.run([str(PROJECT / "tools/whisper-mlx/.venv/bin/python"), str(PROJECT / "tools/take_check.py")],
                             input=json.dumps({"lang": script.get("checkLang", lang), "items": items}), capture_output=True, text=True, check=True)
        for r, it in zip(json.loads(res.stdout), items):
            print(f"{'✅' if r['wer'] < 0.2 else '⚠️ '} wer {r['wer']:.2f}  heard: {r['heard'].strip()}")
        subprocess.run(["rm", "-rf", str(tmp)])


if __name__ == "__main__":
    main()
