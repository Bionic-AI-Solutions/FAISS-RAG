# BMAD Architecture Clarification: Correct Understanding

**Date:** 2026-01-07  
**Purpose:** Document the correct architectural understanding of `_bmad/`, `_bmad-output/`, and `docs/`

## Your Understanding (VERIFIED ✅)

### `_bmad-output/` - Project-Specific Technical Information

**Purpose:** Contains all project-specific technical information and progress tracking

**Contains:**

- ✅ **Planning artifacts** (`planning-artifacts/`):

  - Epics (`epics.md`)
  - PRD (`prd.md`)
  - Architecture (`architecture.md`)
  - Product briefs
  - Design specifications

- ✅ **Implementation artifacts** (`implementation-artifacts/`):
  - Story files (e.g., `4-1-faiss-vector-search-implementation.md`)
  - Story verification documents (e.g., `story-5.1-verification.md`)
  - Sprint status (`sprint-status.yaml`)
  - Development progress tracking

**Used By:**

- Agents read from `_bmad-output/` to understand project progress
- Agents write to `_bmad-output/` to track implementation
- Agents continue work based on information in `_bmad-output/`

### `_bmad/` - Agent Behavior and Rules

**Purpose:** Contains all agent behavior, rules, and operational strategies

**Contains:**

- ✅ **Agent definitions** (`agents/`) - Personas, principles, behaviors
- ✅ **Workflow definitions** (`workflows/`) - How agents execute work
- ✅ **Integration rules** (`integrations/`) - OpenProject, Archon patterns
- ✅ **Operational strategies** - Testing strategy, QA workflow, etc.
- ✅ **Configuration** (`_config/`) - Project-specific settings

**Should Contain:**

- ✅ **Testing strategy** - As behavior rules (how agents test)
- ✅ **QA workflow** - As behavior rules (how agents validate)
- ✅ **Operational strategies** - As behavior rules (how agents operate)

**NOT Contains:**

- ❌ Project-specific progress tracking
- ❌ Story implementation details
- ❌ Historical records

### `docs/` - OpenProject Attachments Only

**Purpose:** Contains artifacts that need to be attached to OpenProject work packages

**Should Contain:**

- ✅ **Story verification documents** - For attachment to Story work packages
- ✅ **Story-based designs** - For attachment to Story work packages
- ✅ **Feature-based designs** - For attachment to Feature work packages
- ✅ **Epic-based designs** - For attachment to Epic work packages
- ✅ **UI designs** - For attachment to appropriate work package level
- ✅ **Test summaries** - For attachment to Story work packages

**Should NOT Contain:**

- ❌ **Operational strategies** - These belong in `_bmad/` as behavior rules
- ❌ **Testing strategy** - Should be in `_bmad/` as behavior rules
- ❌ **QA workflow** - Should be in `_bmad/` as behavior rules
- ❌ **Project status reports** - These belong in `_bmad-output/`

## Correct Architecture

```
_bmad/                          ← Agent Behavior & Rules
├── agents/                     ← Agent personas and behaviors
├── workflows/                  ← How agents execute work
├── integrations/               ← Integration patterns
│   └── cursor-rules.mdc       ← Operational rules (always applied)
├── _config/                    ← Project configuration
└── [testing-strategy.md]       ← Testing behavior rules (SHOULD BE HERE)

_bmad-output/                   ← Project Technical Information
├── planning-artifacts/        ← Epics, PRD, Architecture
│   ├── epics.md
│   ├── prd.md
│   └── architecture.md
└── implementation-artifacts/   ← Story files, progress tracking
    ├── 4-1-faiss-vector-search-implementation.md
    ├── story-5.1-verification.md
    └── sprint-status.yaml

docs/                           ← OpenProject Attachments Only
├── STORY_1_5_VERIFICATION.md   ← For attachment to Story WP
├── STORY_4_1_VERIFICATION.md   ← For attachment to Story WP
├── [feature-design.md]        ← For attachment to Feature WP
└── [epic-design.md]            ← For attachment to Epic WP
```

## Current State vs Correct State

### ❌ Current Misplacement

**Files in `docs/` that should be in `_bmad/`:**

- `docs/TESTING_STRATEGY.md` → Should be `_bmad/integrations/testing-strategy.mdc` (behavior rule)
- `docs/QA_TESTING_WORKFLOW.md` → Should be `_bmad/integrations/qa-workflow.mdc` (behavior rule)
- `docs/COMPLETE_AGILE_WORKFLOW.md` → Should be in `_bmad/` as workflow behavior

**Files in `docs/` that are CORRECT:**

- ✅ `docs/STORY_*_VERIFICATION.md` - For OpenProject attachment
- ✅ `docs/EPIC_*_VERIFICATION.md` - For OpenProject attachment

### ✅ Correct Placement

**Files in `_bmad-output/` that are CORRECT:**

- ✅ `_bmad-output/planning-artifacts/epics.md` - Project planning
- ✅ `_bmad-output/implementation-artifacts/4-1-*.md` - Story implementation
- ✅ `_bmad-output/implementation-artifacts/story-5.1-verification.md` - Story verification

**Files in `_bmad/` that are CORRECT:**

- ✅ `_bmad/integrations/cursor-rules.mdc` - Operational rules
- ✅ `_bmad/workflows/STORY_VERIFICATION_STANDARD.md` - Behavior standard
- ✅ `_bmad/bmm/workflows/*/workflow.yaml` - Workflow behaviors

## How Agents Use This Architecture

### Agent Workflow

```
1. Agent activated
   ↓
2. Loads behavior rules from _bmad/
   - Testing strategy (from _bmad/integrations/testing-strategy.mdc)
   - QA workflow (from _bmad/integrations/qa-workflow.mdc)
   - Integration rules (from _bmad/integrations/cursor-rules.mdc)
   ↓
3. Checks OpenProject for current work
   - Gets work packages via MCP
   ↓
4. Reads project progress from _bmad-output/
   - Story files from implementation-artifacts/
   - Epics from planning-artifacts/
   ↓
5. Executes work following behavior rules
   ↓
6. Updates _bmad-output/ with progress
   - Updates story files
   - Creates verification documents
   ↓
7. Attaches verification docs to OpenProject
   - Copies from _bmad-output/ to docs/ (for attachment)
   - Attaches to Story work package via MCP
```

## Action Required

### Move Operational Strategies to `_bmad/`

**Files to move:**

1. `docs/TESTING_STRATEGY.md` → `_bmad/integrations/testing-strategy.mdc`
2. `docs/QA_TESTING_WORKFLOW.md` → `_bmad/integrations/qa-workflow.mdc`
3. `docs/COMPLETE_AGILE_WORKFLOW.md` → `_bmad/integrations/agile-workflow.mdc`

**Format:**

- Convert to `.mdc` format (Cursor rule format)
- Add frontmatter: `alwaysApply: true` or `alwaysApply: false`
- Structure as behavior rules, not documentation

### Keep in `docs/` (Correct)

**Files that should stay in `docs/`:**

- ✅ `docs/STORY_*_VERIFICATION.md` - For OpenProject attachment
- ✅ `docs/EPIC_*_VERIFICATION.md` - For OpenProject attachment
- ✅ Any design documents for attachment

## Verification

### Your Understanding is ✅ CORRECT

**Summary:**

1. ✅ `_bmad-output/` = Project-specific technical information and progress
2. ✅ `_bmad/` = Agent behavior and rules (including operational strategies)
3. ✅ `docs/` = OpenProject attachments only (verification docs, designs)

**Key Insight:**

- **Operational strategies** (testing strategy, QA workflow) = **Behavior rules** = Should be in `_bmad/`
- **Project progress** (story files, epics) = **Technical information** = Should be in `_bmad-output/`
- **Verification documents** (for attachment) = **Artifacts** = Should be in `docs/`

This ensures:

- ✅ Agents know HOW to operate (from `_bmad/`)
- ✅ Agents know WHAT to do (from `_bmad-output/` and OpenProject)
- ✅ Artifacts are attached to work packages (from `docs/`)

