# Lessons learned

Problems found while editing raw talking-head footage with this pipeline, and their fixes. Add your own to `LESSONS.md` in your video project (newest first), so the next reel goes faster.

## Transcripts

- **Whisper hides the mistakes you want to cut.** By default it writes the clean sentence and skips "um"s and abandoned starts. `transcribe.py --verbatim` primes it with a disfluent example; on a test with planted retakes it then wrote "Umm", "Ah", "Hmm" and both halves of "they, but they're".
- **Broken-off takes can get a full stop** ("And getting stuck is where."). Don't trust punctuation to tell a finished take from an abandoned one; compare lengths across takes.
- **Warm-up words stick to the first line.** "Okay, [pause] so the best way…" came through as one line. A lead-in word before a 0.4 s pause is now trimmed.
- **Hyphenated words come apart** ("to" + "-do"). cut.py glues them back for the captions.

## Takes

- **The last take is usually the best, not always.** Speakers often nail delivery on take 1 and then over-think it. Offer the alternative when takes differ in wording, not only in completeness.
- **Two different lines can open alike** ("You need to practise. You need to rest."). The opening rule needs five similar words, but read the ✗ reasons anyway.

## Footage

- **iPhone HDR video looks flat** after the cut (HLG to SDR without tone mapping). Record in SDR, or add a `grade`. ingest.py warns.
- Phone files carry a rotation flag; ingest.py applies it before anything reads the frame size.
