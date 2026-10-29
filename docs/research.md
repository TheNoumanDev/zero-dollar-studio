# Open-sourcing the 0x45.dev video skills: research (2026-10-29)

Goal: publish `make-video`, `clipping` and `cartoon` Claude Code skills, plus the free DM guide PDFs, in one public
GitHub repo that videos can link to. Star counts are live `gh api` reads from 2026-10-29 unless marked otherwise.

---

## A. What is popular in this space and why it works

### Claude skills collections
| Repo | Stars | Why the name and README work |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | 308k | One evocative word, and the promise is obvious: skills give your agent superpowers. |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 306k | Author brand plus the plainest possible noun. Tagline: "Skills for Real Engineers. Straight from my .agents directory." A creator's personal skills folder sells itself. **This is the closest model for you.** |
| [anthropics/skills](https://github.com/anthropics/skills) | ~185k | The official one. It has `skills/`, `spec/`, `template/` and `.claude-plugin/`, and installs with `/plugin marketplace add anthropics/skills`. |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 78k | "awesome-" plus the exact search term. People search for and link curated lists. |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 57k | Same pattern, with a funny, over-the-top tagline. |
| [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | 45k | Anthropic's official plugin marketplace. |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 37k | Says "1000+ skills" and that they work in "Claude Code, Codex, Gemini CLI, Cursor": a number plus cross-tool reach. |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | 16k | Another "awesome" list. **Get listed here and in the lists above** (open a PR once the repo is live). |

### Video with Claude Code / agents
| Repo | Stars | Notes |
|---|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 75k (Apache-2.0) | "Write HTML. Render video. Built for agents." Three short verb sentences. Installs with `npx skills add heygen-com/hyperframes`. |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 69k | "Make videos programmatically with React". Ships an official skill: `npx skills add remotion-dev/remotion` ([skills.sh listing](https://skills.sh/digitalsamba/claude-code-video-toolkit/remotion)). |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | 2.4k | "AI-native video production toolkit for Claude Code". The name is the search query. |
| [wshuyi/remotion-video-skill](https://github.com/wshuyi/remotion-video-skill) | 437 | `<tool>-<thing>-skill` naming. |
| [hassancs91/claude-faceless-shorts-creator](https://github.com/hassancs91/claude-faceless-shorts-creator) | 290 | Built on the "faceless channel" niche keyword. |
| [AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts) | 253 | Short "claude-" plus format name. |
| [runesleo/claude-video-kit](https://github.com/runesleo/claude-video-kit) | 121 | "Agent Skill + Remotion pipeline". Close to your make-video skill, so it's a direct competitor. |

### AI short-video makers / OpusClip alternatives
| Repo | Stars | Notes |
|---|---|---|
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 136k | Says the outcome ("money printer"). "One click" HD shorts from a keyword. The most viral naming in the niche. |
| [linyqh/NarratoAI](https://github.com/linyqh/NarratoAI) | 12k | AI narration/recap editing. |
| [zhouxiaoka/autoclip](https://github.com/zhouxiaoka/autoclip) | 9.9k | "One link, one click, get clips". Podcast to Shorts plus captions and posting copy, which is exactly your clipping skill. |
| [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | 8.1k | Pairs "Shorts" with "GPT", the hot term of its day. |
| [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | 5.7k | The description names its rivals ("Open-source alternative to Opus Clip, Vidyo.ai, Klap & SubMagic") and says "free, no watermarks, no per-clip credits". **Copy this SEO trick.** |
| [op7418/Youtube-clipper-skill](https://github.com/op7418/Youtube-clipper-skill) | 2.3k | A clipping **skill** for Claude Code. This is your closest competitor for #2. |
| [gyoridavid/short-video-maker](https://github.com/gyoridavid/short-video-maker) | 1.4k | MCP plus REST short-video maker. |
| [xixihhhh/clipforge](https://github.com/xixihhhh/clipforge) | 1.1k (AGPL) | Uses "0 cost" in its README. |
| Smaller ones: [aionixos/openclip](https://github.com/aionixos/openclip), [ClippedAI](https://shaarav4795.github.io/ClippedAI) | n/a | Both self-described as free OpusClip alternatives. |

### Naming patterns that go viral
1. **Author + plain noun** (`mattpocock/skills`): a personal brand works when the README shows real output.
2. **The search query as the name** (`claude-code-video-toolkit`, `awesome-claude-skills`, `claude-shorts`).
3. **The outcome or promise** (`MoneyPrinterTurbo`, `superpowers`, AutoClip's "one link, one click").
4. **Naming the paid tool you replace** in the description ("open-source OpusClip alternative", "free, no watermark").
5. **Short tool-like coinages** (`hyperframes`, `remotion`). These only win with big backing or a great demo GIF.
6. In READMEs, the hooks that work are a demo GIF or video at the top, a one-line install, "$0 / free / local / no API keys", and a "works with Claude Code, Codex, Cursor" badge.

---

## B. How to publish skills and plugins officially

**SKILL.md format** ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills), spec at [agentskills.io](https://agentskills.io)):
- A skill is a folder containing `SKILL.md`. The YAML frontmatter must start on line 1. The anthropics/skills template requires `name` and `description`.
- Optional fields include `when_to_use`, `allowed-tools`, `disable-model-invocation`, `context: fork`, `paths`, `license` and `compatibility` (500 characters max).
- The listing truncates `description` and `when_to_use` combined at **1,536 characters**. Put the main use case first.
- Keep `SKILL.md` **under 500 lines**. Move detail into sibling files (`reference.md`, `scripts/`) and link them from SKILL.md.
- Skills live in `~/.claude/skills/<name>/` (personal), `.claude/skills/<name>/` (project) or `<plugin>/skills/<name>/` (plugin). A plugin skill is invoked as `/plugin-name:skill-name`.

**Plugin and marketplace** ([plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [plugins/publish](https://code.claude.com/docs/en/plugins/publish)):
- The plugin manifest is `.claude-plugin/plugin.json`. Set `name` (kebab-case, **permanent**), `displayName`, `description`, `author`, `homepage`, `repository`, `version`, and add a README.
- The marketplace file is `.claude-plugin/marketplace.json`. It requires `name`, `owner` and `plugins[]`, and each entry needs `name` and `source`. Example:
  ```json
  { "name": "0x45-studio", "owner": { "name": "Nouman" },
    "plugins": [ { "name": "make-video", "source": "./plugins/make-video", "description": "..." },
                 { "name": "clip-shorts", "source": "./plugins/clip-shorts" },
                 { "name": "toon-studio", "source": "./plugins/toon-studio" } ] }
  ```
- Publishing is just pushing to GitHub, with no submission form. Users install with:
  `/plugin marketplace add <you>/<repo>` and then `/plugin install make-video@<marketplace-name>`.
  In v2.1.275 and later this is one command: `/plugin install make-video --marketplace <you>/<repo>`.
- Rules:
  - Validate with `claude plugin validate --strict .`
  - The entry name and the `plugin.json` name must match.
  - Write relative paths from the repo root, with no `..`.
  - Bump `version` on each release, or omit it so the commit SHA is used.
  - Pick a marketplace name unlikely to collide with others.
  - Reserved names such as `claude-plugins-official` are refused.
- Without a marketplace, users can run `claude --plugin-dir ./folder` or drop the folder into `~/.claude/skills/`.

**Anthropic's directory** ([publish docs](https://code.claude.com/docs/en/plugins/publish#submit-to-anthropics-directory)):
- You submit at [claude.ai/directory/manage](https://claude.ai/directory/manage), following [claude.com/docs/plugins/submit](https://claude.com/docs/plugins/submit#submit-a-plugin). This **requires a paid claude.ai plan**, and each version goes through review.
- A listing reaches claude.ai, Cowork and Claude Code (as `<name>@synced`).
- `claude-plugins-official` does **not** take portal submissions. Listing there goes through an Anthropic partner contact only.
- Many components are Claude Code-only, and your skills need a local GPU/Python/ffmpeg setup. A directory listing would mostly fail for claude.ai users. **Recommendation: use your own GitHub marketplace first.**
- [anthropics/skills](https://github.com/anthropics/skills) has about 1k PRs, but its page lists no CONTRIBUTING file. Treat it as a reference and template, not a submission channel.

**claude.ai custom skill upload** ([support.claude.com/en/articles/12512180](https://support.claude.com/en/articles/12512180-using-skills-in-claude), [platform overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)):
- Go to Settings > Capabilities > Skills, then "+", then "Upload a skill", and choose a ZIP whose **root is the skill folder**.
- An uploaded skill is private to that account and needs code execution enabled.
- It is useful as a "lite" path for script-only parts, but your pipeline needs local tools.

**Cross-agent install:** `npx skills add <you>/<repo>` (the [skills.sh](https://skills.sh) CLI used by Remotion and HyperFrames) also works if the repo has `skills/<name>/SKILL.md`. Supporting it costs nothing and adds Codex and Cursor users.

**Suggested repo layout:**
```
<repo>/
  README.md                (GIF demo, "$0, local, Claude Code", 1-line install, links to videos)
  LICENSE                  (MIT for your code)
  THIRD_PARTY_NOTICES.md   (Remotion, models, soundfont: see D)
  .claude-plugin/marketplace.json
  plugins/make-video/{.claude-plugin/plugin.json, skills/make-video/SKILL.md, scripts/}
  plugins/clip-shorts/...   plugins/toon-studio/...
  guides/                  (DM cheat-sheet PDFs + guides/README.md index with keyword -> PDF table)
  examples/                (sample outputs, short MP4/GIF)
```
Strip personal data before pushing:
- Nouman avatar images and voice reference WAVs
- channel-specific posting rules
- any API keys

Run the `scan_secrets` tool from the plugin-authoring MCP before the first push.

---

## C. Name candidates

Availability key: **free** means no GitHub repo with that exact name has more than 5 stars and the npm name is 404 (checked 2026-10-29). **Crowded** means several small repos already use it. **Taken** means an established project already uses it. A GitHub owner/repo is always unique under your own account, so "taken" is about search and SEO confusion.

### (1) Umbrella repo for the 3 skills + PDFs
| Name | Status | Note |
|---|---|---|
| **zero-dollar-studio** | free (gh 0, npm 404) | Says "$0" plus "studio". Matches your story. |
| **zero-dollar-video** | free (gh 0, npm 404) | More literal and searchable. |
| **0x45-studio** | free (gh 0, npm 404) | Brand-first, mattpocock style. Pairs well as the marketplace name. |
| **free-studio-skills** | free (gh 0) | Has keyword value. |
| **makevideo-skill** | free (gh 0) | The search query, but narrow. |
| free-video-skills | free-ish (1 tiny repo) | |
| vidskills / videoskills | crowded, small (max 10 stars) | |
| claude-video-kit | **taken**: runesleo/claude-video-kit (121 stars), same idea | Avoid. |
| claude-studio | **taken**: 557 repos, npm taken | Avoid. |
| clauderoll | free-ish | Cute, but the meaning is unclear. |
| free-video-studio | crowded (lcy362/free-short-video-studio, 32 stars) | |

### (2) Clipping skill (podcast/YouTube link to vertical Shorts)
| Name | Status | Note |
|---|---|---|
| **snipshorts** | free (gh 0, npm 404) | A verb plus the format. Short. |
| **podshorts** | free-ish (2 repos, max 1 star) | Says podcast to Shorts in one word. |
| **clip-shorts** | free-looking (not in search, see above) | The plain search phrase. |
| shortsmith | crowded (mlvps/shortsmith, 15 stars) | |
| reelsmith | crowded (44 repos, one already "claude-reelsmith") | |
| clipsmith | crowded (35 small repos) | |
| clipline | crowded (nxsaken/clipline, 22 stars) | |
| claude-shorts | **taken**: AgriciDaniel/claude-shorts (253 stars) | |
| clip-skill / youtube-clipper | **taken**: op7418/Youtube-clipper-skill (2.3k stars) | |
| autoclip | **taken**: zhouxiaoka/autoclip (9.9k stars) | |
| clipforge | **taken**: xixihhhh/clipforge (1.1k stars) | |
| freeclip / chopshop / clipkit | crowded or npm taken | |

### (3) Cartoon skill (voiced episodes with recurring characters)
| Name | Status | Note |
|---|---|---|
| **cartoonsmith** | free (gh 0, npm 404) | Clear, and searchable for "cartoon". |
| **toonsmith** | free (1 unrelated repo, npm 404) | Short form of the same. |
| **sitcom-skill** | free (gh 0) | Highlights recurring characters. |
| toon-studio / toonstudio | free-ish (2 repos, 0 stars) | |
| toonroom | free-ish (1 repo, 0 stars) | Writers' room vibe. |
| inkreel | crowded (11 tiny repos) | |
| toonforge | crowded (27 tiny repos) | |
| cartoon-kit | crowded (11 tiny repos) | |
| toon-skill | **confusing**: "TOON" is also a JSON-alternative format with existing skills | Avoid. |
| toonloop | **taken**: aalex/toonloop (an animation tool) | |
| episodic | **taken**: npm taken, obra/episodic-memory | |

Tip: whichever names you pick, put the SEO words in the **GitHub description and topics**, not the name. For example: "Free, local OpusClip alternative as a Claude Code skill. Podcast to Shorts with captions. $0, no API keys." Suggested topics: `claude-code`, `claude-skills`, `remotion`, `opus-clip-alternative`, `youtube-shorts`, `ai-video`, `text-to-speech`, `whisper`.

---

## D. Licensing gotchas

| Component | License | What the repo must do |
|---|---|---|
| **Remotion** | Custom "Remotion License" ([LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md), [docs](https://www.remotion.dev/docs/license)). **Not OSI open source.** | Free for individuals, for-profits with ≤3 employees, non-profits, and evaluation. Larger companies need a Company License. You may not sell or relicense a Remotion derivative. Your MIT license covers **only your code**. Remotion is a dependency your users install from npm, and you must not vendor its source. README must say: "This project uses Remotion, which has its own license; companies may need a Remotion Company License - see remotion.dev/license." |
| **Chatterbox TTS** ([resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox), 27k) | MIT | Fine to use. Every output carries the **Perth watermark**, which is imperceptible. Don't strip it, and mention it in the README. Add a voice-cloning consent note: "clone only your own voice or one you have permission to use." Don't ship your voice reference WAVs. |
| **Whisper** (openai/whisper weights) | MIT | Fine to use. Credit it in THIRD_PARTY_NOTICES. Note: this project runs Whisper through `@remotion/whisper-webgpu`, which falls under the **Remotion license**, not MIT. |
| **LivePortrait** ([KwaiVGI/LivePortrait](https://github.com/KwaiVGI/LivePortrait), 19k) | Code and weights MIT | Its default face detector uses the **InsightFace buffalo_l models, which are non-commercial research only**. The usual guidance is to replace them for commercial use ([Replicate note](https://replicate.com/fofr/live-portrait/readme), [FacePoke LICENSE](https://huggingface.co/spaces/jbilcke-hf/FacePoke/blob/main/LICENSE)). A monetized YouTube channel is arguably commercial. **Don't bundle the weights.** Make the face step optional, have users download models themselves, and plan a MediaPipe or other permissive detector swap. |
| **JoyVASA** ([jdh-algo/JoyVASA](https://github.com/jdh-algo/JoyVASA), 883) | MIT | Its `pretrained_weights` also include `insightface/models/buffalo_l`. The same non-commercial caveat applies. It also depends on wav2vec2/HuBERT weights, which have their own terms. |
| **InsightFace models** | Non-commercial research | Avoid them in anything you ship. Document the restriction if users choose to install them. |
| **GeneralUser GS soundfont** ([license text](https://scancode-licensedb.aboutcode.org/generaluser-gs-2.0.html)) | Custom permissive (ScanCode classes it as "Permissive") | Free to use for your own music creation, private or commercial, and redistribution is allowed. The author says he **cannot be 100% sure where every sample came from** and warns about use in commercial *software products*. Download it in a setup script rather than committing the .sf2, and include its LICENSE if you do redistribute it. |
| **FluidSynth** | LGPL-2.1 | Call it as an external binary installed by the user. That's fine for an MIT repo. |
| **Your DM PDFs** | Your choice | Use **CC BY 4.0** or CC BY-NC 4.0 for `guides/` (separate from the MIT code). This keeps attribution to @0x45.dev when they're shared. |
| **anthropics/skills content** | Apache-2.0 for most; doc skills source-available | Don't copy the docx/pdf/pptx/xlsx skills into your repo. |

Also: don't commit the Nouman 3D character images or the cloned voice. Keep the brand assets in a separate private folder and use a neutral placeholder character in the examples.

---
Sources (other than those linked inline): [fast.io awesome-claude-skills 2026](https://www.fast.io/resources/awesome-claude-skills-directory-2026.md),
[GitHub topic: ai-clipping](https://github.com/topics/ai-clipping), [HyperFrames writeup](https://themenonlab.blog/blog/heygen-hyperframes-video-as-code),
[claude.ai directory](https://claude.ai/directory), GitHub API and npm registry checks run 2026-10-29.
