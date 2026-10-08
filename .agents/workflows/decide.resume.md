---
description: Resume a saved decision workspace at the first step that is not done yet. Use when user wants to
  continue an earlier decision ("continue", "resume", "làm tiếp", "tiếp tục quyết định").
---

## Resume a Decision

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
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
python3 .agents/skills/make-decision/scripts/search.py --stdin --status <<'TASK'
$ARGUMENTS
TASK
```

3. Read the files of the steps already done: they hold the decision statement, criteria and
   scores so far. Do not redo finished steps; check that their facts still hold.

4. Continue from the step marked **Next**. Do the work with the user, write the result into the
   step's file, then mark the step done and see the following one:
```
python3 .agents/skills/make-decision/scripts/search.py --done <step> -p <workspace>
```
   Repeat until every step is done. Never mark a step done that the user has not actually settled.

5. When all steps are done, log the decision with its confidence and review date, then present
   the decision, its kill criteria and the review date in the user's language:
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --journal --confidence <0-100> --review-in 30d -p <workspace> <<'TASK'
<the decision in one sentence, as written in 06-DECISION.md>
TASK
```
