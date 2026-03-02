# Feature Specification: Make-Decision Skill

**Feature Branch**: `001-make-decision-skill`  
**Created**: 2025-07-15  
**Status**: Draft  
**Input**: User description: "Skill sau này nên bắt đầu. make-decision"

## Clarifications

### Session 2026-03-03

- Q: What is the scope boundary between make-decision and problem-solving-pro? → A: Complementary but independent. Content must strictly follow the same structured methodology source as problem-solving-pro, focusing on decision/choice phases: hypothesis-driven analysis, logic trees for option evaluation, prioritization, workplanning, and synthesis.
- Q: Should knowledge domains (biases, analysis techniques) overlap with problem-solving-pro? → A: Yes, self-contained. The methodology is the single source of truth; make-decision includes its own complete set of decision-relevant content from the methodology, regardless of what problem-solving-pro already covers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decision Plan Generation (Priority: P1)

A user faces a complex decision (e.g., choosing between job offers, selecting a vendor, deciding on a product strategy) and needs a structured approach. They describe their decision situation and receive a comprehensive decision-making plan that includes: recommended decision framework, evaluation criteria, bias warnings, and a step-by-step process to reach a well-reasoned conclusion.

**Why this priority**: This is the core value proposition — transforming an unstructured decision into a structured, repeatable process. Without this, the skill has no primary use case.

**Independent Test**: Can be fully tested by describing any decision scenario (e.g., "Should I hire contractor A or B?") and verifying a complete decision plan is returned with framework recommendation, criteria, and bias warnings.

**Acceptance Scenarios**:

1. **Given** a user describes a decision situation in natural language, **When** the plan command is executed, **Then** the system returns a structured decision plan containing: recommended framework, evaluation criteria template, relevant bias warnings, and step-by-step decision process.
2. **Given** a user provides a vague decision description (e.g., "help me decide"), **When** the plan command is executed, **Then** the system still generates a plan using default assumptions and flags areas needing more context.
3. **Given** a user describes a decision with multiple stakeholders, **When** the plan command is executed, **Then** the plan includes stakeholder alignment considerations and consensus-building recommendations.

---

### User Story 2 - Domain Knowledge Search (Priority: P2)

A user wants to explore specific decision-making concepts — such as a particular framework (e.g., "weighted scoring matrix"), a cognitive bias (e.g., "sunk cost fallacy"), or a decision type (e.g., "irreversible decisions"). They search the knowledge base and receive relevant entries ranked by relevance.

**Why this priority**: Enables users to learn and explore decision-making knowledge independently. Builds on the plan generation by letting users drill deeper into specific concepts.

**Independent Test**: Can be fully tested by searching for any decision concept (e.g., "anchoring bias") and verifying relevant results are returned with descriptions, examples, and applicability guidance.

**Acceptance Scenarios**:

1. **Given** a user searches for a specific decision framework name, **When** the search is executed, **Then** matching entries are returned ranked by relevance with descriptions and usage guidance.
2. **Given** a user searches for a broad concept (e.g., "group decisions"), **When** the search is executed across all domains, **Then** results from multiple relevant domains are returned (frameworks, biases, facilitation techniques).
3. **Given** a user searches for a term with no exact match, **When** the search is executed, **Then** the closest related entries are returned based on semantic similarity.

---

### User Story 3 - Decision Journal (Priority: P3)

A user wants to document a decision they are about to make — capturing the context, options considered, criteria used, expected outcomes, and rationale. This creates a persistent record that can be reviewed later to improve future decision-making by comparing predictions against actual outcomes.

**Why this priority**: Adds long-term value by enabling reflective practice. Decision journals are a proven method for improving judgment over time, but the skill functions without them.

**Independent Test**: Can be fully tested by creating a decision journal entry for any decision (e.g., "Choosing cloud provider") and verifying a structured markdown file is saved with all required sections.

**Acceptance Scenarios**:

1. **Given** a user requests to journal a decision, **When** the journal command is executed with decision context, **Then** a structured markdown file is created containing: decision statement, options, criteria, expected outcomes, confidence level, and rationale.
2. **Given** a user wants to review past decisions, **When** a review command is executed, **Then** a summary of past decision journal entries is displayed with key metadata (date, decision, confidence, outcome status).
3. **Given** a journal entry exists for a past decision, **When** the user updates it with the actual outcome, **Then** the entry is updated and a reflection prompt is generated comparing prediction vs. reality.

---

### User Story 4 - Comparison Matrix Generation (Priority: P4)

A user has multiple options to evaluate (e.g., 3 software tools, 4 apartment options) and needs a structured side-by-side comparison. They provide the options and criteria, and the system generates a weighted comparison matrix with scoring guidance.

**Why this priority**: Provides concrete decision-support output. Useful but more specialized than the core plan generation or search functionality.

**Independent Test**: Can be fully tested by providing options and criteria (e.g., "Compare Slack vs Teams vs Discord for team communication") and verifying a formatted comparison matrix is generated.

**Acceptance Scenarios**:

1. **Given** a user provides options and evaluation criteria, **When** the matrix command is executed, **Then** a formatted comparison matrix is generated with weighted scoring guidance for each criterion.
2. **Given** a user provides options but no explicit criteria, **When** the matrix command is executed, **Then** the system suggests relevant criteria based on the decision domain and generates the matrix with those suggested criteria.

---

### Edge Cases

- What happens when a user describes a trivial decision (e.g., "what should I eat for lunch")? The system should still provide a lightweight response but note that formal decision frameworks may be overkill for low-stakes choices.
- How does the system handle conflicting criteria where no option clearly dominates? The system should flag trade-offs explicitly and recommend sensitivity analysis or stakeholder prioritization.
- What happens when the user provides extremely long or complex decision descriptions? The system should extract the core decision elements and summarize, then proceed with plan generation.
- How does the system handle decisions with incomplete information? The system should identify information gaps, recommend what data to gather, and proceed with the available information while flagging uncertainty.
- What happens when a search query matches no entries in the knowledge base? The system should return a helpful message suggesting related terms or broader search concepts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a natural-language decision description and generate a structured decision-making plan containing: recommended framework, evaluation criteria, bias warnings, and step-by-step process.
- **FR-002**: System MUST automatically classify the decision type (e.g., reversible vs. irreversible, individual vs. group, strategic vs. operational) based on the user's description.
- **FR-003**: System MUST provide a searchable knowledge base of decision-making frameworks ranked by relevance to the search query.
- **FR-004**: System MUST provide a searchable knowledge base of cognitive biases relevant to decision-making, each with description, warning signs, and mitigation strategies.
- **FR-005**: System MUST support searching across multiple knowledge domains simultaneously (frameworks, biases, decision types, criteria templates, facilitation techniques).
- **FR-006**: System MUST generate context-aware bias warnings based on the decision type and scenario described by the user.
- **FR-007**: System MUST create structured decision journal entries as persistent markdown files containing: decision statement, options, criteria, expected outcomes, confidence level, and rationale.
- **FR-008**: System MUST generate weighted comparison matrices for multi-option evaluation, with scoring guidance for each criterion.
- **FR-009**: System MUST suggest relevant evaluation criteria when the user does not provide explicit criteria, based on the decision domain.
- **FR-010**: System MUST support auto-detection of relevant knowledge domains from the user's query without requiring the user to specify domains manually.
- **FR-011**: System MUST provide a workflow guide (PROMPT.md) that instructs the AI assistant on how to use the skill's tools in the correct sequence.
- **FR-012**: System MUST operate using only standard library dependencies (no external package installation required).
- **FR-013**: System MUST include anti-patterns for each decision type — common mistakes to avoid when making that category of decision.
- **FR-014**: System MUST support persisting decision plans to named project files for later reference.

### Key Entities

- **Decision Framework**: A structured methodology derived from the source methodology for evaluating and choosing between options (e.g., hypothesis-driven decision trees, logic trees for option decomposition, weighted prioritization matrices, Day One answer synthesis). Key attributes: name, description, best-for scenarios, steps, strengths, limitations.
- **Decision Type**: A classification of decisions by characteristics aligned with the methodology's problem categories (e.g., reversible/irreversible, individual/group, strategic/tactical, time-pressured/deliberate). Key attributes: name, description, characteristics, recommended frameworks, common pitfalls.
- **Cognitive Bias**: A systematic pattern of deviation from rational judgment relevant to decisions, with debiasing strategies from the methodology. Key attributes: name, description, warning signs, impact on decisions, mitigation strategies, examples.
- **Analysis Technique**: Analytical methods from the source methodology applied to decision evaluation (e.g., sensitivity analysis, scenario planning, expected value calculation, Bayesian updating). Key attributes: name, description, when to use, inputs required, output format.
- **Decision Journal Entry**: A persistent record of a decision capturing the hypothesis-driven process. Key attributes: decision statement, date, hypothesis, options considered, logic tree, criteria used, framework applied, expected outcomes, confidence level, rationale, actual outcome (added later).
- **Workplan Template**: Structured templates for planning the decision execution process, derived from the methodology's workplanning approach. Key attributes: decision type, activities, owners, timeline, deliverables, review points.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a complete decision-making plan from a natural-language description in under 30 seconds of processing time.
- **SC-002**: The knowledge base contains at least 8 decision frameworks, 10 cognitive biases, 6 decision types, 6 criteria templates, and 6 facilitation techniques (minimum 36 total knowledge entries).
- **SC-003**: Search queries return relevant results for 90% of common decision-making terms (frameworks, biases, techniques) on the first attempt.
- **SC-004**: Generated decision plans include at least 3 distinct sections: recommended framework, bias warnings, and evaluation criteria — providing actionable guidance without additional research.
- **SC-005**: Decision journal entries capture all essential decision metadata (statement, options, criteria, rationale, confidence) in a single structured file that is human-readable.
- **SC-006**: The skill operates with zero external dependencies — only standard library modules are used.
- **SC-007**: Users can search, generate plans, and create journals using intuitive command-line flags without needing to memorize complex syntax.
- **SC-008**: Comparison matrices clearly present trade-offs between options, enabling users to make more informed choices compared to unstructured deliberation.

## Assumptions

- The skill follows the same architectural pattern as the existing problem-solving-pro skill: PROMPT.md workflow guide + CSV knowledge base + Python BM25 search engine with plan generation.
- **All decision-making content must strictly derive from the same structured methodology source as problem-solving-pro** — focusing on the decision/choice phases of that methodology (hypothesis trees, logic trees, prioritization, analysis techniques, workplanning, synthesis). No generic or unrelated frameworks.
- The primary user is an AI assistant (Claude/Copilot) that reads the PROMPT.md and executes the Python scripts on behalf of the human user.
- Decision journal files are stored locally in the workspace and are not synced to any external service.
- The skill is complementary but independent from problem-solving-pro — either can be used standalone. problem-solving-pro focuses on defining and structuring problems; make-decision focuses on evaluating options and choosing the best course of action.
- The skill is self-contained: it includes its own complete set of decision-relevant knowledge (biases, analysis techniques, etc.) derived from the methodology, even if some entries overlap with problem-solving-pro. Each skill must function independently.
- No book title, author name, or direct quotations appear anywhere in the skill files.
