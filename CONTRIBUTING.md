# Contributing

Thanks for helping. Bug reports, fixes, new lessons and ports to other platforms are all welcome.

## Reporting a bug

Open an [issue](https://github.com/TheNoumanDev/zero-dollar-studio/issues/new/choose) with:
- which skill and version (`/plugin list` in Claude Code, or the `version` in `plugins/<skill>/.claude-plugin/plugin.json`)
- your agent (Claude Code, Codex, Gemini CLI, …), your Mac's chip and macOS version
- the command that failed and the last 30 lines of its output
- for a bad video, the QA report (`stories/<slug>/qa/report.md`) and a frame or two

Never attach voice samples or videos of people who haven't agreed to it.

## Making a change

1. Fork, then branch from `main`.
2. Skill text lives in `plugins/<skill>/skills/<skill>/SKILL.md`. Keep it short and plain: the agent reads every word.
3. Project files a skill copies into a user's video project live in `plugins/<skill>/skills/<skill>/template/`.
4. Before opening a PR:
   - `claude plugin validate --strict .` passes
   - for template changes: copy make-video's template (plus your add-on) into a scratch folder, then `npm install`, `npm run lint` and one example render pass
   - bump `version` in that plugin's `.claude-plugin/plugin.json`
5. Explain what you tested in the PR.

## Ground rules

- **$0 and local.** No paid APIs, API keys or cloud render services in the default path.
- **Licences matter.** Every tool or model needs a licence that allows commercial use (no InsightFace models, no macOS `say` voices). Add new ones to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Never commit model weights, voice samples or media you don't own; download them in a setup script instead.
- **Ask before downloading.** If your change adds a download, add it (with its size) to the skill's download table.
- **Never post or upload** anything on the user's behalf.

By contributing you agree that your code is released under the MIT licence and guide content under CC BY 4.0.
