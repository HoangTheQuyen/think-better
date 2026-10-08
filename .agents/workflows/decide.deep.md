---
description: Deep decision analysis with detailed criteria, multiple frameworks,
  and thorough comparison. Use when user says "deep", "thorough",
  "compare carefully", or faces a high-stakes choice.
---

## Decision Making (Deep Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
```

2. Run deep analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   decision type, add `--type "<decision type>"` (values are listed in SKILL.md);
   otherwise omit it and the script auto-detects.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py "$ARGUMENTS" --plan --depth deep -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py "$ARGUMENTS" --plan --depth deep --persist --step-docs -p "<project-name>" -f markdown
```

4. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide.exec` | Executive summary for leadership/board |
| `/solve.deep` | Deep risk analysis of the chosen option |
| Add "save step-by-step" | Create markdown workspace for each step |
```
