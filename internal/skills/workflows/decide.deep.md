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
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth deep -f markdown <<'TASK'
$ARGUMENTS
TASK
```

3. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
   Later sessions continue it with `/decide.resume`.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth deep --persist --step-docs -p "<project-name>" -f markdown <<'TASK'
$ARGUMENTS
TASK
```

4. If the user has scored the options (or asks which one wins), total the scores: use the
   plan's criteria and weights, one score (1-5) per criterion for each option, in that order.
   The output names the winner and the smallest weight change that would flip it.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --matrix -f markdown -c "<criterion>:<weight>,..." --scores "<option>:<s1>,<s2>,...;<option>:..." <<'TASK'
$ARGUMENTS
TASK
```

5. Present the output in the user's language (the plan is in English; keep option names as the
   user wrote them). The plan already ends with a **Next Steps** table: show that table once, at the end
   of your answer, and do not add another one.
