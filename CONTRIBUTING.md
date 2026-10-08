# Contributing to Think Better

Thanks for helping make AI assistants think better! This guide gets you from
clone to merged PR, and explains how to add the things people contribute most:
**skills**, **slash-command workflows**, **knowledge records**, and **AI targets**.

> Tiếng Việt: PR và issue bằng tiếng Việt hay tiếng Anh đều được chào đón.

## TL;DR

```bash
git clone https://github.com/<you>/think-better.git && cd think-better
# ...edit files under .agents/ or internal/...
make embed-prep   # mirror .agents/ into internal/skills (or: go generate ./internal/skills)
make check        # vet + Go tests + Python smoke tests — the same checks CI runs
git commit -m "feat(make-decision): add OODA loop framework"
```

No `make`? Run the three commands directly:
`go generate ./internal/skills && go test ./... && python3 scripts/smoke_test_skills.py`.

## Development setup

| Tool | Version | Used for |
|------|---------|----------|
| Go | 1.25+ (see `go.mod`) | CLI, tests, embedding |
| Python | 3.9+ | Skill scripts (standard library only — no pip installs) |
| golangci-lint | v2 (optional) | `make lint` |
| GoReleaser | v2 (optional) | `make release-snapshot` |
| Nix (optional) | flakes | `nix develop` gives you Go + Python + make |

## How the repo fits together

```
.agents/                     ← SOURCE OF TRUTH — edit here
├── skills/<skill-name>/     SKILL.md, PROMPT.md, scripts/*.py, data/*.csv
└── workflows/*.md           slash commands (/solve, /decide.deep, ...)

internal/skills/             ← GENERATED mirror of .agents/ (embedded into the binary)
├── skills/  workflows/      do not edit by hand; run `go generate ./internal/skills`
├── gen/                     the generator
├── registry.go              skills are auto-discovered from SKILL.md frontmatter
└── sources_test.go          fails if the mirror drifts or a skill is malformed

internal/targets/            AI platforms (claude, copilot, antigravity, opencode)
internal/installer/          install / uninstall / status logic
internal/cli/                subcommands
cmd/think-better/            main package
scripts/smoke_test_skills.py runs every skill's search.py in CI
```

The mirror in `internal/skills/` is committed so `go install` works without a
build step. `TestEmbeddedInSync` fails CI if you forget to regenerate it — the
error message tells you the exact command to run.

## Adding a new skill

Skills are discovered automatically — **no Go code changes are needed**.

1. Create `.agents/skills/<skill-name>/` (lowercase, kebab-case).
2. Add `SKILL.md` starting with frontmatter:

   ```markdown
   ---
   name: <skill-name>            # must equal the directory name
   description: |
     One-sentence summary shown by `think-better list`. Use when user says
     "trigger phrase", "another phrase", "cụm từ tiếng Việt", ...
   ---
   ```

   The **first sentence** of `description` is the short summary; the rest
   tells the AI when to activate the skill.
3. Add `PROMPT.md` (entry point for assistants that do not read frontmatter).
4. Optional: `scripts/search.py` and `data/*.csv`. Scripts must use only the
   Python standard library and work on Python 3.9+. Any skill with
   `scripts/search.py` is picked up by the smoke test automatically; it must
   accept a query, `--json`, `--plan`, `--format ascii|markdown` and
   `--depth quick|standard|deep|executive`. Classification and output-path
   behavior is covered by `scripts/test_skill_engines.py`; add a case there
   when you change keywords or reasoning rules.
5. `make embed-prep && make check`, then open a PR.

## Adding knowledge records (CSV rows)

Most content contributions are rows in `.agents/skills/*/data/*.csv`.

- Keep the header and column count unchanged (tests enforce a consistent column count).
- Quote fields that contain commas.
- Write in English — the AI translates queries before searching.
- Cite the source (book, paper, author) in the PR description.

## Adding or changing a workflow (slash command)

Workflows live in `.agents/workflows/<command>.md` and are installed as slash
commands for targets that support them: Antigravity and Claude Code as-is,
GitHub Copilot as `<command>.prompt.md` prompt files (agent mode,
`$ARGUMENTS` becomes `${input:task}`). A workflow belongs to the skill whose
`.agents/skills/<skill>/` path it references: it is installed and uninstalled
with that skill.

- Frontmatter must have a `description`. Do not put `: ` or ` #` in an unquoted
  value; strict YAML parsers reject it (a test checks this).
- Reference skills as `.agents/skills/<skill>/...`; the installer rewrites the
  path for each target (e.g. `.claude/skills/<skill>/...`).
- Use `$ARGUMENTS` for the user's input.
- A test fails if a workflow references a skill that does not exist.

## Adding a new AI target

1. Add an entry to `Targets` in `internal/targets/target.go`
   (`InstallPattern` must contain `{skill}`; set `WorkflowPattern` if the
   platform supports slash-command files).
2. Add the name to the tests in `internal/targets/target_test.go` and to the
   CI smoke loop in `.github/workflows/ci.yml`.
3. Document it in the README "Works with" line and the target table.

## Commits and pull requests

- Branch from `main`: `feat/...`, `fix/...`, `docs/...`.
- Use [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `refactor:`, `test:`.
  Scope with the skill or package when useful: `feat(problem-solving-pro): ...`.
- Keep PRs focused: one skill / feature / fix per PR.
- Fill in the PR template. CI must be green before review.

## Releasing (maintainers)

1. Make sure `main` is green.
2. `git tag vX.Y.Z && git push origin vX.Y.Z`
3. The `Release` workflow runs [GoReleaser](.goreleaser.yaml): it tests,
   cross-compiles, writes `checksums.txt`, publishes the GitHub Release, and
   commits the Homebrew formula (`Formula/`) and Scoop manifest (`bucket/`)
   back to `main` — this repo is its own tap and bucket. `install.sh` /
   `install.ps1` pick up the release automatically and verify the checksum.

`Formula/` and `bucket/` are generated by releases — don't edit them by hand.

Dry-run locally with `make release-snapshot` (needs
[goreleaser](https://goreleaser.com/install/)). The raw binary asset names
(`think-better-<os>-<arch>[.exe]`) are what the install scripts download —
don't change them.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report
security issues privately as described in [SECURITY.md](SECURITY.md).
