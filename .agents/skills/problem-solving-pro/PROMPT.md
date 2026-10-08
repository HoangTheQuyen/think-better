# Goal

Help users solve complex problems systematically using proven frameworks — turning vague issues into structured analyses with actionable recommendations.

# problem-solving-pro

Comprehensive structured problem-solving framework for tackling any complex challenge. Contains a 7-step methodology, 18 decomposition frameworks, 8 prioritization techniques, 15 analysis tools, 12 cognitive biases with debiasing strategies, 10 communication patterns, 13 mental models, and 10 team dynamics patterns. Searchable database with reasoning-based recommendations that adapts to your specific problem type. Requests can be in English or Vietnamese (with or without accents).

## Prerequisites

**IMPORTANT: Detect the correct Python command first.** Some systems use `python3`, others use `python`. Run:

```bash
python3 --version 2>/dev/null || python --version
```

Use whichever command succeeds (`python3` or `python`) for ALL script calls below. If the system only has `python` (common on Windows), substitute `python` everywhere you see `python3` in this document.

If neither works, Python is not installed: tell the user that the scripts need Python 3.9+ and
**ask before installing anything**; do not run a package manager on your own.

> **Note:** On Windows, Python 3 is typically available as `python` (not `python3`).

---

## Running the Scripts

Run every command from the **project root** with the path shown, e.g.
`python3 .agents/skills/problem-solving-pro/scripts/search.py ...` (the installer adjusts this path for
your AI tool). Saved plans and journals are written to the project, never inside the skill folder.
Saving again never overwrites files that already exist (they hold your notes); add `--force`
to replace them.

### Passing the user's text

When the query is the user's own words (a request, an error message, a pasted log), pass it on
stdin with `--stdin` instead of quoting it, so quotes, backticks and `$` never reach the shell.
Every example below does this.

Use exactly this delimiter, `THINK_BETTER_EOF_7f3a`, quoted as shown:

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan <<'THINK_BETTER_EOF_7f3a'
<the user's text, unchanged>
THINK_BETTER_EOF_7f3a
```

**Check the text first.** The heredoc ends at the first line that is exactly `THINK_BETTER_EOF_7f3a`;
anything after it would run as shell commands. If a line of the user's text is exactly that
delimiter, do not use the heredoc: write the text unchanged to a temporary file with your
file-editing tool (not the shell), run `python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan < <file>`, then delete the file.

In PowerShell (keep `'@` at the start of its line):

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new()
@'
<the user's text, unchanged>
'@ | python .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan
```

The here-string ends at a line that starts with `'@`. If a line of the user's text starts with
`'@`, write the text to a file instead and run
`Get-Content -Raw -Encoding UTF8 <file> | python .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan`.

---

## How to Use This Workflow

When user requests problem-solving help (analyze, solve, diagnose, decompose, find a root cause, plan, strategy, recommendation), follow this workflow. For bugs and code changes use code-solving; for choosing between known options use make-decision.

**Language:** answer in the user's language. The scripts' output is in English: translate it
when you present it, and keep commands, flags, file names and option names exactly as written.

If the user has not described the problem yet, ask what it is before running anything.

### Step 1: Understand the Problem

Extract key information from user's problem description:
- **Context** (→ `--category`): Business performance, market entry, organizational change, product, cost reduction, innovation, crisis, data/analytics, partnership/M&A, policy
- **Type** (→ `--type`): Diagnostic, opportunity, design, prediction, negotiation — or by complexity: well-structured, ill-structured, wicked
- **Keywords**: revenue, growth, decline, entry, change, innovation, cost, crisis, etc.
- **Context**: Industry, scale, time pressure, stakeholder dynamics

### Step 2: Generate Problem-Solving Plan (REQUIRED)

**Always start with `--plan`** to get comprehensive recommendations with reasoning:

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan -f markdown <<'THINK_BETTER_EOF_7f3a'
<the user's problem, unchanged>
THINK_BETTER_EOF_7f3a
```

If the user asked to save the work ("save", "step-by-step", "workspace"), run the Step 2b
command instead of this one: it prints the same plan.

**Classify it yourself when you can** — you understand the problem better than keyword matching:

- `--type <type>` — how the problem is shaped: Well-Structured, Ill-Structured, Wicked, Diagnostic, Opportunity, Design, Prediction, Negotiation
- `--category "<context>"` — selects the reasoning rule (decomposition, analyses, communication style): Business Performance, Market Entry Strategy, Organizational Change, Product Development, Cost Reduction, Innovation / Disruption, Crisis / Turnaround, Data / Analytics Problem, Partnership / M&A, Policy / Public Sector

Omit either flag to auto-detect (from English keywords). The plan reports what it used as
**Type** and **Context** and whether each was set by you, auto-detected, a weak guess or no match.
When nothing matched, the plan starts with a note such as "No problem type matched clearly. Re-run
with `--type` (...)" listing the values: re-run with the flag instead of presenting generic defaults.

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan --type Diagnostic --category "Business Performance" -f markdown <<'THINK_BETTER_EOF_7f3a'
revenue down 20% despite market growth
THINK_BETTER_EOF_7f3a
```

This command:
1. Classifies the problem type and context (or uses `--type` / `--category`)
2. Applies the context's reasoning rule: decomposition, analyses, communication style, decision rules
3. Picks the mental models and bias warnings named for this context and problem type, then fills up from search
4. Returns a solving plan: the 7 steps with their quality gates, decomposition, prioritization, analysis,
   decision rules, communication, mental models, bias warnings, anti-patterns and a checklist
5. Ends with a **Next Steps** table for the depth used: present it once, do not add another

**Depth** (`--depth`) changes what the plan contains:

| Depth | Contents |
|-------|----------|
| `quick` | One screen: classification, process, decomposition, main analysis, 2 mental models, 2 biases, anti-patterns, first move |
| `standard` (default) | Adds the 7 steps with quality gates, prioritization, decision rules, communication, 3 models, 3 biases, team, checklist |
| `deep` | Adds more alternatives, 5 mental models with danger zones, 4 biases with warning signs, pitfalls per step, strengths and limits of the analysis |
| `executive` | Everything in `deep` plus an **Executive Summary (SCR)**, **Key Risks** and **Decision Needed** |

`--json` with `--plan` prints the plan as JSON (with `--persist`, a `saved` entry lists the files).

### Step 2b: Persist Problem-Solving Plan

When the user asks to save ("save", "step-by-step", "workspace"),
run this instead of the Step 2 command, not after it:

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan --persist -p "Project Name" -f markdown <<'THINK_BETTER_EOF_7f3a'
<the user's problem, unchanged>
THINK_BETTER_EOF_7f3a
```

This creates:
- `solving-plans/project-name/PLAN.md` — Complete problem-solving plan (with the original request)

Add `--step-docs` for a workspace with one file per step (`00-OVERVIEW.md` with a **Done?** column,
`01-PROBLEM-DEFINITION.md` pre-filled with the request, ... `07-RECOMMENDATION.md`, `BIAS-WARNINGS.md`,
`DECISION-LOG.md`). Each step file starts with what to do and its **Done when** quality gate.

### Step 2c: Resume Later

A saved workspace is how work continues in a new session (`/solve.resume`):

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --status [-p "<short-name>"] <<'THINK_BETTER_EOF_7f3a'
<the user's text, or nothing>
THINK_BETTER_EOF_7f3a
python3 .agents/skills/problem-solving-pro/scripts/search.py --done <step> -p "<short-name>"
```

`--status` shows each step's file, whether it was filled in and whether it is done, then the **next**
step with what to do, its quality gate and pitfalls. Without `-p`, it picks the workspace whose name or
request matches the text given on stdin, else the most recently changed one. `--done <step>` (1-7 or a
name: define, decompose, prioritize, plan, analyze, synthesize, communicate) ticks the step in
`00-OVERVIEW.md`; `--undone <step>` reopens it. Read the files of finished steps before continuing, and
tick a step only when its file shows the work.

### Step 3: Deep-Dive Domain Searches

Use when the plan's recommendation needs more detail, OR when user asks about a specific topic (e.g., "how do I do a root cause analysis?"):

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --domain <domain> [-n <max_results>] <<'THINK_BETTER_EOF_7f3a'
<keywords>
THINK_BETTER_EOF_7f3a
```

**When to use domain searches:**

| Need | Domain | Example |
|------|--------|---------|
| Understand the methodology steps | `steps` | `--domain steps "define problem"` |
| Classify the problem | `problem-types` | `--domain problem-types "wicked systemic"` |
| Choose decomposition framework | `decomposition` | `--domain decomposition "MECE logic tree"` |
| Pick prioritization technique | `prioritization` | `--domain prioritization "impact feasibility"` |
| Select analysis tools | `analysis` | `--domain analysis "root cause benchmark"` |
| Identify cognitive biases | `biases` | `--domain biases "confirmation anchoring"` |
| Structure communication | `communication` | `--domain communication "pyramid executive"` |
| Apply mental models | `heuristics` | `--domain heuristics "first principles inversion"` |
| Improve team dynamics | `team` | `--domain team "red team brainstorm"` |

### Step 4: Apply the Framework

Guide the user through the recommended process:

1. **Define**: Help craft a precise problem statement
2. **Decompose**: Build the recommended logic tree (MECE)
3. **Prioritize**: Apply 80/20 to focus on what matters
4. **Plan**: Design specific analyses for priority issues
5. **Analyze**: Guide data gathering and hypothesis testing
6. **Synthesize**: Extract 'so what' insights and build the argument
7. **Communicate**: Structure the recommendation for the audience

---

## Search Reference

### Available Domains

| Domain | Records | Use For | Example Keywords |
|--------|---------|---------|------------------|
| `steps` | 7 | Understanding each step of the methodology | define, disaggregate, prioritize, analyze, synthesize, communicate |
| `problem-types` | 8 | Classifying the type of problem | diagnostic, opportunity, wicked, prediction, negotiation, design |
| `decomposition` | 18 | Choosing how to break down the problem | issue tree, hypothesis tree, MECE, profitability, process, scenario |
| `prioritization` | 8 | Deciding where to focus effort | pareto, impact-feasibility, sensitivity, dot-voting, MoSCoW, weighted |
| `analysis` | 15 | Selecting analytical methods | benchmark, root cause, regression, scenario, fermi, A/B test, pre-mortem |
| `biases` | 12 | Identifying thinking errors to avoid | confirmation, anchoring, sunk cost, groupthink, overconfidence, framing |
| `communication` | 10 | Structuring findings and recommendations | pyramid, SCR, action titles, BLUF, one-page, storytelling, day-1 answer |
| `heuristics` | 13 | Applying mental models to the problem | first principles, inversion, second-order, Bayesian, Occam, leverage |
| `team` | 10 | Improving team problem-solving effectiveness | red team, brainstorm, psychological safety, hypothesis-driven, workplan |

---

## Example Workflow

**User request:** "Our company's revenue has declined 20% this year despite the market growing. Help me figure out what's going on and what to do about it."

### Step 1: Understand the Problem
- Problem type: Business Performance / Diagnostic
- Complexity: Ill-structured (multiple potential causes)
- Keywords: revenue, decline, market growth, performance gap
- Context: Company underperforming vs market

### Step 2: Generate Problem-Solving Plan (REQUIRED)

```bash
python3 .agents/skills/problem-solving-pro/scripts/search.py --stdin --plan -f markdown <<'THINK_BETTER_EOF_7f3a'
Our company's revenue has declined 20% this year despite the market growing. Help me figure out what's going on and what to do about it.
THINK_BETTER_EOF_7f3a
```

**Output:** Complete plan with profitability tree decomposition, Pareto prioritization, benchmarking + root cause analysis toolkit, pyramid principle communication, and bias warnings (confirmation bias, anchoring).

### Step 3: Deep-Dive Searches

```bash
# Get decomposition framework details
python3 .agents/skills/problem-solving-pro/scripts/search.py "profitability revenue cost" --domain decomposition

# Get root cause analysis methodology
python3 .agents/skills/problem-solving-pro/scripts/search.py "root cause 5 whys diagnostic" --domain analysis

# Check for relevant biases
python3 .agents/skills/problem-solving-pro/scripts/search.py "confirmation bias anchoring" --domain biases
```

### Step 4: Apply the Framework

Walk the user through:
1. **Define**: "Revenue declined 20% YoY (vs market +5%) — identify root drivers and recommend recovery actions within 90 days"
2. **Decompose**: Profitability tree → Revenue (Price × Volume) → Costs (Fixed + Variable)
3. **Prioritize**: Which branches explain >80% of the decline?
4. **Analyze**: Benchmark against competitors, test hypotheses on each priority branch
5. **Synthesize**: Group findings into themes, extract 'so what' for each
6. **Communicate**: Start with the recommendation (pyramid), support with evidence

**Then:** Synthesize the plan + domain searches into a structured problem-solving approach for the user.

---

## Output Formats

The `--plan` flag supports two output formats:

- ASCII box (default): best for terminal display
- `-f markdown`: best for chat and documents
- `--json`: the plan as data

---

## Key Principles

1. **Start with the problem, not the solution** — Invest time in defining and framing before solving
2. **Disaggregate before analyzing** — Break it down MECE before diving into any branch
3. **Prioritize ruthlessly** — 80/20: focus on the vital few issues that drive the answer
4. **Be hypothesis-driven** — State your best guess early, then test it (Day 1 Answer)
5. **So what?** — Every finding must pass the 'so what' test to matter
6. **Answer first** — Lead with the recommendation, support with evidence (Pyramid Principle)
7. **Watch for biases** — Confirmation bias, anchoring, and groupthink are the most dangerous
8. **Iterate** — Update your answer as evidence comes in (Bayesian updating)
9. **Simple first** — Use the simplest analysis that answers the question (Occam's Razor)
10. **Communication is the final product** — The best analysis is worthless if you can't drive action
11. **What you'd have to believe** — When stuck or attached to an idea, ask "what would have to be true for this to be the right answer?" to break framing ruts and rigorously test assumptions.

---

## Constraints

- **Always start with Step 2** (`--plan`) before doing domain searches — the plan provides context for everything else
- **Problem statement must be specific** — reject vague statements; ask for measurable outcomes
- **Keep the logic tree to 3 levels max** — deeper than 3 loses clarity
- **Limit to top 3 priority branches** — 80/20 rule; don't analyze everything
- **When user is vague, ask** — if the problem type is unclear, ask: "What would success look like?" before running the plan

---

## Error Handling

If a command fails (an `Error:` or `usage:` message, or a non-zero exit), show the error to the
user. If it names an input you chose (a flag value, scores, a workspace name), fix that and
re-run; otherwise stop. Never present a plan the script did not produce.

1. **Check Python**: Run `python3 --version` or `python --version`. If neither is found, tell the user and ask before installing anything
2. **Manual fallback**: Only if Python is missing and the user does not want to install it, apply the Key Principles above manually and say clearly that the script did not run:
   - Ask the user to describe the problem → classify the type yourself
   - Suggest a decomposition framework (e.g., Issue Tree for diagnostic, Hypothesis Tree for uncertain causes)
   - Walk through the 7-step methodology: Define → Decompose → Prioritize → Plan → Analyze → Synthesize → Communicate
   - Warn about the 3 most common biases for that problem type
3. **Script errors**: If `search.py` returns no results, try broader keywords or search a different domain
4. **Non-English queries**: Classification matches English keywords only; the framework content is in English. For other languages, translate the user's key terms to English, or pass `--type` and `--category` yourself
5. **"No ... matched clearly"**: the plan used generic defaults. Re-run with `--type` and `--category` (the note lists the values)

