# zero-dollar-studio

**Make YouTube videos with Claude Code for $0.** Script, cloned voice, captions, music, animation and an AI host, all made by local, free tools and driven by Claude Code skills.

By **[TheNoumanDev](https://github.com/TheNoumanDev)**. This is the toolkit behind [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA), a channel where every video, including the host, is made this way.

> 🚧 Work in progress: the guides are live, `make-video` is in early release (v0.1), and the other skills are being cleaned up.

## What's here

| Folder | What |
|---|---|
| [`guides/`](guides/) | Free PDF guides from the videos (Claude desktop cheat sheet, $0 video stack, AI avatar build, daily pipeline) |
| [`plugins/make-video`](plugins/make-video/) | Idea → script → voice → captions → music → Remotion render → QA → ready to post |
| `plugins/snipshorts` *(soon)* | A long podcast or YouTube link → vertical Shorts with captions and posting copy |
| `plugins/cartoonsmith` *(soon)* | Voiced cartoon episodes with recurring characters |

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install make-video@zero-dollar-studio
```

Then ask Claude Code for a video ("make a 30-second Short explaining how DNS works"). The first run sets up a video project and downloads about 6 GB of free models. You need macOS on Apple Silicon, Node 20+ and Homebrew.

## The free stack

Claude Code · Remotion · Chatterbox (voice clone) · Whisper (captions) · FluidSynth (music) · JoyVASA + LivePortrait (AI face, coming in make-video v0.2)

## Licenses

- Code: MIT. **Remotion has its own license**: free for individuals and companies of up to 3 people. Larger companies need a [Remotion Company License](https://www.remotion.dev/license).
- Guides (`guides/`): [CC BY 4.0](guides/LICENSE).
- Third-party models keep their own licenses. Some face-model weights are non-commercial and are never used here; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Only clone voices you have consent for. Chatterbox adds an inaudible watermark; leave it in.
