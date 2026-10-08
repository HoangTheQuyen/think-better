---
description: Review code for real defects by tracing callers, checking the review checklist and reporting
  findings with failure scenarios. Use when user asks to review a PR or code ("review code").
---

## Code Review

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
```

2. Generate the plan:
   Run from the project root (use `python` if `python3` is missing).
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py "$ARGUMENTS" --plan --type review -f markdown
```

3. Work the steps in order. Before moving on, produce each step's **Gate** evidence for real
   (run the repro, the tests, the checks) and show it briefly. Never claim a gate you did not run.

4. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py "$ARGUMENTS" --plan --type review --persist --step-docs -p "<project-name>" -f markdown
```

5. Finish with the hand-off from Step 7, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/code.debug` | Fix a defect the review found |
| `/decide` | Settle a design disagreement |
| Add "save step-by-step" | Create a workspace file per step |
```
