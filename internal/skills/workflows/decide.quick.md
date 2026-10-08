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
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth quick -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. Present the output in the user's language (the plan is in English; keep option names as the
   user wrote them). The plan already ends with a **Next Steps** table: show that table once, at the end
   of your answer, and do not add another one.
