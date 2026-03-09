# Goal

Help users solve complex problems systematically using proven frameworks — turning vague issues into structured analyses with actionable recommendations.

# problem-solving-pro

Comprehensive structured problem-solving framework for tackling any complex challenge. Contains a 7-step methodology, 10 decomposition frameworks, 8 prioritization techniques, 12 analysis tools, 12 cognitive biases with debiasing strategies, 10 communication patterns, 12 mental models, and 10 team dynamics patterns. Searchable database with reasoning-based recommendations that adapts to your specific problem type.

## Prerequisites

Check if Python is installed:

```bash
python3 --version || python --version
```

If Python is not installed, install it based on user's OS:

**macOS:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3
```

**Windows:**
```powershell
winget install Python.Python.3.12
```

---

## How to Use This Workflow

When user requests problem-solving help (analyze, solve, diagnose, decide, structure, decompose, plan, strategy, recommendation), follow this workflow:

### Step 1: Understand the Problem

Extract key information from user's problem description:
- **Problem type**: Business performance, market entry, organizational change, product, cost reduction, innovation, crisis, data/analytics, partnership/M&A, policy
- **Complexity**: Well-structured, ill-structured, wicked
- **Keywords**: revenue, growth, decline, entry, change, innovation, cost, crisis, etc.
- **Context**: Industry, scale, time pressure, stakeholder dynamics

### Step 2: Generate Problem-Solving Plan (REQUIRED)

**Always start with `--plan`** to get comprehensive recommendations with reasoning:

```bash
python3 prompts/problem-solving-pro/scripts/search.py "<problem_description>" --plan [-p "Project Name"]
```

This command:
1. Classifies the problem type automatically
2. Searches across all 9 knowledge domains in parallel
3. Applies reasoning rules to select best frameworks and tools
4. Returns a complete solving plan: methodology, decomposition, analysis, communication, mental models, bias warnings
5. Includes anti-patterns to avoid and a problem-solving checklist

**Example:**
```bash
python3 prompts/problem-solving-pro/scripts/search.py "revenue declining 20% despite market growth" --plan -p "Revenue Recovery"
```

### Step 2b: Persist Problem-Solving Plan

To save the plan for reference:

```bash
python3 prompts/problem-solving-pro/scripts/search.py "<problem>" --plan --persist -p "Project Name"
```

This creates:
- `solving-plans/project-name/PLAN.md` — Complete problem-solving plan

### Step 3: Deep-Dive Domain Searches

Use when the plan's recommendation needs more detail, OR when user asks about a specific topic (e.g., "how do I do a root cause analysis?"):

```bash
python3 prompts/problem-solving-pro/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
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
| `decomposition` | 10 | Choosing how to break down the problem | issue tree, hypothesis tree, MECE, profitability, process, scenario |
| `prioritization` | 8 | Deciding where to focus effort | pareto, impact-feasibility, sensitivity, dot-voting, MoSCoW, weighted |
| `analysis` | 12 | Selecting analytical methods | benchmark, root cause, regression, scenario, fermi, A/B test, pre-mortem |
| `biases` | 12 | Identifying thinking errors to avoid | confirmation, anchoring, sunk cost, groupthink, overconfidence, framing |
| `communication` | 10 | Structuring findings and recommendations | pyramid, SCR, action titles, BLUF, one-page, storytelling, day-1 answer |
| `heuristics` | 12 | Applying mental models to the problem | first principles, inversion, second-order, Bayesian, Occam, leverage |
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
python3 prompts/problem-solving-pro/scripts/search.py "revenue declining 20% despite market growth" --plan -p "Revenue Diagnosis"
```

**Output:** Complete plan with profitability tree decomposition, Pareto prioritization, benchmarking + root cause analysis toolkit, pyramid principle communication, and bias warnings (confirmation bias, anchoring).

### Step 3: Deep-Dive Searches

```bash
# Get decomposition framework details
python3 prompts/problem-solving-pro/scripts/search.py "profitability revenue cost" --domain decomposition

# Get root cause analysis methodology
python3 prompts/problem-solving-pro/scripts/search.py "root cause 5 whys diagnostic" --domain analysis

# Check for relevant biases
python3 prompts/problem-solving-pro/scripts/search.py "confirmation bias anchoring" --domain biases
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

```bash
# ASCII box (default) - best for terminal display
python3 prompts/problem-solving-pro/scripts/search.py "market entry strategy" --plan

# Markdown - best for documentation
python3 prompts/problem-solving-pro/scripts/search.py "market entry strategy" --plan -f markdown
```

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

---

## Constraints

- **Always start with Step 2** (`--plan`) before doing domain searches — the plan provides context for everything else
- **Problem statement must be specific** — reject vague statements; ask for measurable outcomes
- **Keep the logic tree to 3 levels max** — deeper than 3 loses clarity
- **Limit to top 3 priority branches** — 80/20 rule; don't analyze everything
- **When user is vague, ask** — if the problem type is unclear, ask: "What would success look like?" before running the plan

---

## Error Handling

If the Python scripts fail or are unavailable:

1. **Check Python**: Run `python3 --version` — if not found, guide the user to install it
2. **Manual fallback**: If scripts cannot run, apply the Key Principles above manually:
   - Ask the user to describe the problem → classify the type yourself
   - Suggest a decomposition framework (e.g., Issue Tree for diagnostic, Hypothesis Tree for uncertain causes)
   - Walk through the 7-step methodology: Define → Decompose → Prioritize → Plan → Analyze → Synthesize → Communicate
   - Warn about the 3 most common biases for that problem type
3. **Script errors**: If `search.py` returns no results, try broader keywords or search a different domain
4. **Non-English queries**: The knowledge base is English-only. Translate the user's key terms to English before calling `search.py` — this ensures rich results for any language

