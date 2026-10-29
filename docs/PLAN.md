# Open-source plan and tracker

## Status (updated 29 Oct 2026)

| Item | State | Link |
|---|---|---|
| Public repo `TheNoumanDev/zero-dollar-studio` | ✅ live (29 Oct) | [repo](https://github.com/TheNoumanDev/zero-dollar-studio) |
| `guides/`: CLAUDE, AVATAR, STACK, PIPELINE PDFs | ✅ live | [guides](https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/guides) |
| `.claude-plugin/marketplace.json` (empty `plugins`) | ✅ validates (warning: no plugins yet) | [marketplace.json](https://github.com/TheNoumanDev/zero-dollar-studio/blob/main/.claude-plugin/marketplace.json) |
| LICENSE (MIT code) + `guides/LICENSE` (CC BY 4.0) | ✅ done | |
| `make-video` skill | ⏳ not started (release step 2) | |
| `snipshorts` skill | ⏳ not started (release step 3) | |
| `cartoonsmith` skill | ⏳ not started (release step 4) | |
| `THIRD_PARTY_NOTICES.md` | ⏳ ships with the first skill | |
| Awesome-list PRs (ComposioHQ, travisvn, VoltAgent) | ⏳ after the first skill ships | |
| Hero GIF in README | ⏳ | |

Video link for guides: https://github.com/TheNoumanDev/zero-dollar-studio/tree/main/guides

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
