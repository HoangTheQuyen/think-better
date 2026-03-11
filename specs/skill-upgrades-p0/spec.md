# Feature Specification: Tiered Analysis Depth & Step-by-Step Documentation

## Overview

**Feature Name**: Tiered Analysis Depth & Step-by-Step Documentation Output  
**Priority**: P0 (Highest)  
**Status**: Draft  

### Problem Statement

Currently, both AI skills (problem-solving-pro and make-decision) produce a single, fixed-depth analysis regardless of context. Whether a user faces a quick tactical question or a complex strategic decision, they receive the same level of detail. This leads to:

- **Over-analysis** of simple problems (wasted time)
- **Under-analysis** of complex problems (missed insights)
- **Single-file output** that's hard to navigate for multi-step processes

### Feature Description

Enable users to control the depth and output format of their analysis through two capabilities:

1. **Tiered Analysis Depth**: Allow users to select from 4 depth levels (quick, standard, deep, executive) to match the analysis complexity to the decision/problem complexity
2. **Step-by-Step Documentation**: Generate a structured directory of separate markdown files (one per methodology step) instead of a single monolithic output

## User Scenarios & Testing

### US1: Quick Analysis (P1)
**As a** user facing a simple, time-sensitive decision  
**I want** a brief, focused analysis covering only the core essentials  
**So that** I can get actionable guidance in under 30 seconds of reading

**Acceptance Criteria:**
- User can request a "quick" depth analysis
- Output includes only: problem/decision type classification, core framework/approach, and key bias warnings
- Output is noticeably shorter than the default (standard) analysis
- All other features (search, journal, matrix) continue working unchanged

### US2: Deep & Executive Analysis (P1)
**As a** user facing a complex, high-stakes problem  
**I want** a thorough analysis with more results, alternatives, and detailed mental model explanations  
**So that** I can explore all angles before making a critical decision

**Acceptance Criteria:**
- User can request "deep" or "executive" depth analysis
- Deep analysis returns more results per domain and shows alternative frameworks
- Executive analysis returns maximum results and includes detailed explanations of mental models
- Output is noticeably richer than the standard analysis

### US3: Step-by-Step Documentation (P2)
**As a** user working through a structured problem-solving process  
**I want** the analysis saved as separate files per step  
**So that** I can work through each step independently and track progress

**Acceptance Criteria:**
- User can request step-by-step documentation output when saving
- Each methodology step gets its own markdown file with templates for user input
- An overview file links all step files together
- A bias warnings file and decision log are included
- The directory structure is clear and navigable
- Each file contains actionable templates (checklists, tables, placeholders)

### US4: Backward Compatibility (P1)
**As an** existing user  
**I want** all current behavior to remain unchanged by default  
**So that** I don't need to learn new flags or change my workflow

**Acceptance Criteria:**
- Default behavior (no new flags) produces identical output to the current version
- All existing features (search, journal, matrix, persist) work unchanged
- No breaking changes to the CLI interface

## Functional Requirements

### FR1: Depth Levels
- **FR1.1**: Support 4 depth levels: quick, standard, deep, executive
- **FR1.2**: Default depth is "standard" (current behavior)
- **FR1.3**: Quick depth shows fewer sections and fewer results per domain
- **FR1.4**: Deep depth shows all sections, more results, alternative approaches, and detailed explanations
- **FR1.5**: Executive depth shows maximum detail including all alternatives and appendices

### FR2: Step-by-Step Output
- **FR2.1**: When step-by-step mode is active with file saving, create a directory with individual files
- **FR2.2**: Problem-solving-pro: 7 step files + overview + bias warnings + decision log
- **FR2.3**: Make-decision: 6 step files + overview + bias warnings + decision log
- **FR2.4**: Each step file includes editable templates with placeholders for user input
- **FR2.5**: Overview file provides navigation links to all step files

### FR3: Cross-Skill Consistency
- **FR3.1**: Both skills must support the same depth levels with consistent naming
- **FR3.2**: Both skills must support step-by-step output with consistent directory structure
- **FR3.3**: Changes must be mirrored between `internal/skills/` and `.agents/skills/` directories

## Success Criteria

1. **SC1**: Users can complete a quick analysis in under 15 seconds of reading (vs ~45 seconds for standard)
2. **SC2**: Deep/executive analyses provide at least 50% more actionable insights than standard
3. **SC3**: Step-by-step output creates a usable project workspace that users can fill in over days
4. **SC4**: All existing tests pass without modification
5. **SC5**: Default behavior is 100% backward compatible

## Assumptions

- Users invoke these skills through AI assistant prompts (Gemini, Copilot, etc.)
- The AI assistant passes flags to the Python scripts based on user intent
- The existing BM25 search engine performance is adequate for all depth levels
- Markdown is the preferred documentation format for step-by-step output

## Dependencies

- Existing Python scripts: `search.py`, `advisor.py`, `core.py` in both skill directories
- Existing CSV knowledge bases in both skill `data/` directories
- Existing Go embed mechanism for packaging skills into the CLI binary

## Out of Scope

- Multi-perspective analysis (reverse, devil's advocate, etc.) — planned for P1
- New thinking frameworks and mental models — planned for P1
- New strategic-thinking skill — planned for P2
- Changes to the BM25 search engine itself
- Changes to the Go CLI binary code
