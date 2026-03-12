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
// turbo
```
cd .agents/skills/problem-solving-pro/scripts && python search.py "$ARGUMENTS" --plan --depth executive -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
// turbo
```
cd .agents/skills/problem-solving-pro/scripts && python search.py "$ARGUMENTS" --plan --depth executive --persist --step-docs -p "$PROJECT_NAME" -f markdown
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
