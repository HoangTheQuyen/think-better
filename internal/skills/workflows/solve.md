---
description: Analyze a problem with standard depth. Use when user says "solve",
  "analyze", "diagnose", "debug", "figure out", "what's wrong", "root cause",
  or describes a problem.
---

## Problem Solving (Standard Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Run the analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   problem type and context, add `--type <type> --category "<context>"` (values are listed
   in SKILL.md); otherwise omit them and the script auto-detects.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py "$ARGUMENTS" --plan -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py "$ARGUMENTS" --plan --persist --step-docs -p "<project-name>" -f markdown
```

4. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.deep` | Deeper analysis with more frameworks & mental models |
| `/solve.exec` | Executive summary for leadership |
| `/decide` | Switch to comparing & making a decision |
```
