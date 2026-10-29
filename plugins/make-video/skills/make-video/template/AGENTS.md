# AGENTS.md: working in this Remotion project

Instructions for AI coding agents (Claude Code, Codex, Cursor, …) creating videos here.

- **Remotion version:** 4.0.534 (pinned exactly; keep every `remotion` / `@remotion/*` package on the same version)
- **Package manager:** npm. Add Remotion packages (and their peers, such as `@huggingface/transformers`) with `npx remotion add <pkg>` so the versions match. Plain `npm i` once broke fresh installs.
- **Python tools:** a separate Python 3.11 env in `.venv` (voice, music, QA). Set everything up with `tools/setup.sh`, which is safe to re-run.
- **Making a video end to end:** follow the `make-video` skill (from the zero-dollar-studio plugin) and add what you learn to `LESSONS.md`.
- **Remotion skills (recommended):** `npx skills add remotion-dev/skills` installs the official Remotion agent skills. Read `remotion-best-practices` before writing Remotion code.

## Project layout

```
src/
  index.ts                 registerRoot — do not change
  Root.tsx                 registers every <Composition>
  config/video.ts          resolution, fps, scene lengths (single source of truth)
  config/theme.ts          colors and fonts (Google Fonts via @remotion/google-fonts)
  lib/animation.ts         helpers: sec, progress, fadeIn, fadeOut, springIn, stagger, mix, useScale, easings
  components/              reusable visuals: AnimatedText, Background, Shape
  compositions/
    SampleIntro/           demo: 3 scenes + TransitionSeries + background music
      index.tsx            timeline (scenes, transitions, audio)
      scenes/*.tsx         one file per scene
    FridgeDrama/           voiced character story (reference for §"Voiced stories")
      data.ts              imports timeline.json + captions.json; mouthOpen(), activeLine()
      Characters.tsx       SVG characters with a shared animated Face
      Captions.tsx         3-word caption pages, active word in speaker colour
    _Template/             starter to copy for new compositions
private/                   personal reference media (photos, voice): git-ignored, never upload anywhere
stories/<slug>/            script.json (you write) → timeline.json, captions-report.json, timing.csv (generated)
tools/
  setup.sh                 one-time install + checks (Chatterbox, Whisper models, FluidSynth, soundfont)
  make-story.sh            one command: voice → captions → music/SFX → lint → render → −14 LUFS master
  voice.py                 Chatterbox TTS per line (cached by text + voice settings); Whisper-checks each take, retakes unclear ones (take_check.py)
  captions.mjs             Whisper (WebGPU) word timings snapped onto script text
  music.py                 MIDI score + FluidSynth render + numpy SFX, keyed to story events
  qa.py                    final gate: loudness, caption accuracy, beat sync, frozen/same-looking stretches
  voices/                  (optional) your own reference clips to clone character voices from
  models/  soundfonts/     downloaded weights (git-ignored)
public/                    static assets, loaded with staticFile("…")
  audio/  images/  fonts/  <slug>/ (generated story audio + captions)
out/                       renders (git-ignored)
```

## Non-negotiable Remotion rules

1. **All animation must be driven by `useCurrentFrame()`.** Never use CSS transitions or animations, `setTimeout`, `requestAnimationFrame`, or `Date.now()`, because they flicker or break when rendering. The ESLint rule `@remotion/non-pure-animation` catches most of these.
2. **Write time in seconds, not raw frames.** Use `sec(seconds, fps)` and the `lib/animation.ts` helpers with `fps` from `useVideoConfig()`, so changing the frame rate keeps the same timing.
3. **Scale sizes with `useScale()`.** Design at 1920 px wide and multiply every px value by `scale`, so other resolutions (4K, 1080×1920 vertical) keep the same proportions.
4. **Clamp interpolations** (`extrapolateLeft/Right: "clamp"`). The helpers already do this.
5. **Assets:** put files in `public/` and reference them with `staticFile("audio/x.mp3")`. Use `<Img>` from `remotion` for images, and `<Audio>` / `<Video>` from `@remotion/media`.
6. **Fonts:** load them in `config/theme.ts` with `loadFont()` at module level, and only load the weights you need.
7. **Keep `defaultProps` inline in `Root.tsx`** so Studio can save edits made in its props panel.
8. Prefer individual CSS transform properties (`translate`, `scale`, `rotate`) over `transform` strings. This makes keyframes editable in Studio.

## Creating scenes

- A scene is a component that fills the frame with `<AbsoluteFill>`. Inside a `<Sequence>` or `<TransitionSeries.Sequence>`, `useCurrentFrame()` starts at 0 at the start of the scene.
- Typical structure: `<Background />`, decorative `<Shape />`s, then a centered `<AbsoluteFill>` holding the text.
- Stagger entrances with `stagger(index, startSeconds, gapSeconds)`.

## Animating typography

- `<AnimatedText text="…" size={120} delay={0.2} />` reveals text word by word from a mask. `size` is in design px.
- For custom text motion: `const t = progress(frame, fps, start, duration)`, then `opacity: t, translate: \`0 ${mix(t, 40, 0) * scale}px\``.
- Use `FONTS.display` for headlines and `FONTS.body` for supporting text. Colors come from `COLORS`.

## Animating graphics

- `<Shape kind="circle|ring|square|pill" size x y delay spin float />` pops in, then floats and spins. `x` and `y` are percentages.
- Use `springIn()` for playful pops and `progress(..., EASE_OUT)` for clean UI motion. Use `Easing.bezier` for custom curves.

## Transitions between scenes

Use `TransitionSeries` from `@remotion/transitions` (see `SampleIntro/index.tsx`). Transitions **overlap** scenes, so total duration = sum of scenes − sum of transitions. Update the composition's duration function (for example `getSampleIntroDuration`) when you add scenes. Presentations include `fade()`, `slide({direction})`, `wipe()`, `flip()`, and `clockWipe()`. Set `premountFor={fps}` on each sequence.

## Synchronizing audio

- `<Audio src={staticFile("audio/track.mp3")} volume={…} />` from `@remotion/media`. Put audio inside a `<Sequence from={sec(2, fps)}>` (or use the `from` prop) to start it later.
- Fade audio with `interpolate(frame, [...], [...])` on `volume`. See `SampleIntro/index.tsx`.
- **Sync visuals to beats or voiceover:** list the cue times in seconds (for example `const CUES = {drop: 2.4}`), then start animations at `sec(CUES.drop, fps)`. Never hard-code frame numbers.
- `public/audio/ambient.mp3` is a placeholder track. Replace it with real music.

## Voiced stories (AI voices, captions, music)

Follow the `make-video` skill. In short: write `stories/<slug>/script.json`, build the composition from `timeline.json` / `captions.json`, then run `tools/make-story.sh stories/<slug> <CompositionId>`. Every tool is free and runs locally:

| Need | Tool | License |
|---|---|---|
| Voices + cloning | Chatterbox 0.1.7 (Resemble AI), on the Apple GPU | MIT (adds an inaudible Perth watermark) |
| Word timings | `@remotion/whisper-webgpu`, model `small.en` | Remotion license / MIT weights |
| Music | MIDI via `mido` → FluidSynth + GeneralUser GS soundfont | free for commercial music |
| SFX | synthesized in `tools/music.py` with numpy | yours |

A character with no `refVoice` uses Chatterbox's built-in voice. To clone a voice, set `refVoice` to a clean 10-30 s WAV in `tools/voices/`: **only your own voice, or someone who has agreed**. Never use macOS `say` voices as references in published work (Apple's licence is non-commercial). Leave Chatterbox's inaudible watermark in.

## Creating a new composition

1. Copy `src/compositions/_Template/` to `src/compositions/MyVideo/` and rename the component.
2. Register it in `src/Root.tsx`:
   ```tsx
   <Composition id="MyVideo" component={MyVideo}
     width={VIDEO.width} height={VIDEO.height} fps={VIDEO.fps}
     durationInFrames={secondsToFrames(10)}
     defaultProps={{ title: "Hello" }} />
   ```
   Composition IDs may only contain letters, numbers, and `-`.
3. For a different format, pass explicit values (for example `width={1080} height={1920}` for vertical). `useScale()` adapts the layout.

## Changing resolution, frame rate, or duration

Edit `src/config/video.ts`: `VIDEO.width/height/fps` and `SAMPLE_INTRO_TIMING` (seconds). Nothing else needs to change. One-off render overrides: `--scale=2` (for example 4K from 1080p) or `--frames=0-89` (partial render).

## Previewing and rendering

```bash
npm run dev                                   # Remotion Studio at http://localhost:3000
npm run render                                # out/SampleIntro.mp4 (H.264, yuv420p)
npx remotion render MyVideo out/MyVideo.mp4   # any composition
npx remotion still SampleIntro out/f.png --frame=60
npx remotion compositions                     # list composition IDs
npm run lint                                  # ESLint + TypeScript; run before finishing
```

**Verify your work:** after changes, run `npm run lint`, then render stills at key frames (`npx remotion still … --frame=N --scale=0.5`) and look at them before rendering the full MP4.

## Network note: if remotion.media is blocked

On some networks `remotion.media` (Remotion's asset host) can't be reached. Two workarounds are in place:
- **Rendering browser:** `remotion.config.ts` falls back to the installed Google Chrome. Run `npx remotion browser ensure` to retry the download; when it succeeds, the fallback turns off automatically.
- **Whisper models:** `tools/setup.sh` mirrors them from Hugging Face into `tools/models/` (the Transformers.js cache layout), and `tools/captions.mjs` reads them from there.

## Docs

- https://www.remotion.dev/docs/ (append `.md` to any docs URL for raw markdown)
- https://www.remotion.dev/docs/ai/skills
