# CLI Interface Contract: make-decision search.py

**Date**: 2026-03-03
**Type**: Command-line interface
**Entry Point**: `python3 prompts/make-decision/scripts/search.py`

## Commands

### 1. Decision Plan Generation

```bash
python3 prompts/make-decision/scripts/search.py "<decision_description>" --plan [-p "Project Name"] [-f markdown|ascii] [--persist]
```

**Input**:
- `<decision_description>` (positional, required): Natural language description of the decision
- `--plan` (flag, required for this command): Triggers plan generation mode
- `-p` / `--project` (optional): Project name for file persistence
- `-f` / `--format` (optional, default: "ascii"): Output format — "ascii" or "markdown"
- `--persist` (optional): Save plan to `decision-plans/{project-slug}/PLAN.md`

**Output** (stdout):
```
╔══════════════════════════════════════════════════════════╗
║           DECISION-MAKING PLAN: {description}           ║
╠══════════════════════════════════════════════════════════╣
║ Decision Type: {classified type}                        ║
║ Complexity: {low/medium/high}                           ║
╠══════════════════════════════════════════════════════════╣
║ RECOMMENDED FRAMEWORK                                   ║
║ {framework name}: {brief description}                   ║
║ Steps: 1. ... 2. ... 3. ...                            ║
╠══════════════════════════════════════════════════════════╣
║ EVALUATION CRITERIA                                     ║
║ {criteria template for this domain}                     ║
║ Weights: {suggested weights}                            ║
╠══════════════════════════════════════════════════════════╣
║ ANALYSIS TECHNIQUES                                     ║
║ 1. {technique}: {why for this decision}                ║
║ 2. {technique}: {why for this decision}                ║
╠══════════════════════════════════════════════════════════╣
║ BIAS WARNINGS                                           ║
║ ⚠ {bias}: {how it applies here}                       ║
║ ⚠ {bias}: {how it applies here}                       ║
║ Debiasing: {concrete actions}                           ║
╠══════════════════════════════════════════════════════════╣
║ GROUP FACILITATION (if applicable)                      ║
║ {technique}: {why for this decision context}           ║
╠══════════════════════════════════════════════════════════╣
║ ANTI-PATTERNS TO AVOID                                  ║
║ ✗ {anti-pattern from decision type}                    ║
╠══════════════════════════════════════════════════════════╣
║ DECISION CHECKLIST                                      ║
║ □ Problem clearly defined                              ║
║ □ Options exhaustively listed (MECE)                   ║
║ □ Criteria defined before evaluating                   ║
║ □ Key assumptions identified                           ║
║ □ Sensitivity tested                                   ║
║ □ Bias check completed                                 ║
║ □ Stakeholders aligned                                 ║
║ □ Decision documented (journal)                        ║
╚══════════════════════════════════════════════════════════╝
```

**Exit codes**: 0 = success, 1 = error (invalid input, file write failure)

---

### 2. Domain Search

```bash
python3 prompts/make-decision/scripts/search.py "<query>" --domain <domain> [-n <max_results>]
```

**Input**:
- `<query>` (positional, required): Search terms
- `--domain` (required for this command): One of: `frameworks`, `types`, `biases`, `analysis`, `criteria`, `facilitation`
- `-n` / `--results` (optional, default: 3): Maximum results to return

**Output** (stdout):
```
=== DOMAIN: {domain} | Query: "{query}" | Results: {count} ===

[1] {primary field value} ({category})
    {description}
    When to Use: {when_to_use}
    {domain-specific fields...}

[2] ...
```

**Exit codes**: 0 = success (including 0 results), 1 = error

---

### 3. Auto-Domain Search

```bash
python3 prompts/make-decision/scripts/search.py "<query>" [-n <max_results>]
```

**Input**:
- `<query>` (positional, required): Search terms
- No `--domain` flag: auto-detects relevant domains

**Output** (stdout): Results from all matching domains, grouped by domain.

---

### 4. Decision Journal

```bash
python3 prompts/make-decision/scripts/search.py --journal "<decision_statement>" [-p "Project Name"]
python3 prompts/make-decision/scripts/search.py --journal --review
python3 prompts/make-decision/scripts/search.py --journal --update "<journal_id>" --outcome "<actual_outcome>"
```

**Sub-commands**:

#### Create Journal Entry
- `--journal "<decision_statement>"`: Creates new journal entry
- `-p` (optional): Project name for context
- **Output**: Creates `.decisions/{date}-{slug}.md`, prints path to stdout

#### Review Past Decisions
- `--journal --review`: Lists all journal entries
- **Output** (stdout):
```
=== DECISION JOURNAL: {count} entries ===

[1] 2026-03-03 | Vendor Selection | Confidence: High | Status: Decided
[2] 2026-02-28 | Tech Stack Choice | Confidence: Medium | Status: Reviewed
...
```

#### Update with Outcome
- `--journal --update "<id>" --outcome "<text>"`: Updates existing entry with actual outcome
- **Output**: Updated file path, reflection prompt to stdout

---

### 5. Comparison Matrix

```bash
python3 prompts/make-decision/scripts/search.py --matrix "<options_description>" [-c "criteria1,criteria2,..."]
```

**Input**:
- `--matrix "<options_description>"`: Natural language describing the options to compare
- `-c` / `--criteria` (optional): Comma-separated criteria. If omitted, auto-suggested from criteria templates.

**Output** (stdout):
```
=== COMPARISON MATRIX ===
Decision: {description}

              | Criteria 1 (w:25) | Criteria 2 (w:20) | ... | TOTAL
Option A      |     ? / 5         |     ? / 5         | ... |   ?
Option B      |     ? / 5         |     ? / 5         | ... |   ?
Option C      |     ? / 5         |     ? / 5         | ... |   ?

Scoring Guide:
- Criteria 1: 5=excellent fit, 4=good, 3=adequate, 2=poor, 1=unacceptable
- Criteria 2: ...

Instructions: Fill in scores (1-5) for each cell, then calculate weighted totals.
```

---

## Available Domains

| Domain Key | CSV File | Primary Field | Description |
|-----------|----------|---------------|-------------|
| `frameworks` | decision-frameworks.csv | Framework | Decision-making methodologies |
| `types` | decision-types.csv | Decision Type | Decision classifications |
| `biases` | cognitive-biases.csv | Bias | Cognitive biases in decisions |
| `analysis` | analysis-techniques.csv | Technique | Analytical evaluation methods |
| `criteria` | criteria-templates.csv | Domain | Evaluation criteria templates |
| `facilitation` | facilitation.csv | Technique | Group decision techniques |

## Error Handling

| Condition | Behavior |
|-----------|----------|
| No query provided | Print usage help, exit 1 |
| Invalid domain name | Print available domains, exit 1 |
| No search results | Print "No results found. Try: {suggestions}", exit 0 |
| Journal directory doesn't exist | Auto-create `.decisions/`, continue |
| Journal file already exists | Append timestamp suffix, warn on stderr |
| File write permission denied | Print error to stderr, exit 1 |
