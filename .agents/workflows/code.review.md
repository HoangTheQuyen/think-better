---
description: Review code for real defects by tracing callers, checking the review checklist and
  reporting findings with failure scenarios. Use when user asks to review a PR or code ("review
  code").
---

## Code Review

### Rules

- **The user's text**: goes between the two `THINK_BETTER_EOF_7f3a` lines of a command, exactly as
  given. It is read from stdin, so quotes, backticks and `$` in it are safe; never move it onto the
  command line or into quotes. Before running, check that no line of it is exactly
  `THINK_BETTER_EOF_7f3a`. If one is, do not use the heredoc: write the text unchanged to a
  temporary file with your file-editing tool and run the same command with `< <that file>` in place
  of the heredoc. PowerShell: see "Passing the user's text" in SKILL.md.
- **No text**: if the user gave no request with the command, use `Review the current changes` as the
  text: the plan reviews the git diff.
- **Errors**: run from the project root (use `python` if `python3` is missing). If a command fails
  (an `Error:` or `usage:` message, or a non-zero exit), show the error to the user. If it names an
  input you chose (a flag value, scores, a workspace name), fix that and re-run once; otherwise
  stop. Never present a plan the script did not produce.
- **Output**: the plan is your working method: follow its steps and gates instead of writing your
  own plan, and treat "Context from the project" as leads to verify by reading the code.
- **Language**: Respond in English. The script's output is in English: show it as it is, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: the plan already ends with a **Next steps** table for this command: show it once,
  at the end of your answer, and do not add another one.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
```

2. Generate the plan. If the user asked to save the work ("save", "step-by-step", "workspace"), run step 3 instead of this command.
   The plan includes the diff (uncommitted changes, else this branch against the default branch).
   If the user names a branch, tag or commit to compare against, add `--diff <base>`.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type review -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

3. Save instead (only when the user asked to save): the same plan, plus a workspace with one file
   per step. Replace `<project-name>` with a short name for this work; files are saved in the
   project and `/code.resume` continues them in a later session.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type review --persist --step-docs -p "<project-name>" -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

4. Work the steps in order. Before moving on, produce each step's **Gate** evidence for real
   (run the repro, the tests, the checks) and show it briefly. Never claim a gate you did not run.
   In a saved workspace, write the evidence into the step's file, then tick the gate with
   `--done <step> -p <project-name>` (see SKILL.md).

5. Finish with the hand-off from Step 7, followed by the plan's **Next steps** table (once).
