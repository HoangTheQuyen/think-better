# Goal

Help users make better decisions in minutes instead of hours by applying proven frameworks, detecting cognitive biases, and structuring the evaluation process.

# make-decision

Comprehensive decision-making framework for structured evaluation of options. Contains 10 decision frameworks, 8 decision type classifications, 12 cognitive biases with debiasing strategies, 10 analysis techniques, 15 criteria templates (technology, tech stack, hiring, vendors, investment, market entry, product features, pricing, organizational change, location, job offers, relocation, education, housing, and a general fallback) and 8 group facilitation techniques. The plan names the options it found in the request, picks the framework, analysis methods and biases for the decision type, and suggests five weighted criteria. A scoring calculator totals the matrix, names the winner and finds the smallest weight change that would flip it.

## Prerequisites

**IMPORTANT: Detect the correct Python command first.** Some systems use `python3`, others use `python`. Run:

```bash
python3 --version 2>/dev/null || python --version
```

Use whichever command succeeds (`python3` or `python`) for ALL script calls below. If the system only has `python` (common on Windows), substitute `python` everywhere you see `python3` in this document. The scripts need Python 3.9+ and only the standard library.

If neither works, Python is not installed: tell the user that the scripts need Python 3.9+ and
**ask before installing anything**; do not run a package manager on your own.

> **Note:** On Windows, Python 3 is typically available as `python` (not `python3`).

---

## Running the Scripts

Run every command from the **project root** with the path shown, e.g.
`python3 .agents/skills/make-decision/scripts/search.py ...` (the installer adjusts this path for
your AI tool). Saved plans, workspaces and journals are written to the project (or to `-o <dir>`),
never inside the skill folder. Saving again never overwrites files that already exist (they hold
your notes); add `--force` to replace them.

### Passing the user's text

**Anything taken from the user's message goes on stdin** with `--stdin`, never on the command
line: the decision for `--plan`, the options for `--matrix`, the statement for `--journal` and the
outcome for `--journal --update`. Quotes, backticks and `$` then never reach the shell. Only short
values you compose yourself (`-c` criteria, `--scores`, `-p` names) go on the command line.

Use exactly this delimiter, `THINK_BETTER_EOF_7f3a`, quoted as shown:

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan <<'THINK_BETTER_EOF_7f3a'
<the user's text, unchanged>
THINK_BETTER_EOF_7f3a
```

**Check the text first.** The heredoc ends at the first line that is exactly `THINK_BETTER_EOF_7f3a`;
anything after it would run as shell commands. If a line of the user's text is exactly that
delimiter, do not use the heredoc: write the text unchanged to a temporary file with your
file-editing tool (not the shell), run `python3 .agents/skills/make-decision/scripts/search.py --stdin --plan < <file>`, then delete the file.

In PowerShell (keep `'@` at the start of its line):

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new()
@'
<the user's text, unchanged>
'@ | python .agents/skills/make-decision/scripts/search.py --stdin --plan
```

The here-string ends at a line that starts with `'@`. If a line of the user's text starts with
`'@`, write the text to a file instead and run
`Get-Content -Raw -Encoding UTF8 <file> | python .agents/skills/make-decision/scripts/search.py --stdin --plan`.

---

## How to Use This Workflow

When user requests decision-making help (decide, choose between options, weigh a trade-off), follow this workflow. To find why something went wrong use problem-solving-pro; for bugs and code changes use code-solving.

**Language:** Respond in English. The scripts' output is in English: show it as it is, and keep commands, flags, file names and option names exactly as written
(option names as the user wrote them).

If the user has not said what they are deciding, ask what the decision and the options are before running anything.

### Step 1: Understand the Decision

Extract key information from user's decision description:
- **Decision type**: Binary choice, multi-option, resource allocation, strategic, operational, under uncertainty, group/stakeholder, time-pressured
- **Options**: What alternatives are being considered? (Add "do nothing" / "wait" if it is a real option.)
- **Context**: Industry, stakes, timeline, stakeholders, reversibility
- **Constraints**: Budget, time, resources, dependencies

### Step 2: Generate Decision Plan (REQUIRED)

**Always start with `--plan`** to get comprehensive recommendations:

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan -f markdown [-p "Project Name"] <<'THINK_BETTER_EOF_7f3a'
<the user's decision, unchanged>
THINK_BETTER_EOF_7f3a
```

If the user asked to save the work ("save", "step-by-step", "workspace"), run the Step 2b command instead of this one: it prints the same plan.

**Classify it yourself when you can** — you understand the decision better than keyword matching.
Add `--type "<decision type>"`, one of: Binary Choice, Multi-Option Selection, Resource Allocation, Strategic Direction, Operational / Tactical, Decision Under Uncertainty, Group / Stakeholder Decision, Time-Pressured Decision.
Without it the script scores each type's signal phrases (e.g. "deadline", "board", "uncertain")
and adds the options it found ("A vs B" or "A or B" leans Binary Choice, three or more lean Multi-Option Selection). The plan says what
matched; when nothing did, it says so and lists the `--type` values: then re-run with `--type`.

The plan contains:
1. The request, the decision type (and why), and the **options** found in the request
2. The framework the decision type recommends, with its steps
3. **Five weighted criteria** from the best matching template (General Decision when none fits)
4. Analysis techniques and **bias warnings** chosen for the decision type and the domain
5. Facilitation for group decisions, anti-patterns, and a checklist
6. A **Next Steps** table at the end: show it once, do not add your own

**Depth** changes what the plan contains (`--depth`, default `standard`):

| Depth | Contains |
|-------|----------|
| `quick` | Options, the framework's steps, the top 3 criteria, 2 biases, and whether it is a one-way door |
| `standard` | Full plan: framework with alternatives, 5 criteria with "what a 5 looks like", 2 analysis techniques, 3 biases, scoring command, checklist |
| `deep` | Standard plus framework alternatives explained, how to apply each technique, how to detect each bias, reversibility, a pre-mortem, sensitivity questions and the information to gather |
| `executive` | A recommendation-first brief: recommendation, decision needed (owner, deadline, type, reversibility), key risks, criteria and weights, what would change the call; framework, biases and analysis as an appendix |

`--json` prints the plan as JSON (with `options`, `criteria.items`, `bias_warnings`, `reversibility`, ...).

### Step 2b: Save the Plan, Resume Later

When the user asks to save, run this instead of the Step 2 command, not after it:

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan --persist --step-docs -p "Project Name" -f markdown <<'THINK_BETTER_EOF_7f3a'
<the user's decision, unchanged>
THINK_BETTER_EOF_7f3a
```

`--persist` alone writes `decision-plans/<project-name>/PLAN.md`. With `--step-docs` it creates a
workspace: `00-OVERVIEW.md` (the request, options, and a step table with a **Done?** column),
`01-DECISION-TYPE.md` (the request quoted, decision statement, owner, deadline), `02-FRAMEWORK.md`,
`03-CRITERIA.md` (the five criteria and weights pre-filled), `04-ANALYSIS.md`, `05-OPTIONS.md` (the
options and a criteria × options matrix pre-filled), `06-DECISION.md` (decision, **pre-mortem**,
**kill criteria**, review date), `BIAS-WARNINGS.md` and `DECISION-LOG.md`.

In a later session (`/decide.resume`):

```bash
# Which steps are done and what to do next (-p name, or the workspace the text matches, or the latest)
python3 .agents/skills/make-decision/scripts/search.py --stdin --status [-p project-name] <<'THINK_BETTER_EOF_7f3a'
<the user's text, or nothing>
THINK_BETTER_EOF_7f3a
# Mark a step done (1-6 or classify, framework, criteria, analysis, options, decide); --undone reopens it
python3 .agents/skills/make-decision/scripts/search.py --done criteria -p project-name
```

Only mark a step done when the user has actually settled it.

### Step 3: Deep-Dive Domain Searches

Use when the plan's recommendation needs more detail, OR when user asks about a specific topic (e.g., "what biases should I watch for?"). Pass the keywords on stdin like any other text; fixed example keywords such as those below may go on the command line:

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --domain <domain> [-n <max_results>] <<'THINK_BETTER_EOF_7f3a'
<keywords>
THINK_BETTER_EOF_7f3a
```

| Need | Domain | Example |
|------|--------|---------|
| Choose a decision framework | `frameworks` | `--domain frameworks "hypothesis uncertainty"` |
| Classify the decision type | `types` | `--domain types "binary strategic"` |
| Identify cognitive biases | `biases` | `--domain biases "confirmation sunk cost"` |
| Select analysis techniques | `analysis` | `--domain analysis "sensitivity break-even"` |
| Get evaluation criteria | `criteria` | `--domain criteria "pricing housing"` |
| Plan group facilitation | `facilitation` | `--domain facilitation "pre-mortem red team"` |

### Step 4: Compare and Score Options

With the options from the user's message on stdin:

```bash
# Empty matrix with the template's criteria and weights
python3 .agents/skills/make-decision/scripts/search.py --stdin --matrix -f markdown <<'THINK_BETTER_EOF_7f3a'
Which CRM: Salesforce, HubSpot or Pipedrive
THINK_BETTER_EOF_7f3a

# Your own criteria and weights, and the scores (1-5, one per criterion, in -c order)
python3 .agents/skills/make-decision/scripts/search.py --stdin --matrix -f markdown \
  -c "Cost:3,Speed:2,Risk:1" --scores "React:4,3,5;Vue:5,4,3" <<'THINK_BETTER_EOF_7f3a'
React vs Vue
THINK_BETTER_EOF_7f3a
```

Options are read from "A vs B vs C", "A, B or C", "Which X: A, B or C", "between A and B". With `--scores` the matrix shows the
weighted totals, the **winner**, and the **sensitivity**: for each criterion, the weight at which
another option would tie the winner, with the smallest such change called out. A winner that flips
under a small change is fragile: firm up that criterion before deciding. Weights may be any
positive numbers (shown with their share of the total); `-c "Cost,Speed"` weighs them equally.

### Step 5: Document the Decision

After reaching a conclusion, create a journal entry. It records the options, the framework, the
criteria, your **confidence** and a **review date** (default 30 days):

```bash
# Create (statement on stdin; --options and --framework override what the script finds)
python3 .agents/skills/make-decision/scripts/search.py --stdin --journal --confidence 70 --review-in 6w \
  [--options "AWS, Azure"] [--framework "Weighted Criteria Matrix"] [-p "Project"] <<'THINK_BETTER_EOF_7f3a'
Chose AWS for the Q3 migration
THINK_BETTER_EOF_7f3a

# Review: all entries, newest first; --due lists only those past their review date
python3 .agents/skills/make-decision/scripts/search.py --journal --review [--due]

# Record what actually happened (outcome on stdin); it is appended, nothing is overwritten
python3 .agents/skills/make-decision/scripts/search.py --stdin --journal --update "q3-migration" <<'THINK_BETTER_EOF_7f3a'
Migration finished on time, 15% under budget
THINK_BETTER_EOF_7f3a
```

Journal files live in `.decisions/` with ASCII file names. An
`--update` id that matches no entry, or several, is an error (exit code 1) listing the matches.

---

## Search Reference

### Available Domains

| Domain | Records | Use For | Example Keywords |
|--------|---------|---------|------------------|
| `frameworks` | 10 | Choosing a decision methodology | hypothesis, logic tree, weighted matrix, sensitivity, expected value, scenario, pros-cons, pre-mortem, reversibility, iterative |
| `types` | 8 | Classifying the type of decision | binary, multi-option, resource allocation, strategic, operational, uncertainty, group, time-pressured |
| `biases` | 12 | Identifying thinking errors to avoid | confirmation, anchoring, sunk cost, status quo, overconfidence, framing, availability, groupthink, planning fallacy, loss aversion |
| `analysis` | 10 | Selecting analytical methods | sensitivity, break-even, decision tree, scenario, scoring, opportunity cost, risk-reward, bayesian, pre-mortem, reference class |
| `criteria` | 15 | Getting evaluation criteria templates (5 criteria each) | technology, tech stack, hiring, vendor, investment, market entry, product feature, pricing, organizational change, location, job offer, relocation, education, housing, general |
| `facilitation` | 8 | Planning group decision sessions | pre-mortem, red team, nominal group, debate, dot voting, anonymous input, devil's advocate, workplan |

---

## Example Workflow

**User request:** "We need to choose between building in-house, buying a SaaS solution, or hiring a development agency for our new CRM system."

### Step 1: Understand the Decision
- Decision type: Multi-Option Selection
- Options: Build in-house, Buy SaaS, Hire agency
- Context: Technology decision with long-term impact
- Constraints: Budget, timeline, team capacity

### Step 2: Generate Decision Plan

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --plan -f markdown -p "CRM Decision" <<'THINK_BETTER_EOF_7f3a'
We need to choose between building in-house, buying a SaaS solution, or hiring a development agency for our new CRM system.
THINK_BETTER_EOF_7f3a
```

**Output:** Multi-Option Selection (3 options found), Weighted Criteria Matrix with its steps,
Technology Selection criteria (functionality fit 25, total cost of ownership 20, integration 20,
scalability and security 20, vendor stability 15), Relative Value Scoring and Sensitivity Analysis,
bias warnings (Anchoring Effect, Sunk Cost Fallacy, ...), and a checklist.

### Step 3: Deep-Dive Searches

```bash
python3 .agents/skills/make-decision/scripts/search.py "status quo sunk cost technology" --domain biases
python3 .agents/skills/make-decision/scripts/search.py "structured debate team" --domain facilitation
```

### Step 4: Score the Options

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --matrix -f markdown \
  -c "Functionality fit:25,Total cost of ownership:20,Integration ease:20,Scalability and security:20,Vendor stability:15" \
  --scores "Build in-house:5,2,4,3,3;Buy SaaS:4,4,4,4,5;Hire agency:4,3,3,3,2" <<'THINK_BETTER_EOF_7f3a'
Build in-house vs Buy SaaS vs Hire agency
THINK_BETTER_EOF_7f3a
```

### Step 5: Document the Decision

```bash
python3 .agents/skills/make-decision/scripts/search.py --stdin --journal --confidence 75 -p "CRM Decision" <<'THINK_BETTER_EOF_7f3a'
CRM platform: buy SaaS rather than build or outsource
THINK_BETTER_EOF_7f3a
```

**Then:** Synthesize the plan, searches, and matrix into a structured recommendation for the user, walking them through each step of the recommended framework.

---

## Output Formats

`--plan` and `--matrix` print an ASCII box/table by default (best for a terminal); `-f markdown`
gives Markdown (best for chat and documents); `--plan --json` and `--matrix --json` give JSON.

---

## Key Decision-Making Principles

1. **Define before deciding** — Invest time in framing the decision correctly before evaluating options
2. **Map options exhaustively** — Use MECE decomposition to ensure no alternatives are missed
3. **Criteria before options** — Define evaluation criteria BEFORE seeing options to prevent anchoring
4. **Hypothesis-driven** — State your Day One answer early, then test it with evidence
5. **Prioritize ruthlessly** — 80/20: focus analysis on the few factors that actually drive the decision
6. **Test sensitivity** — Identify which assumptions would flip the decision if changed
7. **Watch for biases** — Confirmation bias, anchoring, and sunk cost fallacy are the most dangerous
8. **Stress-test with pre-mortem** — Assume the decision failed and work backward to find blind spots
9. **Classify reversibility** — Two-way door decisions deserve quick action; one-way doors deserve deep analysis
10. **Document and reflect** — Keep a decision journal with a review date to improve calibration over time

---

## Constraints

- **Always start with Step 2** (`--plan`) before doing domain searches — the plan provides context for everything else
- **Do NOT skip bias detection** — every decision has biases; explicitly address them
- **Keep recommendations under 500 words** — decision-makers skim, not read
- **Never present more than 5 criteria** — every template has exactly 5 (quick depth shows the top 3); if the user adds one, drop or merge the lightest so there are still at most 5
- **When in doubt, ask** — if the user's decision type is unclear, ask one clarifying question before running the plan

---

## Error Handling

If a command fails (an `Error:` or `usage:` message, or a non-zero exit), show the error to the
user. If it names an input you chose (a flag value, scores, a workspace name), fix that and
re-run; otherwise stop. Never present a plan the script did not produce.

1. **Check Python**: Run `python3 --version` or `python --version`. If neither is found, tell the user and ask before installing anything
2. **Manual fallback**: Only if Python is missing and the user does not want to install it, apply the Key Decision-Making Principles above manually and say clearly that the script did not run:
   - Ask user to describe the decision → classify the type yourself
   - Suggest a framework based on the type (e.g., Weighted Matrix for multi-option, Pros-Cons-Fixes for binary)
   - Warn about the 3 most common biases for that decision type
   - Walk through the framework step by step
3. **Script errors**: Errors go to stderr with exit code 1 (e.g. a journal id with no or several matches, scores that do not match the criteria); fix the input the message names and re-run
4. **No type matched**: the plan says so and lists the `--type` values; pick one and re-run
5. **Languages**: keywords are matched in English. For other languages, translate the key terms to English before calling `search.py`. Respond in English.
