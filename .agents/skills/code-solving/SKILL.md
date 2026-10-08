---
name: code-solving
description: |
  Structured coding workflow for non-trivial code work: debug, build features, refactor, optimize, migrate and review code through 7 steps with evidence-based quality gates. Use when user says
  "fix this bug", "debug this", "exception", "stack trace", "crash", "the code is not working",
  "add a feature", "refactor", "clean up this code", "the code is slow", "memory leak",
  "flaky test", "CI is failing", "production is down", "upgrade the dependency", "migrate",
  "review my code", "write tests", "sửa lỗi", "bị lỗi", "thêm tính năng", "tái cấu trúc",
  "tối ưu code", "code chạy chậm", "nâng cấp thư viện", "review code".
  Trivial edits (a typo, a rename, a one-line change with an obvious result) do not need this
  process; just make the change.
  Do NOT use for problems outside the code (business, product, process; use problem-solving-pro)
  or for weighing alternatives such as two designs or libraries (use make-decision).
---

# Goal

Make code changes the way a careful senior engineer does: define done before coding, map the change, work in small verified steps, and prove the result with evidence instead of claiming it.

# code-solving

A 7-step method (Define → Decompose → Prioritize → Plan → Execute → Verify → Communicate) applied to 12 task types: debug, feature, refactor, performance, flaky-test, incident, migration, review, test, explain, security and quick-fix. Every step has a **gate**: a concrete piece of evidence that must exist before moving on. The knowledge base has 149 records: debugging techniques, change techniques (feature flags, expand-contract, strangler fig…), testing strategies, design principles, engineering biases, a review checklist, hand-off templates and 44 common error messages across languages with their likely causes. The script also detects the project's own test, lint and build commands.

## Prerequisites

Detect the Python command first: `python3 --version 2>/dev/null || python --version`. Use whichever works (`python` on most Windows machines) in every command below. The scripts use only the standard library. If neither works, tell the user that Python 3.9+ is needed and ask before installing anything; do not install it yourself.

---

## Running the Scripts

Run every command from the **project root** with the path shown, e.g.
`python3 .agents/skills/code-solving/scripts/search.py ...` (the installer adjusts this path for
your AI tool). Saved plans are written to the project, never inside the skill folder.
Saving again never overwrites files that already exist (they hold your notes); add `--force`
to replace them.

### Passing the user's text

When the query is the user's own words (a request, an error message, a pasted log), pass it on
stdin with `--stdin` instead of quoting it, so quotes, backticks and `$` never reach the shell.
Every example below does this.

Use exactly this delimiter, `THINK_BETTER_EOF_7f3a`, quoted as shown:

```bash
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan <<'THINK_BETTER_EOF_7f3a'
<the user's text, unchanged>
THINK_BETTER_EOF_7f3a
```

**Check the text first.** The heredoc ends at the first line that is exactly `THINK_BETTER_EOF_7f3a`;
anything after it would run as shell commands. If a line of the user's text is exactly that
delimiter, do not use the heredoc: write the text unchanged to a temporary file with your
file-editing tool (not the shell), run `python3 .agents/skills/code-solving/scripts/search.py --stdin --plan < <file>`, then delete the file.

In PowerShell (keep `'@` at the start of its line):

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new()
@'
<the user's text, unchanged>
'@ | python .agents/skills/code-solving/scripts/search.py --stdin --plan
```

The here-string ends at a line that starts with `'@`. If a line of the user's text starts with
`'@`, write the text to a file instead and run
`Get-Content -Raw -Encoding UTF8 <file> | python .agents/skills/code-solving/scripts/search.py --stdin --plan`.

---

## How to Use This Workflow

**Language:** answer in the user's language. The scripts' output is in English: translate it
when you present it, and keep commands, flags, file names and option names exactly as written.

If the user has not said what they want done, ask before running anything. Trivial edits (a typo,
a rename, a one-line change with an obvious result) do not need the plan: make the change and
show the check that proves it.

### Step 1: Classify the Task

Pick the type yourself; you understand the request better than keyword matching.

| Type | Use when |
|------|----------|
| `debug` | Wrong result, error, exception or crash with an unknown cause |
| `feature` | Adding behavior that does not exist yet |
| `refactor` | Changing structure without changing behavior |
| `performance` | Too slow, too much memory, does not scale |
| `flaky-test` | A test or CI job fails sometimes or only in CI |
| `incident` | Production is broken and users are affected now |
| `migration` | Upgrading a dependency or moving code/data to another system or version |
| `review` | Assessing a change for defects and risks |
| `test` | Writing tests for existing code or raising coverage |
| `explain` | Understanding how existing code works, without changing it |
| `security` | Fixing a vulnerability, an injection, a leaked secret or a vulnerable dependency |
| `quick-fix` | A few-line change with an obvious result (typo, text, config value); the plan keeps only Define, Execute, Verify and Communicate |

### Step 2: Generate the Plan (REQUIRED)

```bash
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type <type> -f markdown <<'THINK_BETTER_EOF_7f3a'
<the user's request, unchanged>
THINK_BETTER_EOF_7f3a
```

If the user asked to save the work ("save", "step-by-step", "workspace", "lưu", "lưu lại",
"lưu từng bước"), run the Step 5 command instead of this one: it prints the same plan.

Omit `--type` to auto-detect (the plan says when it is unsure). The plan contains the 7 steps with task-specific guidance and gates, the project's own check commands, techniques, testing strategy, design principles, bias warnings, a review checklist and the hand-off template.

The plan opens with **Context from the project**: facts the script found in the code and git, so Step 2 starts from them instead of a blank search. Pass the user's full error output and stack trace in the request; the script reads it.

| Context | Found from |
|---------|------------|
| Where the error points | Stack-trace and compiler-error frames (Python, JS/TS, Go, Java/Kotlin, C#, Rust, …) resolved to project files, with the source line; library frames are dropped |
| Files and symbols | File names and identifiers in the request: where each symbol is defined and how many files mention it |
| Recent commits | The last commits touching those files (regressions usually start there) |
| Working tree | Branch and uncommitted changes |
| Diff (reviews) | Changed files with line counts, and the review areas they touch (security, data safety, API compatibility, concurrency, error handling, performance, observability, missing tests); those areas go first in the review checklist |

Reviews include the diff automatically: uncommitted changes if there are any, else the branch against the default branch, else the last commit. Name a base with `--diff <base>` (a branch, tag or commit). Skip all lookups with `--no-context`. To see only the context, run `--stdin --context` with the user's text in the same heredoc.

Treat the context as leads to verify, not conclusions: read the code at each location before relying on it.

When the request contains a known error message (for example `Cannot read properties of undefined`, `nil pointer dereference`, `ModuleNotFoundError`), the plan adds a **Known error** section with its meaning, likely causes, what to check first and the root-cause fix. The likely causes pre-fill the hypothesis log of a saved workspace.

Depth: `--depth quick` (Define, Execute, Verify only), `standard` (default), `deep` (pitfalls per step, extra techniques, full review checklist), `executive` (deep plus a stakeholder summary).

To see only the project's commands: `python3 .agents/skills/code-solving/scripts/search.py --detect`

### Step 3: Work the Steps, Gate by Gate

Go through the steps in order and keep the user informed in short updates. For each step:

1. Do the step using the task-specific guidance in the plan.
2. Produce the gate's evidence for real: run the repro, run the tests, read the code.
3. Show the evidence briefly (the command and the relevant output lines), then move on.

| Step | Gate (evidence required) |
|------|--------------------------|
| 1. Define | A check that fails today: failing test, repro command, benchmark baseline or acceptance criteria |
| 2. Decompose | Change map: files and functions involved and their callers |
| 3. Prioritize | Ordered work list; the first slice can be finished and verified alone |
| 4. Plan | Each task has a proving test or check and a rollback |
| 5. Execute | Small steps, each ending green; a log of hypotheses or progress |
| 6. Verify | The Step 1 check passes; the project's checks are green; review checklist done |
| 7. Communicate | Hand-off artifact (PR description, postmortem, design doc or review report) |

**Never claim a gate is met without having produced its evidence in this session.** If a command cannot run (missing tool, no network, no test suite), say so plainly and say what you did instead.

For small tasks, keep the steps light, but do not drop Define and Verify.

### Step 4: Deep-Dive Searches

```bash
python3 .agents/skills/code-solving/scripts/search.py --stdin --domain <domain> <<'THINK_BETTER_EOF_7f3a'
<keywords>
THINK_BETTER_EOF_7f3a
```

| Domain | Contents |
|--------|----------|
| `debugging` | Read the error, minimal repro, recent changes, git bisect, divide and conquer, hypothesis log, tracing, differential diagnosis, stress and repeat, profiling, read the tests… |
| `changes` | Thin vertical slice, spike, feature flag, preparatory refactoring, Mikado, seams, expand-contract, strangler fig, branch by abstraction, codemods, dependency upgrade for a vulnerability |
| `testing` | Regression test first, TDD, acceptance tests, characterization, property-based, contract, snapshot, benchmark, hermetic tests, test pyramid, mutation testing, coverage gap analysis |
| `principles` | KISS, YAGNI, DRY (rule of three), SRP, separation of concerns, dependency direction, fail fast, validate at the boundary, least privilege… |
| `biases` | Anchoring, confirmation bias, streetlight effect, works on my machine, premature optimization, rewrite fallacy, coverage theater, illusion of understanding… |
| `review` | Correctness, edge cases, error handling, security, concurrency, performance, data safety, API compatibility, tests, readability, observability |
| `artifacts` | PR description, commit message, ADR, postmortem, design doc, bug report, review report, status update, code explanation, security fix note |
| `errors` | 44 common error messages (JS/TS, Python, Go, Java, C#, Rust, SQL, infrastructure): meaning, likely causes, first checks, fix |
| `steps`, `task-types` | The method itself |

### Step 5: Save a Workspace (optional)

When the user asks to save or work step by step ("save", "step-by-step", "workspace", "lưu",
"lưu lại", "lưu từng bước"), run this instead of the Step 2 command, not after it:

```bash
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan --type <type> --persist --step-docs -p "<short-name>" -f markdown <<'THINK_BETTER_EOF_7f3a'
<the user's request, unchanged>
THINK_BETTER_EOF_7f3a
```

This creates `coding-plans/<short-name>/` with `00-OVERVIEW.md`, `01-DEFINE.md`, `02-CHANGE-MAP.md`, `03-PLAN.md`, `04-LOG.md`, `05-VERIFY.md` and the hand-off file. Fill them in as you work, and tick each gate once its evidence is in the file:

```bash
python3 .agents/skills/code-solving/scripts/search.py --done <step> -p "<short-name>"   # 1-7 or define, decompose, ...
```

### Step 6: Resume Later

A saved workspace is how work continues in a new session (`/code.resume`):

```bash
python3 .agents/skills/code-solving/scripts/search.py --stdin --status [-p "<short-name>"] <<'THINK_BETTER_EOF_7f3a'
<the user's text, or nothing>
THINK_BETTER_EOF_7f3a
```

It shows each step's file, whether it was filled in and whether its gate is ticked, then the **next** step with its guidance and gate. Without `-p`, it picks the workspace whose name or request matches the text given on stdin, else the most recently changed one. Read the files of finished steps before continuing, re-run the Step 1 check, and never tick a gate whose evidence you did not produce. `--undone <step>` reopens a gate.

---

## When to Use the Other Skills

- **Two or more designs with real trade-offs** (library, database, architecture): use **make-decision** (`/decide`) and record the choice as an ADR.
- **The root problem is not in the code** (process, product, business metrics): use **problem-solving-pro** (`/solve`).

---

## Key Principles

1. **Define done before writing code**: a check that fails today and must pass when done.
2. **Read before you change**: trace the real call path; do not guess structure from names.
3. **Small steps, always green**: one change, run the checks, commit.
4. **Root cause, not symptom**: a fix without a failing test first is a guess.
5. **Measure, don't assume**: for performance, profiles and numbers decide.
6. **Evidence over claims**: every "done" and "passes" is backed by output you ran.
7. **Reversible first**: flags, expand-contract and rollbacks before irreversible steps.
8. **Hand it over cleanly**: outcome first, evidence, risks, rollback.

## Constraints

- Always run Step 2 (`--plan`) before starting work on a non-trivial task; trivial edits (typo, rename, one-line change) skip it.
- Do not skip, disable or weaken tests to get green; do not swallow errors to make symptoms disappear.
- Do not mix refactoring with behavior changes in one step.
- Ask the user when expected behavior or acceptance criteria are unclear, instead of guessing.

## Error Handling

If a command fails (an `Error:` or `usage:` message, or a non-zero exit), show the error to the
user. If it names an input you chose (a flag value, scores, a workspace name), fix that and
re-run; otherwise stop. Never present a plan the script did not produce.

If Python is missing and the user does not want to install it, you may apply the method manually,
saying clearly that the script did not run: classify the task with the table above, walk the 7 steps with the gates from the Step 3 table, find the project's test command (README, CI config, package.json, Makefile), and finish with a PR description that leads with the outcome and lists the checks you ran. The knowledge base is in English; translate the user's key terms before searching.
