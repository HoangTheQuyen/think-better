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
   Run from the project root (use `python` if `python3` is missing). If you can tell the
   decision type, add `--type "<decision type>"` (values are listed in SKILL.md);
   otherwise omit it and the script auto-detects.
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth executive -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth executive --persist --step-docs -p "<project-name>" -f markdown <<'TASK'
$ARGUMENTS
TASK
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
