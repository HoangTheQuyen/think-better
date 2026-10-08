---
description: Executive-level problem analysis — maximum detail, all frameworks,
  mental models with full explanations. Use when user says "executive",
  "leadership", "board", "stakeholder", or needs comprehensive analysis
  for decision-makers.
---

## Problem Solving (Executive Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Run executive analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   problem type and context, add `--type <type> --category "<context>"` (values are listed
   in SKILL.md); otherwise omit them and the script auto-detects.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py "$ARGUMENTS" --plan --depth executive -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py "$ARGUMENTS" --plan --depth executive --persist --step-docs -p "<project-name>" -f markdown
```

4. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide.exec` | Executive-level decision from this analysis |
| Add "save step-by-step" | Create full markdown workspace |
| `/decide` | Compare options at standard depth |
```
