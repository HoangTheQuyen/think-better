---
description: Refactor safely without changing behavior, using characterization tests and small green steps.
  Use when user asks to refactor, clean up or restructure code ("tái cấu trúc").
---

## Refactor

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
```

2. Generate the plan:
   Run from the project root (use `python` if `python3` is missing).
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type refactor -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. Work the steps in order. Before moving on, produce each step's **Gate** evidence for real
   (run the repro, the tests, the checks) and show it briefly. Never claim a gate you did not run.

4. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type refactor --persist --step-docs -p "<project-name>" -f markdown <<'TASK'
$ARGUMENTS
TASK
```

5. Finish with the hand-off from Step 7, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/code.deep` | Deeper plan: pitfalls per step, full review checklist |
| `/decide` | Choose between designs; record an ADR |
| Add "save step-by-step" | Create a workspace file per step |
```
