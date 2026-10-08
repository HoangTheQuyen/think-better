---
description: Executive-level decision analysis with maximum detail, all frameworks, comprehensive
  stakeholder briefing. Use when user says "executive", "leadership", "board", "stakeholder", or
  needs a comprehensive decision briefing for decision-makers. Not for ranking tasks inside a code
  change (use /code) or for finding a root cause (use /solve).
---

## Decision Making (Executive Depth)

### Rules

- **The user's text**: goes between the two `THINK_BETTER_EOF_7f3a` lines of a command, exactly as
  given. It is read from stdin, so quotes, backticks and `$` in it are safe; never move it onto the
  command line or into quotes. Before running, check that no line of it is exactly
  `THINK_BETTER_EOF_7f3a`. If one is, do not use the heredoc: write the text unchanged to a
  temporary file with your file-editing tool and run the same command with `< <that file>` in place
  of the heredoc. PowerShell: see "Passing the user's text" in SKILL.md.
- **No text**: if the user gave no request with the command, ask what decision they face and which
  options they are weighing and wait for the answer before running anything.
- **Errors**: run from the project root (use `python` if `python3` is missing). If a command fails
  (an `Error:` or `usage:` message, or a non-zero exit), show the error to the user. If it names an
  input you chose (a flag value, scores, a workspace name), fix that and re-run once; otherwise
  stop. Never present a plan the script did not produce.
- **Output**: present the plan: it is the analysis, so do not replace it with your own. If it says
  no decision type matched, re-run with `--type` (values are in the note and in SKILL.md) before
  presenting. Keep option names exactly as the user wrote them.
- **Language**: answer in the user's language. The script's output is in English: translate it when
  you present it, and keep commands, flags, file names and option names exactly as written.
- **Next steps**: the plan already ends with a **Next steps** table for this command: show it once,
  at the end of your answer, and do not add another one.

### Steps

1. Read the skill instructions:
// turbo
```
cat .agents/skills/make-decision/SKILL.md
```

2. Run the analysis. If the user asked to save the work ("save", "step-by-step", "workspace", "lưu",
   "lưu lại", "lưu từng bước"), run step 3 instead of this command.
   If you can tell the decision type, add `--type "<decision type>"` (values are listed in
   SKILL.md); otherwise omit it and the script auto-detects.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth executive -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

3. Save instead (only when the user asked to save): the same plan, plus a workspace with one file
   per step. Replace `<project-name>` with a short name for this work; files are saved in the
   project and `/decide.resume` continues them in a later session.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --depth executive --persist --step-docs -p "<project-name>" -f markdown <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

4. Score the options only if the user has scored them or asks which one wins: use the
   plan's criteria and weights, one score (1-5) per criterion for each option, in that order.
   It totals the scores and names the winner and the smallest weight change that would flip it.
// turbo
```
python3 .agents/skills/make-decision/scripts/search.py --stdin --matrix -f markdown -c "<criterion>:<weight>,..." --scores "<option>:<s1>,<s2>,...;<option>:..." <<'THINK_BETTER_EOF_7f3a'
$ARGUMENTS
THINK_BETTER_EOF_7f3a
```

5. Present the plan (and the scores, if any) in the user's language.
