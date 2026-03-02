# Tasks: Make-Decision Skill

**Input**: Design documents from `/specs/001-make-decision-skill/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md

**Tests**: Not requested in feature specification. No test tasks included.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in all task descriptions

## Path Conventions

All source files under `.github/prompts/make-decision/`:
- Data: `.github/prompts/make-decision/data/*.csv`
- Scripts: `.github/prompts/make-decision/scripts/*.py`
- Workflow: `.github/prompts/make-decision/PROMPT.md`
- Journals: `.decisions/*.md` (runtime, at workspace root)
- Plans: `decision-plans/{project-slug}/PLAN.md` (runtime, at workspace root)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project directory structure and skeleton files

- [X] T001 Create directory structure: `.github/prompts/make-decision/data/` and `.github/prompts/make-decision/scripts/`
- [X] T002 [P] Create empty CSV files with headers for all 6 data domains per data-model.md field definitions in `.github/prompts/make-decision/data/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: BM25 search engine and CSV configuration â€” MUST complete before any user story

**CRITICAL**: All user story tasks depend on core.py being functional with all 6 domain configs.

- [X] T003 Implement BM25 search engine class in `.github/prompts/make-decision/scripts/core.py` â€” include BM25 class (k1=1.5, b=0.75), tokenizer, IDF calculation, scoring (port from problem-solving-pro pattern, adapt to 6 new domains)
- [X] T004 Define CSV_CONFIG dictionary in `.github/prompts/make-decision/scripts/core.py` for all 6 domains: `frameworks` (decision-frameworks.csv), `types` (decision-types.csv), `biases` (cognitive-biases.csv), `analysis` (analysis-techniques.csv), `criteria` (criteria-templates.csv), `facilitation` (facilitation.csv) â€” with search_cols and output_cols per data-model.md
- [X] T005 Implement `load_csv()`, `search_domain()`, `search_all()`, and `auto_detect_domains()` functions in `.github/prompts/make-decision/scripts/core.py`
- [X] T006 [P] Populate `.github/prompts/make-decision/data/decision-frameworks.csv` with 10 frameworks from research.md R1 (Hypothesis-Driven Decision Tree, Logic Tree Option Decomposition, Weighted Criteria Matrix, Sensitivity Analysis Decision, Expected Value Calculation, Scenario Planning Matrix, Pros-Cons-Fixes Analysis, Pre-Mortem Decision Test, Reversibility Filter, Iterative Hypothesis Testing)
- [X] T007 [P] Populate `.github/prompts/make-decision/data/decision-types.csv` with 8 decision types from research.md R2 (Binary Choice, Multi-Option Selection, Resource Allocation, Strategic Direction, Operational/Tactical, Decision Under Uncertainty, Group/Stakeholder Decision, Time-Pressured Decision)
- [X] T008 [P] Populate `.github/prompts/make-decision/data/cognitive-biases.csv` with 12 biases from research.md R3 (Confirmation Bias, Anchoring Effect, Sunk Cost Fallacy, Status Quo Bias, Overconfidence, Framing Effect, Availability Heuristic, Groupthink, Planning Fallacy, Loss Aversion, Recency Bias, Survivorship Bias)
- [X] T009 [P] Populate `.github/prompts/make-decision/data/analysis-techniques.csv` with 10 techniques from research.md R4 (Sensitivity Analysis, Break-Even Analysis, Decision Tree Analysis, Scenario Analysis, Relative Value Scoring, Opportunity Cost Assessment, Risk-Reward Matrix, Bayesian Update Protocol, Pre-Mortem Analysis, Reference Class Forecasting)
- [X] T010 [P] Populate `.github/prompts/make-decision/data/criteria-templates.csv` with 8 templates from research.md R5 (Technology Selection, Hiring Decision, Vendor/Partner Selection, Investment/Resource Allocation, Market Entry/Expansion, Product Feature Prioritization, Organizational Change, Location/Facility)
- [X] T011 [P] Populate `.github/prompts/make-decision/data/facilitation.csv` with 8 techniques from research.md R6 (Pre-Mortem, Red Team Challenge, Nominal Group Technique, Structured Debate, Dot Voting Prioritization, Anonymous Input Round, Devil's Advocate Assignment, Workplan Alignment Session)

**Checkpoint**: BM25 engine operational with 56 entries across 6 CSV domains. Can verify with: `python3 prompts/make-decision/scripts/core.py` (if __main__ test block included)

---

## Phase 3: User Story 1 â€” Decision Plan Generation (Priority: P1) MVP

**Goal**: User describes a decision in natural language â†’ receives a comprehensive structured decision plan with framework recommendation, criteria, bias warnings, and step-by-step process.

**Independent Test**: Run `python3 prompts/make-decision/scripts/search.py "choosing between AWS and Azure for cloud migration" --plan` and verify output contains: decision type classification, recommended framework, evaluation criteria, bias warnings, analysis techniques, and decision checklist.

### Implementation for User Story 1

- [X] T012 [US1] Implement `DecisionAdvisor` class in `.github/prompts/make-decision/scripts/advisor.py` with `__init__(self, query, search_fn)` that stores query and search function reference
- [X] T013 [US1] Implement decision type classification logic in `DecisionAdvisor.classify_decision_type()` in `.github/prompts/make-decision/scripts/advisor.py` â€” keyword matching against decision-types.csv to auto-detect type from natural language description (FR-002)
- [X] T014 [US1] Implement `DecisionAdvisor.generate()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” orchestrates: classify type â†’ search frameworks â†’ search biases â†’ search analysis â†’ search criteria â†’ search facilitation â†’ assemble plan dict with all sections (FR-001, FR-006, FR-009, FR-010)
- [X] T015 [US1] Implement `DecisionAdvisor.format_ascii_box()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” renders plan dict as ASCII box output per contracts/cli-interface.md format (sections: Decision Type, Recommended Framework, Evaluation Criteria, Analysis Techniques, Bias Warnings, Group Facilitation, Anti-Patterns, Decision Checklist)
- [X] T016 [US1] Implement `DecisionAdvisor.format_markdown()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” renders plan dict as markdown output with headers and bullet lists
- [X] T017 [US1] Implement CLI argument parser in `.github/prompts/make-decision/scripts/search.py` with argparse â€” positional `query`, flags: `--plan`, `--domain`, `-n/--results`, `-p/--project`, `-f/--format`, `--persist`, `--journal`, `--review`, `--update`, `--outcome`, `--matrix`, `-c/--criteria`
- [X] T018 [US1] Implement `--plan` command handler in `.github/prompts/make-decision/scripts/search.py` â€” instantiates DecisionAdvisor, calls generate(), formats output per -f flag, prints to stdout
- [X] T019 [US1] Implement `DecisionAdvisor.persist_plan()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” writes plan to `decision-plans/{project-slug}/PLAN.md` when --persist flag is used (FR-014)

**Checkpoint**: `python3 prompts/make-decision/scripts/search.py "Should I hire contractor A or B?" --plan` returns a complete decision plan. `--persist -p "Hiring Decision"` saves to `decision-plans/hiring-decision/PLAN.md`.

---

## Phase 4: User Story 2 â€” Domain Knowledge Search (Priority: P2)

**Goal**: User searches for specific decision-making concepts and receives relevant entries ranked by BM25 relevance.

**Independent Test**: Run `python3 prompts/make-decision/scripts/search.py "sunk cost" --domain biases` and verify matching bias entries returned. Run `python3 prompts/make-decision/scripts/search.py "group decision uncertainty"` (auto-domain) and verify results from multiple domains.

### Implementation for User Story 2

- [X] T020 [US2] Implement `--domain` search command handler in `.github/prompts/make-decision/scripts/search.py` â€” accepts domain key, calls `search_domain()` from core.py, formats and prints results per contracts/cli-interface.md domain search format (FR-003, FR-004)
- [X] T021 [US2] Implement auto-domain search command handler (no --domain flag) in `.github/prompts/make-decision/scripts/search.py` â€” calls `auto_detect_domains()` then `search_all()` from core.py, groups results by domain (FR-005, FR-010)
- [X] T022 [US2] Implement no-results handling in `.github/prompts/make-decision/scripts/search.py` â€” when search returns 0 results, suggest related terms based on domain keywords (edge case from spec)

**Checkpoint**: All 6 domains searchable individually and via auto-detect. `--domain frameworks "hypothesis"` returns Hypothesis-Driven Decision Tree. Auto-search for "group decision" returns results from types, biases, and facilitation domains.

---

## Phase 5: User Story 3 â€” Decision Journal (Priority: P3)

**Goal**: User can create, review, and update decision journal entries as persistent markdown files in `.decisions/` directory.

**Independent Test**: Run `python3 prompts/make-decision/scripts/search.py --journal "Choosing cloud provider"` â†’ verify `.decisions/2026-03-03-choosing-cloud-provider.md` created with all required sections. Run `--journal --review` â†’ verify entry listed.

### Implementation for User Story 3

- [X] T023 [US3] Implement `DecisionAdvisor.create_journal()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” creates `.decisions/` directory if needed, generates structured markdown file with sections: Decision Statement, Date, Hypothesis, Options, Criteria, Expected Outcomes, Confidence Level, Rationale, Actual Outcome (blank), Reflection (blank) per data-model.md entity 7 (FR-007)
- [X] T024 [US3] Implement `--journal` create command handler in `.github/prompts/make-decision/scripts/search.py` â€” parses journal decision statement, calls create_journal(), prints file path to stdout
- [X] T025 [US3] Implement `DecisionAdvisor.review_journals()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” scans `.decisions/` directory, parses each markdown file for metadata (date, decision, confidence, status), formats summary list
- [X] T026 [US3] Implement `--journal --review` command handler in `.github/prompts/make-decision/scripts/search.py` â€” calls review_journals(), prints formatted list per contracts/cli-interface.md
- [X] T027 [US3] Implement `DecisionAdvisor.update_journal()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” accepts journal ID and actual outcome text, updates existing markdown file, generates reflection prompt comparing prediction vs. reality
- [X] T028 [US3] Implement `--journal --update` command handler in `.github/prompts/make-decision/scripts/search.py` â€” parses journal ID and --outcome text, calls update_journal(), prints updated file path and reflection prompt

**Checkpoint**: Full journal lifecycle: create â†’ review â†’ update with outcome. `.decisions/` directory contains structured markdown files that are human-readable.

---

## Phase 6: User Story 4 â€” Comparison Matrix Generation (Priority: P4)

**Goal**: User provides options to compare and receives a weighted comparison matrix with scoring guidance.

**Independent Test**: Run `python3 prompts/make-decision/scripts/search.py --matrix "Compare Salesforce vs HubSpot vs Pipedrive for CRM"` â†’ verify formatted matrix output with criteria, weights, and scoring guide.

### Implementation for User Story 4

- [X] T029 [US4] Implement `DecisionAdvisor.generate_matrix()` method in `.github/prompts/make-decision/scripts/advisor.py` â€” parses options from description, matches domain to criteria-templates.csv for auto-suggested criteria and weights, formats comparison matrix table per contracts/cli-interface.md (FR-008, FR-009)
- [X] T030 [US4] Implement `--matrix` command handler in `.github/prompts/make-decision/scripts/search.py` â€” parses options description and optional -c criteria, calls generate_matrix(), prints formatted matrix to stdout

**Checkpoint**: `--matrix "AWS vs Azure vs GCP"` generates matrix with Technology Selection criteria. `--matrix "Hire Alice vs Bob" -c "skills,culture,growth"` generates matrix with custom criteria.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Workflow documentation and final validation

- [X] T031 Create PROMPT.md workflow guide in `.github/prompts/make-decision/PROMPT.md` â€” include: skill description, prerequisites, step-by-step usage workflow (Step 1: Understand â†’ Step 2: Generate Plan â†’ Step 3: Deep-Dive Searches â†’ Step 4: Compare â†’ Step 5: Journal), search reference table with all 6 domains, example workflow, output formats, key decision-making principles from methodology â€” per FR-011 and following problem-solving-pro PROMPT.md pattern
- [X] T032 Validate all CLI commands against contracts/cli-interface.md â€” verify exit codes, output formats, error handling per contract
- [X] T033 Run quickstart.md validation â€” execute all 5 quickstart commands and verify expected outputs
- [X] T034 Verify no book title, author name, or direct quotations in any skill file (content derivation constraint from research.md R8)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies â€” can start immediately
- **Foundational (Phase 2)**: T003-T005 depend on T001-T002. T006-T011 (CSV population) can run in parallel with T003-T005 (different files). T003-T005 must complete before any user story.
- **User Story 1 (Phase 3)**: Depends on T003-T005 (core.py complete). T006-T011 must be complete for plan generation to return meaningful results.
- **User Story 2 (Phase 4)**: Depends on T003-T005 and T017 (CLI parser from US1). Can run in parallel with late US1 tasks (T018-T019).
- **User Story 3 (Phase 5)**: Depends on T012 (DecisionAdvisor class) and T017 (CLI parser). Can run in parallel with US2 and US4.
- **User Story 4 (Phase 6)**: Depends on T012 (DecisionAdvisor class) and T017 (CLI parser). Can run in parallel with US2 and US3.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational phase â€” no dependencies on other stories
- **User Story 2 (P2)**: Depends on T017 (CLI parser from US1) â€” otherwise independent
- **User Story 3 (P3)**: Depends on T012 (DecisionAdvisor from US1) and T017 (CLI parser) â€” otherwise independent
- **User Story 4 (P4)**: Depends on T012 (DecisionAdvisor from US1) and T017 (CLI parser) â€” otherwise independent

### Within Each User Story

- Advisor methods before CLI handlers
- Core logic before formatting
- Create before review/update (US3)

### Parallel Opportunities

- **Phase 2**: T006-T011 (all 6 CSVs) can be populated in parallel â€” all different files
- **Phase 2**: CSV population (T006-T011) can run in parallel with core.py development (T003-T005)
- **Phase 3+**: After T012 (DecisionAdvisor class) and T017 (CLI parser), advisor methods for US3 (T023, T025, T027) and US4 (T029) can be implemented in parallel with US2 tasks (T020-T022) â€” all target different functions in different logical areas
- **Phase 7**: T032, T033, T034 are independent validation tasks that can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all CSV population tasks together (6 different files):
T006: Populate decision-frameworks.csv (10 entries)
T007: Populate decision-types.csv (8 entries)
T008: Populate cognitive-biases.csv (12 entries)
T009: Populate analysis-techniques.csv (10 entries)
T010: Populate criteria-templates.csv (8 entries)
T011: Populate facilitation.csv (8 entries)

# In parallel with CSV work, develop core engine:
T003: BM25 class in core.py
T004: CSV_CONFIG in core.py
T005: Load/search functions in core.py
```

## Parallel Example: Post-Foundation

```bash
# After T012 (DecisionAdvisor) and T017 (CLI parser) complete:

# Developer A: US1 plan generation
T014: generate() method
T015: format_ascii_box() method

# Developer B: US3 journal (parallel)
T023: create_journal() method
T024: --journal CLI handler

# Developer C: US4 matrix (parallel)
T029: generate_matrix() method
T030: --matrix CLI handler
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T011) â€” 56 CSV entries + BM25 engine
3. Complete Phase 3: User Story 1 (T012-T019) â€” plan generation
4. **STOP and VALIDATE**: `search.py "any decision" --plan` returns complete plan
5. This alone delivers the core value proposition

### Incremental Delivery

1. Setup + Foundational â†’ BM25 engine ready with full knowledge base
2. Add US1 (Plan Generation) â†’ Test independently â†’ **MVP delivered!**
3. Add US2 (Domain Search) â†’ Test independently â†’ Deeper exploration enabled
4. Add US3 (Decision Journal) â†’ Test independently â†’ Reflective practice enabled
5. Add US4 (Comparison Matrix) â†’ Test independently â†’ Structured comparison enabled
6. Polish â†’ PROMPT.md, validation, cleanup

### Total Task Count

| Phase | Tasks | Parallelizable |
|-------|-------|---------------|
| Phase 1: Setup | 2 | 1 |
| Phase 2: Foundational | 9 | 6 |
| Phase 3: US1 Plan Generation | 8 | 0 |
| Phase 4: US2 Domain Search | 3 | 0 |
| Phase 5: US3 Decision Journal | 6 | 0 |
| Phase 6: US4 Comparison Matrix | 2 | 0 |
| Phase 7: Polish | 4 | 3 |
| **Total** | **34** | **10** |

---

## Notes

- No test tasks included â€” tests not requested in feature specification
- [P] tasks target different files with no dependencies
- [Story] label maps task to specific user story for traceability
- Content constraint: all CSV data derives strictly from the structured problem-solving methodology â€” no book titles, author names, or direct quotations
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
