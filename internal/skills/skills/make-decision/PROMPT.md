# Goal

Help users make better decisions in minutes instead of hours by applying proven frameworks, detecting cognitive biases, and structuring the evaluation process.

# make-decision

Comprehensive decision-making framework for structured evaluation of options. Contains 10 decision frameworks, 8 decision type classifications, 12 cognitive biases with debiasing strategies, 10 analysis techniques, 8 domain-specific criteria templates, and 8 group facilitation techniques. Searchable knowledge base with BM25 ranking that auto-recommends frameworks, criteria, and bias warnings tailored to your specific decision type.

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

When user requests decision-making help (decide, choose, compare, evaluate, select, prioritize, trade-off, weigh options), follow this workflow:

### Step 1: Understand the Decision

Extract key information from user's decision description:
- **Decision type**: Binary choice, multi-option, resource allocation, strategic, operational, under uncertainty, group/stakeholder, time-pressured
- **Options**: What alternatives are being considered?
- **Context**: Industry, stakes, timeline, stakeholders, reversibility
- **Constraints**: Budget, time, resources, dependencies

### Step 2: Generate Decision Plan (REQUIRED)

**Always start with `--plan`** to get comprehensive recommendations:

```bash
python3 prompts/make-decision/scripts/search.py "<decision_description>" --plan [-p "Project Name"]
```

This command:
1. Classifies the decision type automatically
2. Searches across all 6 knowledge domains
3. Recommends the best framework for this type of decision
4. Identifies relevant evaluation criteria with weights
5. Warns about cognitive biases likely to affect this decision
6. Suggests analysis techniques and facilitation methods
7. Includes anti-patterns to avoid and a decision checklist

**Example:**
```bash
python3 prompts/make-decision/scripts/search.py "choosing between AWS and Azure for cloud migration" --plan -p "Cloud Migration"
```

### Step 2b: Persist Decision Plan

To save the plan for reference:

```bash
python3 prompts/make-decision/scripts/search.py "<decision>" --plan --persist -p "Project Name"
```

This creates:
- `decision-plans/project-name/PLAN.md` — Complete decision-making plan

### Step 3: Deep-Dive Domain Searches

Use when the plan's recommendation needs more detail, OR when user asks about a specific topic (e.g., "what biases should I watch for?"):

```bash
python3 prompts/make-decision/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

**When to use domain searches:**

| Need | Domain | Example |
|------|--------|---------|
| Choose a decision framework | `frameworks` | `--domain frameworks "hypothesis uncertainty"` |
| Classify the decision type | `types` | `--domain types "binary strategic"` |
| Identify cognitive biases | `biases` | `--domain biases "confirmation sunk cost"` |
| Select analysis techniques | `analysis` | `--domain analysis "sensitivity break-even"` |
| Get evaluation criteria | `criteria` | `--domain criteria "technology vendor"` |
| Plan group facilitation | `facilitation` | `--domain facilitation "pre-mortem red team"` |

### Step 4: Compare Options

Use when user has 2+ named options to compare (e.g., "A vs B vs C"). Generate a comparison matrix:

```bash
python3 prompts/make-decision/scripts/search.py --matrix "AWS vs Azure vs GCP" [-c "cost,scalability,security"]
```

This generates a weighted comparison matrix with criteria auto-suggested from templates (or custom criteria via `-c`), scoring guide, and calculation instructions.

### Step 5: Document the Decision

Use after reaching a conclusion. Creates a journal entry for future reflection and calibration:

```bash
# Create journal entry
python3 prompts/make-decision/scripts/search.py --journal "Choosing cloud provider for Q3 migration"

# Review past decisions
python3 prompts/make-decision/scripts/search.py --journal --review

# Update with actual outcome (weeks/months later)
python3 prompts/make-decision/scripts/search.py --journal --update "choosing-cloud" --outcome "Chose AWS, migration completed on time, 15% under budget"
```

---

## Search Reference

### Available Domains

| Domain | Records | Use For | Example Keywords |
|--------|---------|---------|------------------|
| `frameworks` | 10 | Choosing a decision methodology | hypothesis, logic tree, weighted matrix, sensitivity, expected value, scenario, pros-cons, pre-mortem, reversibility, iterative |
| `types` | 8 | Classifying the type of decision | binary, multi-option, resource allocation, strategic, operational, uncertainty, group, time-pressured |
| `biases` | 12 | Identifying thinking errors to avoid | confirmation, anchoring, sunk cost, status quo, overconfidence, framing, availability, groupthink, planning fallacy, loss aversion |
| `analysis` | 10 | Selecting analytical methods | sensitivity, break-even, decision tree, scenario, scoring, opportunity cost, risk-reward, bayesian, pre-mortem, reference class |
| `criteria` | 8 | Getting evaluation criteria templates | technology, hiring, vendor, investment, market entry, product feature, organizational change, location |
| `facilitation` | 8 | Planning group decision sessions | pre-mortem, red team, nominal group, debate, dot voting, anonymous input, devil's advocate, workplan |

---

## Example Workflow

**User request:** "We need to choose between building in-house, buying a SaaS solution, or hiring a development agency for our new CRM system."

### Step 1: Understand the Decision
- Decision type: Multi-Option Selection / Technology Selection
- Options: Build in-house, Buy SaaS, Hire agency
- Context: Technology decision with long-term impact
- Constraints: Budget, timeline, team capacity

### Step 2: Generate Decision Plan

```bash
python3 prompts/make-decision/scripts/search.py "build vs buy vs outsource CRM system" --plan -p "CRM Decision"
```

**Output:** Complete plan with decision type classification (Multi-Option Selection), recommended framework (Weighted Criteria Matrix), Technology Selection criteria with weights, analysis techniques (Sensitivity Analysis, Opportunity Cost), bias warnings (Status Quo Bias, Sunk Cost Fallacy), and decision checklist.

### Step 3: Deep-Dive Searches

```bash
# Get detailed framework guidance
python3 prompts/make-decision/scripts/search.py "weighted criteria evaluation" --domain frameworks

# Check for relevant biases
python3 prompts/make-decision/scripts/search.py "status quo sunk cost technology" --domain biases

# Get facilitation guidance for team decision
python3 prompts/make-decision/scripts/search.py "structured debate team" --domain facilitation
```

### Step 4: Compare Options

```bash
python3 prompts/make-decision/scripts/search.py --matrix "Build in-house vs Buy SaaS vs Hire agency"
```

### Step 5: Document the Decision

```bash
python3 prompts/make-decision/scripts/search.py --journal "CRM platform: build vs buy vs outsource" -p "CRM Decision"
```

**Then:** Synthesize the plan, searches, and matrix into a structured decision recommendation for the user, walking them through each step of the recommended framework.

---

## Output Formats

The `--plan` flag supports two output formats:

```bash
# ASCII box (default) - best for terminal display
python3 prompts/make-decision/scripts/search.py "market entry strategy" --plan

# Markdown - best for documentation
python3 prompts/make-decision/scripts/search.py "market entry strategy" --plan -f markdown
```

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
10. **Document and reflect** — Keep a decision journal to improve calibration over time

---

## Constraints

- **Always start with Step 2** (`--plan`) before doing domain searches — the plan provides context for everything else
- **Do NOT skip bias detection** — every decision has biases; explicitly address them
- **Keep recommendations under 500 words** — decision-makers skim, not read
- **Never present more than 5 criteria** — choice overload defeats the purpose
- **When in doubt, ask** — if the user's decision type is unclear, ask one clarifying question before running the plan

---

## Error Handling

If the Python scripts fail or are unavailable:

1. **Check Python**: Run `python3 --version` — if not found, guide the user to install it
2. **Manual fallback**: If scripts cannot run, apply the Key Decision-Making Principles above manually:
   - Ask user to describe the decision → classify the type yourself
   - Suggest a framework based on the type (e.g., Weighted Matrix for multi-option, Pros-Cons-Fixes for binary)
   - Warn about the 3 most common biases for that decision type
   - Walk through the framework step by step
3. **Script errors**: If `search.py` returns no results, try broader keywords or search a different domain
4. **Non-English queries**: The knowledge base is English-only. Translate the user's key terms to English before calling `search.py` — this ensures rich results for any language

