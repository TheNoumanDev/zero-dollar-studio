# Lessons learned

Problems found while editing raw talking-head footage with this pipeline, and their fixes. Add your own to `LESSONS.md` in your video project (newest first), so the next reel goes faster.

## Transcripts

- **Whisper hides the mistakes you want to cut.** By default it writes the clean sentence and skips "um"s and abandoned starts. `transcribe.py --verbatim` primes it with a disfluent example; on a test with planted retakes it then wrote "Umm", "Ah", "Hmm" and both halves of "they, but they're".
- **Broken-off takes can get a full stop** ("And getting stuck is where."). Don't trust punctuation to tell a finished take from an abandoned one; compare lengths across takes.
- **Warm-up words stick to the first line.** "Okay, [pause] so the best way…" came through as one line. A lead-in word before a 0.4 s pause is now trimmed.
- **Whisper hides pauses inside words.** On a real phone recording "go" lasted 2.2 s and "own" 1 s: the pauses before them. With no visible gaps, a restart said after a pause looked like one run-on line. audio.py trims long words to their voiced part.
- **Whisper ends words early** (median 0.14 s, 1 word in 10 by 0.6 s+), so a cut after "no editor." came out "no edit". audio.py moves each word end out to where the voice stops (at most 0.35 s, never into the next word).
- **A bilingual take loses a language silently.** Transcribed as English, the first 26 s (Hindi) of a recording simply had no words. takes.py now flags speech with no transcript.
- **Lists look like false starts.** "don't forget to subscribe, don't forget to click the follow button" was cut as a restart. A comma-ended fragment now counts only when the retry repeats all of it.
- **Hyphenated words come apart** ("to" + "-do"). cut.py glues them back for the captions.

- **Whisper `small` can't do Hinglish.** Language `hi` gave garbled Devanagari; `en` silently translated ("na editing app" → "no dating app"). `large-v3-turbo` + `hi` + conditioning on previous text + a Roman Hinglish prompt fixed it, but only reliably when the prompt was the speaker's own script: a generic Hinglish prompt still translated half the lines, and the same settings flipped between Roman and English on tiny input changes (wav vs mp4, VAD on/off).
- **Without conditioning, Roman Hinglish drifts to Devanagari** after ~30 s: the prompt only steers the first window.
- **Whisper invents outros over trailing silence**: "Thank you for watching", "Don't forget to subscribe", "Bye!", once "Thank you" ×5 in one second. takes.py drops lines with no voice under them or after the last speech.

## Takes

- **The last take is usually the best, not always.** Speakers often nail delivery on take 1 and then over-think it. Offer the alternative when takes differ in wording, not only in completeness.
- **Two different lines can open alike** ("You need to practise. You need to rest."). The opening rule needs five similar words, but read the ✗ reasons anyway.

## Script review

- **People read their notes aloud.** A test take included its own stage directions ("pause for a second, then do it again"). They're spoken content to the tools, so the review step has to drop them.

## Sound

- **One-pass loudnorm misses -14 LUFS on quiet voices.** A browser-recorded voice mixed with SFX pops came out at -16.4: the true-peak ceiling stopped it first. make-reel.sh now repeats exact gain + a limiter on a WAV until it's within 0.3 LU (-14.2 on the same reel).

## Footage

- **iPhone HDR video looks flat** after the cut (HLG to SDR without tone mapping). Record in SDR, or add a `grade`. ingest.py warns.
- Phone files carry a rotation flag; ingest.py applies it before anything reads the frame size.
