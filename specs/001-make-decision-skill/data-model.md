# Data Model: Make-Decision Skill

**Date**: 2026-03-03
**Source**: [spec.md](spec.md) + [research.md](research.md)

## Entities

### 1. Decision Framework

A structured methodology for evaluating and choosing between options, derived from the source methodology.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Framework | string | yes | Name of the framework (unique identifier) |
| Category | string | yes | Classification: hypothesis-driven, decomposition, evaluation, stress-test, meta-framework |
| Keywords | string | yes | Comma-separated search terms for BM25 matching |
| Description | string | yes | 1-2 sentence explanation of the framework |
| When to Use | string | yes | Decision contexts where this framework is most appropriate |
| Steps | string | yes | Numbered step-by-step process to apply the framework |
| Strengths | string | yes | What this framework does well |
| Limitations | string | yes | Known weaknesses or blind spots |
| Best For | string | yes | Decision types this framework pairs with (references Decision Type entity) |
| Complexity | string | yes | Low / Medium / High — effort to apply |

**Validation Rules**:
- Framework name must be unique across all entries
- Keywords must contain at least 3 terms
- Steps must contain numbered items (1. 2. 3.)
- Best For must reference valid Decision Type names

**Relationships**:
- Decision Type → recommended frameworks (many-to-many via Best For field)
- Analysis Technique → used within framework steps

---

### 2. Decision Type

A classification of decisions by characteristics, determining which frameworks and analysis techniques to recommend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Decision Type | string | yes | Name of the type (unique identifier) |
| Keywords | string | yes | Comma-separated search terms |
| Characteristics | string | yes | Defining features of this decision category |
| Recommended Frameworks | string | yes | Comma-separated framework names |
| Analysis Methods | string | yes | Comma-separated analysis technique names |
| Common Pitfalls | string | yes | Anti-patterns — mistakes to avoid |
| Warning Signs | string | yes | Indicators that suggest this decision type |
| Example Scenarios | string | yes | Concrete examples of this type |

**Validation Rules**:
- Decision Type name must be unique
- Recommended Frameworks must reference valid Framework names
- Analysis Methods must reference valid Analysis Technique names

**Relationships**:
- Framework (many-to-many) — referenced by Recommended Frameworks
- Analysis Technique (many-to-many) — referenced by Analysis Methods
- Cognitive Bias — certain biases are more dangerous for certain types

---

### 3. Cognitive Bias

A systematic pattern of deviation from rational judgment, with detection methods and debiasing strategies.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Bias | string | yes | Name of the bias (unique identifier) |
| Category | string | yes | Classification: information-processing, social, memory, probability, emotional |
| Keywords | string | yes | Comma-separated search terms |
| Description | string | yes | What the bias is and how it manifests |
| Impact on Decisions | string | yes | How this bias distorts decision-making specifically |
| How to Detect | string | yes | Warning signs that this bias is operating |
| Debiasing Strategy | string | yes | Concrete actions to counteract this bias |
| Example | string | yes | Real-world decision scenario showing this bias |
| Severity | string | yes | High / Medium / Low — impact magnitude on typical decisions |

**Validation Rules**:
- Bias name must be unique
- Severity must be one of: High, Medium, Low
- Debiasing Strategy must be actionable (verb-first)

**Relationships**:
- Decision Type → biases particularly dangerous for that type
- Facilitation Technique → techniques that counter specific biases

---

### 4. Analysis Technique

Analytical methods for evaluating decision options, with clear inputs and outputs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Technique | string | yes | Name of the technique (unique identifier) |
| Category | string | yes | Classification: quantitative, qualitative, hybrid, meta-analysis |
| Keywords | string | yes | Comma-separated search terms |
| Description | string | yes | What the technique does |
| When to Use | string | yes | Decision contexts where this technique adds value |
| Inputs Required | string | yes | What data/information is needed to apply |
| How to Apply | string | yes | Step-by-step application process |
| Output Format | string | yes | What the technique produces (chart, number, ranking, etc.) |
| Strengths | string | yes | What it does well |
| Limitations | string | yes | Known weaknesses |
| Complexity | string | yes | Low / Medium / High |

**Validation Rules**:
- Technique name must be unique
- Complexity must be one of: Low, Medium, High
- How to Apply must contain actionable steps

**Relationships**:
- Decision Type → analysis methods (many-to-many)
- Framework → techniques used within framework steps

---

### 5. Criteria Template

Reusable sets of evaluation criteria for common decision domains with suggested weights.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Domain | string | yes | Decision domain name (unique identifier) |
| Keywords | string | yes | Comma-separated search terms |
| Description | string | yes | What type of decisions this template serves |
| Criteria | string | yes | Comma-separated list of criteria names |
| Default Weights | string | yes | Comma-separated integer weights (must sum to 100) |
| Measurement Guidance | string | yes | How to score each criterion (1-5 scale guidance) |
| Common Mistakes | string | yes | Typical errors when evaluating this domain |

**Validation Rules**:
- Domain must be unique
- Number of Default Weights must match number of Criteria
- Default Weights must sum to 100

**Relationships**:
- Decision Type → templates commonly used for that type
- Framework (Weighted Criteria Matrix) → uses these templates

---

### 6. Facilitation Technique

Methods for improving group decision quality, with structured facilitation guidance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Technique | string | yes | Name of the technique (unique identifier) |
| Category | string | yes | Classification: divergent, convergent, stress-test, alignment |
| Keywords | string | yes | Comma-separated search terms |
| Description | string | yes | What this technique accomplishes |
| When to Use | string | yes | Group decision contexts where this helps |
| Group Size | string | yes | Recommended range (e.g., "3-12") |
| Time Required | string | yes | Estimated duration (e.g., "30-60 min") |
| Steps | string | yes | Facilitation instructions |
| Counters Bias | string | yes | Which cognitive biases this technique mitigates |
| Output | string | yes | What the group produces at the end |

**Validation Rules**:
- Technique name must be unique
- Counters Bias must reference valid Bias names
- Steps must contain numbered facilitation instructions

**Relationships**:
- Cognitive Bias → facilitation techniques that counter it
- Decision Type (Group/Stakeholder) → relevant techniques

---

### 7. Decision Journal Entry (Runtime Entity)

A persistent record of a decision, created by the advisor.py script. Not a CSV — generated as a markdown file.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (slug) | yes | Auto-generated from date + decision title |
| decision_statement | string | yes | Clear statement of the decision being made |
| date_created | date | yes | When the journal entry was created |
| hypothesis | string | yes | Day One answer — initial hypothesis before analysis |
| options | list[string] | yes | Options being considered |
| criteria | list[string] | yes | Criteria used to evaluate options |
| framework_used | string | no | Which decision framework was applied |
| analysis_summary | string | no | Key findings from analysis |
| expected_outcomes | string | yes | What the decision-maker expects will happen |
| confidence_level | string | yes | High / Medium / Low |
| rationale | string | yes | Why this option was chosen |
| actual_outcome | string | no | Filled in later — what actually happened |
| reflection | string | no | Filled in later — comparison of prediction vs. reality |

**State Transitions**:
```
[Created] → decision_statement, hypothesis, options, criteria, confidence filled
    ↓
[Analyzed] → framework_used, analysis_summary updated
    ↓
[Decided] → rationale, expected_outcomes finalized
    ↓
[Reviewed] → actual_outcome, reflection added (days/weeks/months later)
```

**Storage**: `.decisions/{date}-{slug}.md` at workspace root. One file per entry.

---

## Entity Relationship Summary

```
Decision Type ──→ recommends ──→ Decision Framework (many-to-many)
Decision Type ──→ uses ──→ Analysis Technique (many-to-many)
Decision Type ──→ vulnerable to ──→ Cognitive Bias (many-to-many)
Decision Framework ──→ applies ──→ Analysis Technique (within steps)
Cognitive Bias ──→ countered by ──→ Facilitation Technique (many-to-many)
Criteria Template ──→ serves ──→ Decision Type (many-to-one)
Decision Journal Entry ──→ applied ──→ Decision Framework (one-to-one, optional)
Decision Journal Entry ──→ used ──→ Criteria Template (one-to-one, optional)
```

## CSV File Mapping

| Entity | CSV File | Expected Records |
|--------|----------|-----------------|
| Decision Framework | decision-frameworks.csv | 10 |
| Decision Type | decision-types.csv | 8 |
| Cognitive Bias | cognitive-biases.csv | 12 |
| Analysis Technique | analysis-techniques.csv | 10 |
| Criteria Template | criteria-templates.csv | 8 |
| Facilitation Technique | facilitation.csv | 8 |
| **Total** | **6 files** | **56 entries** |

> Decision Journal Entry is a runtime entity generated by advisor.py, not stored in CSV.
