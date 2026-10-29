# zero-dollar-studio

**Make YouTube videos with Claude Code for $0.** Script, cloned voice, captions, music, animation and an AI host, all made by local, free tools and driven by Claude Code skills.

By **[TheNoumanDev](https://github.com/TheNoumanDev)**. This is the toolkit behind [@0x45.dev](https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA), a channel where every video, including the host, is made this way.

> 🚧 Early release: all three skills are v0.1. Issues and PRs are welcome.

## What's here

| Folder | What |
|---|---|
| [`guides/`](guides/) | Free PDF guides from the videos (Claude desktop cheat sheet, $0 video stack, AI avatar build, daily pipeline) |
| [`plugins/make-video`](plugins/make-video/) | Idea → script → voice → captions → music → Remotion render → QA → ready to post |
| [`plugins/snipshorts`](plugins/snipshorts/) | A podcast or interview link → vertical Shorts with the speaker tracked, captions, SFX and posting copy. A free, open-source OpusClip alternative with no watermark |
| [`plugins/cartoonsmith`](plugins/cartoonsmith/) | Voiced cartoon episodes with recurring characters: talking rigs from your own character art, lip sync, captions and music |

## Install

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install make-video@zero-dollar-studio
/plugin install snipshorts@zero-dollar-studio     # optional add-on
/plugin install cartoonsmith@zero-dollar-studio   # optional add-on
```

snipshorts and cartoonsmith are add-ons: they copy their tools into the video project that make-video sets up.

Then ask Claude Code for a video ("make a 30-second Short explaining how DNS works"). The first run sets up a video project and downloads about 6 GB of free models. You need macOS on Apple Silicon, Node 20+ and Homebrew.

## The free stack

Claude Code · Remotion · Chatterbox (voice clone) · Whisper (captions) · FluidSynth (music) · YuNet (speaker framing) · Rhubarb (lip sync) · Indic Parler-TTS (Hindi and other Indian languages) · JoyVASA + LivePortrait (AI face, coming in make-video v0.2)

## Licenses

- Code: MIT. **Remotion has its own license**: free for individuals and companies of up to 3 people. Larger companies need a [Remotion Company License](https://www.remotion.dev/license).
- Guides (`guides/`): [CC BY 4.0](guides/LICENSE).
- Third-party models keep their own licenses. Some face-model weights are non-commercial and are never used here; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Only clone voices you have consent for. Chatterbox adds an inaudible watermark; leave it in.
