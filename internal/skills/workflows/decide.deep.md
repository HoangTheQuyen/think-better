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
// turbo
```
cd .agents/skills/make-decision/scripts && python search.py "$ARGUMENTS" --plan --depth deep -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
// turbo
```
cd .agents/skills/make-decision/scripts && python search.py "$ARGUMENTS" --plan --depth deep --persist --step-docs -p "$PROJECT_NAME" -f markdown
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
