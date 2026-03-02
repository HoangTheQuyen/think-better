# Implementation Plan: Make-Decision Skill

**Branch**: `001-make-decision-skill` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-make-decision-skill/spec.md`

## Summary

Build a self-contained decision-making skill that provides structured frameworks, bias detection, analysis techniques, and decision journaling - all derived from the source methodology (hypothesis-driven, logic trees, prioritization, workplanning, synthesis). Follows the same architectural pattern as problem-solving-pro: PROMPT.md workflow guide + CSV knowledge base + Python BM25 search engine with plan generation.

## Technical Context

**Language/Version**: Python 3.10+ (standard library only)
**Primary Dependencies**: None - standard library only (csv, re, math, json, pathlib, argparse, collections)
**Storage**: CSV files (knowledge base), Markdown files (decision journals, persisted plans)
**Testing**: Manual CLI validation (consistent with problem-solving-pro)
**Target Platform**: Cross-platform (macOS, Linux, Windows) - CLI tool invoked by AI assistant
**Project Type**: CLI skill (PROMPT.md + data CSVs + Python scripts)
**Performance Goals**: Plan generation < 30 seconds, search results < 5 seconds
**Constraints**: Zero external dependencies, standard library only, no network access required
**Scale/Scope**: ~36+ knowledge entries across 6 CSV domains, 3 Python scripts, 1 PROMPT.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`.specify/memory/constitution.md`) contains only template placeholders - no project-specific rules have been defined. Therefore:

- **No gates to evaluate**: All constitution sections are template defaults
- **No violations possible**: No rules exist to violate
- **Status**: PASS (vacuously - no constraints defined)

## Project Structure

### Documentation (this feature)

```text
specs/001-make-decision-skill/
+-- plan.md              # This file
+-- research.md          # Phase 0 output
+-- data-model.md        # Phase 1 output
+-- quickstart.md        # Phase 1 output
+-- contracts/           # Phase 1 output (CLI interface contracts)
+-- tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.github/prompts/make-decision/
+-- PROMPT.md                    # Workflow guide for AI assistant
+-- data/
|   +-- decision-frameworks.csv  # 8+ decision frameworks
|   +-- decision-types.csv       # 6+ decision type classifications
|   +-- cognitive-biases.csv     # 10+ biases relevant to decisions
|   +-- analysis-techniques.csv  # 8+ analysis methods for evaluation
|   +-- criteria-templates.csv   # 6+ domain-specific criteria sets
|   +-- facilitation.csv         # 6+ group decision techniques
+-- scripts/
    +-- core.py                  # BM25 search engine + CSV config
    +-- search.py                # CLI entry point (search, --plan, --domain)
    +-- advisor.py               # DecisionAdvisor class (plan generation, journal, matrix)
```

**Structure Decision**: Follows the established skill pattern from problem-solving-pro - a single skill directory under `.github/prompts/` containing PROMPT.md, data/ CSVs, and scripts/ Python files.

## Complexity Tracking

> No constitution violations to justify - constitution is template-only.
