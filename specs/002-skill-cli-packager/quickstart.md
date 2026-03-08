# Quickstart: Skill CLI Packager

**Feature**: 002-skill-cli-packager  
**Date**: 2026-03-03

---

## Prerequisites

- Go 1.22+ (for building from source)
- Python 3.x (for running installed skill scripts — soft requirement)

## Build

```bash
# Clone the repository
git clone <repo-url>
cd decision-maker

# Build for current platform
make build

# Build for all platforms (linux/darwin/windows × amd64/arm64)
make build-all

# Run tests
make test
```

The binary is output to `bin/make-decision` (or `bin/make-decision.exe` on Windows).

## Usage

### Install a skill

```bash
# Install the make-decision skill for Claude
./bin/make-decision init --ai claude --skill make-decision

# Install all skills for Copilot
./bin/make-decision init --ai copilot

# Force overwrite existing installation
./bin/make-decision init --ai claude --force
```

### List available skills

```bash
# Human-readable table
./bin/make-decision list

# JSON output
./bin/make-decision list --json
```

### Check prerequisites

```bash
./bin/make-decision check
```

### Uninstall a skill

```bash
./bin/make-decision uninstall --ai claude --skill make-decision
```

## After Installation

Once installed, open your AI assistant (Claude or Copilot in VS Code) and type:

```
/make-decision <your decision problem>
```

The AI will guide you through a structured decision-making workflow.

## Development

```bash
# Run directly without building
go run ./cmd/make-decision init --ai claude

# Run tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Prepare embedded skills (copies from .github/prompts/ to skills/)
make embed-prep
```

## Project Structure

```
cmd/make-decision/main.go     # CLI entry point
internal/skills/               # Skill registry + embed
internal/installer/            # File installation logic
internal/targets/              # AI target definitions
internal/checker/              # Prerequisite checks
internal/cli/                  # Subcommand handlers
skills/                        # Build-time copy of skill files (gitignored)
Makefile                       # Build automation
```
