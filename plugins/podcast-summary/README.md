# podcast-summary

A Claude Code skill that turns a podcast or interview link into an animated summary video: 2-6 minutes in 16:9, and/or a 60-second Short. The story is told in the speakers' **own voices**, as whole-sentence clips cut from the episode. On screen, each speaker's real photo is animated into a talking face by a local AI model driven by their own voice, or they appear as a code-drawn mascot. Your commentary stays text only: a big topic title per scene, stat, ranking and list cards, context lines and reaction bubbles. Real stills from the episode flash between scenes. You get a mastered video, a thumbnail and ready-to-post copy. No subscription, no upload: the tools run on your machine.

Made by [TheNoumanDev](https://github.com/TheNoumanDev).

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install podcast-summary@zero-dollar-studio
```

podcast-summary is an add-on to [make-video](../make-video) and uses the [snipshorts](../snipshorts) tools. If you don't have them yet:

```
/plugin install make-video@zero-dollar-studio
/plugin install snipshorts@zero-dollar-studio
```

Then ask Claude Code: *"make an animated summary of this podcast: <link>"*. It reads the whole transcript, picks the story and shows you the scenes before building anything.

## Two rules

- **Disclose AI-animated faces.** The talking faces are synthetic media of real people. On YouTube set *Altered or synthetic content* to **Yes**, add the AI label on Instagram/TikTok, and say it in the description. The posting kit marks every such video and reminds you.
- **Real voices only, and credit the show.** Voices are never pitch-shifted, sped up or disguised. Credit the show by name on the end card, in the description and in the pinned comment. You need the rights to use the episode: keep clips short and the summary transformative.

## What you need

- A make-video project with the snipshorts tools (macOS on Apple Silicon, Node 20+, Homebrew, ffmpeg)
- About 300 MB more for the cut-out tools, plus, for AI talking faces, about 1.4 GB of model weights and 2 GB of Python packages
- Patience for the AI face: about 20 s of compute per second of speech on an M1 Max, so it runs in the background

## What it does

| Step | Tool | License |
|---|---|---|
| Source + captions | [yt-dlp](https://github.com/yt-dlp/yt-dlp), YouTube auto-captions or local [Whisper](https://github.com/SYSTRAN/faster-whisper) | Unlicense / MIT |
| Real-voice clips, snapped to whole words and silence, Whisper-checked | `tools/summary/build.py` | MIT |
| Cut-out + real mouth shapes | [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet), [rembg](https://github.com/danielgatis/rembg) | MIT / Apache-2.0 |
| AI talking face from the real voice | [JoyVASA](https://github.com/jdh-algo/JoyVASA) + [LivePortrait](https://github.com/KwaiVGI/LivePortrait), patched so InsightFace is never loaded | MIT |
| Video | [Remotion](https://www.remotion.dev): the `PodcastSummary` composition | **Remotion license**, see below |
| Thumbnail | `DuoThumb` (host + guest) or `ProThumb` (one face, three layouts) | MIT |
| Master + posting kit | ffmpeg (-14 LUFS), snipshorts' post rules | LGPL/GPL / MIT |

## Licenses and responsibility

- This plugin's code is MIT. **Remotion is not open source**: it's free for individuals and companies of up to 3 people, and larger companies need a [Remotion Company License](https://www.remotion.dev/license). Remotion is installed from npm; none of its code is included here.
- No model weights ship with this plugin. `setup-aiface.sh` downloads JoyVASA, LivePortrait and chinese-hubert-base from their official Hugging Face pages, and never downloads InsightFace (non-commercial). See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).
- The episode, the cut-outs and the renders stay on your machine and out of git. Nothing is uploaded or posted.

## Author

Made by **[TheNoumanDev](https://github.com/TheNoumanDev)** (Nouman), who runs the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel. Issues and PRs are welcome on [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio).
