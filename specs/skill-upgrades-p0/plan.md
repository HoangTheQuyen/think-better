# Implementation Plan: Tiered Analysis Depth & Step-by-Step Docs

## Technical Context

- **Language**: Python 3 (scripts), Go (CLI binary)
- **Architecture**: BM25 search engine → Advisor engine → Output formatters
- **Key files**: `search.py` (CLI entry), `advisor.py` (plan generation), `core.py` (BM25 engine)
- **Mirror requirement**: All changes in `internal/skills/skills/` must be mirrored to `.agents/skills/`
- **Two skills**: `problem-solving-pro` (9 domains, 7-step methodology) and `make-decision` (6 domains, decision frameworks)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Depth config location | Python dict constants in `advisor.py` | Simple, colocated with usage, no extra files |
| Depth multiplier approach | Multiply existing `max_results` per domain | Reuses existing search infrastructure |
| Section filtering | String checks against DEPTH_CONFIG sections list | Lightweight, easy to extend |
| Step-docs structure | Numbered files (00-OVERVIEW, 01-...) | Natural reading order, simple navigation |
| Backward compat | Default `depth="standard"` matches current behavior | Zero-change upgrade path |

## File Changes

### problem-solving-pro

| File | Change Type | Description |
|------|-------------|-------------|
| `scripts/advisor.py` | MODIFY | Add `DEPTH_CONFIG`, `VALID_DEPTHS`, depth-aware `generate()`, `_should_include()`, `persist_step_by_step()` |
| `scripts/search.py` | MODIFY | Add `--depth` and `--step-docs` CLI arguments |
| `SKILL.md` | MODIFY | Document new flags in usage section |
| `PROMPT.md` | MODIFY | Document new flags in usage section |

### make-decision

| File | Change Type | Description |
|------|-------------|-------------|
| `scripts/advisor.py` | MODIFY | Add `DEPTH_CONFIG`, `VALID_DEPTHS`, depth-aware `generate()`, `persist_step_by_step()` |
| `scripts/search.py` | MODIFY | Add `--depth` and `--step-docs` CLI arguments |
| `SKILL.md` | MODIFY | Document new flags |
| `PROMPT.md` | MODIFY | Document new flags |

### Mirror

Copy all 8 files from `internal/skills/skills/` → `.agents/skills/`

## Depth Configuration

| Level | Multiplier | Sections | Alternatives | Notes |
|-------|-----------|----------|-------------|-------|
| quick | 0.5x | core only | No | Minimal, fast |
| standard | 1.0x | all | No | Current default |
| deep | 1.7x | all | Yes | More results, show alternatives |
| executive | 2.5x | all | Yes | Maximum detail, appendices |

## Step-by-Step File Structure

### problem-solving-pro (9 files)
```
solving-plans/<project>/
├── 00-OVERVIEW.md
├── 01-PROBLEM-DEFINITION.md
├── 02-DECOMPOSITION.md
├── 03-PRIORITIZATION.md
├── 04-ANALYSIS-PLAN.md
├── 05-FINDINGS.md (template)
├── 06-SYNTHESIS.md
├── 07-RECOMMENDATION.md
├── BIAS-WARNINGS.md
└── DECISION-LOG.md
```

### make-decision (8 files)
```
decision-plans/<project>/
├── 00-OVERVIEW.md
├── 01-DECISION-TYPE.md
├── 02-FRAMEWORK.md
├── 03-CRITERIA.md
├── 04-ANALYSIS.md
├── 05-OPTIONS.md (template)
├── 06-DECISION.md
├── BIAS-WARNINGS.md
└── DECISION-LOG.md
```
