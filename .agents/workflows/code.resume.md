---
description: Resume a saved coding workspace at the first step whose gate is not met yet. Use when user wants to
  continue earlier coding work ("continue", "resume", "làm tiếp").
---

## Resume Coding Work

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
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
python3 .agents/skills/code-solving/scripts/search.py --stdin --status <<'TASK'
$ARGUMENTS
TASK
```

3. Read the workspace files of the steps already done: they hold the decisions and evidence so far.
   Do not redo finished steps; check that their evidence still holds (re-run the Step 1 check).

4. Continue from the step marked **Next**. Produce its **Gate** evidence for real, write it into the
   step's file, then tick the gate and see the following step:
```
python3 .agents/skills/code-solving/scripts/search.py --done <step> -p <workspace>
```
   Repeat until every gate is met. Never tick a gate whose evidence you did not produce.

5. When all gates are met, finish with the hand-off file, then append:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/code.review` | Review the finished change |
| `/code` | Start a new task |
| Add "save step-by-step" | Create a workspace file per step |
```
