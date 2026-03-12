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
// turbo
```
cd .agents/skills/problem-solving-pro/scripts && python search.py "$ARGUMENTS" --plan -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
// turbo
```
cd .agents/skills/problem-solving-pro/scripts && python search.py "$ARGUMENTS" --plan --persist --step-docs -p "$PROJECT_NAME" -f markdown
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
