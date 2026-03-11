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
// turbo
```
cd .agents/skills/problem-solving-pro/scripts && python search.py "$ARGUMENTS" --plan --depth quick -f markdown
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
