# Tasks: Skill CLI Packager

**Input**: Design documents from `/specs/002-skill-cli-packager/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Go module initialization, project structure, build tooling, and embedded skills directory

- [X] T001 Initialize Go module and create project directory structure per plan.md (`go.mod`, `cmd/make-decision/`, `internal/skills/`, `internal/installer/`, `internal/targets/`, `internal/checker/`, `internal/cli/`)
- [X] T002 Create Makefile with `embed-prep`, `build`, `build-all`, `test`, `clean` targets and cross-compilation matrix in `Makefile`
- [X] T003 [P] Add `skills/` to `.gitignore` and configure Makefile `embed-prep` target to copy `.github/prompts/make-decision/` and `.github/prompts/problem-solving-pro/` into `skills/` (excluding `__pycache__/`)
- [X] T004 [P] Create version variables (`version`, `commit`, `buildDate`) with `-ldflags -X` injection in `cmd/make-decision/main.go`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core packages that ALL user stories depend on — skill embedding, AI target registry, and shared CLI infrastructure

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement SkillPackage struct and skill registry with metadata (Name, Description, EntryPoint, Dependencies) in `internal/skills/registry.go` per data-model.md
- [X] T006 Implement embed.FS directive (`//go:embed all:skills`) and file discovery from embedded filesystem in `internal/skills/embed.go` per research.md R1; include init-time validation that all registry skills have ≥1 file in the embedded FS (fail fast if build missed files, satisfying FR-001 AC5)
- [X] T007 Implement AITarget struct and target registry (claude, copilot) with case-insensitive lookup and InstallPattern resolution in `internal/targets/target.go` per data-model.md
- [X] T008 Implement InstallStatus computation (installed/incomplete/not-installed) by comparing embedded file list against filesystem in `internal/installer/status.go` per data-model.md
- [X] T009 [P] Implement shared CLI types: SharedFlags struct, `addSharedFlags()` helper, `validateAI()`, `isTerminal()`, `prompt()`, and `confirm()` functions in `internal/cli/shared.go` per research.md R2, R6
- [X] T010 [P] Implement main entry point with subcommand dispatch (`init`, `list`, `uninstall`, `check`, `version`, `help`) and `printUsage()` in `cmd/make-decision/main.go` per contracts/cli-interface.md

**Checkpoint**: Foundation ready — skill embedding works, targets resolve, status detection works, CLI dispatches commands

---

## Phase 3: User Story 1 — Install Skill for Claude (Priority: P1) 🎯 MVP

**Goal**: `make-decision init --ai claude` installs all skill files to `.github/prompts/<skill>/` with conflict detection, `--force` support, and prerequisite warnings

**Independent Test**: Run `make-decision init --ai claude` in a fresh temp directory. Verify `.github/prompts/make-decision/PROMPT.md` and all data/scripts files exist with correct content. Run again without `--force` to verify conflict prompt. Run with `--force` to verify overwrite.

### Implementation for User Story 1

- [X] T011 [US1] Implement `Installer.Install()` method: extract files from embed.FS to target directory, create parent dirs, set file permissions (.py → 0o755, else → 0o644), return list of created files in `internal/installer/installer.go` per research.md R1, R3
- [X] T012 [US1] Implement conflict detection in `Installer.Install()`: check InstallStatus before writing, display list of files that would change, prompt user if installed/incomplete and `--force` not set, skip in non-interactive mode without `--force` in `internal/installer/installer.go` per spec.md FR-003
- [X] T013 [US1] Implement `init` subcommand handler: parse `--ai`, `--skill`, `--force` flags, resolve AI target, warn if `.github/` directory doesn't exist, iterate skills, call Installer.Install(), print summary with file count and next-steps message in `internal/cli/init.go` per contracts/cli-interface.md init command
- [X] T014 [US1] Implement prerequisite check during init: detect Python 3 availability via `exec.LookPath`, warn (not block) if missing, include guidance in output in `internal/checker/checker.go` per spec.md FR-006
- [X] T015 [US1] Wire init command into main dispatch, run `make embed-prep && make build`, and verify `./bin/make-decision init --ai claude` works end-to-end in a temp directory

**Checkpoint**: User Story 1 fully functional — `make-decision init --ai claude` installs skills with conflict detection and prerequisite warnings

---

## Phase 4: User Story 2 — Install Skill for GitHub Copilot (Priority: P2)

**Goal**: `make-decision init --ai copilot` installs skill files, and `--ai` defaults to interactive prompt or env var when omitted

**Independent Test**: Run `make-decision init --ai copilot` and verify files at `.github/prompts/make-decision/`. Run `make-decision init` without `--ai` and verify interactive prompt or `MAKE_DECISION_AI` env var fallback.

### Implementation for User Story 2

- [X] T016 [US2] Verify copilot target end-to-end: run `make-decision init --ai copilot` in a temp directory and confirm install path resolves identically to claude (copilot already registered in T007; this is a verification task, not new code)
- [X] T017 [US2] Implement `--ai` default resolution: check `MAKE_DECISION_AI` env var, then interactive prompt if terminal, else error in `internal/cli/init.go` per contracts/cli-interface.md and spec.md FR-007
- [X] T018 [US2] Verify `make-decision init --ai copilot` installs identically to claude target, and `make-decision init` (no `--ai`) prompts or uses env var

**Checkpoint**: Both claude and copilot targets work, `--ai` auto-resolves when omitted

---

## Phase 5: User Story 3 — List Available Skills (Priority: P3)

**Goal**: `make-decision list` shows all bundled skills with install status in table or JSON format

**Independent Test**: Run `make-decision list` and verify table output with correct status. Run `make-decision list --json` and verify valid JSON output.

### Implementation for User Story 3

- [X] T019 [US3] Implement `list` subcommand handler: iterate skill registry, compute InstallStatus for each skill in current directory, format output as aligned table using `text/tabwriter` in `internal/cli/list.go` per contracts/cli-interface.md list command
- [X] T020 [US3] Implement `--json` flag for list command: output JSON with skills array containing name, description, fileCount, status, installPath in `internal/cli/list.go` per contracts/cli-interface.md JSON output spec
- [X] T021 [US3] Wire list command into main dispatch and verify `make-decision list` and `make-decision list --json` output

**Checkpoint**: `make-decision list` shows accurate skill inventory with install status

---

## Phase 6: User Story 4 — Uninstall Skill (Priority: P4)

**Goal**: `make-decision uninstall --ai claude --skill make-decision` removes all installed skill files and empty parent directories

**Independent Test**: Install a skill, then run uninstall, verify all files removed and `.github/prompts/make-decision/` directory is gone.

### Implementation for User Story 4

- [X] T022 [US4] Implement `Uninstaller.Uninstall()` method: remove all skill files, remove empty directories up to `.github/prompts/`, confirm before removal unless `--force` in `internal/installer/uninstaller.go` per contracts/cli-interface.md uninstall command
- [X] T023 [US4] Implement `uninstall` subcommand handler: parse `--ai`, `--skill` (required), `--force` flags, resolve target path, check InstallStatus, call Uninstaller, print summary in `internal/cli/uninstall.go` per contracts/cli-interface.md
- [X] T024 [US4] Wire uninstall command into main dispatch and verify full install → uninstall cycle

**Checkpoint**: Full lifecycle works — init installs, list shows status, uninstall removes cleanly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Check command, help/version polish, and build validation

- [X] T025 [P] Implement `check` subcommand handler: scan for Python 3, report installed skill status, exit code 1 if prerequisites missing in `internal/cli/check.go` per contracts/cli-interface.md check command
- [X] T026 [P] Implement `version` subcommand: print version, commit, buildDate from ldflags variables in `cmd/make-decision/main.go` per contracts/cli-interface.md
- [X] T027 Verify all `--help` output for each subcommand matches contracts/cli-interface.md, update FlagSet.Usage overrides in `internal/cli/*.go`
- [X] T028 Run `make build-all` to verify cross-compilation for all 6 platform targets (linux/darwin/windows × amd64/arm64)
- [X] T029 Run quickstart.md validation: execute full workflow (build → init → list → check → uninstall) in a temp directory

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — the MVP
- **User Story 2 (Phase 4)**: Depends on Phase 3 (extends init command)
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can parallelise with Phase 3/4
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can parallelise with Phase 3/4/5
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational — no dependency on other stories
- **US2 (P2)**: Depends on US1 (extends the init command with env var / prompt fallback)
- **US3 (P3)**: Depends on Foundational — independent of US1/US2
- **US4 (P4)**: Depends on Foundational — independent of US1/US2/US3

### Within Each User Story

- Core logic (installer/uninstaller) before CLI handler
- CLI handler before wiring into main dispatch
- Wire-up includes end-to-end verification

### Parallel Opportunities

- T003 and T004 can run in parallel (Setup phase — different files)
- T009 and T010 can run in parallel (Foundational — different files)
- T025 and T026 can run in parallel (Polish — different files)
- US3 (list) and US4 (uninstall) can run in parallel with US1 if team capacity allows (both only depend on Foundational)

---

## Parallel Example: Foundational Phase

```
# These can run simultaneously (different packages):
T005: internal/skills/registry.go    (skill registry)
T006: internal/skills/embed.go       (embed directives)
  ↓ (T005+T006 complete)
T007: internal/targets/target.go     (AI targets — depends on registry pattern)
T008: internal/installer/status.go   (install status — depends on skills + targets)
  ↓ (T007+T008 complete)

# These can run in parallel with T005-T008 (no cross-dependency):
T009: internal/cli/shared.go         (shared CLI utilities)
T010: cmd/make-decision/main.go      (subcommand dispatch)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T010)
3. Complete Phase 3: User Story 1 (T011–T015)
4. **STOP and VALIDATE**: `make-decision init --ai claude` works end-to-end
5. Binary is self-contained and functional

### Incremental Delivery

1. Setup + Foundational → Build infrastructure ready
2. Add US1 (init --ai claude) → Test → **MVP ships!**
3. Add US2 (copilot + ai default) → Test → Multiple AI targets
4. Add US3 (list) → Test → Discovery
5. Add US4 (uninstall) → Test → Full lifecycle
6. Polish → Cross-compilation, help text, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No test tasks generated (tests not explicitly requested in spec)
- Total: 29 tasks across 7 phases
- `skills/` directory is gitignored and generated by `make embed-prep`
- All file paths are relative to repository root
