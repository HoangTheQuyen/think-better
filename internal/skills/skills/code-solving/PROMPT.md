# Goal

Make code changes the way a careful senior engineer does: define done before coding, map the change, work in small verified steps, and prove the result with evidence instead of claiming it.

# code-solving

A 7-step method (Define → Decompose → Prioritize → Plan → Execute → Verify → Communicate) applied to 8 task types: debug, feature, refactor, performance, flaky-test, incident, migration and review. Every step has a **gate**: a concrete piece of evidence that must exist before moving on. The knowledge base has 91 records: debugging techniques, change techniques (feature flags, expand-contract, strangler fig…), testing strategies, design principles, engineering biases, a review checklist and hand-off templates. The script also detects the project's own test, lint and build commands.

## Prerequisites

Detect the Python command first: `python3 --version 2>/dev/null || python --version`. Use whichever works (`python` on most Windows machines) in every command below. The scripts use only the standard library.

---

## Running the Scripts

Run every command from the **project root** with the path shown, e.g.
`python3 .agents/skills/code-solving/scripts/search.py ...` (the installer adjusts this path for
your AI tool). Saved plans are written to the project, never inside the skill folder.
Saving again never overwrites files that already exist (they hold your notes); add `--force`
to replace them.

### Passing the user's text

When the query is the user's own words (a request, an error message, a pasted log), pass it on
stdin with `--stdin` instead of quoting it, so quotes, backticks and `$` never reach the shell:

```bash
python3 .agents/skills/code-solving/scripts/search.py --stdin --plan <<'TASK'
<the user's text, unchanged>
TASK
```

In PowerShell (keep `'@` at the start of its line):

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new()
@'
<the user's text, unchanged>
'@ | python .agents/skills/code-solving/scripts/search.py --stdin --plan
```

---

## How to Use This Workflow

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

### Step 2: Generate the Plan (REQUIRED)

```bash
python3 .agents/skills/code-solving/scripts/search.py "<task description>" --plan --type <type>
```

Omit `--type` to auto-detect (the plan says when it is unsure). The plan contains the 7 steps with task-specific guidance and gates, the project's own check commands, techniques, testing strategy, design principles, bias warnings, a review checklist and the hand-off template.

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
python3 .agents/skills/code-solving/scripts/search.py "<keywords>" --domain <domain>
```

| Domain | Contents |
|--------|----------|
| `debugging` | Read the error, minimal repro, recent changes, git bisect, divide and conquer, hypothesis log, tracing, differential diagnosis, stress and repeat, profiling… |
| `changes` | Thin vertical slice, spike, feature flag, preparatory refactoring, Mikado, seams, expand-contract, strangler fig, branch by abstraction, codemods |
| `testing` | Regression test first, TDD, acceptance tests, characterization, property-based, contract, snapshot, benchmark, hermetic tests, test pyramid |
| `principles` | KISS, YAGNI, DRY (rule of three), SRP, separation of concerns, dependency direction, fail fast… |
| `biases` | Anchoring, confirmation bias, streetlight effect, works on my machine, premature optimization, rewrite fallacy… |
| `review` | Correctness, edge cases, error handling, security, concurrency, performance, data safety, API compatibility, tests, readability, observability |
| `artifacts` | PR description, commit message, ADR, postmortem, design doc, bug report, review report, status update |
| `steps`, `task-types` | The method itself |

### Step 5: Save a Workspace (optional)

When the user asks to save or work step by step:

```bash
python3 .agents/skills/code-solving/scripts/search.py "<task>" --plan --type <type> --persist --step-docs -p "<short-name>"
```

This creates `coding-plans/<short-name>/` with `00-OVERVIEW.md`, `01-DEFINE.md`, `02-CHANGE-MAP.md`, `03-PLAN.md`, `04-LOG.md`, `05-VERIFY.md` and the hand-off file. Fill them in as you work.

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

- Always run Step 2 (`--plan`) before starting work on a non-trivial task.
- Do not skip, disable or weaken tests to get green; do not swallow errors to make symptoms disappear.
- Do not mix refactoring with behavior changes in one step.
- Ask the user when expected behavior or acceptance criteria are unclear, instead of guessing.

## Error Handling

If the scripts cannot run, apply the method manually: classify the task with the table above, walk the 7 steps with the gates from the Step 3 table, find the project's test command (README, CI config, package.json, Makefile), and finish with a PR description that leads with the outcome and lists the checks you ran. The knowledge base is in English; translate the user's key terms before searching.
