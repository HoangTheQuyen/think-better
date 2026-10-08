---
description: Resume a saved problem-solving workspace at the first step that is not done yet. Use when user
  wants to continue earlier problem-solving work ("continue", "resume", "pick up where we left off", "làm tiếp",
  "tiếp tục").
---

## Resume Problem Solving

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Show the workspace and its next step:
   Run from the project root (use `python` if `python3` is missing).
   Keep the request between the two `TASK` lines exactly as given: it is read from stdin, so
   quotes, backticks and `$` in it are safe. Never move it onto the command line or into quotes
   (PowerShell: see "Passing the user's text" in SKILL.md).
   The request picks the workspace whose name or original request it matches best; with no match
   it is the most recently changed one. Add `-p <name>` if the user named a workspace.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --status <<'TASK'
$ARGUMENTS
TASK
```

3. Read the files of the steps already done (start with `01-PROBLEM-DEFINITION.md`, which holds the
   original request): they hold the problem statement, the tree and the evidence so far.
   Do not redo finished steps; check that the problem statement still holds.

4. Continue from the step marked **Next**. Do the work with the user, write it into the step's file
   until its **Done when** (quality gate) is met, then tick the step and see the following one:
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --done <step> -p <workspace>
```
   Repeat until every step is done. Never tick a step whose file does not show the work.
   `--undone <step>` reopens a step.

5. When all steps are done, present the recommendation from `07-RECOMMENDATION.md`, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.exec` | Executive summary of this work for leadership |
| `/decide` | Compare the options the analysis produced |
| `/solve` | Start a new problem |
```
