# Feature Specification: Skill CLI Packager

**Feature Branch**: `002-skill-cli-packager`  
**Created**: 2026-03-03  
**Status**: Draft  
**Input**: User description: "Viết code golang để đóng gói bộ skill sau. Ví dụ sau muốn xài chỉ cần gõ: make-decision init --ai claude để install bộ skill này cho claude."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Install Skill for Claude (Priority: P1)

A developer has cloned or downloaded the decision-maker repository. They want to start using the `make-decision` skill in their project with Claude (GitHub Copilot with Claude backend). They run a single command from their project directory and the skill files are installed into the correct location so that Claude can discover and use them immediately.

**Why this priority**: This is the core value proposition — zero-friction installation of a skill into a specific AI assistant. Without this, users must manually copy files and know the correct directory structure.

**Independent Test**: Run `make-decision init --ai claude` in a fresh project directory. Verify that `.github/prompts/make-decision/` is created with PROMPT.md, all CSV data files, and all Python scripts. Verify Claude can discover `/make-decision` as a prompt.

**Acceptance Scenarios**:

1. **Given** a project directory without the skill installed, **When** user runs `make-decision init --ai claude`, **Then** all skill files are copied to `.github/prompts/make-decision/` with correct directory structure (PROMPT.md, data/*.csv, scripts/*.py)
2. **Given** the skill files are already installed, **When** user runs `make-decision init --ai claude`, **Then** the CLI detects the existing installation and prompts whether to overwrite or skip
3. **Given** the user runs `make-decision init --ai claude` with `--force` flag, **Then** existing skill files are overwritten without prompting
4. **Given** Python is not installed on the system, **When** user runs `make-decision init --ai claude`, **Then** the CLI warns that Python is required for the skill scripts and provides installation instructions

---

### User Story 2 — Install Skill for GitHub Copilot (Priority: P2)

A developer wants to use the `make-decision` skill with GitHub Copilot (VS Code). The CLI installs the skill into the Copilot-compatible location so it appears as a slash command.

**Why this priority**: Supports the second most common AI assistant. Uses the same `.github/prompts/` convention as Claude, but may need different configuration.

**Independent Test**: Run `make-decision init --ai copilot` in a project directory. Verify the skill is installed and accessible via Copilot's prompt system.

**Acceptance Scenarios**:

1. **Given** a project directory, **When** user runs `make-decision init --ai copilot`, **Then** skill files are installed to `.github/prompts/make-decision/` (same structure as Claude since Copilot uses the same convention)
2. **Given** no `--ai` flag is provided, **When** user runs `make-decision init`, **Then** the CLI checks the `MAKE_DECISION_AI` environment variable, prompts interactively if in a terminal, or errors with guidance if non-interactive

---

### User Story 3 — List Available Skills (Priority: P3)

A user wants to see what skills are available for installation and what is already installed in their project.

**Why this priority**: Discovery and status visibility. Helps users understand what they have and what's available before installing.

**Independent Test**: Run `make-decision list` and verify it shows available skills and their installation status.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** user runs `make-decision list`, **Then** a table shows all bundled skills with name, description, and install status (installed/not installed)
2. **Given** a skill is already installed, **When** user runs `make-decision list`, **Then** the installed skill shows its install path and file count

---

### User Story 4 — Uninstall Skill (Priority: P4)

A user wants to remove a previously installed skill from their project cleanly.

**Why this priority**: Cleanup capability. Lower priority because it's rarely needed, but important for completeness.

**Independent Test**: Run `make-decision uninstall --ai claude` after installing, verify all skill files are removed.

**Acceptance Scenarios**:

1. **Given** the skill is installed, **When** user runs `make-decision uninstall --ai claude`, **Then** all skill files in `.github/prompts/make-decision/` are removed
2. **Given** the skill is not installed, **When** user runs `make-decision uninstall --ai claude`, **Then** the CLI reports that no installation was found

---

### Edge Cases

- What happens when the target directory is read-only or permission denied? → CLI prints clear error with required permissions
- What happens when running from outside a git repository? → CLI works regardless, but warns if no `.github/` directory exists
- What happens when the Go binary doesn't have the skill files embedded? → Build-time validation ensures all required files are present
- What happens when partial installation exists (some files missing)? → CLI detects incomplete installation and offers to repair
- What happens on different OS (Windows, macOS, Linux)? → Go cross-compilation handles this; paths use `filepath` package for OS-appropriate separators

## Functional Requirements *(mandatory)*

### FR-001: Skill File Embedding

The CLI binary must contain all skill files (PROMPT.md, CSV data files, Python scripts) embedded at build time. Users should not need a separate download or repository clone to install a skill — the single binary is self-contained.

**Acceptance Criteria**:
- All files from `.github/prompts/make-decision/` are embedded in the binary
- All files from `.github/prompts/problem-solving-pro/` are embedded in the binary
- Embedded files preserve their relative directory structure
- Binary size includes all embedded assets
- Build fails if any expected skill files are missing

### FR-002: Init Command — Skill Installation

The `init` command copies embedded skill files to the correct location for the specified AI assistant.

**Syntax**: `make-decision init [--ai <assistant>] [--force] [--skill <name>]`

**Acceptance Criteria**:
- `--ai claude` installs to `.github/prompts/<skill-name>/` in the current working directory
- `--ai copilot` installs to `.github/prompts/<skill-name>/` in the current working directory
- `--skill` flag selects which skill to install
- Without `--skill`, installs all available skills (default behavior)
- Creates parent directories if they don't exist
- Preserves file permissions appropriate for the OS
- Outputs a summary of installed files and paths
- Returns exit code 0 on success, non-zero on failure

### FR-003: Idempotent Installation & Conflict Detection

Running `init` when files already exist must handle conflicts gracefully.

**Acceptance Criteria**:
- Detects existing installation by checking for PROMPT.md in the target directory
- Without `--force`: prompts user to confirm overwrite (interactive) or skips (non-interactive/piped)
- With `--force`: overwrites all files without prompting
- Displays what files would change before prompting
- Partial installations (missing files) are detected and reported as "incomplete — repair recommended"

### FR-004: List Command — Skill Discovery

The `list` command shows available skills and their installation status.

**Syntax**: `make-decision list [--json]`

**Acceptance Criteria**:
- Shows all bundled skills with: name, short description, file count
- For each skill, shows install status relative to current directory: "installed", "not installed", or "incomplete"
- `--json` flag outputs machine-readable JSON
- Human-readable table format by default

### FR-005: Uninstall Command — Skill Removal

The `uninstall` command removes previously installed skill files.

**Syntax**: `make-decision uninstall [--ai <assistant>] --skill <name> [--force]`

**Acceptance Criteria**:
- Removes all files in the skill's installation directory
- Removes empty parent directories up to `.github/prompts/`
- Does not remove `.github/prompts/` itself or other skills
- Confirms removal before proceeding (unless `--force` is used)
- Reports "not installed" if skill files don't exist

### FR-006: Prerequisite Validation

Before completing installation, the CLI validates that required runtime dependencies are available.

**Acceptance Criteria**:
- Checks for Python 3 availability (required by skill scripts)
- Warns (does not block) if Python is not found, with installation guidance
- Validation runs automatically during `init`, can be run standalone with `make-decision check`

### FR-007: AI Assistant Target Resolution

The CLI must support multiple AI assistant targets with correct file placement.

**Acceptance Criteria**:
- `claude` and `copilot` both map to `.github/prompts/<skill>/` (same convention)
- Future AI targets can be added without changing existing code structure
- AI target names are case-insensitive (`Claude`, `CLAUDE`, `claude` all work)
- Invalid AI target names produce a clear error listing valid options
- Default AI target when `--ai` is omitted: prompt user to choose, or use environment variable `MAKE_DECISION_AI`

### FR-008: Cross-Platform Support

The CLI must work on Windows, macOS, and Linux without modification.

**Acceptance Criteria**:
- File paths use OS-appropriate separators
- Line endings in copied files match the source (preserve as-is)
- Binary is distributable as a single executable per platform
- No external runtime dependencies for the CLI itself (Go compiles to static binary)

## Key Entities *(mandatory if data is involved)*

### Skill Package

A self-contained collection of files that together form an AI assistant skill.

**Attributes**:
- Name (string, unique identifier, e.g., "make-decision")
- Description (string, short human-readable summary)
- Files (list of relative file paths within the skill)
- Entry Point (path to PROMPT.md — the file the AI reads to activate the skill)
- Dependencies (list of runtime requirements, e.g., "python3")

### AI Target

A supported AI assistant where skills can be installed.

**Attributes**:
- Name (string, e.g., "claude", "copilot")
- Install Path Pattern (string template, e.g., ".github/prompts/{skill-name}/")
- Description (string, human-friendly name like "GitHub Copilot (Claude)")

### Install Status (computed at runtime)

Represents the current state of a skill installation. Computed by inspecting the filesystem — not persisted.

**Attributes**:
- Skill Name (references Skill Package)
- AI Target (references AI Target)
- Install Path (resolved absolute path)
- Installed Files (list of file paths that exist on disk)
- Missing Files (list of expected files not found on disk)
- Status (installed | incomplete | not-installed)

## Success Criteria *(mandatory)*

### SC-001: One-Command Installation

Users can install a decision-making skill into their AI assistant with a single command in under 5 seconds, with no manual file copying or configuration editing.

### SC-002: Zero-Configuration Operation

The CLI works immediately after download — no setup, no config files, no environment variables required for the default use case. The binary is fully self-contained.

### SC-003: Cross-Platform Reliability

The same skill installation succeeds identically on Windows, macOS, and Linux, producing correct file structures on each platform.

### SC-004: Discoverability After Installation

After running `init`, the installed skill is immediately discoverable by the target AI assistant — the user can type `/make-decision` and the AI responds with the skill's workflow.

### SC-005: Safe Re-Installation

Running the install command multiple times never corrupts existing installations. Users are informed of conflicts and can choose to overwrite or skip.

## Assumptions

- The `.github/prompts/` directory convention is used by both Claude (in VS Code) and GitHub Copilot for discovering prompt-based skills
- Users have Go installed only if building from source; end users receive pre-built binaries
- Python 3 is a soft dependency — the CLI warns but does not block installation if Python is absent
- The CLI binary name matches the primary skill name (`make-decision`) for intuitive UX
- Skills are bundled at build time using Go's `embed` package
- The current two skills (make-decision, problem-solving-pro) are the initial skill set; the architecture supports adding more skills later
- File sizes are small enough (< 1MB total) that embedding in the binary is practical

## Out of Scope

- Publishing the CLI to package managers (homebrew, apt, chocolatey) — future consideration
- Auto-update mechanism for the CLI binary
- Skill marketplace or remote skill registry
- Custom skill creation by end users
- Integration testing with actual AI assistants (manual verification only)
- Skill versioning or upgrade-in-place workflows

