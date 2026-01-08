# BMAD Architecture Analysis: Where Do Testing Procedures Belong?

## Current State

### Current Location: `_bmad/integrations/`

**Testing procedures currently in integrations:**

- `testing-strategy.mdc` - Unit + Integration tests requirement
- `qa-workflow.mdc` - QA testing workflow
- `system-readiness-procedure.mdc` - System readiness for integration tests
- `test-data-responsibility.mdc` - Test data creation responsibility
- `browser-testing-procedure.mdc` - Browser testing procedure

### Problem

**These are NOT external system integrations.** They are **fundamental testing methodology** that should be part of the core development methodology (BMM), not integrations.

---

## Architecture Layers

### 1. CORE (`_bmad/core/`)

**Purpose:** Framework mechanics, generic workflows, reusable across ALL projects

**Contains:**

- Workflow execution engine (`tasks/workflow.xml`)
- Agent loading mechanisms
- Generic workflows (brainstorming, party-mode)
- Framework-level components

**Characteristics:**

- Framework-agnostic
- Reusable across all project types
- No project-specific assumptions

### 2. BMM (`_bmad/bmm/`)

**Purpose:** Development methodology, project-specific processes

**Contains:**

- Development workflows (analysis, planning, implementation)
- **Test architecture (`testarch/`)** - Testing workflows and knowledge
- Agent definitions (Dev, PM, TEA, etc.)
- Development processes

**Characteristics:**

- Software development methodology
- Project-specific but methodology-level
- Contains testing methodology

**Current Test Architecture Structure:**

```
_bmad/bmm/
├── workflows/
│   └── testarch/
│       ├── framework/      # Test framework setup
│       ├── atdd/           # Acceptance test-driven development
│       ├── automate/       # Test automation
│       ├── test-design/    # Test scenario design
│       ├── test-review/    # Test quality review
│       ├── trace/          # Requirements traceability
│       ├── nfr-assess/     # Non-functional requirements
│       └── ci/             # CI/CD pipeline
├── testarch/
│   └── knowledge/          # Test knowledge base
│       ├── fixture-architecture.md
│       ├── data-factories.md
│       ├── test-levels-framework.md
│       └── ...
└── agents/
    └── tea.md             # Test Engineer Agent
```

### 3. INTEGRATIONS (`_bmad/integrations/`)

**Purpose:** External system integrations, team operating procedures

**Contains:**

- OpenProject integration (work management, document storage)
- Archon integration (external knowledge search)
- **Operating procedures** (testing, QA, browser testing) ← **WRONG LOCATION?**

**Characteristics:**

- External system integrations
- Team-specific operating procedures
- Project-specific configurations

---

## The Problem

### Testing Procedures Are Methodology, Not Integrations

**Current location:** `_bmad/integrations/`
**Should be:** `_bmad/bmm/testarch/` or `_bmad/bmm/workflows/testarch/`

**Why:**

1. **Testing is core methodology** - Not an external system integration
2. **BMM has testarch/** - Dedicated test architecture area
3. **Consistency** - Other test workflows are in `bmm/workflows/testarch/`
4. **Logical grouping** - Testing procedures belong with testing workflows

### Why They're Currently in Integrations

**Historical reasons:**

1. **Cursor rules mechanism** - `.mdc` files with `alwaysApply: true` work well in `integrations/`
2. **Catch-all folder** - `integrations/` became a place for "operating procedures"
3. **Quick access** - Easy to find and load automatically
4. **No clear alternative** - BMM didn't have a clear place for "always-apply" procedures

---

## Proposed Solution

### Option 1: Move to BMM Test Architecture (RECOMMENDED)

**Location:** `_bmad/bmm/testarch/procedures/`

**Structure:**

```
_bmad/bmm/testarch/
├── knowledge/              # Test knowledge base (existing)
├── procedures/             # Testing procedures (NEW)
│   ├── testing-strategy.mdc
│   ├── qa-workflow.mdc
│   ├── system-readiness.mdc
│   ├── test-data-responsibility.mdc
│   └── browser-testing.mdc
└── workflows/             # Test workflows (via bmm/workflows/testarch/)
```

**Pros:**

- ✅ Logically grouped with test architecture
- ✅ Consistent with BMM structure
- ✅ Clear separation: knowledge vs procedures vs workflows
- ✅ Part of core methodology

**Cons:**

- ⚠️ Need to ensure Cursor still loads them (may need path update)
- ⚠️ Breaking change for existing projects

### Option 2: Keep in Integrations, Add Reference

**Location:** Keep in `_bmad/integrations/`, but add clear documentation

**Structure:**

```
_bmad/integrations/
├── testing-strategy.mdc      # Testing methodology (references BMM/testarch)
├── qa-workflow.mdc           # QA workflow (references BMM/testarch)
└── ...

_bmad/bmm/testarch/
└── procedures/               # Reference implementations
    └── README.md            # "See integrations/ for always-apply procedures"
```

**Pros:**

- ✅ No breaking changes
- ✅ Cursor rules continue to work
- ✅ Clear documentation of why they're there

**Cons:**

- ❌ Still logically wrong location
- ❌ Confusing for new users
- ❌ Doesn't solve the architectural issue

### Option 3: Hybrid Approach (BEST)

**Location:** Procedures in BMM, Cursor rules in integrations

**Structure:**

```
_bmad/bmm/testarch/procedures/
├── testing-strategy.md          # Full procedure (markdown, not .mdc)
├── qa-workflow.md
├── system-readiness.md
├── test-data-responsibility.md
└── browser-testing.md

_bmad/integrations/
└── testing-procedures.mdc       # Cursor rule that references BMM procedures
    # Always-apply rule that loads procedures from bmm/testarch/procedures/
```

**Pros:**

- ✅ Logically correct (procedures in BMM)
- ✅ Cursor rules still work (via integrations)
- ✅ Clear separation of concerns
- ✅ Best of both worlds

**Cons:**

- ⚠️ Slight complexity (two files per procedure)
- ⚠️ Need to maintain references

---

## Recommendation: Option 3 (Hybrid)

### Implementation Plan

1. **Create procedures directory in BMM:**

   ```
   _bmad/bmm/testarch/procedures/
   ```

2. **Move procedures to BMM (as .md files):**

   - `testing-strategy.md`
   - `qa-workflow.md`
   - `system-readiness.md`
   - `test-data-responsibility.md`
   - `browser-testing.md`

3. **Create Cursor rule aggregator in integrations:**

   ```
   _bmad/integrations/testing-methodology.mdc
   ```

   - Contains `alwaysApply: true`
   - References procedures in `bmm/testarch/procedures/`
   - Provides quick summaries
   - Ensures procedures are loaded

4. **Update documentation:**
   - Update STRUCTURE_GUIDE.md
   - Update integrations/README.md
   - Document the hybrid approach

### Benefits

- ✅ **Architecturally correct** - Procedures in methodology (BMM)
- ✅ **Functionally correct** - Cursor rules still work (integrations)
- ✅ **Clear separation** - Procedures vs rules
- ✅ **Maintainable** - Single source of truth for procedures
- ✅ **Discoverable** - Procedures in logical location

---

## What Should Stay in Integrations?

**True integrations (external systems):**

- `openproject/` - OpenProject integration
- `archon/` - Archon integration
- `workflows/project-init/` - Project initialization

**Team operating procedures (project-specific):**

- `cursor-rules.mdc` - Cursor IDE integration rules
- `agent-integration-mixin.md` - Agent integration capabilities

**Aggregator rules (that reference BMM procedures):**

- `testing-methodology.mdc` - References BMM testarch procedures
- Other methodology aggregators as needed

---

## Summary

**The Issue:**
Testing procedures are in `integrations/` but they're methodology, not integrations.

**The Solution:**
Move procedures to `_bmad/bmm/testarch/procedures/` and create Cursor rule aggregators in `integrations/` that reference them.

**The Benefit:**

- Architecturally correct (methodology in BMM)
- Functionally correct (Cursor rules still work)
- Clear separation of concerns
- Better discoverability

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-08  
**Status:** Proposal for Review
