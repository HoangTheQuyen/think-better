# decision-maker Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-03

## Active Technologies
- Go 1.22+ + Go stdlib only (`embed`, `flag`, `os`, `path/filepath`, `fmt`, `io/fs`, `text/tabwriter`); cobra is optional — stdlib `flag` or a minimal subcommand approach is sufficient (002-skill-cli-packager)
- Go `embed.FS` for bundled skill files; local filesystem for installation target (002-skill-cli-packager)

- Python 3.10+ (standard library only) + None - standard library only (csv, re, math, json, pathlib, argparse, collections) (001-make-decision-skill)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.10+ (standard library only): Follow standard conventions

## Recent Changes
- 002-skill-cli-packager: Added Go 1.22+ + Go stdlib only (`embed`, `flag`, `os`, `path/filepath`, `fmt`, `io/fs`, `text/tabwriter`); cobra is optional — stdlib `flag` or a minimal subcommand approach is sufficient

- 001-make-decision-skill: Added Python 3.10+ (standard library only) + None - standard library only (csv, re, math, json, pathlib, argparse, collections)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
