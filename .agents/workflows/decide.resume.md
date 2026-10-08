---
description: Resume a saved decision workspace (decision-plans/) at the first step that is not done
  yet. Use when user wants to continue an earlier decision ("continue the decision", "resume").
---

## Resume a Decision

### Rules

- **The user's text**: goes between the two `THINK_BETTER_EOF_7f3a` lines of a command, exactly as
  given. It is read from stdin, so quotes, backticks and `$` in it are safe; never move it onto the
  command line or into quotes. Before running, check that no line of it is exactly
  `THINK_BETTER_EOF_7f3a`. If one is, do not use the heredoc: write the text unchanged to a
  temporary file with your file-editing tool and run the same command with `< <that file>` in place
  of the heredoc. PowerShell: see "Passing the user's text" in SKILL.md.
- **No text**: if the user gave no text with the command, leave the heredoc empty: `--status` then
  resumes the most recently changed workspace.
- **Errors**: run from the project root (use `python` if `python3` is missing). If a command fails
  (an `Error:` or `usage:` message, or a non-zero exit), show the error to the user. If it names an
  input you chose (a flag value, scores, a workspace name), fix that and re-run once; otherwise
  stop. Never present a plan the script did not produce.
- **Output**: `--status` lists each step's file and whether it is done, then the **Next** step with
  its guidance. If it says there is no saved workspace, tell the user and suggest starting one with
  `/decide` and asking to save it; do not invent a workspace.
- **Language**: Respond in English. The script's output is in English: show it as it is, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: do not add a Next steps table; end with the decision, its kill criteria and the
  review date.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
```

2. Show the workspace and its next step.
   The text picks the workspace whose name or original request it matches best; with no match
   it is the most recently changed one. Add `-p <name>` if the user named a workspace.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --status <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
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
   the decision, its kill criteria and the review date:
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --journal --confidence <0-100> --review-in 30d -p <workspace> <<'THINK_BETTER_EOF_7f3a'
<the decision in one sentence, as written in 06-DECISION.md>
THINK_BETTER_EOF_7f3a
```
