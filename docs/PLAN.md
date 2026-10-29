# Open-source plan and tracker

## Status (updated 30 Oct 2026)

| Item | State | Link |
|---|---|---|
| Public repo `TheNoumanDev/zero-dollar-studio` | ✅ live (29 Oct) | [repo](https://github.com/TheNoumanDev/zero-dollar-studio) |
| `guides/`: CLAUDE, AVATAR, STACK, PIPELINE PDFs | ✅ live | [guides](https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/guides) |
| `.claude-plugin/marketplace.json` | ✅ live with make-video, snipshorts, cartoonsmith; `--strict` passes | [marketplace.json](https://github.com/TheNoumanDev/zero-dollar-studio/blob/main/.claude-plugin/marketplace.json) |
| LICENSE (MIT code) + `guides/LICENSE` (CC BY 4.0) | ✅ done | |
| `make-video` skill v0.1 | ✅ live 29 Oct; `/plugin install` tested from GitHub | [plugins/make-video](https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/plugins/make-video) |
| `snipshorts` skill v0.1 | ✅ live 30 Oct (add-on to make-video); end-to-end Short rendered in test | [plugins/snipshorts](https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/plugins/snipshorts) |
| `cartoonsmith` skill v0.1 | ✅ live 30 Oct (add-on to make-video); placeholder-cast episode rendered, QA PASS | [plugins/cartoonsmith](https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/plugins/cartoonsmith) |
| `THIRD_PARTY_NOTICES.md` | ✅ live | [notices](https://github.com/TheNoumanDev/zero-dollar-studio/blob/main/THIRD_PARTY_NOTICES.md) |
| Awesome-list PRs (ComposioHQ, travisvn, VoltAgent) | ⏳ after the first skill ships | |
| Hero GIF in README | ⏳ | |

Video link for guides: https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/guides

---

## TODO (work in order; tick when pushed)

**make-video v0.1** (voiced story → captions → music → render → QA, no AI face yet)
- [x] `plugins/make-video/` with `.claude-plugin/plugin.json` and a README
- [x] `template/`: a minimal Remotion starter (FridgeDrama example, `_Template`, shared components) with no 0x45.dev, Nouman or Jalebee assets
- [x] `template/tools/`: voice.py, take_check.py, captions.mjs, music.py, qa.py, prodlog.py, make-story.sh, setup.sh, requirements.txt, scrubbed of personal paths and channel rules
- [x] No WAVs or weights in git: setup.sh downloads models; voices are Chatterbox's default voice or the user's own recording
- [x] `SKILL.md` made generic (scaffold step, setup, brief → script → pipeline → QA); channel-specific lessons cut, general lessons moved to `reference/lessons.md`
- [x] Add to `marketplace.json`; `claude plugin validate --strict` passes
- [x] Smoke test: scaffold into a temp folder, `npm install`, lint + typecheck, render the example (29 Oct: full run OK, QA FIX only on visual variety in the example)
- [x] `THIRD_PARTY_NOTICES.md` (Remotion, Chatterbox, Whisper, FluidSynth, GeneralUser GS, ffmpeg, OpenCV)
- [x] Root README: install lines (demo GIF still to do), "what you need" (macOS Apple Silicon, ~6 GB disk)
- [x] Pushed 29 Oct (install from GitHub tested in a clean config)
- [ ] Fresh-machine test of `tools/setup.sh` (full ~6 GB download)
- [ ] Launch video + Short ("I open-sourced the skill that makes my videos"), repo link pinned

**make-video v0.1.x:** tune the Fridge Drama example so QA's variety check passes; README demo GIF; optional DeepFilterNet denoise step

**make-video v0.2:** optional AI face step (JoyVASA + LivePortrait, user downloads weights, never InsightFace), `npx skills add` symlink in `skills/`

**snipshorts v0.1** ✅ pushed 30 Oct: tools/podcast + PodcastShort, YuNet framing, optional watermark/end card, local ready-to-post folder (no uploads). Reaction avatar, upscaling, covers and MLX transcription left out.
- [ ] Test the 1080p yt-dlp section fetch, split-screen layout, `romanize.py`, `people.py --label`
- [ ] v0.2: optional cover maker (rembg) and upscaling

**cartoonsmith v0.1** ✅ pushed 30 Oct: series bible, rigs from your own sheets (split → align), automatic shot edit, Rhubarb lip sync, optional Parler for Indian languages, placeholder cast example. No Sharma/Jalebee art shipped.
- [ ] Fresh install of Rhubarb, Real-ESRGAN and the `WITH_PARLER=1` venv; render a 9:16 episode, group shots, a second set
- [ ] Launch with a Jalebee TV demo episode (needs your OK to show that art)
- [ ] v0.2: body motion (AnimatedDrawings), AI-video inserts

**Launch chores:** hero GIF, awesome-list PRs (ComposioHQ, travisvn, VoltAgent), pin the repo on your GitHub profile, new guide PDFs as they come out (add the PDF plus a row in `guides/README.md`)

---

## Plan (drafted 29 Oct 2026)

Goal: one public GitHub repo that videos can link to ("all guides + skills here"), which grows the channel and your GitHub profile. Research and sources: [research.md](research.md).

## 1. Names: decided 29 Oct

**Repo / marketplace: `zero-dollar-studio` · clipping skill: `snipshorts` · cartoon skill: `cartoonsmith`** (plus `make-video`).

Options that were considered:

| Use | Top picks (free on GitHub + npm as of 29 Oct) | Avoid (taken / too close) |
|---|---|---|
| Umbrella repo + marketplace | **zero-dollar-studio**, 0x45-studio, zero-dollar-video | claude-video-kit (121★, same idea), claude-studio |
| Clipping skill | **snipshorts**, podshorts, clip-shorts | autoclip (9.9k★), Youtube-clipper-skill (2.3k★), claude-shorts, clipforge |
| Cartoon skill | **cartoonsmith**, toonsmith, sitcom-skill | toon-skill (TOON is a data format) |

Why these: the repos that went viral either promise an outcome ("$0", "MoneyPrinter"), use the exact search phrase, or are creator name + plain noun (mattpocock/skills). The description should name what we replace: *"free, open-source OpusClip alternative, no watermark"*.

## 2. Repo layout

```
README.md                    hero GIF made by the tools themselves, install in 2 lines
.claude-plugin/marketplace.json
plugins/make-video/          .claude-plugin/plugin.json + skills/make-video/SKILL.md + scripts/
plugins/snipshorts/
plugins/cartoonsmith/
skills/<name>/SKILL.md       symlinks, so `npx skills add` works for Codex/Cursor too
guides/                      the DM PDFs + keyword table (CC BY 4.0)
THIRD_PARTY_NOTICES.md       Remotion, Chatterbox, Whisper, JoyVASA/LivePortrait, soundfont
```

## 3. Publishing

1. **GitHub marketplace (free, instant):** push the repo with `.claude-plugin/marketplace.json`. Users run `/plugin marketplace add <you>/zero-dollar-studio` and `/plugin install make-video@zero-dollar-studio`. Check first with `claude plugin validate --strict .`.
2. **Anthropic's directory (optional, reviewed):** submit at claude.ai/directory/manage (needs a paid plan).
3. **Awesome lists:** after launch, open PRs to ComposioHQ/awesome-claude-skills, travisvn/awesome-claude-skills and VoltAgent's list.
4. **claude.ai upload:** a zipped skill folder can be uploaded as a custom skill. Mention it in the README.

## 4. Order of release

| Step | What | Why first |
|---|---|---|
| 1 | `guides/` + README (done locally) | Zero risk; videos can link it from tomorrow |
| 2 | **make-video** skill | Matches the channel story ("this video was made by it") |
| 3 | **Clipping** skill | Biggest search demand (OpusClip alternative) |
| 4 | **Cartoon** skill | Most unique; launch it with a Jalebee TV episode as the demo |

Each launch = one 0x45.dev video + Short ("I open-sourced the skill that…") with the repo link pinned.

## 5. Must-do before any push (licensing + privacy)

- Remotion is **not** open source: say so in the README and don't vendor its code (this also covers `@remotion/whisper-webgpu`).
- The face step stays optional; never ship InsightFace weights (non-commercial). Our pipeline already avoids InsightFace.
- Don't commit the soundfont; download it in setup.
- Never commit `private/`, the Nouman avatar images, voice clips, `secrets/`, or channel posting tools.
- Strip personal paths (absolute home-folder paths) and channel-specific rules from the skills; move them into an example config.
- Run a secret scan before the first push.

## 6. Decisions waiting on you

1. ~~Names~~: decided (zero-dollar-studio, snipshorts, cartoonsmith).
2. ~~GitHub account~~: personal (TheNoumanDev).
3. ~~Create and push~~: done 29 Oct 2026.
