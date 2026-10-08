---
description: Deep coding plan with pitfalls per step, extra techniques and the full review checklist.
  Use for risky or high-impact code changes.
---

## Coding Task (Deep)

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
```

2. Generate the plan:
   Run from the project root (use `python` if `python3` is missing).
   Pick the task type yourself when you can: add `--type <type>` (debug, feature, refactor,
   performance, flaky-test, incident, migration, review); otherwise it is auto-detected.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py "$ARGUMENTS" --plan --depth deep -f markdown
```

3. Work the steps in order. Before moving on, produce each step's **Gate** evidence for real
   (run the repro, the tests, the checks) and show it briefly. Never claim a gate you did not run.

4. If user mentions "save", "persist", "step-by-step", "workspace":
   Replace `<project-name>` with a short name for this work; files are saved in the project.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py "$ARGUMENTS" --plan --depth deep --persist --step-docs -p "<project-name>" -f markdown
```

5. Finish with the hand-off from Step 7, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide` | Choose between designs; record an ADR |
| `/solve` | The root problem is outside the code |
| Add "save step-by-step" | Create a workspace file per step |
```
