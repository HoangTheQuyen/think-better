---
description: Explain how code works by tracing a real input through it with file:line evidence,
  without changing it. Use when user asks how something works or what code does ("giải thích code").
---

## Explain Code

### Rules

- **The user's text**: goes between the two `THINK_BETTER_EOF_7f3a` lines of a command, exactly as
  given. It is read from stdin, so quotes, backticks and `$` in it are safe; never move it onto the
  command line or into quotes. Before running, check that no line of it is exactly
  `THINK_BETTER_EOF_7f3a`. If one is, do not use the heredoc: write the text unchanged to a
  temporary file with your file-editing tool and run the same command with `< <that file>` in place
  of the heredoc. PowerShell: see "Passing the user's text" in SKILL.md.
- **No text**: if the user gave no request with the command, ask what code or behavior they want
  explained and wait for the answer before running anything.
- **Errors**: run from the project root (use `python` if `python3` is missing). If a command fails
  (an `Error:` or `usage:` message, or a non-zero exit), show the error to the user. If it names an
  input you chose (a flag value, scores, a workspace name), fix that and re-run once; otherwise
  stop. Never present a plan the script did not produce.
- **Output**: the plan is your working method: follow its steps and gates instead of writing your
  own plan, and treat "Context from the project" as leads to verify by reading the code.
- **Language**: answer in the user's language. The script's output is in English: translate it when
  you present it, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: the plan already ends with a **Next steps** table for this command: show it once,
  at the end of your answer, and do not add another one.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/code-solving/SKILL.md
```

2. Generate the plan. If the user asked to save the work ("save", "step-by-step", "workspace",
   "lưu", "lưu lại", "lưu từng bước"), run step 3 instead of this command.
   Files and symbols named in the text are located under "Context from the project": start there.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type explain -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

3. Save instead (only when the user asked to save): the same plan, plus a workspace with one file
   per step. Replace `<project-name>` with a short name for this work; files are saved in the
   project and `/code.resume` continues them in a later session.
// turbo
```
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type explain --persist --step-docs -p "<project-name>" -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

4. Work the steps in order without changing any code. Back every claim with file:line you
   read or output you ran (a test, a log line); list what you could not confirm as open questions.
   In a saved workspace, write the evidence into the step's file, then tick the gate with
   `--done <step> -p <project-name>` (see SKILL.md).

5. Finish with the hand-off from Step 7, followed by the plan's **Next steps** table (once).
