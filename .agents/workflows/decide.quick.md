---
description: Quick decision — fast, essential framework only. Use when user says
  "quick", "decide fast", or needs a rapid decision.
---

## Decision Making (Quick Depth)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
```

2. Run quick analysis:
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   decision type, add `--type "<decision type>"` (values are listed in SKILL.md);
   otherwise omit it and the script auto-detects.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py "$ARGUMENTS" --plan --depth quick -f markdown
```

3. Present the output, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide` | Full standard comparison |
| `/decide.deep` | Detailed comparison with alternatives |
| `/solve.quick` | Quick scan of the root problem first |
```
