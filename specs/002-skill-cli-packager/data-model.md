# Data Model: Skill CLI Packager

**Feature**: 002-skill-cli-packager  
**Date**: 2026-03-03  
**Source**: [spec.md](spec.md) Key Entities section + [research.md](research.md)

---

## Entity: SkillPackage

A self-contained collection of files that together form an AI assistant skill, bundled inside the CLI binary.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | string | yes | Unique identifier (e.g., `"make-decision"`, `"problem-solving-pro"`) |
| Description | string | yes | Short human-readable summary shown in `list` output |
| EntryPoint | string | yes | Relative path to the skill's main file (always `"PROMPT.md"`) |
| Files | []string | yes | List of all relative file paths within the skill |
| Dependencies | []string | no | Runtime requirements (e.g., `["python3"]`) |

### Computed Properties

| Property | Derivation |
|----------|------------|
| FileCount | `len(Files)` |
| HasScripts | Any file in `scripts/` subdirectory |
| DataFiles | Files matching `data/*.csv` |

### Relationships

- A SkillPackage contains 1+ files from the embedded `fs.FS`
- A SkillPackage can be installed to 1+ AITargets
- A SkillPackage's Name maps directly to the slash command (`/make-decision`)

### Registry (compile-time constant)

```go
var Registry = []SkillPackage{
    {
        Name:         "make-decision",
        Description:  "Structured decision-making with frameworks, biases analysis, and facilitation",
        EntryPoint:   "PROMPT.md",
        Dependencies: []string{"python3"},
    },
    {
        Name:         "problem-solving-pro",
        Description:  "Systematic problem solving with decomposition, analysis tools, and reasoning",
        EntryPoint:   "PROMPT.md",
        Dependencies: []string{"python3"},
    },
}
```

Files are dynamically discovered from the embedded `fs.FS` at runtime (not hardcoded).

---

## Entity: AITarget

A supported AI assistant platform where skills can be installed.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | string | yes | Canonical identifier (e.g., `"claude"`, `"copilot"`) |
| Aliases | []string | no | Alternative names (e.g., `["github-copilot"]`) |
| DisplayName | string | yes | Human-friendly name (e.g., `"Claude (VS Code)"`) |
| InstallPattern | string | yes | Path template: `".github/prompts/{skill}/"` |

### Validation Rules

- Name is case-insensitive for matching (stored lowercase)
- InstallPattern must contain `{skill}` placeholder
- `{skill}` is replaced with `SkillPackage.Name` at install time

### Registry (compile-time constant)

```go
var Targets = []AITarget{
    {
        Name:           "claude",
        DisplayName:    "Claude (VS Code Copilot Chat)",
        InstallPattern: ".github/prompts/{skill}/",
    },
    {
        Name:           "copilot",
        DisplayName:    "GitHub Copilot",
        InstallPattern: ".github/prompts/{skill}/",
    },
}
```

Note: Both targets currently use the same install path. The abstraction exists to support future AI targets with different conventions.

---

## Entity: InstallStatus

Represents the current state of a skill installation in a directory. This is computed at runtime, NOT persisted.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| SkillName | string | References SkillPackage.Name |
| TargetName | string | References AITarget.Name |
| InstallPath | string | Resolved absolute path (e.g., `/home/user/project/.github/prompts/make-decision/`) |
| Status | enum | `installed` \| `incomplete` \| `not-installed` |
| InstalledFiles | []string | Files that exist on disk |
| MissingFiles | []string | Files in SkillPackage but not on disk |

### Status Derivation

```
if no files exist on disk           → not-installed
if all SkillPackage.Files exist     → installed
if some files exist, some missing   → incomplete
```

### Relationships

- Computed by comparing SkillPackage.Files against filesystem at AITarget.InstallPattern
- Used by `list` command for status display
- Used by `init` command for conflict detection

---

## State Transitions

```
                    init --force
not-installed ──────────────────────► installed
      │                                    │
      │         init (no --force)          │
      └──────► prompt user ───► yes ───────┘
                    │
                    └──► no ──► (no change)

installed ──── uninstall ──────────► not-installed

incomplete ─── init ───────────────► installed (repair)
      │
      └─────── uninstall ─────────► not-installed
```

---

## No Persistent Storage

This CLI has **no database, config files, or state files**. All state is computed at runtime by inspecting the filesystem:

1. Skill registry → compiled into binary
2. AI targets → compiled into binary
3. Install status → derived by checking if files exist on disk
4. No `.make-decision.json` or lock files — keeps things simple
