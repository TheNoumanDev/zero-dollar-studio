# snipshorts

A Claude Code skill that turns a long podcast, interview or talk into vertical Shorts, Reels and TikToks. It's a free, open-source alternative to OpusClip: no credits, no watermark, and the tools run on your machine.

Give it a YouTube link or a local video. Claude picks the best 20-45 s moments, the tools jump-cut the dead air and keep the active speaker in frame (or split the screen for two people), and Remotion adds punch zooms, word-synced keyword captions, motion graphics, a cold-open rewind and sound effects. You get finished MP4s and, if you want, a ready-to-post folder with titles, captions and tags.

Made by [TheNoumanDev](https://github.com/TheNoumanDev).

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install snipshorts@zero-dollar-studio
```

snipshorts is an add-on to [make-video](../make-video). If you don't have it yet:

```
/plugin install make-video@zero-dollar-studio
```

Then ask Claude Code: *"make Shorts from this podcast: <link>"*. It asks how many clips you want. The first time, it sets up a make-video project (if you have none) and adds the snipshorts tools to it.

## What you need

- A make-video project (macOS on Apple Silicon, Node 20+, Homebrew, ffmpeg; see [make-video](../make-video))
- [Claude Code](https://claude.com/claude-code), logged in. Moment picking, the edit plan and the post copy call the `claude` CLI on your PATH, so they use your Claude subscription. No API key.
- About 1 GB of free disk space for the extra Python packages and the Whisper model, plus room for the source videos

## What it does

| Step | Tool | License |
|---|---|---|
| Download | [yt-dlp](https://github.com/yt-dlp/yt-dlp): full episode at 720p, then each moment again in 1080p | Unlicense |
| Transcript | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Whisper small, CPU), or the platform's own auto-captions | MIT |
| Moments, edit plan, post copy | Claude Code (`claude -p`, your subscription) | |
| Speaker tracking | [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) face detector on [OpenCV](https://opencv.org): faces, shot cuts, active speaker by mouth motion. No face recognition. | MIT / Apache-2.0 |
| Name tags (optional) | Clothing colour under each face, matched to people you label once | |
| Video | [Remotion](https://www.remotion.dev) (React): crop, zooms, captions, graphics, rewind | **Remotion license**, see below |
| SFX | Synthesised with numpy (whoosh, pop, boom, ding, rewind); no samples | |
| Master | ffmpeg loudnorm to -14 LUFS | LGPL/GPL |

One command runs it: `tools/podcast/make-shorts.sh podcasts/<slug> 5`.

## Licenses and responsibility

- **You are responsible for having the rights to clip the source.** Use your own show, get the creator's permission, or make sure your use is fair use (or fair dealing) where you live. Reused footage can get copyright claims or strikes, and TV footage is matched aggressively.
- This plugin's code is MIT. **Remotion is not open source**: it's free for individuals and companies of up to 3 people, and larger companies need a [Remotion Company License](https://www.remotion.dev/license). Remotion is installed from npm; none of its code is included here.
- Third-party tools and models keep their own licenses. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).
- Nothing is uploaded or posted. `post.py` only writes a local folder you post from yourself.
- No videos, images, audio or model weights are included. `tools/podcast/setup.sh` installs the packages and downloads the face detector from its official source. The Whisper model downloads on first use.

## Author

Made by **[TheNoumanDev](https://github.com/TheNoumanDev)** (Nouman), who runs the [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA) YouTube channel. Issues and PRs are welcome on [zero-dollar-studio](https://github.com/TheNoumanDev/zero-dollar-studio).
