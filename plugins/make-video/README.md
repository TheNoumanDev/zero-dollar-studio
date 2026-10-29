# make-video

A Claude Code skill that turns a one-line idea into a finished, checked MP4: script, voice, word-synced captions, music and SFX, Remotion render, loudness master and an automatic QA gate. Everything runs locally and costs $0: no API keys, no credits, no watermark.

Made by [TheNoumanDev](https://github.com/TheNoumanDev). It's the pipeline behind [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA).

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install make-video@zero-dollar-studio
```

Then ask Claude Code: *"make a 30-second Short explaining how DNS works"*. The first time, it sets up a video project and downloads the models.

## What you need

- macOS on Apple Silicon (Chatterbox and the take checker run on the Apple GPU)
- Node 20+, [Homebrew](https://brew.sh) (setup installs ffmpeg, uv and FluidSynth)
- About 8 GB of free disk space (about 6 GB of models)

## What it does

| Step | Tool | License |
|---|---|---|
| Script | Claude Code, with a length budget, an explainer template and a sourced-claims check | |
| Voice | [Chatterbox](https://github.com/resemble-ai/chatterbox) (built-in voice, or a clone of your own) | MIT |
| Take check | [Whisper](https://github.com/openai/whisper) large-v3-turbo on MLX: re-records lines it can't hear clearly | MIT |
| Captions | Whisper small.en via `@remotion/whisper-webgpu`, spelling from your script | Remotion license |
| Music + SFX | MIDI written as code → [FluidSynth](https://github.com/FluidSynth/fluidsynth) + GeneralUser GS soundfont | LGPL-2.1 (external binary) / soundfont license |
| Video | [Remotion](https://www.remotion.dev) (React) | **Remotion license**, see below |
| QA | ffmpeg + OpenCV: loudness, caption accuracy, beat sync, frozen and look-alike stretches | |

One command runs the lot: `tools/make-story.sh stories/<slug> <CompositionId>`.

## Licenses and responsibility

- This plugin's code is MIT. **Remotion is not open source**: it's free for individuals and companies of up to 3 people, and larger companies need a [Remotion Company License](https://www.remotion.dev/license). Remotion is installed from npm; none of its code is included here.
- Third-party tools and models keep their own licenses. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).
- **Only clone your own voice, or one you have permission to use.** Chatterbox adds an inaudible watermark to everything it makes; leave it in. Label AI voices where the platform asks (YouTube: "altered or synthetic content").
- No voice samples, model weights or soundfonts are included; `tools/setup.sh` downloads the models from their official sources.

## Coming next

v0.2 adds an optional AI talking face (JoyVASA + LivePortrait, without the non-commercial InsightFace models).

## Author

Made by **[TheNoumanDev](https://github.com/TheNoumanDev)** (Nouman), who runs the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel, where every video, including the AI host, is made with this skill. Issues and PRs are welcome on [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio).
