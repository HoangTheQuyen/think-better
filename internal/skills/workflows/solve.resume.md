---
description: Resume a saved problem-solving workspace (solving-plans/) at the first step that is not
  done yet. Use when user wants to continue earlier problem analysis ("continue the analysis", "pick
  up where we left off").
---

## Resume Problem Solving

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
  `/solve` and asking to save it; do not invent a workspace.
- **Language**: Respond in English. The script's output is in English: show it as it is, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: the status output has no Next steps table; add the one in step 5 once, when every
  step is done.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Show the workspace and its next step.
   The text picks the workspace whose name or original request it matches best; with no match
   it is the most recently changed one. Add `-p <name>` if the user named a workspace.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --status <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
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

5. When all steps are done, present the recommendation from `07-RECOMMENDATION.md`, then end with:

```
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.exec` | Executive summary of this work for leadership |
| `/decide` | Compare the options the analysis produced |
| `/solve` | Start a new problem |
```
