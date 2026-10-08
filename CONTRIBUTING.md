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
make check        # vet + Go tests + Python tests + docs checks — the same checks CI runs
git commit -m "feat(make-decision): add OODA loop framework"
```

No `make`? Run the commands directly:
`go generate ./internal/skills && go test ./... && python3 scripts/smoke_test_skills.py && python3 scripts/test_skill_engines.py && python3 scripts/test_docs.py`.

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
internal/installer/          install / update / uninstall / status logic; manifests
                             (manifest.go) record what was written, so user edits
                             are kept; all writes refuse symlinks (safefs.go)
internal/cli/                subcommands
cmd/think-better/            main package
scripts/smoke_test_skills.py runs every skill's search.py in CI
scripts/test_docs.py         docs match the repo: counts, commands, install paths, bias names, links
scripts/test_doc_samples.py  the sample outputs in the docs match a real run
```

### When the docs checks fail

`scripts/test_docs.py` fails when a count in README.md, USER-GUIDE.md, QUICK-REFERENCE.md or
the website no longer matches the CSV files, workflows or AI targets; update the number it
names. It also runs `scripts/test_doc_samples.py`, which re-runs the requests shown as samples
(README, website, examples): if you change a knowledge base or the classification and a sample
changes, re-run the request, update the sample in the docs it names (English and Vietnamese)
and the expected values in `scripts/test_doc_samples.py`.

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
commands for targets that support them: Antigravity, Claude Code and
OpenCode (`.opencode/commands/`) as-is,
GitHub Copilot as `<command>.prompt.md` prompt files (agent mode,
`$ARGUMENTS` becomes `${input:task}`). A workflow belongs to the skill whose
`.agents/skills/<skill>/` path it references: it is installed and uninstalled
with that skill.

- Frontmatter must have a `description`. Do not put `: ` or ` #` in an unquoted
  value; strict YAML parsers reject it (a test checks this).
- Reference skills as `.agents/skills/<skill>/...`; the installer rewrites the
  path for each target (e.g. `.claude/skills/<skill>/...`).
- Use `$ARGUMENTS` for the user's input, alone on its line inside a quoted heredoc
  that the script reads with `--stdin` (a test checks this):

  ```
  python3 .agents/skills/<skill>/scripts/search.py --stdin --plan <<'THINK_BETTER_EOF_7f3a'
  $ARGUMENTS
  THINK_BETTER_EOF_7f3a
  ```

  Never write `"$ARGUMENTS"` on a command line: the user's text often holds
  backticks, `$` or quotes (pasted errors), and the shell would run or mangle them.
- A test fails if a workflow references a skill that does not exist.

## Adding a new AI target

1. Add an entry to `Targets` in `internal/targets/target.go`
   (`InstallPattern` must contain `{skill}`; set `WorkflowPattern` if the
   platform supports slash-command files; set `GlobalInstallPattern` and
   `GlobalWorkflowPattern`, relative to the home directory, if the platform
   has user-level skills, to enable `--global`). Link the docs you used in a
   comment next to the paths. If you change a path that releases already
   installed to, add the old one to `LegacyInstallPatterns`: `update` and
   `init` then move existing installs (as for Copilot's `.github/prompts/<skill>/`).
2. Add the name to the tests in `internal/targets/target_test.go` and to the
   CI smoke loop in `.github/workflows/ci.yml`.
3. Document it in the README "Works with" line, the target table and "How a skill is
   picked", the USER-GUIDE install table, and the website (`docs/index.html`);
   `scripts/test_docs.py` fails until README, guides and website mention it
   and the README and USER-GUIDE install tables show its paths.

## Commits and pull requests

- Branch from `main`: `feat/...`, `fix/...`, `docs/...`.
- Use [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `refactor:`, `test:`.
  Scope with the skill or package when useful: `feat(problem-solving-pro): ...`.
- Keep PRs focused: one skill / feature / fix per PR.
- Fill in the PR template. CI must be green before review.

## Releasing (maintainers)

1. Bump `VERSION` (e.g. `1.4.0`, no `v`) and add the release's section to
   [CHANGELOG.md](CHANGELOG.md) in a PR to `main`; merge it once `main` is green. `flake.nix` reads it, and the release refuses a tag that
   does not match it (`v1.4.0-rc.1` matches `1.4.0`).
2. Either push a tag on `main`: `git tag vX.Y.Z && git push origin vX.Y.Z`,
   or, without a local checkout, open **Actions → Release → Run workflow** on
   `main` (leave the version empty to use `VERSION`); the workflow creates the
   tag on that commit. Manual runs from other branches, and tags on commits
   that are not on `main`, are rejected.
3. The [Release workflow](.github/workflows/release.yml) first validates the
   version (tag on `main`, matches `VERSION`, not already published) and runs
   the whole CI suite on that commit (vet, tests on 3 OSes, golangci-lint,
   Python tests, upgrades from earlier releases). Then
   [GoReleaser](.goreleaser.yaml) cross-compiles, writes `checksums.txt`, SBOMs
   and a cosign signature, and uploads them to a **draft** GitHub Release:
   nothing is public yet, and `install.sh` still installs the previous release.
   Next the workflow attests build provenance for every asset (see
   [SECURITY.md](SECURITY.md#verifying-releases)). Only after the attestations
   succeed does it commit the Homebrew formula (`Formula/`) and Scoop manifest
   (`bucket/`) to `main` with `.github/scripts/publish-package-manifests.sh`
   (this repo is its own tap and bucket; skipped for pre-releases) and, as the
   very last step, publish the release. `install.sh` / `install.ps1` pick it
   up automatically and verify the checksum.
4. If a run fails, fix the cause and re-run the failed jobs (or run the
   workflow again for the same version): a tag that already exists on the same
   commit is reused, the draft is replaced, and manifests that are already up
   to date are left alone. A tag on a different commit, or a version that is
   already published, is refused.
5. After the release, run `git fetch --tags && make known-hashes` and commit the updated
   `internal/installer/known_hashes.json` in a PR to `main`. It records what
   every release tag installed, so `update` recognizes unmodified files in
   installs made by old releases (those from before manifests, v1.3.0 and
   earlier, depend on it). CI warns when a release tag is missing from it.

`Formula/` and `bucket/` are generated by releases — don't edit them by hand.

GitHub Actions in the workflows are pinned to commit SHAs (with the version in
a comment); Dependabot opens grouped `ci:` PRs to update them weekly.
GoReleaser and golangci-lint are pinned to exact versions in the workflows
(and `GOLANGCI_LINT_VERSION` in the `Makefile`); Dependabot does not touch
those, so bump them together by hand.
Dry-run locally with `make release-check` and `make release-snapshot` (needs
[goreleaser](https://goreleaser.com/install/) and, for SBOMs,
[syft](https://github.com/anchore/syft)). The raw binary asset names
(`think-better-<os>-<arch>[.exe]`) are what the install scripts download —
don't change them.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report
security issues privately as described in [SECURITY.md](SECURITY.md).
