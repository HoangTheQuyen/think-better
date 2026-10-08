---
description: Explain how code works by tracing a real input through it with file:line evidence, without changing
  it. Use when user asks how something works or what code does ("giải thích code").
---

## Explain Code

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
   Files and symbols named in the request are located under "Context from the project": start there.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type explain -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. Work the steps in order without changing any code. Back every claim with file:line you
   read or output you ran (a test, a log line); list what you could not confirm as open questions.

4. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type explain --persist --step-docs -p "<project-name>" -f markdown <<'TASK'
$ARGUMENTS
TASK
```

5. Finish with the hand-off from Step 7, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/code.debug` | Fix a bug the explanation turned up |
| `/decide` | Weigh a design change the explanation suggests |
| Add "save step-by-step" | Create a workspace file per step |
```
