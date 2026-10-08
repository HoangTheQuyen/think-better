# User Guide: How to Use Think Better

How to install the three bundled skills, use their slash commands, run their scripts yourself,
and fix the usual problems. For a one-page summary see the [Quick Reference](QUICK-REFERENCE.md).

---

## 🚀 Quick Start (5 minutes)

### 1. Download and Install

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex

# Homebrew / Scoop / go install / Nix: see the README

# Or build from source:
git clone https://github.com/HoangTheQuyen/think-better.git && cd think-better
make build          # Linux/macOS: writes bin/think-better
.\build.ps1         # Windows: writes bin\think-better.exe
```

### 2. Install the Skills in Your Project

Run this in your project's root folder:

```bash
# For Claude Code
think-better init --ai claude

# For GitHub Copilot
think-better init --ai copilot

# For Antigravity
think-better init --ai antigravity

# For OpenCode
think-better init --ai opencode

# For every project at once (GitHub Copilot: the skills only, not the slash commands)
think-better init --ai claude --global

# Only one skill (its slash commands come with it)
think-better init --ai claude --skill code-solving

# Without a slash command you do not want (repeatable or comma-separated; remembered)
think-better init --ai claude --exclude-command code.perf

# See what would be written first
think-better init --ai claude --dry-run
```

Where the files go:

| AI tool | Skills | Slash commands | `--global` |
|---------|--------|----------------|------------|
| Claude Code | `.claude/skills/<skill>/` | `.claude/commands/` | `~/.claude/skills/`, `~/.claude/commands/` |
| GitHub Copilot | `.github/skills/<skill>/` | `.github/prompts/*.prompt.md` | `~/.copilot/skills/` (skills only) |
| Antigravity | `.agents/skills/<skill>/` | `.agents/workflows/` | `~/.gemini/config/skills/`, `~/.gemini/config/workflows/` |
| OpenCode | `.opencode/skills/<skill>/` | `.opencode/commands/` | `~/.config/opencode/skills/`, `~/.config/opencode/commands/` |

`--global` for GitHub Copilot installs the skills only: VS Code keeps user-level prompt files in
your profile folder, which differs per OS and profile, so install the slash commands per project
(`think-better init --ai copilot`). Releases up to v1.4.0 put Copilot's skills in
`.github/prompts/<skill>/`; `think-better update` (or `init`) moves them to `.github/skills/<skill>/`.

Run `init` in the project root: it installs into the current folder, and warns when a parent
folder already has an install. In your home directory, `think-better init --ai claude` is the
same as `--global` (`~/.claude/` is the user-level install), and the CLI says so.

### 3. Keep the Skills Up to Date

After upgrading the `think-better` binary, update every install (this project and `--global`) at once:

```bash
think-better check            # installed / outdated / modified / incomplete, per location (--json, --strict)
think-better update --dry-run # show what would change
think-better update           # apply (limit with --ai, --skill or --global)
think-better diff             # what changed in the files you edited (their .new versions)
```

`update`, `check`, `list`, `diff` and `uninstall` work from any folder inside the project: they
look upward for the project's install (up to the repository root, never into your home directory)
and print `note: using the project at ...`.

Each install records what it wrote in `.think-better.json` (and `.think-better-workflows.json`
next to the slash commands). Files you edited are never overwritten silently: `update` (and `init`
on an existing install) keeps them and writes the new version next to them as `<file>.new`;
`--force` replaces them after saving yours as `<file>.bak`. Installs made by v1.3.0 or earlier,
before these manifests existed, are recognized too: files you did not change are simply updated.
`think-better diff` shows each edited file against its `.new` (see
[Troubleshooting](#troubleshooting) for what to do next).

A slash command you deleted comes back on `update`, which lists the ones it restored. To keep one
out for good, exclude it: `think-better update --exclude-command code.perf` (repeatable or
comma-separated, e.g. `--exclude-command code.perf,code.test`). The choice is stored in the
workflow manifest, so later updates remember it; `--include-command code.perf` installs it again.

### 4. Open Your AI Assistant

- **Claude Code:** open Claude Code (terminal, IDE extension or desktop) in the project
- **GitHub Copilot:** open VS Code and switch Copilot Chat to **agent mode**; the skills are in `.github/skills/`, the commands are prompt files in `.github/prompts/`
- **OpenCode:** run `opencode` in the project; the commands are in `.opencode/commands/`
- **Antigravity:** open the project in Antigravity; the commands are in `.agents/workflows/`

### 5. Start Using

Type a slash command, or describe the problem in your own words:

```
/decide.deep Should we migrate to microservices?
/solve.quick Signups dropped 15% after the pricing change
/code.debug TypeError in checkout after the last deploy
"Should we migrate to microservices?"
```

**Natural language** works in every supported tool, because each loads the skills by their
description: Claude Code, OpenCode, Antigravity and GitHub Copilot (agent mode, skills in
`.github/skills/`) pick the skill from its trigger phrases ("should I", "root cause",
"fix this bug", ...). A slash command picks the skill and the
depth for certain.

### All slash commands

| Skill | Command | Use it for |
|-------|---------|------------|
| make-decision | `/decide.quick` | A fast scan: options, framework, top criteria, two biases |
| | `/decide` | The default decision plan |
| | `/decide.deep` | High stakes: pre-mortem, sensitivity, information to gather |
| | `/decide.exec` | A recommendation-first brief for leadership |
| | `/decide.resume` | Continue a saved decision workspace (no text: the latest) |
| problem-solving-pro | `/solve.quick` | A short scan of a problem |
| | `/solve` | The default 7-step plan |
| | `/solve.deep` | Alternatives, more mental models and pitfalls |
| | `/solve.exec` | Adds an executive summary (SCR), key risks and the decision needed |
| | `/solve.resume` | Continue a saved problem workspace (no text: the latest) |
| code-solving | `/code` | Any code change; the task type is detected |
| | `/code.deep` | The same with more techniques and the full review checklist |
| | `/code.debug` | Bugs and crashes: a failing test first, then the fix |
| | `/code.feature` | A feature in small tested slices |
| | `/code.refactor` | Better structure, same behavior |
| | `/code.perf` | Measure, optimize, measure again |
| | `/code.review` | Review the diff and the risk areas it touches (no text: your current changes) |
| | `/code.test` | Tests that can actually fail |
| | `/code.explain` | How code works, with file:line evidence, without changing it |
| | `/code.resume` | Continue a saved coding workspace (no text: the latest) |

The other commands ask what you need when you type them without text. Each skill also knows
what it is not for and points you to the right one: bugs and code changes go to `/code*`,
choices between options to `/decide*`, business and other non-code problems to `/solve*`. The plan
the script prints is in English.

Add *"save step-by-step"* to any request to get a Markdown workspace with one file per step:
`decision-plans/<name>/`, `solving-plans/<name>/` or `coding-plans/<name>/`. Saving again keeps the
files you already filled in.

---

## 📚 Bundled Skills

### Running the scripts yourself

Your AI runs the skill scripts for you. To run them yourself, work from your **project root**
and call the script by its path (Python 3, standard library only; on Windows use `python`):

```bash
# Paths for a Claude Code install. Other tools: .opencode/skills/..., .agents/skills/...,
# .github/skills/... (Copilot); --global installs: see the table in Quick Start.
DECIDE=.claude/skills/make-decision/scripts/search.py
SOLVE=.claude/skills/problem-solving-pro/scripts/search.py
CODE=.claude/skills/code-solving/scripts/search.py

python3 $DECIDE "Postgres vs MongoDB vs DynamoDB for our order service" --plan
```

PowerShell: `$DECIDE = ".claude/skills/make-decision/scripts/search.py"; python $DECIDE "..." --plan`.

Plans, workspaces and journals are written to the folder you run from (or `-o <dir>`), never
inside the skill folder. For text with quotes, backticks or `$`, pass it on stdin with `--stdin`
(the slash commands always do):

```bash
python3 $DECIDE --stdin --plan <<'THINK_BETTER_EOF_7f3a'
Should we "rewrite" the $billing service?
THINK_BETTER_EOF_7f3a
```

The three scripts share the same spellings for the common options: `-p` / `--project-name` /
`--project` names the saved plan or workspace, `-n` / `--max-results` / `--results` sets how many
search results to show, and `-o` / `--output-dir`, `-f` / `--format`, `--depth`, `--json` mean
the same everywhere. Saving into an existing workspace (`--persist -p <name>`) for a different
request or type stops with an error: pick another name with `-p`, or add `--force` to replace it.

The rest of this guide uses `$DECIDE`, `$SOLVE` and `$CODE` for these paths.

### Skill 1: make-decision

**What it does:** Guides you through structured decision-making with frameworks, bias detection,
weighted scoring and a decision journal.

**Best for:**
- Choosing between two or more options (technologies, vendors, candidates, offers)
- Resource allocation (budget, headcount)
- Strategic choices and decisions under uncertainty
- Team decisions that need agreement

**Knowledge base:** 10 decision frameworks, 8 decision types, 12 cognitive biases with remedies,
10 analysis techniques, 15 criteria templates (5 criteria each) and 8 facilitation techniques.

```bash
# Step 1: Generate a decision plan (always start here)
python3 $DECIDE "your decision question here" --plan -p "Project Name"

# Step 2: Look things up in one domain
python3 $DECIDE "relevant keywords" --domain frameworks    # 10 decision frameworks
python3 $DECIDE "relevant keywords" --domain types         # 8 decision types
python3 $DECIDE "relevant keywords" --domain biases        # 12 cognitive biases
python3 $DECIDE "relevant keywords" --domain criteria      # 15 criteria templates
python3 $DECIDE "relevant keywords" --domain analysis      # 10 analysis techniques
python3 $DECIDE "relevant keywords" --domain facilitation  # 8 facilitation techniques

# Step 3: Comparison matrix (at most 5 criteria); add --scores (1-5, 5 = best) for totals,
# winner and sensitivity. Options: "A vs B vs C", "A, B and C", or a numbered or bulleted list
python3 $DECIDE --matrix "Option A vs Option B vs Option C" \
  -c "criterion1:3,criterion2:2,criterion3:1" --scores "Option A:4,3,5;Option B:5,4,3;Option C:3,3,4"

# Step 4: Document the decision (with your confidence and when to review it)
python3 $DECIDE --journal "Decision title" -p "Project Name" --confidence 70 --review-in 30d

# Step 5: Later: list decisions due for review, then record the actual outcome
python3 $DECIDE --journal --review --due
python3 $DECIDE --journal --update "decision-slug" \
  --outcome "What actually happened and what you learned"
```

The plan names the options it found in your question, suggests five weighted criteria from the
best matching template, and warns about the biases that fit the decision type. Example:
`"Postgres vs MongoDB vs DynamoDB for our order service"` gives **Multi-Option Selection**, the
**Weighted Criteria Matrix**, the **Tech Stack / Framework Choice** criteria and warnings for
Anchoring Effect, Availability Heuristic and Confirmation Bias.

`--depth quick|standard|deep|executive` changes what the plan contains (executive is a
recommendation-first brief). Journals go to `.decisions/` in your
project. Say "save step-by-step" to get a `decision-plans/<name>/` workspace with one file per
step and a **Done?** column in `00-OVERVIEW.md`; in a later session, `/decide.resume` (or
`$DECIDE --status`) shows which steps are done and continues at the next one.

### Skill 2: problem-solving-pro

**What it does:** Guides you through the 7-step problem-solving method (Define → Disaggregate →
Prioritize → Workplan → Analyze → Synthesize → Communicate) with decomposition trees,
prioritization, analysis tools, mental models and bias warnings.

**Best for:**
- Root cause analysis of business and product problems (revenue, churn, conversion, signups)
- Organizational and process problems
- Market, cost and strategy questions
- Data and analytics investigations

For bugs, incidents and other problems in code, use **code-solving** (Skill 3, `/code.debug`):
it adds a failing test before the fix and runs your project's own checks.

**How it works:**

```
/solve Signups dropped 15% after the pricing change. Traffic is flat, the drop is
mostly on the annual plan, and the pricing page was redesigned at the same time.

# Or with depth control:
/solve.quick Signups dropped 15% after the pricing change
/solve.deep Revenue dropped 20% despite market growth
/solve.exec Revenue dropped 20% despite market growth
```

For the first request the plan classifies the problem as **Diagnostic** in the **Business
Performance** context and recommends:

1. **Define precisely**: a problem statement that passes the "so what?" test
2. **Disaggregate** with a Profitability Tree (price × volume, fixed and variable costs)
3. **Prioritize** with Sensitivity Analysis: which branches move the answer most
4. **Analyze** with Benchmarking, root cause analysis (5 Whys) and A/B tests
5. **Communicate** with the Pyramid Principle: the answer first, then the arguments
6. **Watch for** Confirmation Bias, Narrative Fallacy and Availability Heuristic

Run it yourself:

```bash
python3 $SOLVE "Signups dropped 15% after the pricing change" --plan
python3 $SOLVE "Signups dropped 15% after the pricing change" --plan --depth deep -f markdown
python3 $SOLVE "root cause 5 whys" --domain analysis
```

Add `--type` and `--category` when you know them (e.g. `--type Diagnostic --category "Business
Performance"`); the plan shows which **Type** and **Context** it used. `/solve.exec` adds an
executive summary (SCR), key risks and the decision needed. Say "save step-by-step" to get a
`solving-plans/<name>/` workspace with one file per step; in a later session, `/solve.resume` (or
`$SOLVE --status`) shows which steps are done and continues at the first open one.

### Skill 3: code-solving

**What it does:** Takes your AI through 7 steps for any code change — Define, Decompose,
Prioritize, Plan, Execute, Verify, Communicate — and requires real evidence at each step
(a failing test before the fix, passing checks after) instead of "it should work now".

**Best for:**
- Bugs and crashes (`/code.debug`)
- New features in small tested slices (`/code.feature`)
- Refactoring without changing behavior (`/code.refactor`)
- Slow code and memory leaks (`/code.perf`)
- Code review with concrete failure scenarios (`/code.review`)
- Writing tests that can actually fail, with coverage before and after (`/code.test`)
- Understanding unfamiliar code with file:line evidence, without changing it (`/code.explain`)
- Security fixes and few-line changes (`/code`, auto-detected, or `--type security|quick-fix`);
  trivial edits (a typo, a one-line change) are just done, without the 7 steps
- Flaky tests, production incidents and migrations (`/code`, auto-detected, or `--type flaky-test|incident|migration`)

**How it works:**

```
/code.debug Checkout throws "TypeError: Cannot read properties of undefined (reading 'id')"
since yesterday's deploy. Repro: add a gift card, then pay.

/code.feature Add CSV export to the reports page (date range, max 10k rows)
/code.deep Migrate the auth module from Express 4 to 5
```

| Step | What the AI must show before moving on |
|------|----------------------------------------|
| 1. Define | A failing test, repro command, benchmark baseline or acceptance criteria |
| 2. Decompose | The files and functions involved and who calls them |
| 3–4. Prioritize & Plan | An ordered task list with a test and rollback per task |
| 5. Execute | Small steps, each ending green; a log of what was tried |
| 6. Verify | The Step 1 check passes; your project's test/lint/build commands pass |
| 7. Communicate | A PR description (or postmortem / design doc / review report) |

Every plan opens with **Context from the project**, found in your code and git history:
the project files and lines your stack trace points to (with the source line; library frames
are dropped), where the functions and classes you name are defined, the latest commits on those
files, and your working tree. `/code.review` adds the diff (uncommitted changes, else your
branch against the default branch; `--diff <base>` to pick one) and the risk areas it touches,
which go first in the review checklist. Paste the full error and stack trace into the request.

When the request contains a common error message (44 are known, from `Cannot read properties of
undefined` to `nil pointer dereference` and `CrashLoopBackOff`), the plan adds a **Known error**
section: what it means, the likely causes (which become the hypotheses in the saved log), what to
check first and the root-cause fix.

`--depth quick|standard|deep|executive` sets how much the plan contains (`/code.deep` is the deep
plan). The executive plan, for a change that leadership follows, opens with an **Executive
summary** (before the project context) and ends with a **Stakeholder update (fill in as the work
moves)** section to keep current while you work.

The skill finds your project's own commands (npm/pnpm/yarn, Make, Go, Cargo, pytest with
uv/Poetry/PDM, Maven/Gradle, …), the command to run a single test, and the check steps your
CI runs: `python3 $CODE --detect`. `python3 $CODE --context "<error text>"` shows only what the
request points at in the project. Say "save step-by-step" to get a `coding-plans/<name>/`
workspace with one file per step. Saving again keeps the files you already filled in. The AI
ticks each step's gate in `00-OVERVIEW.md` once its evidence is written down; in a later
session, `/code.resume` (or `$CODE --status`) shows which steps are done and continues at the
first open gate.

---

## 🎯 Decision-Making Workflows

Each scenario shows the commands the AI runs (or you run, from the project root). With a slash
command you only type the first line, e.g. `/decide Keep frontend simple or add more features?`.

### Scenario A: Binary Choice (2 Options)

**Example:** "Keep frontend simple or add more features?"

```bash
# Step 1: Get the decision plan
python3 $DECIDE "Keep frontend simple or add more features?" --plan -p "Product Roadmap"
# → Binary Choice, Pros-Cons-Fixes Analysis, Product Feature Prioritization criteria

# Step 2: Look up the framework
python3 $DECIDE "pros cons fixable" --domain frameworks

# Step 3: Comparison matrix (at most 5 criteria)
python3 $DECIDE --matrix "Keep simple vs Add features" \
  -c "user_value:3,development_time:2,maintainability:2,technical_debt:1,learning_curve:1"

# Step 4: Check the biases for this decision
python3 $DECIDE "status quo confirmation" --domain biases

# Step 5: Document the decision
python3 $DECIDE --journal "Frontend: keep simple vs add features" -p "Product Roadmap"
```

**Key question:**
> "Which cons are fixable vs permanent?"

Fixable cons (solved with documentation, features or process changes) matter less than
permanent cons (fundamental trade-offs).

---

### Scenario B: Multi-Option Selection (3+ Options)

**Example:** "Which cloud provider: AWS, Azure or GCP?"

```bash
# Step 1: Get the decision plan (critical for multi-option!)
python3 $DECIDE "AWS vs Azure vs GCP for our enterprise migration with HIPAA workloads" \
  --plan -p "Cloud Strategy"
# → Multi-Option Selection, Weighted Criteria Matrix, Tech Stack / Framework Choice criteria

# Step 2: Other criteria templates that may fit better
python3 $DECIDE "technology vendor cloud" --domain criteria

# Step 3: Analysis techniques for multi-option decisions
python3 $DECIDE "scoring comparison sensitivity" --domain analysis

# Step 4: Weighted matrix with your scores: totals, winner and the weight change that flips it
python3 $DECIDE --matrix "AWS vs Azure vs GCP" \
  -c "total_cost:25,team_expertise:25,service_coverage:20,support:15,compliance:15" \
  --scores "AWS:4,5,5,5,5;Azure:4,3,4,4,5;GCP:5,2,4,3,4"

# Step 5: Check for anchoring and availability
python3 $DECIDE "anchoring first impression availability" --domain biases

# Step 6: If it is a team decision, a facilitation technique
python3 $DECIDE "anonymous input dot voting" --domain facilitation

# Step 7: Document the final decision
python3 $DECIDE --journal "Cloud migration: chose [WINNER]" -p "Cloud Strategy" --confidence 70 --review-in 3m
```

**Critical steps:**
1. ✅ **Define criteria BEFORE evaluating options** (prevents anchoring)
2. ✅ **Keep it to at most 5 criteria**: merge or drop the lightest ones
3. ✅ **Get independent scores** before the group discussion
4. ✅ **Read the sensitivity result**: which weight change would flip the winner?
5. ✅ **Check references** (for vendors and hires)

---

### Scenario C: Resource Allocation

**Example:** "Allocate 10 engineers across 5 projects"

```bash
# Step 1: Decision plan for allocation
python3 $DECIDE "allocate 10 engineers across 5 competing projects" --plan -p "Q2 Planning"
# → Resource Allocation, Expected Value Calculation, Investment / Resource Allocation criteria

# Step 2: Frameworks for allocating under uncertainty
python3 $DECIDE "expected value iterative hypothesis testing" --domain frameworks

# Step 3: What do we lose by not doing each project?
python3 $DECIDE "opportunity cost" --domain analysis

# Step 4: If it is a team decision, a facilitation technique
python3 $DECIDE "dot voting priority" --domain facilitation
```

**Allocate in rounds.** Commit 50-70% of the people first, measure real velocity and blockers
for 2-3 weeks, then reallocate the rest on evidence. You cannot predict the future accurately;
it is cheaper to allocate conservatively and adjust.

---

### Scenario D: Hiring

**Example:** "Choose between 3 senior engineer candidates"

```bash
# Step 1: Decision plan for hiring
python3 $DECIDE "hiring senior software engineer from 3 finalists" --plan -p "Q1 Hiring"
# → Multi-Option Selection, Weighted Criteria Matrix, Hiring Decision criteria

# Step 2: The hiring criteria template
python3 $DECIDE "hiring candidate" --domain criteria

# Step 3: The biases that matter most in hiring
python3 $DECIDE "first impression confirmation anchoring" --domain biases -n 5

# Step 4: Group facilitation: scores before discussion
python3 $DECIDE "anonymous input devil's advocate" --domain facilitation

# Step 5: Comparison matrix (at most 5 criteria)
python3 $DECIDE --matrix "Candidate A vs Candidate B vs Candidate C" \
  -c "skills_match:25,domain_expertise:25,team_complement:20,growth_potential:15,references:15"

# Step 6: Document the decision
python3 $DECIDE --journal "Senior engineer hire: chose [NAME] based on [CRITERIA]" -p "Q1 Hiring"
```

**Bias mitigation:** define the criteria before seeing resumes, use the same structured questions
for every candidate, score anonymously before the group discussion, give someone the devil's
advocate role for the favorite, and check references with previous managers. The plan warns
about Anchoring Effect (the first candidate or first impression sets the bar), Confirmation Bias
(looking for evidence that confirms the first impression) and Availability Heuristic (one vivid
interview story outweighs the rest).

---

## 🔍 Problem-Solving Workflows

### A business problem: signups dropped

```
/solve.deep Signups dropped 15% after the pricing change. Traffic is flat;
the drop is mostly on the annual plan; the pricing page was redesigned the same week.
```

What to expect, step by step:

1. **Define:** "Annual-plan signups fell 15% in the 4 weeks after the price change (monthly flat);
   find the cause and decide whether to roll back within 2 weeks."
2. **Disaggregate:** signups = visitors × conversion; split conversion by plan, page version,
   traffic source and country (MECE branches).
3. **Prioritize:** the branches that can explain most of the 15% first (price vs page redesign).
4. **Workplan:** one analysis per branch: funnel by step, an A/B test of the old page, a price
   sensitivity check with sales.
5. **Analyze:** test each hypothesis against the data; record what would disprove it.
6. **Synthesize:** one governing thought ("The new annual price, not the page, explains 80% of the drop").
7. **Communicate:** answer first (Pyramid Principle), then the evidence, risks and next steps.

The bias warnings (Confirmation Bias, Narrative Fallacy, Availability Heuristic) remind you that
"it must be the price" is a hypothesis until the data says so. Say "save step-by-step" to get a
`solving-plans/` workspace and continue later with `/solve.resume`.

### A bug in code

Use `/code.debug`, not `/solve`. See [examples/05](examples/05-debugging-race-condition.md) (stale
data after an update) and [examples/06](examples/06-code-debug-typeerror.md) (a TypeError after a deploy).

---

## 💡 Tips for Best Results

### Before you decide or investigate

1. **📋 Define the problem precisely**
   - Not: "Cloud is too expensive"
   - But: "Need cloud infrastructure for 500K req/sec, 18-month migration window, HIPAA compliance"
2. **👥 Identify stakeholders early**: who decides, who is affected, who has relevant experience
3. **⚖️ Define criteria BEFORE evaluating options**: prevents anchoring and post-hoc rationalization
4. **🧠 Check your biases explicitly**: `python3 $DECIDE "relevant keywords" --domain biases`, then apply the remedy
5. **📊 Use the decision journal**: record the rationale and your confidence, then the real outcome

### During the decision

6. **🔍 Read the sensitivity result** for multi-option decisions: which weight change flips the winner?
7. **👂 Use structured group processes**: anonymous input first, then discussion, then a re-vote
8. **🧪 Run small experiments (POCs) for technical decisions**: prove assumptions with real data
9. **📞 Check references**: customers for vendors, previous managers for hires
10. **⏱️ Allocate resources in rounds**: 50-70% first, measure, adjust

### After the decision

11. **📖 Document it**: `python3 $DECIDE --journal "Decision title" -p "Project Name" --confidence 70 --review-in 3m`
12. **📅 Review it**: `python3 $DECIDE --journal --review --due` lists decisions past their review date; record the outcome with `--update`
13. **🎓 Extract lessons**: what worked, what surprised you, which criteria mattered most

---

## 🎓 Decision Frameworks Reference

The plan picks the framework from the decision type. These are the defaults:

| Decision type | Framework the plan recommends | Also suggested |
|---------------|-------------------------------|----------------|
| **Binary Choice** | Pros-Cons-Fixes Analysis | Pre-Mortem Decision Test, Reversibility Filter |
| **Multi-Option Selection** | Weighted Criteria Matrix | Logic Tree Option Decomposition, Sensitivity Analysis Decision |
| **Resource Allocation** | Expected Value Calculation | Sensitivity Analysis Decision, Weighted Criteria Matrix |
| **Strategic Direction** | Scenario Planning Matrix | Hypothesis-Driven Decision Tree, Pre-Mortem Decision Test |
| **Operational / Tactical** | Reversibility Filter | Iterative Hypothesis Testing, Pros-Cons-Fixes Analysis |
| **Decision Under Uncertainty** | Scenario Planning Matrix | Expected Value Calculation, Iterative Hypothesis Testing |
| **Group / Stakeholder Decision** | Pre-Mortem Decision Test | Weighted Criteria Matrix; facilitation: Nominal Group Technique |
| **Time-Pressured Decision** | Reversibility Filter | Pros-Cons-Fixes Analysis |

For problems (not choices) use `/solve`; for code, `/code`.

---

## ⚠️ Cognitive Biases to Watch

### High-risk biases (always watch)

| Bias | What it does | How to counter |
|------|-------------|-----------------|
| **Confirmation Bias** | You notice what confirms your first impression | Actively seek disconfirming evidence |
| **Anchoring Effect** | The first number or option influences everything | Define criteria and get independent estimates before comparing |
| **Sunk Cost Fallacy** | Past investment makes you continue failing projects | Evaluate as if starting fresh today |
| **Overconfidence** | Too certain about uncertain outcomes | Pre-mortem: assume it failed, work backward |
| **Status Quo Bias** | You prefer the current state even when change is better | Reframe as the cost of NOT acting |

### Biases by area

These are the biases the skills' knowledge bases attach to each area (make-decision's criteria
templates, and code-solving for engineering choices):

| Area | Biases |
|------|--------|
| Hiring | Confirmation Bias, Anchoring Effect, Availability Heuristic |
| Tech stack and frameworks | Availability Heuristic, Confirmation Bias, Survivorship Bias |
| Build vs buy, business software | Sunk Cost Fallacy, Status Quo Bias, Planning Fallacy, Not Invented Here |
| Engineering approach | Golden Hammer, Rewrite Fallacy, Premature Optimization |
| Resource allocation and investment | Sunk Cost Fallacy, Overconfidence, Loss Aversion, Planning Fallacy |
| Problem investigations | Confirmation Bias, Narrative Fallacy, Availability Heuristic |

---

## 📖 Learning Path

### Week 1: Get familiar
- [ ] Install the skills
- [ ] Read the [examples](examples/README.md) (01-06)
- [ ] Try one simple decision with `/decide`
- [ ] Try one simple bug with `/code.debug`

### Week 2: Build the habit
- [ ] Make one multi-option decision with the full workflow and scores
- [ ] Use a facilitation technique in a team decision
- [ ] Record the decision in the journal
- [ ] Name and counter one cognitive bias explicitly

### Week 3: Deepen practice
- [ ] Use `/solve.deep` on a real business problem and save it step by step
- [ ] Review a past decision with `--journal --review --due`
- [ ] Walk a colleague through the process

### Week 4+: Make it a team habit
- [ ] Use the frameworks without looking them up
- [ ] Share a decision write-up with your team
- [ ] Contribute an example to [examples/](examples/README.md)

---

## Troubleshooting

**"python3: command not found" or the AI says Python is missing.**
The skills need Python 3.9+ (standard library only). The AI asks you before installing
anything; it never installs Python on its own. Install it (`brew install python`,
`sudo apt install python3`, or `winget install Python.Python.3.12` on Windows), open a new
terminal and run `think-better check`. On Windows Python is usually called `python`; the
slash commands and the AI adapt the command.

**A script fails or prints an error.**
Errors go to stderr as one line that names the input to fix, with exit code 2: an empty
request, scores that do not match the criteria or are outside 1-5, a journal id with no or several
matches, a workspace name already used by another request. A saved workspace that does not exist
(`--status`, `--done`) exits with 1. Run the same command yourself from the project root to see
the full message. If the skill files look broken, run `think-better check`:
it reports each install as installed, outdated, modified or incomplete; `think-better update`
repairs outdated and incomplete installs. Still failing? [Open a bug report](https://github.com/HoangTheQuyen/think-better/issues/new?template=bug_report.md)
with the output of `think-better version` and `think-better check`.

**`.new` files appeared after `think-better update`.**
You had edited those files, so `update` kept your version and wrote the new one next to it as
`<file>.new`. Run `think-better diff` (add `--ai`, `--skill`, `--global` or `--context 10` to
narrow or widen it) to see a unified diff of your file against the new version. Then, per file:
take the new version with `mv <file>.new <file>`, or keep yours with `rm <file>.new` (copy over
what you want first). To take every new version and drop your edits, run
`think-better update --force`: your versions are saved as `<file>.bak` first.

**`check` says a Copilot skill is "at an old location".**
Releases up to v1.4.0 installed Copilot's skills in `.github/prompts/<skill>/`, where Copilot does
not load them. Run `think-better update --ai copilot`: it moves them to `.github/skills/<skill>/`,
keeping files you edited (the new version goes next to them as `.new`). `think-better list --json`
marks such locations with `"legacy": true`.

**A slash command I deleted came back.**
`update` restores deleted slash commands and names them. Exclude the ones you do not want:
`think-better update --exclude-command code.perf`.

**The slash commands do not show up.**
Check where they were installed with `think-better list`, then restart the AI tool or reload the
window. For GitHub Copilot, switch Copilot Chat to agent mode; the commands are the
`.prompt.md` files in `.github/prompts/`. `--global` installs Copilot's skills but not its slash
commands: install those per project with `think-better init --ai copilot`.

**The AI does not pick the skill when I describe a problem.**
Use the slash command instead (`/decide`, `/solve`, `/code`), or name the skill in your request.
In GitHub Copilot, use agent mode, and check with `think-better check` that the skills are in
`.github/skills/`: an install from v1.4.0 or earlier is still in `.github/prompts/<skill>/`, where
Copilot does not load it on its own; `think-better update` moves it.

**`--ai is required in non-interactive mode`.**
Pass `--ai claude` (or another tool), or set `THINK_BETTER_AI=claude` in your shell.

**`installed for several AI tools (...): choose one with --ai`.**
`uninstall` found the skill in more than one tool and has no terminal to ask which. Pass `--ai`,
or set `THINK_BETTER_AI` to one of the tools it lists. (In a terminal it asks, and offers all of
them; an invalid answer is asked again.)

## Uninstall

```bash
think-better uninstall --skill make-decision --dry-run   # see what would be removed
think-better uninstall --skill make-decision             # asks for confirmation
think-better uninstall --all --yes                       # every skill, without asking
think-better uninstall --skill make-decision --global    # a --global install
think-better uninstall --skill make-decision --ai claude # only the Claude Code install
```

`uninstall` removes a skill (`--skill`) or every skill (`--all`) and the slash commands that run
them. It finds the AI tools the skill is installed for in this project (with `--global`: in your
user account), so `--ai` is not needed; when it is installed for several, it asks which (all of
them is a choice), `THINK_BETTER_AI` picks one, and without a terminal it stops and lists them.
Copilot skills at the location used up to v1.4.0 (`.github/prompts/<skill>/`) are found and removed too.

Files you modified are kept and listed, as is any folder that still holds other files; the
skill's manifest is then marked `"uninstalled": true`, so `check` and `update` treat the skill as
not installed and a later `init` installs it fresh. `-y` / `--yes` skips the confirmation (needed
without a terminal, e.g. in CI) and still keeps your modified files. `--force` also deletes the
files you modified (and their `.new` files), without asking, and prints a warning listing them.
In v1.4.0 and earlier `--force` only skipped the confirmation; scripts that used it for that should now use `--yes`.
Your plans and journals (`decision-plans/`, `solving-plans/`, `coding-plans/`,
`.decisions/`) are never touched. To remove the CLI itself, delete the binary
(`~/.local/bin/think-better` from the install script), or `brew uninstall think-better`,
`scoop uninstall think-better`.

## FAQ

**Does it cost tokens?**
The scripts run locally and cost nothing. Your AI tool reads the instructions and the plan the
script prints, which uses some of its context: a slash command file is 2.5-3.8 KB, the skill's
`SKILL.md` (read at the start) 15-20 KB, and a standard plan from the script about 9-12 KB (roughly
2,000-3,000 tokens; `.deep` plans are about twice as long). `.quick` plans are shorter, `.exec` longer.

**Does anything leave my machine?**
No. The CLI copies Markdown, CSV and Python files into your project or home folder, and the
scripts make no network calls and need no accounts or API keys. Your request goes only to the
AI tool you already use, as it would without the skills.

**Should I commit the installed skills?**
Committing `.claude/`, `.github/skills/` and `.github/prompts/`, `.opencode/` or `.agents/` lets everyone on the team
use the same skills and commands without installing them; the `.think-better.json` manifests let
`think-better update` tell your edits apart from the shipped files. If only you use them, install
with `--global` or add those folders to `.gitignore`.

**Should I commit `decision-plans/`, `solving-plans/`, `coding-plans/` and `.decisions/`?**
They are your working notes. Commit them when they are useful to the team (a decision record
with its rationale in `.decisions/` is often worth keeping; a step-by-step workspace for a design
review too). Leave out, or add to `.gitignore`, ones with private or temporary content.

**Which language should I write requests in?**
English. The knowledge base keywords and the skills' trigger phrases are in English, so English
requests match best. The plan the script prints is in English too. Say "save step-by-step" to
save a workspace.

**Which skill do I use for a bug?**
`/code.debug` (code-solving). `/solve` is for business, product and organizational problems.

---

## 🆘 Getting Help

### From the skills themselves

```bash
# Look up one domain (from the project root)
python3 $DECIDE "keyword" --domain frameworks
python3 $DECIDE "keyword" --domain biases
python3 $SOLVE "keyword" --domain decomposition
python3 $CODE "keyword" --domain errors

# Every option of a script
python3 $DECIDE --help
```

### From the community

- See [examples/](examples/README.md) for worked case studies
- See the [Quick Reference](QUICK-REFERENCE.md) for a one-page summary
- Ask questions in [GitHub Discussions](https://github.com/HoangTheQuyen/think-better/discussions)
- Report bugs in [GitHub issues](https://github.com/HoangTheQuyen/think-better/issues)

---

## ✅ Checklist: Before You Make a Decision

- [ ] **Problem is precisely defined** (not vague)
- [ ] **Options are explicitly listed** (including "do nothing" when it is real)
- [ ] **Criteria are defined BEFORE evaluating options**
- [ ] **At most 5 criteria, with weights** (not all equally important)
- [ ] **You've checked the relevant biases** (and applied the remedies)
- [ ] **Stakeholders identified** (and included appropriately)
- [ ] **If group decision: using a structured process** (not groupthink)
- [ ] **If technical: a small experiment done** (not just estimates)
- [ ] **If vendor: references checked** (not just the sales pitch)
- [ ] **Decision will be documented** (journal entry created)
- [ ] **Review date set** (`--review-in`)

---

**Next steps:**
1. Install the skills: `think-better init --ai claude`
2. Pick a real decision you're facing this week
3. Work through the workflow above for your decision type
4. Record it in the decision journal
5. When the review date comes: record the actual outcome

Happy deciding! 🎯
