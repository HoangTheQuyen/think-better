---
description: Executive-level decision analysis — maximum detail, all frameworks,
  comprehensive stakeholder briefing. Use when user says "executive",
  "leadership", "board", "stakeholder", or needs a comprehensive
  decision briefing for decision-makers.
---

## Decision Making (Executive Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
```

2. Run executive analysis:
// turbo
```
cd .agents/skills/make-decision/scripts && python search.py "$ARGUMENTS" --plan --depth executive -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
// turbo
```
cd .agents/skills/make-decision/scripts && python search.py "$ARGUMENTS" --plan --depth executive --persist --step-docs -p "$PROJECT_NAME" -f markdown
```

4. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.exec` | Executive analysis of related problems |
| Add "save step-by-step" | Create full markdown workspace |
| `/decide` | Re-analyze at standard depth for a different perspective |
```
