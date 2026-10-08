# Changelog

All notable changes to Think Better are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Docs, website and issue/PR templates are English only: the Vietnamese README section and
  website text were removed.

## [1.5.0] - 2026-10-08

### Breaking

- `uninstall --force` now also deletes files you modified (and their `.new`) and warns
  when it does. To skip the confirmation and keep your edits, use the new `--yes` (`-y`).
- make-decision exits with code 2 instead of 1 for bad input (empty text, bad matrix or
  scores, unknown step), like the other two skills.

### Fixed

- Upgrading an install made by v1.3.0 or earlier no longer marks unedited files as
  modified: `update` wrote a `.new` for almost every file, `uninstall` kept them all and
  `check` failed. The CLI now knows the files every release shipped.
- After `uninstall` keeps an edited file, the skill stays uninstalled: `check` passes and
  `update` no longer installs it again.
- `init --ai claude` run in the home directory no longer overwrites the user-level
  install with project paths; it acts as `--global`.
- Commands run from a project subdirectory find the project's install.
- Slash commands: user text that contained a line `TASK` could end the heredoc and run the
  rest as shell commands; the delimiter is now `THINK_BETTER_EOF_7f3a` and the assistant
  checks for it. SKILL.md examples no longer put user text on the command line.
- code-solving classifies "Add …" features, unaccented Vietnamese, stack traces and names
  like MySQL correctly; problem-solving no longer reduces keywords to single generic words;
  make-decision reads "A, B and C" and numbered option lists.
- Saving into an existing workspace with a different request or type no longer mixes two
  plans (it needs `--force` or another `-p`); workspace names fold accents in every skill.
- C# stack frames with spaces in the path resolve; symbols are found outside git.
- ASCII boxes line up with Vietnamese text; long requests are up to 5x faster.

### Added

- GitHub Copilot skills install to `.github/skills/`, where Copilot loads them, and
  support `--global` (`~/.copilot/skills/`). Old installs under `.github/prompts/<skill>/`
  are moved by `update`.
- `think-better diff` shows how your edited files differ from the new `.new` versions.
- `uninstall` finds where a skill is installed (no `--ai` needed) and accepts `--all`
  and `--yes`.
- `--exclude-command` / `--include-command` keep individual slash commands out.
- Slash commands with no text: `/code.review` reviews the current changes, the resume
  commands open the latest workspace, the others ask first. Answers come in your language,
  and saving accepts "save", "save again" and "save step-by-step".
- All three skill scripts accept `-p`/`--project-name`/`--project` and
  `-n`/`--max-results`/`--results`; code-solving's executive depth opens with a summary.
- CI tests upgrading from v1.3.0 and v1.4.0 on Linux and macOS.

### Changed

- Skill descriptions route requests to the right skill ("Do NOT use for …"), trivial edits
  skip the code-solving process, and skills ask before installing Python.
- Docs: README, guides and website match the CLI and real script output (checked in CI),
  with Troubleshooting, FAQ and Roadmap sections; the website no longer needs the Tailwind
  CDN or JavaScript to show its content.
- Releases are published only after every step succeeded (draft first, Homebrew and Scoop
  updated last) and can be re-run; GitHub Actions are pinned to commit SHAs.

## [1.4.0] - 2026-10-08

### Changed

- README rewritten around install, a 30-second example per skill and accurate counts
  (323 knowledge records, 20 slash commands, 4 AI tools); website updated for `/code`,
  OpenCode, Homebrew and Scoop.
- Examples: the five placeholder templates are replaced by a worked `/code.debug` example.
- Security and conduct reports go to hoangthequyen01@gmail.com.

### Added

- Installs record what they wrote (`.think-better.json`); new `think-better update` refreshes
  installed skills and keeps files you edited (the new version is saved as `.new`; `--force`
  overwrites and keeps a `.bak`). Writes refuse symlinks.
- problem-solving-pro: Vietnamese keywords (with or without accents), real depth levels, resumable
  workspaces (`--status`, `--done`) and `/solve.resume`.
- make-decision: Vietnamese support, options read from the request, new criteria templates (tech
  stack, pricing, job offer, relocation, education, housing), weighted scoring with the smallest
  weight change that flips the winner, journal review dates, resumable workspaces and
  `/decide.resume`; the `C:\Users` journal crash and note overwrite are fixed.
- Shared stemmer: hire/hiring/hired, uncertain/uncertainty and similar forms now meet in all skills.
- Release: `VERSION` file checked against the tag, CI gates the release, SBOMs, cosign signature and
  build attestations, scheduled flake lock updates, PR title check.
- `CHANGELOG.md`.
- `scripts/test_docs.py`: fails when README or website counts drift from the skills'
  CSV files, workflows and AI targets, or when a relative link in the docs is broken.

### Removed

- `GITHUB-SETUP.md` (obsolete launch checklist), the `specs/` drafts from March and the
  unused `doc/icon.png`.

## [1.3.0] - 2026-10-08

### Added

- code-solving reads the project before planning: stack-trace frames mapped to project
  files and lines, where named symbols are defined, recent commits on those files, the
  working tree, and for reviews the diff with the risk areas it touches
  (`--context`, `--diff [BASE]`, `--no-context`) (#44).
- Task types `test`, `explain`, `security` and `quick-fix`, with `/code.test` and
  `/code.explain` (#45).
- Known errors: 44 common error messages with likely causes, first checks and the
  root-cause fix; the plan adds a "Known error" section (code-solving now has 149
  records, was 91) (#45).
- Resume saved workspaces: `--status`, `--done <step>`, `--undone <step>` and
  `/code.resume` (#46).

### Fixed

- All slash commands pass the user's text on stdin (`--stdin`) instead of the shell
  command line, so backticks, `$` and quotes in pasted errors are safe (#43).
- Saving a workspace again keeps files you already filled in; `--force` replaces them (#43).
- Sharper task-type detection for `/code`; `--detect` finds uv/Poetry/PDM/Pipenv,
  single-test commands, JS workspaces and CI check steps (#43).

## [1.2.0] - 2026-10-08

### Added

- `init --global` and `uninstall --global` install for your user account: Claude Code
  (`~/.claude/`), OpenCode (`~/.config/opencode/`) and Antigravity (`~/.gemini/config/`) (#42).

### Fixed

- `list` and `check` look in every AI tool's folders, in the project and the user account;
  Copilot, OpenCode and Antigravity installs no longer show as "not installed" (#42).

## [1.1.1] - 2026-10-08

### Added

- OpenCode slash commands in `.opencode/commands/` (#41).

## [1.1.0] - 2026-10-08

### Added

- code-solving skill: 7 steps with evidence gates for debug, feature, refactor,
  performance, flaky-test, incident, migration and review tasks, a 91-record knowledge
  base and detection of the project's test/lint/build commands. Slash commands `/code`,
  `/code.deep`, `/code.debug`, `/code.feature`, `/code.refactor`, `/code.perf`,
  `/code.review` (#38).
- Slash commands for Claude Code (`.claude/commands/`) and GitHub Copilot
  (`.github/prompts/*.prompt.md`, agent mode) (#30, #39).
- Releases with GoReleaser; this repository is its own Homebrew tap and Scoop bucket (#36).
- Releases can be started from the Actions tab (#40).
- Install scripts verify the SHA-256 checksum and accept `THINK_BETTER_VERSION` and
  `INSTALL_DIR` (#30).
- `--type` / `--category` let the AI pass its own classification to the skill scripts (#37).
- CI on Linux, macOS and Windows with lint, Python 3.9/3.13 smoke tests and installer
  checks; contributor guide, code of conduct and issue templates (#30).

### Changed

- Skills are discovered from `SKILL.md` frontmatter and mirrored with
  `go generate ./internal/skills`; the binary is built from `cmd/think-better` (#30).
- Workflows belong to the skill they run: `init --skill X` and `uninstall --skill X`
  install and remove only X's commands (#39).

### Fixed

- problem-solving-pro reasoning rules were never applied; decision types for "A vs B"
  and "A vs B vs C" (#37).
- Plans and journals are written to the project, not into the installed skill folder;
  project names are sanitized (#37).

## [1.0.3] - 2026-04-05

### Added

- Nix flake (`nix run github:HoangTheQuyen/think-better`) (#25).
- CI workflow and automatic release on tag push (#26).

### Fixed

- Workflows are installed even when a skill fails to install; the install scripts no
  longer hard-code `--ai claude`.

## [1.0.2] - 2026-03-12

### Fixed

- `init` installs the `/solve` and `/decide` workflow files for Antigravity; 1.0.1 shipped
  them without installing them (#23).

### Added

- MIT license file (#22).

## [1.0.1] - 2026-03-12

### Added

- OpenCode target (`think-better init --ai opencode`) (#8).
- `/solve` and `/decide` workflows with four depth levels (`.quick`, standard, `.deep`,
  `.exec`), step-by-step workspaces and next-step suggestions (#5).
- Landing page at thinkbetter.dev (#1, #5).

### Fixed

- Python detection on Windows and other platforms where only `python` exists (#4).
- Stale references in the User Guide and Quick Reference (#7).

## [1.0.0] - 2026-03-09

### Added

- First release: the `think-better` CLI (`init`, `list`, `check`, `uninstall`, `version`)
  for Claude Code, GitHub Copilot and Antigravity.
- make-decision and problem-solving-pro skills: BM25 search over their CSV knowledge
  bases, plan generation, comparison matrix and decision journal.
- One-line install scripts for macOS, Linux and Windows and cross-platform release binaries.

[Unreleased]: https://github.com/HoangTheQuyen/think-better/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/HoangTheQuyen/think-better/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/HoangTheQuyen/think-better/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/HoangTheQuyen/think-better/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/HoangTheQuyen/think-better/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/HoangTheQuyen/think-better/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/HoangTheQuyen/think-better/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/HoangTheQuyen/think-better/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/HoangTheQuyen/think-better/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/HoangTheQuyen/think-better/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/HoangTheQuyen/think-better/releases/tag/v1.0.0
