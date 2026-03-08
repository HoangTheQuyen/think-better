# Research: Skill CLI Packager

**Feature**: 002-skill-cli-packager  
**Date**: 2026-03-03  
**Purpose**: Resolve all technical decisions and establish patterns

---

## R1: Go `embed` Package for File Embedding

**Decision**: Use Go's `embed.FS` with `//go:embed all:skills` directive to bundle skill files into the binary.

**Rationale**:
- Go's `embed` package is stdlib, zero dependencies, compile-time guaranteed
- `embed.FS` implements `fs.FS` interface, enabling `fs.WalkDir` for extraction
- `all:` prefix required to include dotfiles/underscore-prefixed files if any
- Files embedded relative to the source file containing the directive

**Key Details**:
- Permissions NOT preserved — `embed.FS` reports `0o444` for all files. Must set permissions manually: `.py` → `0o755`, others → `0o644`
- No symlinks supported — files must be actual files in the embed directory
- Empty directories not preserved — created on extraction if needed
- Paths inside `embed.FS` always use forward slashes regardless of OS
- `fs.Sub()` allows rooting into a specific skill subdirectory

**Extraction Pattern**:
```go
func extractSkill(fsys fs.FS, skillName string, targetDir string) error {
    sub, _ := fs.Sub(fsys, skillName)
    return fs.WalkDir(sub, ".", func(path string, d fs.DirEntry, err error) error {
        target := filepath.Join(targetDir, filepath.FromSlash(path))
        if d.IsDir() {
            return os.MkdirAll(target, 0o755)
        }
        data, _ := fs.ReadFile(sub, path)
        return os.WriteFile(target, data, fileMode(path))
    })
}
```

**Alternatives Considered**:
- External asset directory → requires distribution of multiple files, defeats single-binary goal
- `go generate` + base64 encoding → more complex, no benefit over `embed`

---

## R2: CLI Subcommand Architecture (stdlib only)

**Decision**: Use `flag.FlagSet` per subcommand with `os.Args[1]` dispatch. No external CLI framework.

**Rationale**:
- 4 subcommands (init, list, uninstall, check) is simple enough for stdlib
- Zero external dependencies aligns with project constraints
- `flag.FlagSet` with `ContinueOnError` provides clean error handling

**Key Patterns**:
- Shared flags via `SharedFlags` struct + `addSharedFlags(fs, &sf)` helper
- `main()` calls `os.Exit(run())` — `run()` returns int for testability
- Each subcommand in its own file: `internal/cli/init.go`, `internal/cli/list.go`, etc.
- Help text: custom `printUsage()` listing all subcommands
- Per-subcommand help via `FlagSet.Usage` override

**Alternatives Considered**:
- `cobra` → overkill for 4 commands, adds external dependency
- `urfave/cli` → same reason, unnecessary complexity
- Global `flag.Parse()` → doesn't support subcommands

---

## R3: Cross-Platform File Operations

**Decision**: Use `path/filepath` for OS-specific paths, `os.MkdirAll` for directory creation, `os.WriteFile` for file writing.

**Rationale**:
- `filepath.Join` and `filepath.FromSlash` handle OS path separator conversion
- `os.MkdirAll` creates nested directories idempotently
- `os.WriteFile` atomic-enough for small files (skill files are all < 100KB)

**Key Details**:
- Line endings preserved as-is (no conversion) — source files use LF
- File permissions: Windows ignores Unix permissions, so `0o644`/`0o755` are safe to set everywhere
- Path validation: reject absolute paths and `..` components in skill file paths for security

**Alternatives Considered**:
- `io.Copy` with manual open/create → more code, no benefit for small files
- Third-party filesystem abstraction → unnecessary complexity

---

## R4: GitHub Prompts Discovery Convention

**Decision**: Install skills to `.github/prompts/<skill-name>/` with `PROMPT.md` as the entry point. Same path for both Claude and Copilot.

**Rationale**:
- Convention-based discovery: directory name becomes slash command (`/make-decision`)
- `PROMPT.md` is the canonical entry point file
- No manifest or registration needed — file presence is sufficient
- Both Claude (via VS Code Copilot Chat) and GitHub Copilot use the same `.github/prompts/` directory

**Key Details**:
- Flat prompt files: `.github/prompts/foo.prompt.md` → `/foo`
- Subdirectory skills: `.github/prompts/foo/PROMPT.md` → `/foo`
- Supporting assets (`data/`, `scripts/`) live alongside `PROMPT.md`
- VS Code `chat.promptFilesRecommendations` can optionally promote prompts
- Claude Code CLI (standalone) uses `.claude/commands/` — NOT supported in this CLI (out of scope)

**Alternatives Considered**:
- Different paths per AI target → unnecessary since both use same convention
- Generating `.prompt.md` wrapper files → adds complexity, subdirectory convention already works

---

## R5: Go Project Structure

**Decision**: Standard Go project layout with `cmd/` for entry point and `internal/` for packages.

**Rationale**:
- `cmd/make-decision/main.go` — standard Go entry point convention
- `internal/` prevents external imports, appropriate for a CLI tool
- Separate packages by responsibility: `skills`, `installer`, `targets`, `checker`, `cli`

**Structure**:
```
cmd/make-decision/main.go     # Entry point
internal/skills/               # Embed directives + skill registry
internal/installer/            # File copy/remove logic
internal/targets/              # AI target registry
internal/checker/              # Prerequisite validation
internal/cli/                  # Subcommand handlers
skills/                        # Embedded content source directory
```

**Alternatives Considered**:
- Flat `main` package → doesn't scale, harder to test
- `pkg/` directory → `internal/` is more appropriate for a CLI tool (no external consumers)

---

## R6: Terminal Interactivity Detection

**Decision**: Use `os.Stdin.Stat()` with `os.ModeCharDevice` check for TTY detection.

**Rationale**:
- Zero external dependencies
- Works on Windows, macOS, and Linux
- Covers all cases: terminal, pipe, file redirect, CI/CD

**Behavior**:
| Scenario | `isTerminal()` |
|---|---|
| Interactive terminal | `true` |
| Piped input (`echo "y" \|`) | `false` |
| File redirect (`< input.txt`) | `false` |
| CI/CD pipeline | `false` |

When non-interactive and `--force` not set: error with clear message requiring `--force`.

**Alternatives Considered**:
- `golang.org/x/term` → external dependency, overkill for simple TTY check
- Always require `--force` → poor UX in interactive terminals

---

## R7: Cross-Compilation & Distribution

**Decision**: Use `GOOS`/`GOARCH` with `CGO_ENABLED=0` for static binaries. Makefile for build automation.

**Rationale**:
- Go's built-in cross-compiler requires no additional toolchains
- `CGO_ENABLED=0` guarantees static binaries (no libc dependency)
- 6 target combinations: {linux, darwin, windows} × {amd64, arm64}

**Key Details**:
- Binary naming: `make-decision-<os>-<arch>[.exe]`
- Version injection: `-ldflags "-X main.version=v1.0.0 -X main.commit=abc123"`
- `-s -w` ldflags strip debug symbols (~30% smaller binaries)
- Makefile `build-all` target loops over platform matrix
- GitHub Actions matrix strategy for parallel CI builds

**Alternatives Considered**:
- GoReleaser → nice but adds external tool dependency, Makefile sufficient for this scope
- Docker-based builds → unnecessary, Go cross-compilation is native

---

## R8: Skill Content Organization for Embedding

**Decision**: Maintain a `skills/` directory at repo root that mirrors `.github/prompts/` skill subdirectories. Makefile copies from canonical location before build.

**Rationale**:
- Go's `//go:embed` requires files to be relative to the source file's directory
- Cannot use `..` in embed paths
- Single source of truth: `.github/prompts/<skill>/` is the canonical location
- Makefile `embed-prep` target syncs `.github/prompts/{make-decision,problem-solving-pro}` → `skills/` before build
- The `skills/` directory is gitignored (generated at build time)

**Alternatives Considered**:
- Embed directly from `.github/prompts/` → embed paths cannot use `..`, so source file would need to be at repo root
- Duplicate files permanently in `skills/` → creates two copies, sync issues
- Place Go source file next to `.github/prompts/` → non-standard layout

---

## Summary of Decisions

| # | Topic | Decision | Key Reason |
|---|-------|----------|------------|
| 1 | File embedding | Go `embed.FS` | Stdlib, compile-time safe, zero deps |
| 2 | CLI framework | stdlib `flag.FlagSet` | 4 commands, no external deps needed |
| 3 | File operations | `filepath` + `os.WriteFile` | Cross-platform, simple, sufficient |
| 4 | Install path | `.github/prompts/<skill>/` | Convention used by both Claude & Copilot |
| 5 | Project structure | `cmd/` + `internal/` | Standard Go layout |
| 6 | TTY detection | `os.ModeCharDevice` | Zero deps, cross-platform |
| 7 | Cross-compilation | `GOOS/GOARCH` + Makefile | Native Go, 6 targets |
| 8 | Embed source | `skills/` dir (build-time copy) | Go embed path constraint |
| 9 | Permissions | Extension-based mapping | embed.FS doesn't preserve perms |
| 10 | Interactive prompts | `bufio.Scanner` on stdin | Simple, no deps |
| 11 | Version injection | `-ldflags -X` | Build-time, no code generation |
| 12 | CI builds | GitHub Actions matrix | Parallel, tag-triggered |
