# Lessons learned

Real problems from making videos with this pipeline, and their fixes. Add your own to `LESSONS.md` in your video project (newest first) after every video, so the next one goes faster.

## Voice (Chatterbox)

- **Hiss under the voice is noticed.** Never add vinyl crackle or hiss to music beds. If a cloned voice comes out hissy, run it through a denoiser such as DeepFilterNet (MIT/Apache) and add a 9.5 kHz low-pass.
- **Slower is clearer.** `"pace": "slow"` on every line plus 0.4 s pauses turned a 26 s Short into a 31 s one, and nobody complains that a Short is too clear.
- **Clone from a clean cut.** 10-15 s from a 60-90 s voice note, high-pass + loudnorm −18. A clone of a synthetic or noisy voice copies its artifacts.
- **Names get misheard.** Spell names phonetically in the script and put the real spelling in `caption`.
- **Every voice change means new downstream work** (captions; an AI face if you use one). Fix the script before voicing.
- **Non-English voices** need the multilingual model (`"language": "hi"` etc. in script.json). Write English tech words in the target script (Devanagari for Hindi). Latin words mixed into Hindi made the model ramble. Budget about 45% more time than the English script, and judge by ear, because Whisper scores accented TTS badly.
- **The voice cache** (hash of text + voice settings) turned a 2 min 16 s regeneration into 33-52 s for one-line edits.

## Captions

- Caption pages must not cross a sentence end or a pause over 300 ms ("update now. Follow" read badly).
- Two-line captions on 16:9 should stay ≤ 58 px, from y ≈ 860, above the player's control bar.
- WER treats number words as digits ("ten" = "10"). If a line's `caption` differs from what's spoken ("five point six" vs "5.6"), a WER "FIX" is a false alarm: listen instead.

## Layout and motion

- **Frame 0 must be finished.** Spring-in entrances left the first frame (often the thumbnail) empty. Offset blink timers so frame 0 never catches closed eyes.
- **Look-alike beats fail QA's variety check.** Alternate a gentle zoom and the glow side per beat, and add a slow push-in.
- **A static follow card fails the frozen check.** Give it a little motion.
- Text sized for 0.5× preview stills was too small on a phone: chips ≥ 28 px, body ≥ 54 px at 1080 wide.
- Overlapping purple and orange glows blend into brown mud. Use one glow colour and one idea per image, and look at it at full size *and* phone size.
- Lighting goes *behind* characters, and exits fade out as well as move.
- A 9:16 cut of a 16:9 painting sees only ~600 px of it, so give each camera key its own vertical focus and a softer zoom.

## Rendering and tooling

- A render hung for 23 hours at 0% CPU. Always pass `--timeout=180000 --concurrency=2`, and never run two renders (or two GPU jobs) at once.
- `--log=error` hid a one-off browser-launch failure. Keep full logs when something fails.
- The ESLint rule `@remotion/non-pure-animation` flags any object key named `transition`. Name it `transitionLength`.
- Node 20 has no `await using`, which some Remotion docs use. Replace it with explicit load/dispose.
- Chatterbox needs `chatterbox-tts==0.1.7` and `setuptools<81` (pinned in `tools/requirements.txt`). Without the pin the watermarker is silently `None` and loading crashes.
- A first Hugging Face download (3 GB) stalled silently. Check that the `.incomplete` file is growing; if not, kill it and resume. Never run two downloaders on the same repo at once. `du` doesn't follow HF symlinks, so use `du -shL`.
- One-pass loudnorm under-shot a video with long quiet stretches to −15.5 LUFS. The two-pass master in `make-story.sh` fixes this.
- In JS code inside a Python string inside a template literal, `\s` loses its backslash. Write `\\s`.

## Process

- **Contact sheet every time.** Version 1 of the first story had tiny characters, a light overlay on top of them, and a falling character landing in the captions. One sheet of stills caught all three.
- **Fresh critic per round.** A subagent with no context, shown the stills, found 14 real issues the builder missed (floating objects, a hidden character, voice only 3-6 dB over the music).
- **Sample first.** `SAMPLE=15` renders 15 s for approval before the full render.
- Story-critical props must be big enough to read on a phone.
