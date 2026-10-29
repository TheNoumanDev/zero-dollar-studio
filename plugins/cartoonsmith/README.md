# cartoonsmith

A Claude Code skill for voiced cartoon episodes with recurring characters. You write a series bible (characters, voices, sets) and draw or generate character sheets; it turns each character into a talking rig (a bust with 8 lip-sync mouth shapes and 4 expressions), then makes episodes from a multi-character script: voice, lip sync, captions, music, Remotion render and an automatic QA gate. Everything runs locally and costs $0.

It's an add-on to [make-video](../make-video): it reuses that project's voice, captions, music, render and QA tools.

Made by [TheNoumanDev](https://github.com/TheNoumanDev), who runs [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA).

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install make-video@zero-dollar-studio
/plugin install cartoonsmith@zero-dollar-studio
```

Then ask Claude Code: *"make a cartoon episode where two shopkeepers argue about the shop cat"*. The first time, it sets up a make-video project (if you don't have one), adds cartoonsmith's files, and renders a 13-second example with stand-in characters drawn in code.

## What you need

- Everything make-video needs (macOS on Apple Silicon, Node 20+, Homebrew, about 8 GB free)
- Rosetta 2 for Rhubarb Lip Sync on Apple Silicon (`softwareupdate --install-rosetta`)
- Character sheets you have the rights to use: your own drawings, or an image tool whose terms let you use the output (for example Gemini's free tier). The skill tells you exactly what to ask for.
- Optional: about 5 GB more for the Indic Parler-TTS voice engine (Hindi and other Indian languages)

## What it does

| Step | Tool | License |
|---|---|---|
| Series bible + script | Claude Code, with shot direction per line (sets, two-shots, close-ups, poses, reactions) | |
| Sheets → cut-outs | `split_sheet.py` (OpenCV), optional AI matte with [rembg](https://github.com/danielgatis/rembg) + isnet-general-use | Apache-2.0 / MIT (models Apache-2.0) |
| Upscale (optional) | [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) ncnn | BSD-3-Clause |
| Talking rig | `viseme_align.py`: aligns every face, finds the mouth box | |
| Voice | [Chatterbox](https://github.com/resemble-ai/chatterbox) (make-video), or [Indic Parler-TTS](https://huggingface.co/ai4bharat/indic-parler-tts) + [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) (optional) | MIT · Apache-2.0 · MIT/Apache-2.0 |
| Lip sync | [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) | MIT |
| Captions, music, QA | make-video's tools | see make-video |
| Video | [Remotion](https://www.remotion.dev): a data-driven `Episode` composition | **Remotion license**, see below |

One command runs the lot: `tools/make-episode.sh stories/<slug> <CompositionId>`.

## Licenses and responsibility

- This plugin's code is MIT. **Remotion is not open source**: it's free for individuals and companies of up to 3 people, and larger companies need a [Remotion Company License](https://www.remotion.dev/license).
- Third-party tools and models keep their own licenses. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md). Indic Parler-TTS is gated: you accept its terms on Hugging Face yourself.
- **Use only characters and art you have the rights to.** No character art, sets, voices or model weights are included; the example cast is drawn by a script at setup time.
- **Only clone voices you have permission to use.** Never macOS `say` voices (their licence is non-commercial). Label AI voices where the platform asks (YouTube: "altered or synthetic content").

## Coming next

Body motion from the A-pose sheet (AnimatedDrawings + MediaPipe Pose), and AI action shots placed into your sets.

## Author

Made by **[TheNoumanDev](https://github.com/TheNoumanDev)** (Nouman), who runs the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel. Issues and PRs are welcome on [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio).
