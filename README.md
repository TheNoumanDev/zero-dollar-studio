# zero-dollar-studio

**Make YouTube videos with Claude Code for $0.** Script, cloned voice, captions, music, animation and an AI host, all made by local, free tools and driven by Claude Code skills.

This is the toolkit behind [@0x45.dev](https://youtube.com/@0x45.dev), a channel where every video, including the host, is made this way.

> 🚧 Work in progress: the guides are live, and the skills are being cleaned up for release.

## What's here

| Folder | What |
|---|---|
| [`guides/`](guides/) | Free PDF guides from the videos (Claude desktop cheat sheet, $0 video stack, AI avatar build, daily pipeline) |
| `plugins/make-video` *(soon)* | Idea → script → voice → captions → music → Remotion render → QA → ready to post |
| `plugins/snipshorts` *(soon)* | A long podcast or YouTube link → vertical Shorts with captions and posting copy |
| `plugins/cartoonsmith` *(soon)* | Voiced cartoon episodes with recurring characters |

## Install (once the skills ship)

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install make-video@zero-dollar-studio
```

## The free stack

Claude Code · Remotion · Chatterbox (voice clone) · Whisper (captions) · FluidSynth (music) · JoyVASA + LivePortrait (AI face)

## Licenses

- Code: MIT. **Remotion has its own license**: free for individuals and companies of up to 3 people. Larger companies need a [Remotion Company License](https://www.remotion.dev/license).
- Guides (`guides/`): [CC BY 4.0](guides/LICENSE).
- Third-party models keep their own licenses. Some face-model weights are non-commercial; see `THIRD_PARTY_NOTICES.md` (coming with the skills).
- Only clone voices you have consent for. Chatterbox adds an inaudible watermark; leave it in.
