# Implementation Plan: Skill CLI Packager

**Branch**: `002-skill-cli-packager` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-skill-cli-packager/spec.md`

## Summary

Build a Go CLI tool (`make-decision`) that embeds two AI assistant skill sets (make-decision, problem-solving-pro — 25 files, ~316KB) using Go's `embed` package and installs them into the correct directory structure (`.github/prompts/<skill>/`) for Claude and GitHub Copilot. The CLI supports init, list, uninstall, and check commands with cross-platform support (Windows, macOS, Linux) via a single self-contained binary.

## Technical Context

**Language/Version**: Go 1.22+
**Primary Dependencies**: Go stdlib only (`embed`, `flag`, `os`, `path/filepath`, `fmt`, `io/fs`, `text/tabwriter`); cobra is optional — stdlib `flag` or a minimal subcommand approach is sufficient
**Storage**: Go `embed.FS` for bundled skill files; local filesystem for installation target
**Testing**: `go test` with `testing/fstest` for embed verification, temp directories for install/uninstall tests
**Target Platform**: Windows, macOS, Linux (cross-compiled via `GOOS`/`GOARCH`)
**Project Type**: CLI tool
**Performance Goals**: Installation completes in < 2 seconds for all files
**Constraints**: Single static binary, no CGO, no runtime dependencies for the CLI itself; Python 3 is a soft runtime dependency for skill scripts
**Scale/Scope**: 2 skills, 25 files, ~316KB embedded; expandable to more skills

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`.specify/memory/constitution.md`) is currently a template with no concrete principles defined. Therefore:

- **No gate violations**: No constraints to enforce
- **No complexity justifications needed**: No rules defined
- **Status**: PASS (vacuously — no rules to violate)

*Note*: When the constitution is populated with real principles, this section should be re-evaluated against those principles.

## Project Structure

### Documentation (this feature)

```text
specs/002-skill-cli-packager/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-interface.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
cmd/
└── make-decision/
    └── main.go              # Entry point, subcommand dispatch

internal/
├── skills/
│   ├── embed.go             # //go:embed directives, skill registry
│   ├── registry.go          # Skill metadata, file listings
│   └── skills_test.go       # Embed verification tests
├── installer/
│   ├── installer.go         # File copy logic, conflict detection
│   ├── uninstaller.go       # File removal logic
│   ├── status.go            # InstallStatus computation
│   └── installer_test.go    # Install/uninstall tests with temp dirs
├── targets/
│   ├── target.go            # AI target interface + registry (claude, copilot)
│   └── targets_test.go
├── checker/
│   ├── checker.go           # Prerequisites validation (Python check)
│   └── checker_test.go
└── cli/
    ├── init.go              # init subcommand handler
    ├── list.go              # list subcommand handler
    ├── uninstall.go         # uninstall subcommand handler
    ├── check.go             # check subcommand handler
    └── cli_test.go

skills/                      # Embedded skill content (symlinked or copied from .github/prompts/)
├── make-decision/
│   ├── PROMPT.md
│   ├── data/*.csv
│   └── scripts/*.py
└── problem-solving-pro/
    ├── PROMPT.md
    ├── data/*.csv
    └── scripts/*.py

go.mod
go.sum
Makefile                     # Build targets for cross-compilation
```

**Structure Decision**: Single-module Go project with `cmd/` for the entry point and `internal/` for packages. Skills are embedded from a dedicated `skills/` directory at repo root (copied from `.github/prompts/` at build time or directly embedded). This follows standard Go project layout conventions.

## Complexity Tracking

> No constitution violations to justify — constitution is not yet populated.
