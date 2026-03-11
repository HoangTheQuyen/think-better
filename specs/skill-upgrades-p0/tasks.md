# Tasks: Tiered Analysis Depth & Step-by-Step Docs

**Feature**: skill-upgrades-p0  
**Total Tasks**: 16  
**Estimated Effort**: Medium

## Phase 1: Setup

- [x] T001 Add `DEPTH_CONFIG` and `VALID_DEPTHS` constants to `internal/skills/skills/problem-solving-pro/scripts/advisor.py`
- [x] T002 Add `DEPTH_CONFIG` and `VALID_DEPTHS` constants to `internal/skills/skills/make-decision/scripts/advisor.py`

## Phase 2: Core — Tiered Depth (US1, US2, US4)

- [x] T003 [US1][US2] Modify `ProblemSolvingAdvisor.generate()` to accept `depth` parameter and scale `max_results` in `internal/skills/skills/problem-solving-pro/scripts/advisor.py`
- [x] T004 [US1][US2] Modify `DecisionAdvisor.generate()` to accept `depth` parameter and scale domain search counts in `internal/skills/skills/make-decision/scripts/advisor.py`
- [x] T005 [US1] Add `_should_include()` helper and make `format_ascii_box()` depth-aware (conditional sections, depth label) in `internal/skills/skills/problem-solving-pro/scripts/advisor.py`
- [ ] T006 [US1] Make `format_markdown()` depth-aware (conditional sections) in `internal/skills/skills/problem-solving-pro/scripts/advisor.py`
- [x] T007 [US4] Update `generate_solving_plan()` public API to accept `depth` and `step_docs` params in `internal/skills/skills/problem-solving-pro/scripts/advisor.py`
- [x] T008 [US4] Update `generate_decision_plan()` public API to accept `depth` and `step_docs` params in `internal/skills/skills/make-decision/scripts/advisor.py`

## Phase 3: CLI Flags (US1, US2)

- [x] T009 [US1][US2] Add `--depth` and `--step-docs` arguments to `internal/skills/skills/problem-solving-pro/scripts/search.py`
- [x] T010 [US1][US2] Add `--depth` and `--step-docs` arguments to `internal/skills/skills/make-decision/scripts/search.py`

## Phase 4: Step-by-Step Docs (US3)

- [x] T011 [US3] Implement `persist_step_by_step()` in `internal/skills/skills/problem-solving-pro/scripts/advisor.py` — creates 9 markdown files
- [x] T012 [US3] Implement `persist_step_by_step()` in `internal/skills/skills/make-decision/scripts/advisor.py` — creates 8 markdown files

## Phase 5: Documentation

- [ ] T013 [P] Document `--depth` and `--step-docs` in `internal/skills/skills/problem-solving-pro/SKILL.md` and `PROMPT.md`
- [ ] T014 [P] Document `--depth` and `--step-docs` in `internal/skills/skills/make-decision/SKILL.md` and `PROMPT.md`

## Phase 6: Mirror & Verify

- [x] T015 Copy all modified scripts from `internal/skills/skills/` to `.agents/skills/` (4 files)
- [ ] T016 Mirror documentation changes (SKILL.md, PROMPT.md) to `.agents/skills/` (4 files)

## Phase 7: Verification

- [x] T017 Run `go test ./...` and verify all existing tests pass
- [x] T018 [US1] Smoke test: `python search.py "revenue declining" --plan --depth quick`
- [x] T019 [US2] Smoke test: `python search.py "revenue declining" --plan --depth deep -f markdown`
- [x] T020 [US3] Smoke test: `python search.py "revenue declining" --plan --persist --step-docs -p "Test" -o "C:\tmp"`
- [x] T021 [US4] Smoke test: `python search.py "revenue declining" --plan` (default = standard, same as before)
- [ ] T022 [US1] Smoke test make-decision: `python search.py "AWS vs Azure" --plan --depth quick`
- [ ] T023 [US3] Smoke test make-decision: `python search.py "AWS vs Azure" --plan --persist --step-docs -p "Cloud" -o "C:\tmp"`
- [ ] T024 Verify step-docs output: check file count and content in `C:\tmp\solving-plans\` and `C:\tmp\decision-plans\`

## Dependencies

```
T001, T002 → T003, T004 (configs needed first)
T003, T004 → T005-T008 (generate() needed for formatters/API)
T007, T008 → T009, T010 (API needed for CLI)
T007, T008 → T011, T012 (API needed for step-docs)
T009-T012 → T015 (code complete needed for mirror)
T015 → T017-T024 (all code mirrored before verification)
```

## Status Summary

- **Done**: T001-T005, T007-T012, T015, T017-T021 (16/24)
- **Remaining**: T006 (markdown depth-aware), T013-T014 (docs), T016 (mirror docs), T022-T024 (make-decision smoke tests)
