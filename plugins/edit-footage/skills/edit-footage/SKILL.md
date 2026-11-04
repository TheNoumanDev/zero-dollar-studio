---
name: edit-footage
description: Turn your own raw talking-head recording (phone or webcam, several takes, flubs, "um"s and pauses) into a finished vertical reel for $0, locally. Local tools transcribe it word by word, keep the best take of every line, cut false starts, fillers and dead air, then snipshorts' Remotion composition frames your face in 9:16 and adds word-synced captions (bold, bounce or clean), punch zooms, motion graphics, SFX, noise removal and a -14 LUFS master. Use when the user asks to edit, cut or clean up their own recording, talking-head video, selfie video, vlog take or raw footage into a Short, Reel or TikTok. An add-on to a make-video project with the snipshorts tools; runs on macOS.
license: MIT
author: TheNoumanDev (https://github.com/TheNoumanDev)
---

# edit-footage

Turns a person's own raw recording into a finished vertical reel with free, local tools. It sits on snipshorts: same transcript tool, same face framing, same `PodcastShort` composition, edit plan, SFX and master. What it adds is the editing a human would do on raw footage: **the best take of each line, with false starts, fillers and pauses gone.** The only step that calls an agent CLI is the edit plan (zooms, graphics, caption fixes), through snipshorts' `tools/podcast/llm.py` (Claude Code by default, or `SNIPSHORTS_LLM`). Project rules in `AGENTS.md` still apply.

> **Always show the kept script before rendering.** The first run stops after picking takes. Show the user the ✓/✗ script, fix what they want changed, and render only after they OK it.

## 0. Set up (once per project)

1. edit-footage needs a make-video project with the snipshorts tools. If the folder has no `tools/make-story.sh`, set one up with the **make-video** skill (its §0). If it has no `tools/podcast/`, add them with the **snipshorts** skill (its §0, steps 2-4). If either skill isn't installed, tell the user to install it: in Claude Code `/plugin install make-video@zero-dollar-studio` (or `snipshorts@…`) then `/reload-plugins`; in other agents `npx skills add TheNoumanDev/zero-dollar-studio --skill <name>`.
2. edit-footage downloads nothing beyond snipshorts (faster-whisper, OpenCV, YuNet, Whisper `small` on the first transcript, about 650 MB in all). If snipshorts isn't set up yet, show the user its download table and wait for their OK.
3. Copy this skill's `template/` folder over the project: `cp -R <skill dir>/template/. <project>/`. It only adds files (`tools/footage/`, `footage/example/`).
4. Run `tools/footage/setup.sh`. It checks the snipshorts tools are 0.2.1 or newer (`transcribe.py --verbatim`), runs `tools/podcast/setup.sh`, and keeps recordings out of git. Safe to re-run.

## 1. The recording

Put the recording in `footage/<slug>/` and write `footage/<slug>/footage.json` (copy `footage/example/footage.json`). The slug uses only letters, digits and hyphens: it becomes the Remotion composition id.

| Field | Meaning |
|---|---|
| `local` | The recording, or a list of files joined in order (phones often save one file per attempt). Relative to the project, or absolute. |
| `title`, `about` | What the video is about, one line each. Context for the edit plan. |
| `hook` | Optional hook card text for the first 2.5 s. Empty: the plan writes one. |
| `language` | `en` by default. Anything else turns on `romanize.py` (captions in Latin script). |
| `target` | `[min, max]` seconds, `[30, 75]` by default. The script printout warns outside it. |
| `captionStyle` | `bold` (default), `bounce` (playful) or `clean` (calm, sentence case). |
| `denoise` | `true` cleans hum, hiss and room noise (ffmpeg `afftdn`). On by default in the example: phone and laptop mics need it. |
| `grade` | Optional ffmpeg filter chain applied once, e.g. `eq=contrast=1.06:saturation=1.1`. |
| `split`, `screen` | `split` is off (one person to camera). `screen: false` keeps faceless shots as a plain centre crop. |
| `watermark`, `endCard` | As in snipshorts: handle text top-left; optional `{"title", "handle"}` end screen. |

**Recording tips to pass on:** light from the front, phone at eye level, landscape or portrait both work (the crop follows the face). Just say the line again when you flub it, with a short pause before: the tools keep the last full take. Saying "let me start again" or "okay" between takes is fine; those lines are dropped. Turn off iPhone HDR Video (Settings → Camera → Record Video), or colours look flat.

## 2. Make the reel

```bash
tools/footage/make-reel.sh footage/<slug>          # join → transcribe → best takes → print the script, stop
.venv/bin/python tools/footage/takes.py footage/<slug> --keep 4 --drop 7   # flip lines by number
GO=1 tools/footage/make-reel.sh footage/<slug>     # cut → plan → SFX → render → master → contact sheet
GO=1 SAMPLE=10 …                                   # first 10 s only, for a quick look
GO=1 SKIP_PLAN=1 …                                 # keep the plan, re-cut and re-render
RENDER_ONLY=1 …                                    # just re-render after a composition change
RETAKE=1 …                                         # pick takes again from scratch (drops hand edits)
GO=1 PLATFORMS="yt ig tiktok" …                    # also <slug>.yt.mp4, .ig.mp4, .tiktok.mp4
```

| Step | Tool | Output |
|---|---|---|
| Join | `tools/footage/ingest.py` (30 fps, upright, 48 kHz, `grade`) | `footage/<slug>/source.mp4` |
| Transcript | `tools/podcast/transcribe.py --verbatim` (faster-whisper, keeps "um"s and restarts) | `footage/<slug>/words.json` |
| Best takes | `tools/footage/takes.py` (+ `audio.py` timing fixes) | `footage/<slug>/takes.json`, the printed script |
| Cut + framing | `tools/footage/cut.py` (snipshorts `prepare.py`: jump cuts, `denoise`, face tracking) | `public/podcast-shorts/<slug>/source.mp4`, `clip.json` |
| Edit plan | `tools/podcast/plan.py` (agent CLI) | `public/podcast-shorts/<slug>/plan.json` |
| SFX | `tools/podcast/sfx.py` | `public/podcast-shorts/<slug>/sfx.wav` |
| Render | Remotion `PodcastShort` (folder "PodcastShorts" in Studio) | `out/reels/<slug>.mp4`, `.sheet.png` |

The reel's id is the slug; `make-reel.sh` adds it to `src/compositions/PodcastShort/clips.ts`.

## 3. How takes are picked

- **Timings first.** Whisper hides pauses inside words ("go" lasting 2.2 s is a pause plus "go") and ends words early, which clips last syllables at a cut. `tools/footage/audio.py` fixes both once from the audio's loudness (`"refined"` in words.json), so pauses and restarts show and cuts keep whole words.
- **Lines** end at `.` `?` `!` or a pause over 0.9 s.
- **Meta lines** go: "let me start again", "one more time", "cut that", "take two", and a lone "okay" / "sorry" / "wait". A warm-up "okay," or "so," before a pause is trimmed off the line.
- **False starts inside a line** go: "the best way to… the best way to learn" keeps the second try, when the repeat follows a 0.25 s hesitation or a dash, or repeats 3+ words with no punctuation between (said straight through). A comma-ended fragment counts only when the retry repeats all of it, so lists ("don't forget to subscribe, don't forget to click…") and "the more you build, the more you learn" stay.
- **Restarts across a pause**: "link in my bio, go try it out and [pause] go try it on…" cuts the abandoned tail of the first line.
- **Retakes**: lines up to three apart that open the same way (first five words ≥ 80% alike) or share 60% of their words are takes of one line. The last take that finishes its sentence and isn't much shorter than the longest wins; the others show as `retake 1/3, kept line 9`.
- **Fillers** (um, uh, erm, hmm, ah) are cut out of kept lines; pauses over 0.45 s shrink to 0.12 s (snipshorts' jump cuts, with framing alternating 1.0/1.12 so they read as edits).

**Untranscribed speech** is flagged under the script with its times: usually a part in another language than `language` (a bilingual recording), or mumbling. It is left out. For a bilingual take make one reel per language: trim the file, set `language`, delete `words.json`, rerun.

**Review the script.** It prints every line: ✓ kept (cut words dimmed in `[brackets]`), ✗ dropped with the reason, then the estimated length. Things to check: lines you read out that aren't content (notes to yourself, stage directions: drop them), asides at the end ("wow, beautiful": cut those words in `takes.json`), a better earlier take (the speaker may prefer take 1's delivery: `--keep 2 --drop 4`), two different lines that open alike and got merged, and a dropped line the story needs. For finer edits, change `keep` or `cut` (word indices into `words.json`) in `takes.json` by hand and run `takes.py … --show`. If the reel runs long, suggest which lines to drop, never cut on your own.

## 4. Verify before delivering

1. Re-transcribe the reel and read it back: `.venv/bin/python tools/podcast/transcribe.py out/reels/<slug>.mp4 /tmp/check.json` should read as the approved script, with no doubled words or clipped first syllables.
2. Look at the contact sheet `out/reels/<slug>.sheet.png`: face framed, captions off the face, hook card and graphics not colliding.
3. `.venv/bin/python tools/podcast/trackviz.py <slug> out/track.jpg 12` if the speaker moves around a lot.
4. Loudness: `ffmpeg -i out/reels/<slug>.mp4 -af ebur128 -f null -` (about -14 LUFS; make-reel.sh repeats gain + limiter until it's within 0.3 LU).
5. Watch every cut in the final 2 seconds of the reel: an ending on a breath or "so…" is the most common miss.

## 5. Deliver

Give the user the MP4 (and the platform encodes if asked), with the hook the plan used. For titles, captions and tags, snipshorts' `tools/podcast/post.py` writes a local posting folder. **Never upload or post anything** without the user's explicit approval. Standing feedback ("fewer zooms", "no emojis") goes as one line into `podcasts/STYLE.md`, which the edit plan reads; say so when you add one.

## Rules that save hours

- **One render at a time** (`--concurrency=2` is set).
- Whisper tidies speech unless told not to; `--verbatim` primes it with a disfluent example so it writes fillers and restarts. If a retake still disappears from `words.json`, rerun with `--model large-v3` (delete `words.json` first).
- Whisper sometimes ends a broken-off take with a full stop ("And getting stuck is where."). The length rule catches it: a take under 80% of its longest sibling never wins.
- `takes.json` is the source of truth after the first run: `make-reel.sh` reuses it and only `RETAKE=1` rebuilds it.
- In Claude Code, `rm` on `$VAR` paths is blocked by the safety check: write `"${VAR:?}"`.

More lessons: [reference/lessons.md](reference/lessons.md).

## Measured costs (M1 Max, 64 GB)

| Step | Time |
|---|---|
| Join + transcript, 42-77 s raw recording (faster-whisper small, CPU) | ~25-40 s |
| Best takes | instant |
| Cut + face tracking, 23-38 s reel | ~15-25 s |
| plan.py | ~40 s |
| Render 38 s at 1080×1920, master | ~2 min |

---
edit-footage is by [TheNoumanDev](https://github.com/TheNoumanDev), from [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio). Its author runs the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel.
