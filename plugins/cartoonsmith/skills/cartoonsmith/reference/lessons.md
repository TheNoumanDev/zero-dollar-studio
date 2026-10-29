# Lessons learned

Real problems from making cartoon episodes with this pipeline, and their fixes. make-video's lessons apply too. Add your own to `LESSONS.md` in your video project (newest first) after every episode.

## Rigs and lip sync

- **Swap only the mouth, never the whole face.** Whole-frame swaps made outlines and hair shimmer. The rig keeps the base face and shows the aligned face for the current mouth shape only inside a soft mask around the mouth.
- **Align on the upper face.** `viseme_align.py` aligns every face on the hair, eyes and ears (the part that doesn't change), so the head never jumps when the mouth does.
- **Phoneme cues beat loudness.** Choosing mouths from loudness looked random. Rhubarb's phoneme-timed shapes, held as hard cuts, read as speech. 70 ms crossfades between mouths showed two mouths at once.
- **Rhubarb's phonetic mode (non-English) under-opens.** On Hindi the wide-open shape was 3% of cues. The rig picks the open shapes (B/C/D) by loudness for non-English episodes.
- **Expressions cut from a sheet at low resolution look blurry** at full size. Upscale small sheets 4× before aligning.
- **Oversize the eyes and keep a clear lip window.** Small sleepy eyes and a beard over the mouth made a likeness unreadable.

## Art

- **Rigging art must be an A-pose**: arms 30-40° out with a clear gap from the torso, legs apart, nothing overlapping. Arms drawn against the body fused with the clothes, which stretched into smears when animated.
- **Flat 2D animates better than 3D-looking art.** Mesh warps bend painted shading.
- **White clothes on a white page** come out see-through. `split_sheet.py --rembg` fills the holes inside the outline; busts with no hem outline are cropped at the last row of dark ink first.
- Sheets framed differently per cell broke alignment (correlation 0.37). Ask for identical framing and regenerate rather than fixing by hand.

## Voices

- **Indic Parler-TTS** (Apache-2.0, gated) beat Kokoro (robotic) and a Chatterbox clone of a synthetic voice (it copied the artifacts as hiss) for Hindi. `voice_parler.py` renders 3 takes, keeps the least hissy, then denoises (DeepFilterNet) and low-passes at 8 kHz.
- Some Parler speakers are about 10 dB breathier than others; listen before casting. Child voices are the weakest (no child speakers).
- Without a reference clip every Chatterbox character has the same voice. Give each its own consenting reference, or use Parler speakers.
- **Never use macOS `say` voices** in published work: Apple's licence is non-commercial.
- Hindi: write English words in Devanagari (Latin words made the model ramble), and put Roman Hinglish in `caption`. Whisper scores accented TTS badly, so judge by ear.

## Editing

- **Hold the shot through the pause.** A shot that ended with its line left black frames until the next line; each shot now runs until the next one starts.
- **Cut just before the line** (~120 ms) so the new shot has settled when the first syllable lands.
- **Change the picture every line.** Auto framing alternates two-shots and close-ups; QA's variety check fails a same-looking run over 5 s.
- **Reactions are the cheap laugh.** A listener's shocked face on the punchline (`react`) costs nothing and reads instantly.
- With many dialogue-driven cuts in a long episode, the music can't put every cut on a beat (worst was 134 ms over 15 cuts). Accept it for episodes, or score music per scene.
- In zsh, `for x in "a b c"` breaks over rows. Use `while read -r a b c; do …; done <<EOF`.
