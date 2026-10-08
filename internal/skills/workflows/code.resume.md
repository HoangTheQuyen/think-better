---
description: Resume a saved coding workspace (coding-plans/) at the first step whose gate is not met
  yet. Use when user wants to continue earlier coding work ("continue the fix", "resume", "làm tiếp
  phần code").
---

## Resume Coding Work

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
  `/code` and asking to save it; do not invent a workspace.
- **Language**: answer in the user's language. The script's output is in English: translate it when
  you present it, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: the status output has no Next steps table; add the one in step 5 once, when every
  gate is met.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
```

2. Show the workspace and its next step.
   The text picks the workspace whose name or original request it matches best; with no match
   it is the most recently changed one. Add `-p <name>` if the user named a workspace.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --status <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

3. Read the workspace files of the steps already done: they hold the decisions and evidence so far.
   Do not redo finished steps; check that their evidence still holds (re-run the Step 1 check).

4. Continue from the step marked **Next**. Produce its **Gate** evidence for real, write it into the
   step's file, then tick the gate and see the following step:
```
python3 .agents/skills/code-solving/scripts/search.py --done <step> -p <workspace>
```
   Repeat until every gate is met. Never tick a gate whose evidence you did not produce.

5. When all gates are met, finish with the hand-off file, then end with:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/code.review` | Review the finished change |
| `/code` | Start a new task |
```
