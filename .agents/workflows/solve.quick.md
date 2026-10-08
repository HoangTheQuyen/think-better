---
description: Quick problem scan with fast, essential insights only. Use when user says "quick",
  "scan", "overview", or needs a fast answer to a problem. Not for bugs in code (use /code.debug) or
  choosing between options (use /decide).
---

## Problem Solving (Quick Depth)

### Rules

- **The user's text**: goes between the two `THINK_BETTER_EOF_7f3a` lines of a command, exactly as
  given. It is read from stdin, so quotes, backticks and `$` in it are safe; never move it onto the
  command line or into quotes. Before running, check that no line of it is exactly
  `THINK_BETTER_EOF_7f3a`. If one is, do not use the heredoc: write the text unchanged to a
  temporary file with your file-editing tool and run the same command with `< <that file>` in place
  of the heredoc. PowerShell: see "Passing the user's text" in SKILL.md.
- **No text**: if the user gave no request with the command, ask what problem they want to work on
  and wait for the answer before running anything.
- **Errors**: run from the project root (use `python` if `python3` is missing). If a command fails
  (an `Error:` or `usage:` message, or a non-zero exit), show the error to the user. If it names an
  input you chose (a flag value, scores, a workspace name), fix that and re-run once; otherwise
  stop. Never present a plan the script did not produce.
- **Output**: present the plan: it is the analysis, so do not replace it with your own. If it says
  no type or context matched, re-run with `--type` / `--category` (values are in the note and in
  SKILL.md) before presenting.
- **Language**: answer in the user's language. The script's output is in English: translate it when
  you present it, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: the plan already ends with a **Next steps** table for this command: show it once,
  at the end of your answer, and do not add another one.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/problem-solving-pro/SKILL.md
```

2. Run the analysis. To save the work step by step, use `/solve` instead.
   If you can tell the problem type and context, add `--type <type> --category "<context>"`
   (values are listed in SKILL.md); otherwise omit them and the script auto-detects.
// turbo
```
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan --depth quick -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

3. Present the plan in the user's language, then help the user work through its first step.
