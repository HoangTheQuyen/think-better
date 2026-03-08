# CLI Interface Contract: make-decision

**Feature**: 002-skill-cli-packager  
**Date**: 2026-03-03  
**Type**: Command-line interface  

---

## Binary Name

`make-decision` (or `make-decision.exe` on Windows)

## Global Behavior

- Exit code `0` on success
- Exit code `1` on error
- Errors written to stderr
- Normal output written to stdout
- Prompts written to stderr (keeps stdout clean for piping)

---

## Command: `init`

Install a skill into the current project for a specified AI assistant.

### Synopsis

```
make-decision init [--ai <target>] [--skill <name>] [--force]
```

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--ai` | string | (prompt) | AI target: `claude`, `copilot` |
| `--skill` | string | (all) | Skill to install. Omit to install all skills |
| `--force` | bool | false | Overwrite existing files without prompting |

### Output (stdout)

Success:
```
Installing skill "make-decision" for claude...
  Created .github/prompts/make-decision/PROMPT.md
  Created .github/prompts/make-decision/data/decision-frameworks.csv
  Created .github/prompts/make-decision/data/cognitive-biases.csv
  Created .github/prompts/make-decision/data/criteria-templates.csv
  Created .github/prompts/make-decision/data/decision-types.csv
  Created .github/prompts/make-decision/data/analysis-techniques.csv
  Created .github/prompts/make-decision/data/facilitation.csv
  Created .github/prompts/make-decision/scripts/core.py
  Created .github/prompts/make-decision/scripts/advisor.py
  Created .github/prompts/make-decision/scripts/search.py
  Created .github/prompts/make-decision/scripts/populate_data.py

✓ Installed 11 files to .github/prompts/make-decision/

Next steps:
  - Open your AI assistant and type /make-decision to start
  - Python 3 is required for search scripts
```

Conflict (interactive, no `--force`):
```
Skill "make-decision" is already installed at .github/prompts/make-decision/
Overwrite? [y/N]: 
```

Conflict (non-interactive, no `--force`):
```
error: skill "make-decision" already installed. Use --force to overwrite.
```

### Errors (stderr)

```
error: invalid --ai value "gpt": must be claude or copilot
error: unknown skill "foo". Available: make-decision, problem-solving-pro
error: failed to create directory .github/prompts/make-decision/: permission denied
error: --ai is required in non-interactive mode (or use MAKE_DECISION_AI env var)
```

---

## Command: `list`

Show available skills and their installation status.

### Synopsis

```
make-decision list [--json]
```

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--json` | bool | false | Output JSON instead of table |

### Output — Table (default, stdout)

```
SKILL                  DESCRIPTION                                              FILES  STATUS
make-decision          Structured decision-making with frameworks and biases    11     installed
problem-solving-pro    Systematic problem solving with analysis tools           14     not installed
```

### Output — JSON (`--json`, stdout)

```json
{
  "skills": [
    {
      "name": "make-decision",
      "description": "Structured decision-making with frameworks and biases",
      "fileCount": 11,
      "status": "installed",
      "installPath": ".github/prompts/make-decision/"
    },
    {
      "name": "problem-solving-pro",
      "description": "Systematic problem solving with analysis tools",
      "fileCount": 14,
      "status": "not-installed",
      "installPath": ""
    }
  ]
}
```

### Status Values

| Value | Meaning |
|-------|---------|
| `installed` | All skill files present on disk |
| `not-installed` | No skill files found |
| `incomplete` | Some files present, some missing |

---

## Command: `uninstall`

Remove a previously installed skill.

### Synopsis

```
make-decision uninstall [--ai <target>] --skill <name> [--force]
```

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--ai` | string | (prompt) | AI target: `claude`, `copilot` |
| `--skill` | string | (required) | Skill to remove |
| `--force` | bool | false | Skip confirmation prompt |

### Output (stdout)

```
Removing skill "make-decision" for claude...
  Removed .github/prompts/make-decision/scripts/populate_data.py
  Removed .github/prompts/make-decision/scripts/search.py
  Removed .github/prompts/make-decision/scripts/advisor.py
  Removed .github/prompts/make-decision/scripts/core.py
  Removed .github/prompts/make-decision/data/facilitation.csv
  Removed .github/prompts/make-decision/data/analysis-techniques.csv
  Removed .github/prompts/make-decision/data/decision-types.csv
  Removed .github/prompts/make-decision/data/criteria-templates.csv
  Removed .github/prompts/make-decision/data/cognitive-biases.csv
  Removed .github/prompts/make-decision/data/decision-frameworks.csv
  Removed .github/prompts/make-decision/PROMPT.md
  Removed .github/prompts/make-decision/

✓ Removed 11 files
```

### Errors (stderr)

```
error: skill "make-decision" is not installed
error: --skill is required
```

---

## Command: `check`

Validate prerequisites for installed skills.

### Synopsis

```
make-decision check
```

### Output (stdout)

```
Checking prerequisites...
  ✓ Python 3.11.5 found at /usr/bin/python3
  ✓ Skill "make-decision" installed (11 files)
  ✗ Skill "problem-solving-pro" not installed

1 warning: problem-solving-pro is not installed
```

Or when Python is missing:
```
Checking prerequisites...
  ✗ Python 3 not found
    Install from https://python.org or your package manager
  ✓ Skill "make-decision" installed (11 files)

1 warning: Python 3 required for skill scripts
```

### Exit Code

- `0` if all installed skills have their prerequisites met
- `1` if any prerequisite is missing

---

## Command: `help` / `--help` / `-h`

### Synopsis

```
make-decision help
make-decision --help
make-decision -h
```

### Output (stderr)

```
make-decision — install and manage AI decision-making skills

Usage:
  make-decision <command> [options]

Commands:
  init        Install a skill for an AI assistant
  list        Show available skills and install status
  uninstall   Remove an installed skill
  check       Verify prerequisites for installed skills
  version     Show version information
  help        Show this help message

Global options:
  --ai string     AI target: claude, copilot
  --skill string  Skill name (default: all for init, required for uninstall)
  --force         Skip confirmation prompts

Run 'make-decision <command> --help' for command-specific help.
```

---

## Command: `version` / `--version`

### Output (stdout)

```
make-decision v0.1.0 (abc1234 2026-03-03)
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MAKE_DECISION_AI` | Default AI target when `--ai` omitted | `claude` |

---

## Interactive vs Non-Interactive Behavior

| Condition | Behavior |
|-----------|----------|
| Terminal + no `--force` | Prompt before overwrite/uninstall |
| Terminal + `--force` | No prompts, proceed directly |
| Non-terminal + no `--ai` | Error: `--ai required in non-interactive mode` |
| Non-terminal + no `--force` + conflict | Error: `use --force to overwrite` |
| Non-terminal + `--force` | Proceed without prompts |
