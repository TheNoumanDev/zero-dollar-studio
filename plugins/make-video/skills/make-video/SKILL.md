---
name: make-video
description: Make a finished social video (YouTube Short, Instagram Reel or YouTube long-form) for $0 with Remotion and local AI tools, from a one-line idea to a checked MP4. It covers script writing, voices (Chatterbox, with optional cloning of your own voice), word-synced captions (Whisper), music and SFX written as code (FluidSynth), rendering and an automatic QA gate. Use when the user asks to make, create or generate a video, reel, short, story or explainer, to turn a topic, script or data into a video, or to set up a free AI video pipeline. Runs locally on macOS (Apple Silicon); no API keys or credits.
license: MIT
author: TheNoumanDev (https://github.com/TheNoumanDev)
---

# make-video

Turns an idea into a rendered, checked MP4 using only free, local tools. A project made from this skill has its own rules in `AGENTS.md`, so follow them (animation purity, `useScale`, `sec()`, folder layout).

## 0. Set up a video project (once)

If the current folder has no `tools/make-story.sh`, it isn't a video project yet:

1. Ask where to create it (default `~/videos`). Copy the `template/` folder that sits next to this SKILL.md into it, including dotfiles (`cp -R <skill dir>/template/. <dest>/`), then `git init`.
2. Check the requirements: macOS on Apple Silicon, Node 20+, Homebrew, about 8 GB of free disk space. On another OS, say what won't work (Chatterbox and the take checker run on the Apple GPU) before going further.
3. Run `tools/setup.sh` **in the background**. It downloads about 6 GB (Chatterbox, Whisper, soundfont) and takes 10-20 minutes. `SKIP_TAKE_CHECK=1` skips the 1.6 GB take checker.
4. Prove it works: `tools/make-story.sh stories/fridge-drama FridgeDrama` makes the 33 s example (three vegetables argue in a fridge) in about 4 minutes. Show the user `out/FridgeDrama.mp4`.

## 1. Lock the brief (ask only if missing)

| Field | Default |
|---|---|
| Platform / format | Reel/Short: **1080×1920, 30 fps** · YouTube: **1920×1080, 30 fps** · Feed post: 1080×1350 |
| Length | Reel/Short: 15-45 s · YouTube: 3-10 min |
| Kind | **Story** (characters talk, so use §3B) or **Motion graphics** (text, data, diagrams, so use §3A) |
| Topic + single takeaway | The one thing the viewer should remember |
| Audio | Voice (Chatterbox), music + SFX (`tools/music.py`), or music only |
| Voice | Chatterbox's built-in voice, or a clone of **the user's own** recording (§3B). Never clone someone without their consent. |

## 2. Write the script before any code

**Length budget:** spoken English at Chatterbox's pace runs about **2.6 words/s**. Target duration ≈ words ÷ 2.6 + Σ pauses + outro. Check it *before* generating. (Fridge Drama: 62 words + 6.4 s pauses + 3 s outro = 33 s.)

Pacing rules for vertical short-form:
- Hook on screen and audible by **frame 0**. The first 1.5 s decides retention, and frame 0 is often the thumbnail, so never start on an empty or fading frame.
- Each line ≤ 12 words. Captions show ≤ 3 words at a time.
- Something moves **every** second.
- **Safe zone for 1080×1920:** nothing important above y=220 or below y=1540 (platform UI). Like and comment buttons run down the right edge, so put a presenter bottom-left.
- End on a payoff or punchline, then a 2-3 s call-to-action card.

**Explainer template** ("how it works" and dev-tip reels, 45-60 s, 120-160 words):
1. **Hook** (≤ 3 s): a surprising *true* fact or result.
2. **"Here's how it actually works"**: one line that opens the explanation.
3. **2-4 beats**, each with **one number + one analogy** ("a video is just 30 photos a second, like a flipbook").
4. **"But here's the catch"**: the twist, gotcha or common mistake.
5. **One-line payoff**, then one clear call to action (save, share or follow).

Then **list every factual claim with a source link** under the script, mark anything you can't verify, and fix or cut it before voicing. Show the source on screen (small, bottom of the card) when a number or claim appears.

**Craft checklist** for Shorts/Reels:
- **Progress you can see.** Step-by-step videos get `<StepCard steps={[{at: 0, title: "Download it"}, …]} />` (`src/components/StepCard.tsx`): a "STEP 2/4" pill and a segmented bar.
- **Series chip.** An episode marker top-left ("PART 2") makes posts feel bingeable.
- **Show the contrast.** A before/after or "us vs them" works better as a two-column card than as speech.
- **Story beats beat lists.** "Attempt 1 failed → attempt 2 failed → what worked" holds attention better than a list of features.
- **Punchline before the CTA.** One human line, then the call to action.
- Only promise a "comment KEYWORD and I'll DM you" reward if something real (a guide, a prompt, a repo) is waiting behind it.

**Writing for TTS:**
- Don't start a line with "…": Chatterbox improvises a filler word.
- Don't start a line with a bare number word ("Two. The face" came out as "to the face"). Write "Second, …".
- Write numbers and odd names the way they're said ("five point six", "X Z"), and put the real text in the line's `caption` field.
- Round big numbers ("over 600"); TTS garbles "646" and "87,000".
- Short words in hooks blur ("This repo" was heard as "The three"). Reword until the take checker hears them right.
- Don't have several voices shout the same short word together; the mix smears it.
- Punctuation directs delivery: "?" lifts, "." lands, CAPS add emphasis.

## 3A. Motion-graphics video

1. Copy `src/compositions/_Template` → `src/compositions/<Name>`, with one component per beat type (Hook, Point, Stat, List, CTA).
2. Compute the duration from the script (sum of beats − transitions), as `getSampleIntroDuration` does.
3. Register it in `src/Root.tsx` with inline `defaultProps`.
4. Music only: write a timeline JSON with `totalMs`, `outroStartMs` and `events`, then run `tools/music.py`.

## 3B. Voiced story (characters + captions + music)

Create `stories/<slug>/script.json` (copy `stories/fridge-drama/script.json`):
- `characters`: `color`, `exaggeration` (0.3 calm → 0.9 dramatic), and optionally `refVoice`: a clean 10-30 s WAV in `tools/voices/` to clone. Without it, Chatterbox's built-in voice is used. To clone the user's voice: they record 60-90 s talking naturally in a quiet room, then cut a clean 10-15 s piece with no music or echo (`ffmpeg -ss <start> -t 12 -i note.m4a -af highpass=f=80,loudnorm=I=-18 -ar 24000 tools/voices/me.wav`).
- `lines`: `speaker`, `text`, `pauseAfter` (s), optional `event` + `eventAt: "start"` to mark story beats (door opens, hide…) that the animation and music both key off.
- Optional voice direction per line: `emotion` (calm|neutral|warm|excited|dramatic|whisper), `pace` (slow|normal|fast), `emphasis` (words spoken in CAPS and highlighted in captions), `pauseBefore` (s). `"pace": "slow"` with 0.4 s pauses makes every word clear.

Then run **one command**:

```bash
tools/make-story.sh stories/<slug> <CompositionId>     # voice → captions → music/SFX → lint → render → master → QA
SKIP_VOICE=1 tools/make-story.sh …                     # iterate on visuals only
SAMPLE=15 tools/make-story.sh …                        # render the first 15 s for approval, then stop
```

| Tool | Output |
|---|---|
| `tools/voice.py` | `public/<slug>/lines/*.wav` (cached by text + voice settings), `public/<slug>/voice.wav`, `stories/<slug>/timeline.json` (line timings, events, per-frame mouth envelopes). With the take checker installed, Whisper listens to every sentence and re-records unclear ones (`VOICE_TAKES`, default 3). |
| `tools/captions.mjs` | `public/<slug>/captions.json` (word timings from Whisper, spelling from the script), `stories/<slug>/captions-report.json` (word error rate per line) |
| `tools/music.py` | `public/<slug>/music.wav` (MIDI → FluidSynth, fitted to the cuts), `public/<slug>/sfx.wav` |
| `tools/qa.py` | `stories/<slug>/qa/report.md`: PASS / FIX / FAIL |

Build the composition from `timeline.json` / `captions.json` (see `src/compositions/FridgeDrama/data.ts`). Drive mouths with `mouthOpen()`, gaze toward the active speaker, events via `timeline.events.*`, and duration from `timeline.durationInFrames`.

**Any timing change (text or pauses) needs captions again.** Caption times are absolute, so they drift otherwise. `make-story.sh` always reruns captions.

## 4. Verify (always, before saying it's done)

`tools/make-story.sh` ends with `tools/qa.py`, which exits non-zero on FAIL. It checks the file, loudness (-14 ±1 LUFS, true peak ≤ -1), caption accuracy, cuts on the beat (≤ 120 ms), frozen stretches (≤ 3 s), visual variety (longest same-looking run ≤ 5 s), and captions that repeat on-screen text. `LAYOUT=<CompId>` also checks captions against dead zones and the face (the composition needs a `qa` prop that outlines captions `#FF00FF` and the face `#00FFFF`). Read `stories/<slug>/qa/report.md` and fix every FAIL and FIX.

Then check by eye:
1. `npm run lint`.
2. Any line in `stories/<slug>/captions-report.json` with WER > 0.2 is probably mumbled: reword and regenerate (cheap, thanks to the cache).
3. Render stills at key beats (hook, each speaker, each event, outro), join them into one contact sheet, and **look at it**:
   ```bash
   npx remotion still <Id> out/stills/f<N>.png --frame=<N> --scale=0.4
   ffmpeg -i a.png -i b.png … -filter_complex hstack=inputs=K out/stills/contact.png
   ```
   Check character size, the safe zone, overlays covering characters, leftovers behind the outro, caption sync, and text size (chips ≥ 28 px, body ≥ 54 px at 1080 wide).
4. Pull 4-5 frames from the final MP4 and look at them.
5. For anything important, ask a fresh subagent to critique the contact sheet with no context. Fresh eyes find issues the builder misses.

## 5. Deliver

Give the user the MP4, a title, a caption, 3-5 hashtags and a thumbnail frame. **Never post or upload anything without explicit approval.** Remind them to tick YouTube's "altered or synthetic content" label when a cloned voice or AI face is used.

## Rules that save hours

- **One render at a time.** Several Remotion renders at once overloaded the machine for hours. The pipeline already passes `--timeout=180000 --concurrency=2`.
- Add Remotion packages with `npx remotion add <pkg>`, never plain `npm i`, so versions stay matched.
- Loudness: dialogue −16 LUFS, music bed about −24, final master −14 (two-pass, already in `make-story.sh`). Keep the voice at least 10 dB over the music.
- Studio can only save prop edits when `defaultProps` is an inline object in `Root.tsx`.
- Write zsh loops over rows as `while read -r a b c; do …; done <<EOF`, since `for x in "a b c"` breaks.

More lessons, and how to add your own: [reference/lessons.md](reference/lessons.md).

## Measured costs (M1 Max, 64 GB)

| Step | Time |
|---|---|
| Chatterbox model load | ~20 s per run (skipped when every line is cached) |
| Voice generation | first line ~55 s (warm-up), then ~3× real time |
| Take check | ~20-30 s per sentence that needs a retake |
| Captions (Whisper small.en, WebGPU) | ~10 s for 11 lines |
| Music + SFX | 2-5 s |
| Render 1080×1920, 33 s | ~97 s (~3 s per second of video) |
| Full pipeline | ~2 min with voice cached; ~4 min from scratch |

---
make-video is by [TheNoumanDev](https://github.com/TheNoumanDev), from [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio). It's the pipeline behind the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel.
