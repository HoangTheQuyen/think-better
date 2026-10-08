---
description: Deep problem analysis with multiple frameworks, alternatives, and detailed
  mental models. Use when user says "deep", "thorough", "all angles",
  or faces a complex/high-stakes problem.
---

## Problem Solving (Deep Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Run deep analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   problem type and context, add `--type <type> --category "<context>"` (values are listed
   in SKILL.md); otherwise omit them and the script auto-detects.
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan --depth deep -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan --depth deep --persist --step-docs -p "<project-name>" -f markdown <<'TASK'
$ARGUMENTS
TASK
```

4. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.exec` | Executive summary for leadership/stakeholders |
| `/decide.deep` | Detailed comparison of options from this analysis |
| Add "save step-by-step" | Create markdown workspace for each step |
```
