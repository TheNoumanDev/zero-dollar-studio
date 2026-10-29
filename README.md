<p align="center">
  <img src="assets/logo-banner.png" alt="zero-dollar studio: make YouTube videos with Claude Code for $0" width="820">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/code-MIT-5BE3A0"></a>
  <a href="guides/LICENSE"><img alt="Guides: CC BY 4.0" src="https://img.shields.io/badge/guides-CC%20BY%204.0-FFD23F"></a>
  <img alt="Cost: $0" src="https://img.shields.io/badge/cost-%240-FF5C8A">
  <img alt="Runs locally on macOS Apple Silicon" src="https://img.shields.io/badge/runs%20on-macOS%20Apple%20Silicon-A9A3C9">
  <a href="https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA"><img alt="YouTube: @0x45.dev" src="https://img.shields.io/badge/YouTube-%400x45.dev-FF0000?logo=youtube&logoColor=white"></a>
</p>

<p align="center">
  <b>Script, voice, captions, music, animation and QA, made by free local tools and driven by Claude Code skills.</b><br>
  No subscriptions, no credits, no API keys, no watermark.
</p>

## 🎬 Watch it in action

<p align="center">
  <a href="https://www.youtube.com/watch?v=CKhU8AHQ6N4">
    <img src="https://i.ytimg.com/vi/CKhU8AHQ6N4/maxresdefault.jpg" alt="Watch: I make these AI videos for $0, my full free stack explained" width="640">
  </a>
  <br>
  <sub>▶ <a href="https://www.youtube.com/watch?v=CKhU8AHQ6N4"><b>I make these AI videos for $0: my full free stack, explained</b></a> · <a href="https://www.youtube.com/shorts/1wMujOBFRD4">Short version</a><br>
  The script, voice, captions, music and edit were made with these skills; the AI face step lands in make-video v0.2.</sub>
</p>

<table>
  <tr>
    <td width="300" align="center">
      <img src="assets/fridge-drama.gif" alt="Fridge Drama: three vegetables argue in a fridge, made by make-video" width="260">
    </td>
    <td>
      <h3>What you get on day one</h3>
      <p>Install the plugin and ask for a video. Claude checks your Mac, lists what it needs to download, and waits for your OK. Then it sets everything up and renders <b>Fridge Drama</b>: 33 seconds of three vegetables arguing in a fridge, with voices, word-synced captions, music and SFX, all generated on your laptop.</p>
      <p>Then you ask for your own: <i>"make a 30-second Short explaining how DNS works"</i>. Claude writes the script, checks its facts, voices it, captions it, scores it, renders it and runs a QA check on the result.</p>
    </td>
  </tr>
</table>

## 🧰 The skills

| Skill | What it does |
|---|---|
| 🎥 [**make-video**](plugins/make-video/) | Idea → script → voice → captions → music → Remotion render → QA → ready to post |
| ✂️ [**snipshorts**](plugins/snipshorts/) | A podcast or interview link → vertical Shorts with the speaker tracked, captions, SFX and posting copy. **A free, open-source OpusClip alternative with no watermark** |
| 🎨 [**cartoonsmith**](plugins/cartoonsmith/) | Voiced cartoon episodes with recurring characters: talking rigs from your own character art, lip sync, captions and music |
| 📘 [**guides/**](guides/) | Free PDF guides from the videos: Claude desktop cheat sheet, the $0 video stack, the AI avatar build, the daily pipeline |

## ⚡ Install

In Claude Code:

```
/plugin marketplace add TheNoumanDev/zero-dollar-studio
/plugin install make-video@zero-dollar-studio
/plugin install snipshorts@zero-dollar-studio     # optional add-on
/plugin install cartoonsmith@zero-dollar-studio   # optional add-on
```

Then ask for a video. The first run sets up a video project and downloads about 6 GB of free models, after you OK the list. snipshorts and cartoonsmith are add-ons: they copy their tools into the project that make-video sets up.

**You need:** macOS on Apple Silicon, Node 20+, Homebrew and about 8 GB of free disk.

## 🆓 The free stack

| Job | Tool |
|---|---|
| Brain | Claude Code |
| Video | Remotion (React) |
| Voice | Chatterbox (built-in voice, or a clone of your own) · Indic Parler-TTS for Hindi and other Indian languages |
| Captions | Whisper |
| Music + SFX | MIDI written as code → FluidSynth |
| Speaker framing | YuNet |
| Lip sync | Rhubarb |
| AI face | JoyVASA + LivePortrait *(coming in make-video v0.2)* |

## 📜 Licenses

- Code: MIT. **Remotion has its own license**: free for individuals and companies of up to 3 people. Larger companies need a [Remotion Company License](https://www.remotion.dev/license).
- Guides (`guides/`): [CC BY 4.0](guides/LICENSE).
- Third-party models keep their own licenses. Some face-model weights are non-commercial and are never used here; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Only clone voices you have consent for. Chatterbox adds an inaudible watermark; leave it in.

---

<p align="center">
  <img src="assets/logo.png" alt="" width="48"><br>
  Made by <a href="https://github.com/TheNoumanDev"><b>TheNoumanDev</b></a> · the toolkit behind <a href="https://www.youtube.com/channel/UC2ahNqB5F_pp16O27rmlMtA">@0x45.dev</a> on YouTube<br>
  <sub>⭐ Star the repo if it saved you a subscription. Issues and PRs are welcome.</sub>
</p>
