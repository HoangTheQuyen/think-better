# Research: Make-Decision Skill

**Date**: 2026-03-03
**Purpose**: Resolve all technical unknowns and document design decisions for the make-decision skill.

## R1: Decision Frameworks from the Methodology

**Decision**: 10 frameworks identified, all derived from the structured methodology's approach to choosing between options.

**Rationale**: The methodology emphasizes hypothesis-driven analysis, MECE decomposition, and iterative testing. Decision frameworks are extracted from how the methodology applies these concepts to choosing between alternatives.

**Frameworks**:

| # | Framework | Description | Best For |
|---|-----------|-------------|----------|
| 1 | Hypothesis-Driven Decision Tree | Form a Day One answer (initial hypothesis), decompose into testable sub-hypotheses, gather evidence, refine. Avoids boiling-the-ocean analysis. | Complex strategic decisions with incomplete information |
| 2 | Logic Tree Option Decomposition | Use MECE logic trees to map ALL options and sub-options exhaustively. Ensures no alternatives are missed. | Multi-option decisions where option space is unclear |
| 3 | Weighted Criteria Matrix | Define criteria, assign weights based on priorities, score each option 1-5, calculate weighted totals. Explicit and auditable. | Multi-option decisions with clear evaluation criteria |
| 4 | Sensitivity Analysis Decision | Test which assumptions/criteria changes would flip the decision. Identifies what matters most and what's noise. | Decisions where confidence in inputs is uncertain |
| 5 | Expected Value Calculation | Assign probabilities to outcomes, multiply by value, sum for each option. Rational under uncertainty. | Decisions with quantifiable outcomes and probabilities |
| 6 | Scenario Planning Matrix | Define 2-3 key uncertainties, build 4-9 scenarios, evaluate each option across scenarios. Robust choice under ambiguity. | Strategic decisions with high external uncertainty |
| 7 | Pros-Cons-Fixes Analysis | List pros and cons for each option, then for each con ask "can it be fixed?" — transforms binary into nuanced evaluation. | Binary or few-option decisions needing quick assessment |
| 8 | Pre-Mortem Decision Test | Assume the decision failed — work backward to identify what went wrong. Tests blind spots before committing. | High-stakes irreversible decisions |
| 9 | Reversibility Filter | Classify decision as one-way door (irreversible) or two-way door (reversible). Two-way doors → decide fast and iterate. One-way → invest in analysis. | Meta-framework for deciding how much analysis to invest |
| 10 | Iterative Hypothesis Testing | Start with best guess, design minimum viable test, update based on evidence, repeat. Bayesian approach to decisions. | Data-poor environments where learning is possible before committing |

**Alternatives Considered**: Generic frameworks like RAPID, DACI, Cynefin were considered but rejected — they are organizational governance models, not analytical decision methods aligned with the methodology.

## R2: Decision Types Classification

**Decision**: 8 decision types identified, mapped to the methodology's problem categorization.

**Rationale**: The methodology classifies problems by structure and uncertainty. Decision types extend this to the choice-making phase.

| # | Type | Characteristics | Recommended Framework | Anti-Patterns |
|---|------|----------------|----------------------|---------------|
| 1 | Binary Choice | Two clear options (yes/no, A/B). Often seems simple but may hide complexity. | Pros-Cons-Fixes, Pre-Mortem | False binary — forcing two options when more exist |
| 2 | Multi-Option Selection | 3+ options to evaluate. Needs structured comparison. | Weighted Criteria Matrix, Logic Tree | Choice overload — too many options without filtering |
| 3 | Resource Allocation | Distributing limited resources (budget, time, people) across competing priorities. | Expected Value, Sensitivity Analysis | Peanut butter spreading — dividing equally instead of prioritizing |
| 4 | Strategic Direction | Long-term, high-impact, often irreversible. Shapes future option space. | Scenario Planning, Hypothesis-Driven Tree | Analysis paralysis — over-analyzing when decisive action needed |
| 5 | Operational / Tactical | Short-term, lower-impact, typically reversible. Optimize within existing strategy. | Reversibility Filter, Iterative Testing | Over-engineering — applying heavy frameworks to lightweight decisions |
| 6 | Decision Under Uncertainty | Key variables unknown or unknowable. Must decide despite incomplete data. | Scenario Planning, Expected Value, Bayesian Update | False precision — pretending you have more certainty than you do |
| 7 | Group / Stakeholder Decision | Multiple people with different interests must align. Politics and communication matter. | Pre-Mortem, Weighted Matrix (visible), Facilitation | Groupthink — premature consensus without challenging assumptions |
| 8 | Time-Pressured Decision | Deadline forces decision before ideal analysis is complete. Must optimize speed vs. quality. | Reversibility Filter, 80/20 Criteria, Day One Answer | Premature closure — deciding too fast; OR delay — missing the window |

## R3: Cognitive Biases in Decision-Making

**Decision**: 12 biases selected, focused on those the methodology explicitly warns against during option evaluation.

**Rationale**: The methodology emphasizes hypothesis-driven thinking specifically to counter biases. These 12 represent the most dangerous for decision-making.

| # | Bias | Impact on Decisions | Debiasing Strategy |
|---|------|--------------------|--------------------|
| 1 | Confirmation Bias | Seeking evidence that supports preferred option, ignoring contradictory data | Assign devil's advocate; explicitly seek disconfirming evidence |
| 2 | Anchoring Effect | Over-weighting first piece of information (first option, first price, first opinion) | Generate criteria BEFORE seeing options; use structured scoring |
| 3 | Sunk Cost Fallacy | Continuing with failing option because of past investment rather than future value | Evaluate each option as if starting fresh today (zero-based) |
| 4 | Status Quo Bias | Defaulting to current state because change feels risky, even when change is superior | Explicitly compare status quo as one option with same rigor as alternatives |
| 5 | Overconfidence | Overestimating accuracy of own predictions and judgment; too-narrow confidence intervals | Use pre-mortem; assign confidence levels and track calibration |
| 6 | Framing Effect | Different conclusions from same data depending on how options are presented (gain vs. loss frame) | Reframe decision both as gains and losses; check if conclusion changes |
| 7 | Availability Heuristic | Overweighting vivid, recent, or easily recalled examples when estimating probabilities | Use base rates; seek systematic data rather than anecdotes |
| 8 | Groupthink | Team converges on preferred option without critical evaluation; dissent suppressed | Structured dissent: pre-mortem, red team, anonymous input |
| 9 | Planning Fallacy | Underestimating time, cost, and risk of chosen option while overestimating benefits | Use reference class forecasting; compare to similar past decisions |
| 10 | Loss Aversion | Weighing potential losses ~2x more than equivalent gains, leading to excessive risk avoidance | Reframe in terms of opportunity cost; ask "what do we lose by NOT acting?" |
| 11 | Recency Bias | Overweighting recent events when evaluating options, ignoring base rates and long-term patterns | Extend time horizon; look at 5-10 year data, not just recent quarter |
| 12 | Survivorship Bias | Drawing conclusions from successful examples while ignoring failures with same approach | Seek failed examples of each option; ask "who tried this and failed?" |

## R4: Analysis Techniques for Decision Evaluation

**Decision**: 10 analysis techniques, all from the methodology's analytical toolkit applied to option evaluation.

| # | Technique | When to Use | Inputs Required | Output |
|---|-----------|-------------|-----------------|--------|
| 1 | Sensitivity Analysis | When decision depends on uncertain assumptions | Key variables, range of values, decision model | Tornado chart showing which variables flip the decision |
| 2 | Break-Even Analysis | When evaluating threshold-based decisions (invest/don't) | Fixed costs, variable costs, revenue per unit | Break-even point; margin of safety |
| 3 | Decision Tree Analysis | When decision involves sequential choices with probabilistic outcomes | Options, probabilities, payoffs at each branch | Expected value for each path; optimal strategy |
| 4 | Scenario Analysis | When multiple external uncertainties interact | 2-3 key uncertainties, 2-3 values each | Scenario matrix; robustness of each option |
| 5 | Relative Value Scoring | When comparing options across incommensurable criteria | Options, criteria, weights | Ranked options with transparent scoring |
| 6 | Opportunity Cost Assessment | When choosing one option means forgoing others | Value of each forgone alternative | True cost of chosen option including what's sacrificed |
| 7 | Risk-Reward Matrix | When options have different risk profiles | Probability of success, magnitude of reward, downside | 2x2 matrix positioning each option |
| 8 | Bayesian Update Protocol | When new evidence arrives during decision process | Prior probability, evidence, likelihood | Updated probability; revised decision |
| 9 | Pre-Mortem Analysis | When testing robustness of favored option before committing | Assumed decision, team participants | List of failure modes, vulnerability assessment |
| 10 | Reference Class Forecasting | When estimating outcomes of chosen option | Similar past decisions, their actual outcomes | Base rate prediction, confidence interval |

## R5: Criteria Templates

**Decision**: 8 domain-specific criteria templates for common decision types.

**Rationale**: The methodology emphasizes that good analysis starts with the right questions. Criteria templates provide starting-point questions tailored to common domains.

| # | Domain | Criteria | Default Weights |
|---|--------|----------|----------------|
| 1 | Technology Selection | Functionality fit, integration ease, total cost, vendor stability, scalability, security, team capability | 20/15/15/10/15/10/15 |
| 2 | Hiring Decision | Skills match, culture fit, growth potential, compensation alignment, availability, references, team complement | 20/15/15/10/10/10/20 |
| 3 | Vendor / Partner Selection | Quality, price, reliability, alignment, flexibility, reputation, integration effort | 20/15/15/15/10/10/15 |
| 4 | Investment / Resource Allocation | Expected return, risk level, strategic alignment, time to value, resource requirement, opportunity cost | 20/15/20/15/15/15 |
| 5 | Market Entry / Expansion | Market size, competition intensity, barrier to entry, capability fit, regulatory risk, timing, profitability | 20/15/10/15/10/15/15 |
| 6 | Product Feature Prioritization | User impact, revenue impact, implementation effort, strategic alignment, urgency, dependency | 25/20/15/15/15/10 |
| 7 | Organizational Change | Impact on people, implementation complexity, reversibility, cost, timeline, stakeholder support | 20/15/15/15/15/20 |
| 8 | Location / Facility | Cost, talent access, infrastructure, quality of life, regulatory environment, strategic proximity | 20/15/15/15/15/20 |

## R6: Facilitation Techniques for Group Decisions

**Decision**: 8 facilitation techniques from the methodology's team problem-solving approach.

| # | Technique | Group Size | Time | When to Use |
|---|-----------|-----------|------|-------------|
| 1 | Pre-Mortem | 3-12 | 30-60 min | Before committing to high-stakes decision; surfaces hidden risks |
| 2 | Red Team Challenge | 4-8 | 60-120 min | When group seems too aligned; needs adversarial testing |
| 3 | Nominal Group Technique | 5-15 | 45-90 min | When dominant voices suppress diverse input |
| 4 | Structured Debate (Steel Man) | 4-10 | 60-90 min | When two strong options exist; need rigorous comparison |
| 5 | Dot Voting Prioritization | 3-20 | 15-30 min | Quick democratic ranking of criteria or options |
| 6 | Anonymous Input Round | 3-30 | 20-40 min | When hierarchy or politics bias open discussion |
| 7 | Devil's Advocate Assignment | 3-8 | 30-60 min | When a preferred option needs critical challenge before commitment |
| 8 | Workplan Alignment Session | 3-10 | 60-120 min | After decision made; align team on execution plan |

## R7: Architectural Decisions

### Decision: Follow problem-solving-pro pattern exactly

**Rationale**: Proven architecture, consistent user experience, code reuse potential.

**Structure**: 
- `core.py`: BM25 engine with CSV_CONFIG for 6 domains (vs. 9 in problem-solving-pro)
- `search.py`: CLI with `--plan`, `--domain`, `--persist`, `--journal`, `--matrix` flags
- `advisor.py`: `DecisionAdvisor` class with `generate()`, `format_ascii_box()`, `format_markdown()`, `persist_plan()`, `create_journal()`, `generate_matrix()`

### Decision: Journal storage at `.decisions/` directory

**Rationale**: User clarification pending (from clarify phase), defaulting to `.decisions/` at workspace root, one markdown file per decision entry named by date and slug.

### Decision: Comparison matrix as advisor.py method

**Rationale**: Matrix generation is a formatting concern, not a search concern. Belongs in advisor.py alongside plan generation and journal creation.

## R8: Content Derivation Constraint

**Decision**: All content strictly derived from the structured problem-solving methodology.

**Constraint**: No book title, author name, or direct quotations. Content is expressed as general methodology principles.

**How enforced**: Every CSV entry must trace to a methodology concept (hypothesis trees, MECE, 80/20, Day One answer, workplanning, pyramid principle, etc.) rather than external sources.
