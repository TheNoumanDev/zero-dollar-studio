# Lessons learned

Real problems from clipping podcasts, interviews and TV shows with this pipeline, and their fixes. Add your own to `LESSONS.md` in your video project (newest first) after every batch, so the next one goes faster.

## Picking moments

- **The ending is everything.** A clip that "ended abruptly" had stopped on the setup ("So I was cool. I was cool."); the payoff came 10-40 s later. The moment prompt now allows splicing: setup → turn → payoff, middle skipped.
- **Teasers can flip the meaning.** "maybe I'm not made for this" came from "it's NOT heartbreaking where I'm like maybe I'm not made for this". The teaser prompt now forbids fragments that say the opposite out of context. Still read every teaser.
- **Pickers end on fillers.** One clip ended on "right and". Print the first and last words of every moment before rendering.
- **Moments, not chapters.** 1-5 minute "chapter" clips with intros and subscribe asks were rejected. Shorts need a 20-45 s moment plus motion editing.
- **Some bits are all cutaways.** If the person speaking is never on camera, drop the moment.
- For long episodes, a ranked list read off the full transcript lets the user pick their top N. Then write `moments.json` by hand (snap with `moments.find_phrase`).

## Transcripts and captions

- **Platform auto-captions are often enough.** YouTube's auto-captions gave usable word timings for a 68 min episode instantly, in English and in Hindi, via `vtt_words.py`. Strip `>>` speaker marks and `[music]`-style tags (the script does).
- **Non-English sources:** use the platform's auto-captions via `vtt_words.py`, set `"language"` in source.json, and `romanize.py` turns the words into Latin script (the caption font has no other glyphs). Give it the names in `people` so it spells them right.
- **Recognisers mishear key words** ("called" for "cool", names). plan.py returns caption `fixes`; the original word stays in `asr`.
- **Captions drop words** ("tell me about a favorite [memory]"). Check list items and payoffs are complete before rendering.
- **Jump cuts can eat words** the transcript missed (a name said after a dramatic pause, a shouting match). Use `"jumpcut": false` for TV or already-edited footage.
- Whisper loops on long noisy audio. Re-transcribe short windows around the chosen moments instead of the whole file.

## Framing and tracking

- **Mouth motion can't pick the speaker in a wide two-shot**: the more animated person always wins. Two-shots use the split layout instead of guessing.
- **Cut detection needs three signals.** Colour histograms miss close-up ↔ two-shot cuts on the same set; a dark studio with host and guest dressed alike also fooled the face-size check. prepare.py cuts on a histogram jump, a whole-frame grey change (> 4× the recent median, so slow zooms in re-uploads don't count) or a face-size change held for 3 samples.
- **False faces make split-screen flicker.** A hand, a mic, an edge artefact or a face sticker read as a second face. Splits now need two faces scoring ≥ 0.85, of similar size, for at least 0.8 s. When one slips through, change that shot to single framing in `clip.json` (`crop` keys and `shots[].mode`).
- **A masked or turned-away face isn't detected.** Re-aim `cx`/`cy` in `clip.json` by hand.
- 720p sources look soft in 9:16 (a 405×720 crop stretched 2.7×). Always let prepare.py fetch each moment in 1080p, and check the "WxH" it prints.

## Name tags

- **Never use face recognition.** Clothing colour under the face (an HSV histogram) named every shot correctly in a 3-person podcast from 3 labelled shots.
- **It breaks on similar clothes** (orange vs pink shirts, two guests in black taking turns in one chair). Add decoy references for crew and audience, or fix `who` by episode time.
- **Check the rendered frames, not just the people sheet.** Fast cuts inside one detected shot put tags on the wrong person.
- **Don't guess who is who from context.** Two judges got swapped that way. Ask the user, with one labelled still per person.
- Tags leave at their shot's cut and wait for the rewind label and any kinetic slam.

## Layout

- Design sizes at 1080×1920 for a phone: kinetic 250, stat 320, callout 125, quote 118, hook 130 design px. 1× end screens were unreadable; they use 1.7×.
- A kinetic slam over a close-up covered the eyes and repeated the captions. In close-ups it now **replaces** the captions; in split shots it sits on the divider.
- Emphasised caption words get side margin that grows with word length, or the bump makes them touch their neighbours. Long slam words shrink to fit.
- A top graphic that crossed a cut landed on a wide shot and covered a face. Keep top graphics inside one close-up shot.
- A contact sheet caught a quote card mid-fade and it looked empty. Grab a frame 1 s later before calling it a bug.
- Some sources bake in their own pop-ups. Nothing to do but pick another moment if it matters.

## Tools and rendering

- A 1080p section fetch hung for 77 min (ffmpeg stuck, ignored SIGTERM). `kill -9` on that ffmpeg made prepare.py retry and finish.
- Single-pass loudnorm left some clips at -15.6 LUFS. Measure the finished files and adjust with `volume` if needed.
- Prompt templates use `str.format`, so literal braces must be doubled; test templates by formatting them with dummy fields.
- PyAV (faster-whisper) and OpenCV each bundle FFmpeg and print a warning when loaded in one process. The tools never import both.
- Broadcaster footage is aggressively Content-ID'd. Warn the user before posting TV clips.
