# Documentation Structure: `docs/` vs `_bmad/` - Impact Analysis

**Date:** 2026-01-07  
**Purpose:** Explain the relationship between project documentation (`docs/`) and BMAD framework (`_bmad/`)

## Overview

This project uses a **two-tier documentation architecture**:

1. **`_bmad/`** - BMAD Framework (reusable methodology)
2. **`docs/`** - Project-Specific Documentation (how this project uses BMAD)

## Key Differences

### `_bmad/` - BMAD Framework (Source of Truth)

**Purpose:** Reusable methodology framework that can be used across multiple projects

**Contains:**
- Agent definitions (PM, Dev, Analyst, etc.)
- Workflow definitions (create-epics-and-stories, dev-story, etc.)
- Integration patterns (OpenProject, Archon)
- Configuration templates
- Standard operating procedures

**Characteristics:**
- ✅ **Reusable** - Can be copied to other projects
- ✅ **Framework** - Defines HOW to do things (methodology)
- ✅ **Activated by** `.cursor/rules/bmad/` files
- ✅ **Source of truth** - Complete agent/workflow definitions

**Example Files:**
- `_bmad/bmm/agents/pm.md` - Complete PM agent definition
- `_bmad/bmm/workflows/create-epics-and-stories/workflow.md` - Workflow instructions
- `_bmad/integrations/cursor-rules.mdc` - Integration rules (always applied)

### `docs/` - Project-Specific Documentation

**Purpose:** Project-specific documentation explaining how THIS project implements BMAD and its own processes

**Contains:**
- Project-specific workflows and processes
- Verification documents (story/epic completion)
- Project status and analysis
- Configuration guides
- Testing strategies and requirements
- OpenProject cleanup reports
- Implementation guides

**Characteristics:**
- ✅ **Project-specific** - Unique to this project
- ✅ **Implementation details** - HOW this project uses BMAD
- ✅ **Not reusable** - Specific to this codebase
- ✅ **Referenced by** agents/workflows when needed

**Example Files:**
- `docs/TESTING_STRATEGY.md` - **This project's** testing requirements
- `docs/QA_TESTING_WORKFLOW.md` - **This project's** QA process
- `docs/EPIC_4_INCOMPLETE_TASKS_ANALYSIS.md` - **This project's** epic analysis
- `docs/STORY_1_5_VERIFICATION.md` - **This project's** story verification

## Impact of Documentation Created

### New Documentation Created (2026-01-07)

1. **`docs/TESTING_STRATEGY.md`** - Project-specific testing requirements
2. **`docs/TESTING_PRINCIPLES.md`** (updated) - Project-specific testing principles
3. **`docs/QA_TESTING_WORKFLOW.md`** (updated) - Project-specific QA workflow
4. **`docs/COMPLETE_AGILE_WORKFLOW.md`** (updated) - Project-specific agile workflow

### Impact Analysis

#### ✅ Project-Specific Impact (High)

**These docs define THIS project's requirements:**

- **Testing Strategy**: Every story MUST have unit tests + integration tests
- **QA Workflow**: Specific validation steps for this project
- **Agile Workflow**: How this project implements the agile process

**Used By:**
- Developers implementing stories
- Test team validating work
- PM/Scrum Master managing workflow
- AI agents following project-specific processes

**Referenced In:**
- OpenProject work packages (attached as documents)
- Story verification documents
- Task completion checklists

#### ⚠️ BMAD Framework Impact (None - By Design)

**These docs do NOT modify the BMAD framework:**

- `_bmad/` remains unchanged
- BMAD agents/workflows continue to work as defined
- Other projects using BMAD are unaffected

**Why:**
- These are **project-specific** requirements
- BMAD framework is **reusable** across projects
- Each project can have different testing strategies

## How They Work Together

### Activation Flow

```
1. User references: @bmad/bmm/agents/pm
   ↓
2. Cursor loads: .cursor/rules/bmad/bmm/agents/pm.mdc
   ↓
3. .mdc file loads: _bmad/bmm/agents/pm.md (BMAD framework)
   ↓
4. PM agent executes workflow
   ↓
5. Workflow references: docs/TESTING_STRATEGY.md (for human reference)
   ↓
6. Agent follows BMAD framework patterns (from _bmad/)
   ↓
7. Agent MAY read docs/ files IF explicitly instructed by workflow
   ↓
8. Humans read docs/ for project-specific requirements
```

### Critical Distinction: Automatic vs Manual Loading

**BMAD Agents DO NOT automatically load `docs/` files:**

- ✅ Agents automatically load: `_bmad/` files (config.yaml, workflows, agents)
- ❌ Agents do NOT automatically load: `docs/` files
- ✅ Agents CAN load `docs/` files: Only if explicitly instructed by workflow step
- ✅ Humans read `docs/`: For understanding project-specific requirements

**Agent Rule (from all agents):**
```
"Load files ONLY when executing a user chosen workflow or a command requires it, 
EXCEPTION: agent activation step 2 config.yaml"
```

This means:
- `_bmad/bmm/config.yaml` - ✅ Automatically loaded during agent activation
- `docs/TESTING_STRATEGY.md` - ❌ NOT automatically loaded
- `docs/TESTING_STRATEGY.md` - ✅ CAN be loaded if workflow step explicitly says to read it

### Example: Story Implementation

**BMAD Framework (`_bmad/`):**
- Defines: "Dev agent should implement story following workflow"
- Provides: `_bmad/bmm/workflows/dev-story/workflow.md`

**Project Documentation (`docs/`):**
- Defines: "Every story MUST have unit tests + integration tests"
- Provides: `docs/TESTING_STRATEGY.md`

**Result:**
- Dev agent follows BMAD workflow
- Dev agent also follows project-specific testing requirements
- Both are enforced

## Documentation Hierarchy

### Level 1: BMAD Framework (`_bmad/`)
**Purpose:** Reusable methodology

```
_bmad/
├── bmm/agents/pm.md          ← PM agent definition
├── bmm/workflows/dev-story/  ← Development workflow
└── integrations/             ← Integration patterns
```

### Level 2: Cursor Rules (`.cursor/rules/bmad/`)
**Purpose:** Activation layer

```
.cursor/rules/bmad/
├── index.mdc                 ← Master index (always applied)
└── bmm/agents/pm.mdc         ← Activates _bmad/bmm/agents/pm.md
```

### Level 3: Project Documentation (`docs/`)
**Purpose:** Project-specific implementation

```
docs/
├── TESTING_STRATEGY.md       ← This project's testing requirements
├── QA_TESTING_WORKFLOW.md    ← This project's QA process
└── EPIC_4_*.md               ← This project's epic documentation
```

## When to Use Each

### Use `_bmad/` When:
- ✅ Creating reusable agents/workflows
- ✅ Defining methodology patterns
- ✅ Setting up integration standards
- ✅ Creating framework components

### Use `docs/` When:
- ✅ Documenting project-specific requirements
- ✅ Creating verification documents
- ✅ Documenting project status
- ✅ Explaining project-specific processes
- ✅ Creating implementation guides

## Best Practices

### For BMAD Framework (`_bmad/`):
- Keep it **generic** and **reusable**
- Don't include project-specific details
- Focus on **methodology**, not implementation
- Can be versioned and shared across projects

### For Project Documentation (`docs/`):
- Document **project-specific** requirements
- Reference BMAD framework when appropriate
- Keep it **current** and **accurate**
- Attach to OpenProject work packages for traceability

## Summary

| Aspect | `_bmad/` | `docs/` |
|--------|----------|---------|
| **Purpose** | Reusable framework | Project-specific docs |
| **Scope** | Methodology | Implementation |
| **Reusability** | ✅ Across projects | ❌ This project only |
| **Modified By** | Framework updates | Project requirements |
| **Auto-Loaded By Agents** | ✅ Yes (config.yaml, workflows) | ❌ No (only if workflow explicitly instructs) |
| **Read By Humans** | ✅ Yes (framework docs) | ✅ Yes (project requirements) |
| **Referenced In Workflows** | ✅ As executable files | ✅ As documentation references |
| **Example** | PM agent definition | Testing strategy |

## Key Finding: `docs/` Usage Pattern

### Primary Purpose: Human Reference & Record Keeping

**`docs/` files are primarily for:**
1. ✅ **Human understanding** - Project leaders, developers, test team
2. ✅ **Record keeping** - Project history, verification documents, status reports
3. ✅ **Workflow references** - Listed in workflow YAML "REFERENCES" sections for humans
4. ✅ **Explicit loading** - Can be loaded by agents IF workflow step explicitly instructs

### NOT Automatically Loaded by Agents

**BMAD agents:**
- ❌ Do NOT automatically load `docs/` files during activation
- ❌ Do NOT automatically read `docs/` files unless workflow step says to
- ✅ DO automatically load `_bmad/` files (config.yaml, workflows, agents)
- ✅ CAN load `docs/` files if workflow step explicitly says: "Read docs/TESTING_STRATEGY.md"

### Workflow References Pattern

**In workflow YAML files, `docs/` references appear in:**
```yaml
## REFERENCES
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
```

**This means:**
- ✅ **For humans** - Documentation links for understanding
- ✅ **Can be loaded** - If workflow step explicitly says to read them
- ❌ **Not automatic** - Agents don't auto-load these references

## Impact of Recent Documentation

The testing documentation created (`TESTING_STRATEGY.md`, etc.) has:

✅ **High Impact** on this project:
- Defines mandatory testing requirements
- Guides developer and test team workflows
- Ensures quality gates are met

❌ **No Impact** on BMAD framework:
- Framework remains unchanged
- Other projects unaffected
- Methodology patterns preserved

✅ **Positive Impact** on workflow:
- Clear requirements for all stories
- Consistent testing approach
- Better quality assurance

## Related Documentation

- `docs/BMAD_CURSOR_INTEGRATION_EXPLAINED.md` - How BMAD integrates with Cursor
- `docs/BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md` - Complete workflow requirements
- `_bmad/integrations/README.md` - BMAD integrations overview

