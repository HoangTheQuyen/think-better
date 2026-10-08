---
description: Make a decision with standard analysis depth. Use when user says
  "decide", "choose", "compare", "which one", "should I", "weigh options",
  "trade-off", "pros and cons", "help me pick", "evaluate", "select",
  or describes any choice between 2+ alternatives.
---

## Decision Making (Standard Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
```

2. Run the analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   decision type, add `--type "<decision type>"` (values are listed in SKILL.md);
   otherwise omit it and the script auto-detects.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py "$ARGUMENTS" --plan -f markdown
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py "$ARGUMENTS" --plan --persist --step-docs -p "<project-name>" -f markdown
```

4. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide.deep` | More detailed comparison with additional criteria & frameworks |
| `/decide.exec` | Executive-level analysis for board/leadership |
| `/solve` | Deep-dive into the problem before deciding |
```
