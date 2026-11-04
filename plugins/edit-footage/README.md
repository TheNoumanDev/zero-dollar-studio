# edit-footage

A Claude Code skill that edits your own raw talking-head recording into a finished vertical reel. Record on your phone or webcam, flub a line, say it again, leave the "um"s in. edit-footage keeps the best take of every line, cuts the false starts, fillers and pauses, frames your face in 9:16 and adds word-synced captions, punch zooms, motion graphics, sound effects and a loudness-normalised master. No subscription, no upload: the tools run on your machine.

Made by [TheNoumanDev](https://github.com/TheNoumanDev).

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install edit-footage@zero-dollar-studio
```

edit-footage is an add-on to [make-video](../make-video) and uses the [snipshorts](../snipshorts) render tools. If you don't have them yet:

```
/plugin install make-video@zero-dollar-studio
/plugin install snipshorts@zero-dollar-studio
```

Then ask Claude Code: *"edit my recording into a reel: ~/Movies/IMG_0042.MOV"*. It shows you the script it kept (and what it dropped, and why) before rendering anything.

## What you need

- A make-video project with the snipshorts tools (macOS on Apple Silicon, Node 20+, Homebrew, ffmpeg)
- A logged-in coding-agent CLI for the edit plan: [Claude Code](https://claude.com/claude-code) (`claude`) by default, or `SNIPSHORTS_LLM=codex`, `gemini` or a local model command
- About 650 MB for snipshorts' Python packages and the Whisper model, if you don't have them yet

## What it does

| Step | Tool | License |
|---|---|---|
| Join takes, fix rotation | ffmpeg | LGPL/GPL |
| Transcript with fillers and restarts | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Whisper small, CPU), verbatim prompt | MIT |
| Best take of each line, cut false starts and fillers | `tools/footage/takes.py`: fuzzy matching of repeated lines, no model | MIT |
| Face framing | [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) on [OpenCV](https://opencv.org) (no face recognition) | MIT / Apache-2.0 |
| Edit plan | Your agent CLI (`claude -p` by default) | |
| Video | [Remotion](https://www.remotion.dev): snipshorts' `PodcastShort` composition | **Remotion license**, see below |
| Noise removal, master | ffmpeg `afftdn`, loudnorm to -14 LUFS | LGPL/GPL |

Two commands run it: `tools/footage/make-reel.sh footage/<slug>` prints the kept script; `GO=1 tools/footage/make-reel.sh footage/<slug>` renders it.

## Licenses and responsibility

- This plugin's code is MIT. **Remotion is not open source**: it's free for individuals and companies of up to 3 people, and larger companies need a [Remotion Company License](https://www.remotion.dev/license). Remotion is installed from npm; none of its code is included here.
- Third-party tools and models keep their own licenses. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).
- Your recordings stay on your machine and out of git. Nothing is uploaded or posted.

## Author

Made by **[TheNoumanDev](https://github.com/TheNoumanDev)** (Nouman), who runs the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel. Issues and PRs are welcome on [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio).
