# Quickstart: Make-Decision Skill

## Prerequisites

- Python 3.10+ installed
- No external packages required (standard library only)

## Verify Setup

```bash
python3 --version
# Expected: Python 3.10.x or higher
```

## Basic Usage

### 1. Generate a Decision Plan (Start Here)

```bash
python3 prompts/make-decision/scripts/search.py "choosing between AWS and Azure for our cloud migration" --plan
```

This will:
- Auto-classify the decision type (Technology Selection)
- Recommend the best framework (Weighted Criteria Matrix)
- Suggest evaluation criteria with weights
- Warn about relevant biases (anchoring, status quo bias)
- Provide a step-by-step decision process

### 2. Search for Specific Concepts

```bash
# Search for a decision framework
python3 prompts/make-decision/scripts/search.py "hypothesis driven" --domain frameworks

# Search for a cognitive bias
python3 prompts/make-decision/scripts/search.py "sunk cost" --domain biases

# Search across all domains (auto-detect)
python3 prompts/make-decision/scripts/search.py "group decision uncertainty"
```

### 3. Save a Decision Plan

```bash
python3 prompts/make-decision/scripts/search.py "vendor selection for CRM" --plan --persist -p "CRM Vendor"
# Creates: decision-plans/crm-vendor/PLAN.md
```

### 4. Create a Decision Journal Entry

```bash
python3 prompts/make-decision/scripts/search.py --journal "Choosing CRM vendor for sales team"
# Creates: .decisions/2026-03-03-choosing-crm-vendor.md
```

### 5. Generate a Comparison Matrix

```bash
python3 prompts/make-decision/scripts/search.py --matrix "Compare Salesforce vs HubSpot vs Pipedrive for CRM"
# Outputs: Weighted comparison matrix with suggested criteria
```

## Available Domains

| Domain | Command | What You Get |
|--------|---------|-------------|
| `frameworks` | `--domain frameworks` | Decision-making methodologies |
| `types` | `--domain types` | Decision type classifications |
| `biases` | `--domain biases` | Cognitive biases + debiasing strategies |
| `analysis` | `--domain analysis` | Analytical evaluation techniques |
| `criteria` | `--domain criteria` | Domain-specific criteria templates |
| `facilitation` | `--domain facilitation` | Group decision techniques |

## Typical Workflow

1. **Describe** your decision → `--plan` generates a complete approach
2. **Deep-dive** into specific areas → `--domain` searches for details
3. **Compare** options → `--matrix` creates structured comparison
4. **Document** the decision → `--journal` creates a persistent record
5. **Review** later → `--journal --review` lists past decisions
