# Lessons learned

Real problems from making animated podcast summaries with this pipeline, and their fixes. Add your own to `LESSONS.md` in your video project (newest first) after every run.

## Faces

- **AI talking faces beat every cheaper option.** In order of what viewers said: a jaw-drop cut-out puppet "looks like his mouth is broken"; swapping in the person's own mouth from nearby frames (photomouths.py) was better but "still looks bad"; JoyVASA + LivePortrait driven by their real voice looked natural. Drawn mascots work too, but people preferred real faces.
- **`AIFACE_CALM=0.3`.** At the default 1.0, real photos went bug-eyed. 0.3 scales eye/brow/cheek motion down and keeps full lip motion.
- **Pick the base still with care.** It should be the person talking in their own close-up (not the other camera), eyes open, hands away from the chin. Check photomouths' `sheet.jpg`.
- **Black shirt on a black set.** rembg on a tight close-up loses the shirt. A medium shot with the shirt in the box keeps it.
- **Who's who from frames, never from the topic.** The person you'd guess from the subject is often wrong, and a co-host asks most of the questions. Wide shots don't settle it; close-ups and the conversation's logic do. Pitch can't split two male voices at 110-130 Hz.
- **Mascots from this episode's frames**, not from memory: hairline, parting, glasses, facial hair, outfit colour. Receding hair needs skin at the temples or it reads as a cap; long hair must cover the ears.
- **AI faces are slow.** Budget ~22 s of compute per second of speech per person and run aiface.py in the background. After a re-cut, `aiface.py incr` reuses unchanged lines.

## Cuts and captions

- **Captions must match the audio word for word.** A tidied override ("He was like…" for "I was like…", dropped fillers) reads as out of sync. Overrides are aligned to Whisper's word times, so the lit word follows the voice through pauses (median 0.01 s off).
- **Cuts must make sense on their own.** "So I joined him" after a cut: joined whom? Read every line's first and last words; a line starting with So/But/Because/Then or a pronoun needs its lead-in as its own line.
- **Don't end on a list or a setup.** "you coach people at Apple, SpaceX, Google…" cut straight to the next scene felt chopped. Read 30 s past every out point and finish the thought.
- **Out point = end of the last word.** Its start drops the word.
- **Dead air inside a line.** Whisper stretches the next word over a 2 s pause, so snapping can't start the second half on it. Fix that word's start in words.json, then split the line on the pause.
- **A one-word interjection over the other speaker** is misheard on `--check` (WER 1.0): drop it.
- **Rambling host questions:** cut them into two lines on a pause (the gap reads as a cut), and put the skipped part in the scene's `context`.
- **Whisper writes numbers its own way** ("910" for "nine, ten"): a ⚠️ on `--check` isn't always a bad cut. Read what it heard.
- **Hinglish:** YouTube's `hi-orig` captions plus build.py's romanize worked without overrides. Use `fix` for slips.

## Layout

- **Every scene gets a `topic`.** Viewers wanted the main point as a big title at the top for the whole scene; context strips sit under it.
- **Stat cards:** `big` is one line at 150 px and overflows past ~8 characters. Keep it one short word or number; the rest goes in `label`/`sub`.
- **Scene changes:** a 0.8 s gap with a soft whoosh while the next still wipes in, instead of a hard slam.
- **Cast intro:** one big 3:4 card per person, the real photo first, then it flips to the animated version. Small circles were "too small to even show him complete".

## Thumbnails

- **Copy what wins in the niche.** One expressive real face filling half the frame, ≤ 6 words, nothing else (ProThumb). A busy thumbnail with tags, mascots and logos got 0.6% CTR; small details don't read at phone size.
- **Two-person episodes:** DuoThumb, host left and guest right, both facing in, title in the middle. Pick frames where they look at each other, not mid-word looking down.
- **Lead with the guest's fame** when the host isn't known to your audience.
- **Cut-outs:** reuse photomouths' `mouth0.png` for people on a black set. For a busy desk, crop above the table; hide straight cut edges by overlapping people or flipping the edge off-frame.

## Sources

- **yt-dlp can return video-only** at 1080p. Fetch `-f ba[ext=m4a]` separately and mux with `-c:v copy`.
- **Caption downloads 429** often. A local transcript of a 25 min episode takes about a minute with mlx Whisper and its word timings worked first time.
- **Long episodes:** transcribe it whole, read it in ~45 s chunks, then dump word timings only for the windows you pick.
- **A bare link means the summary**, not the full episode. A full re-voice of someone's whole episode is a Content ID risk; summarise instead.
