---
description: Quick problem scan — fast, essential insights only. Use when user says
  "quick", "scan", "overview", or needs a fast answer.
---

## Problem Solving (Quick Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Run quick analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   problem type and context, add `--type <type> --category "<context>"` (values are listed
   in SKILL.md); otherwise omit them and the script auto-detects.
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan --depth quick -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve` | Full standard analysis |
| `/solve.deep` | Deep dive with alternatives & mental models |
| `/decide.quick` | Quick decision from this analysis |
```
