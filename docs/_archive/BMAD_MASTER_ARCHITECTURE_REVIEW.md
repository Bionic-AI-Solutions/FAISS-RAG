# BMad Master Architecture Review & Process Analysis

**Date:** 2026-01-07  
**Reviewer:** BMad Master  
**Status:** ✅ AGREEMENT WITH PROPOSAL + IDENTIFIED GAPS

## Executive Summary

**✅ AGREEMENT:** The proposed architecture is **CORRECT** and aligns with BMAD framework principles:

- `_bmad/` = Agent behavior and rules (operational strategies)
- `_bmad-output/` = Project-specific technical information
- `docs/` = OpenProject attachments only

**⚠️ GAPS IDENTIFIED:** Several process gaps and broken references need immediate attention.

---

## 1. Architecture Agreement ✅

### Proposal Assessment: **CORRECT**

**Your Understanding:**

1. ✅ `_bmad-output/` = Project-specific technical information (epics, stories, progress)
2. ✅ `_bmad/` = Agent behavior and rules (testing strategy, QA workflow)
3. ✅ `docs/` = OpenProject attachments only (verification docs, designs)

**BMad Master Verdict:** **FULLY AGREED** - This architecture is correct and maintains proper separation of concerns.

---

## 2. Process Conflicts & Gaps Analysis

### ✅ STRENGTHS

1. **Behavioral Rules Auto-Loading:**

   - ✅ `cursor-rules.mdc` has `alwaysApply: true` - Automatically loaded
   - ✅ `testing-strategy.mdc` has `alwaysApply: true` - Automatically loaded
   - ✅ `qa-workflow.mdc` has `alwaysApply: true` - Automatically loaded
   - ✅ All agents will automatically receive these rules

2. **Agent Activation Sequence:**

   - ✅ All agents load `config.yaml` during activation (step 2)
   - ✅ Config provides: `user_name`, `communication_language`, `output_folder`, `planning_artifacts`, `implementation_artifacts`
   - ✅ Agents know where to read project context

3. **Workflow Integration:**
   - ✅ Dev workflow pattern updated to include testing steps
   - ✅ Test team workflow pattern updated to include both test suites
   - ✅ Agent principles updated (Dev, TEA)

### ❌ CRITICAL GAPS IDENTIFIED

#### Gap 1: Broken References in Workflows

**Issue:** Workflows reference moved/deleted files in `docs/`:

**Files with Broken References:**

1. `_bmad/bmm/workflows/4-implementation/test-validation/workflow.yaml` (line 184-186):

   ```yaml
   - **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
   - **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
   ```

2. `_bmad/bmm/workflows/4-implementation/bug-management/workflow.yaml` (line 203-205):
   ```yaml
   - **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
   - **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
   ```

**Impact:** Workflows reference non-existent files, causing confusion.

**Fix Required:**

- Update references to point to `_bmad/integrations/qa-workflow.mdc`
- Remove reference to `docs/COMPLETE_AGILE_WORKFLOW.md` (content integrated into qa-workflow.mdc)

#### Gap 2: Verification Document Location Confusion

**Issue:** Verification documents need clarification on where they're created vs. where they're attached.

**Current State:**

- Story verification docs created in `_bmad-output/implementation-artifacts/` (e.g., `story-5.1-verification.md`)
- But they need to be in `docs/` for OpenProject attachment

**Gap:** No clear workflow step that:

1. Creates verification doc in `_bmad-output/implementation-artifacts/`
2. Copies to `docs/` for OpenProject attachment
3. Attaches to Story work package

**Fix Required:**

- Add explicit step in story closure workflow to copy verification docs to `docs/`
- Document this in agent responsibilities

#### Gap 3: PM Agent Missing Story File Location Knowledge

**Issue:** PM agent creates story files, but activation sequence doesn't explicitly reference `_bmad-output/implementation-artifacts/`.

**Current State:**

- PM agent loads `config.yaml` (has `implementation_artifacts` path)
- But no explicit activation step to "remember story files go to `{implementation_artifacts}/`"

**Fix Required:**

- Add activation step or principle to PM agent: "Story files created in `{implementation_artifacts}/`"

#### Gap 4: Test Team Missing Verification Doc Workflow

**Issue:** Test team validates stories but doesn't have explicit instructions on:

1. Where to create verification docs
2. How to attach them to OpenProject

**Current State:**

- Test team knows to validate
- But no explicit workflow for creating/attaching verification docs

**Fix Required:**

- Add verification doc creation step to test-validation workflow
- Document: Create in `_bmad-output/implementation-artifacts/`, copy to `docs/`, attach to OpenProject

#### Gap 5: Dev Agent Missing Integration Test Knowledge Source

**Issue:** Dev agent knows to write integration tests, but doesn't know where to get integration test patterns.

**Current State:**

- Dev agent searches Archon for EXTERNAL patterns
- But integration test patterns might be project-specific

**Gap:** No clear knowledge source for:

- Integration test fixtures
- Integration test patterns specific to this project
- How to set up real services for integration tests

**Fix Required:**

- Document integration test patterns in `_bmad-output/implementation-artifacts/` or `docs/`
- Or reference existing integration tests as examples

---

## 3. Role Responsibilities & Knowledge Sources

### Agent Knowledge Sources Matrix

| Agent             | Knowledge Source                                                                                                                                                                                 | Trigger                      | Records To                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **PM**            | `config.yaml` → `planning_artifacts`, `implementation_artifacts`                                                                                                                                 | User selects workflow        | `_bmad-output/implementation-artifacts/{story-key}.md`                                                                     |
| **Dev**           | `config.yaml` → `implementation_artifacts`<br>`story file` from `_bmad-output/`<br>`project-context.md` (coding standards)<br>Archon (EXTERNAL patterns)<br>`testing-strategy.mdc` (auto-loaded) | Task "In progress" (77)      | Story file updates<br>Code in `app/`<br>Tests in `tests/unit/` and `tests/integration/`                                    |
| **TEA/Test Team** | `config.yaml`<br>`testing-strategy.mdc` (auto-loaded)<br>`qa-workflow.mdc` (auto-loaded)<br>OpenProject (work packages)                                                                          | Task/Story "In testing" (79) | Verification docs in `_bmad-output/implementation-artifacts/`<br>Copy to `docs/` for attachment<br>OpenProject attachments |
| **Architect**     | `config.yaml` → `planning_artifacts`<br>Archon (EXTERNAL architecture patterns)                                                                                                                  | User selects workflow        | `_bmad-output/planning-artifacts/architecture.md`<br>OpenProject Feature attachments                                       |
| **Analyst**       | `config.yaml` → `planning_artifacts`<br>Archon (EXTERNAL research)                                                                                                                               | User selects workflow        | `_bmad-output/planning-artifacts/prd.md`<br>OpenProject Epic attachments                                                   |

### Knowledge Base Access Patterns

**✅ CORRECT:**

- All agents load `config.yaml` during activation (step 2)
- All agents automatically receive `cursor-rules.mdc`, `testing-strategy.mdc`, `qa-workflow.mdc` (alwaysApply: true)
- Dev agent reads story files from `_bmad-output/implementation-artifacts/`
- PM agent creates story files in `_bmad-output/implementation-artifacts/`

**❌ MISSING:**

- Explicit activation step for PM: "Story files created in `{implementation_artifacts}/`"
- Explicit workflow for Test Team: "Create verification doc, copy to `docs/`, attach to OpenProject"
- Integration test pattern knowledge source for Dev

---

## 4. Process Flow: Concept to Production

### Current Flow Analysis

```
CONCEPT → PLANNING → IMPLEMENTATION → TESTING → PRODUCTION
```

#### Phase 1: Concept → Planning ✅

**Agents:** Analyst, PM, Architect  
**Knowledge Sources:**

- ✅ Analyst: Archon (EXTERNAL research) → `_bmad-output/planning-artifacts/prd.md`
- ✅ PM: PRD → `_bmad-output/planning-artifacts/epics.md`
- ✅ Architect: PRD → `_bmad-output/planning-artifacts/architecture.md`

**Records:**

- ✅ PRD in `_bmad-output/planning-artifacts/`
- ✅ Epics in `_bmad-output/planning-artifacts/`
- ✅ Architecture in `_bmad-output/planning-artifacts/`
- ✅ Attach to OpenProject (Project/Epic/Feature level)

**Status:** ✅ NO GAPS

#### Phase 2: Planning → Implementation ⚠️

**Agents:** PM, Dev  
**Knowledge Sources:**

- ✅ PM: Epics → Creates story file in `_bmad-output/implementation-artifacts/`
- ✅ PM: Creates tasks in OpenProject
- ✅ Dev: Story file from `_bmad-output/implementation-artifacts/`
- ✅ Dev: `project-context.md` (coding standards)
- ✅ Dev: Archon (EXTERNAL patterns)
- ✅ Dev: `testing-strategy.mdc` (auto-loaded)

**Records:**

- ✅ Story file in `_bmad-output/implementation-artifacts/`
- ✅ Code in `app/`
- ✅ Unit tests in `tests/unit/`
- ✅ Integration tests in `tests/integration/`
- ✅ Story file updates

**Gap:** ⚠️ PM agent activation doesn't explicitly state story file location

**Status:** ⚠️ MINOR GAP (documentation clarity)

#### Phase 3: Implementation → Testing ⚠️

**Agents:** Dev, Test Team  
**Knowledge Sources:**

- ✅ Dev: Runs both test suites before marking "In testing" (79)
- ✅ Test Team: `testing-strategy.mdc` (auto-loaded)
- ✅ Test Team: `qa-workflow.mdc` (auto-loaded)
- ✅ Test Team: OpenProject (work packages)

**Records:**

- ✅ Test results in OpenProject comments
- ✅ Verification docs in `_bmad-output/implementation-artifacts/`
- ⚠️ Verification docs need to be copied to `docs/` for attachment

**Gap:** ⚠️ No explicit workflow step for copying verification docs to `docs/` and attaching to OpenProject

**Status:** ⚠️ GAP (verification doc workflow)

#### Phase 4: Testing → Production ✅

**Agents:** Test Team, PM  
**Knowledge Sources:**

- ✅ Test Team: Validates all stories closed
- ✅ Test Team: Runs epic-level integration tests
- ✅ PM: Reviews epic closure

**Records:**

- ✅ Story/epic closure in OpenProject
- ✅ Verification docs attached to OpenProject

**Status:** ✅ NO GAPS (assuming verification docs workflow fixed)

---

## 5. Required Fixes

### Fix 1: Update Workflow References (CRITICAL)

**Files to Update:**

1. `_bmad/bmm/workflows/4-implementation/test-validation/workflow.yaml`
2. `_bmad/bmm/workflows/4-implementation/bug-management/workflow.yaml`

**Change:**

```yaml
# OLD:
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`

# NEW:
- **QA Workflow:** `_bmad/integrations/qa-workflow.mdc`
- **Testing Strategy:** `_bmad/integrations/testing-strategy.mdc`
```

### Fix 2: Add Verification Doc Workflow Step

**Add to:** `_bmad/bmm/workflows/4-implementation/test-validation/workflow.yaml`

**New Step:** "Verification Document Creation & Attachment"

**Process:**

1. Create verification doc in `_bmad-output/implementation-artifacts/story-{id}-verification.md`
2. Copy to `docs/STORY_{ID}_VERIFICATION.md`
3. Attach to Story work package in OpenProject
4. Update story file with verification doc reference

### Fix 3: Add PM Agent Activation Step

**Add to:** `_bmad/bmm/agents/pm.md` activation sequence

**New Step:**

```xml
<step n="X">Remember: Story files are created in {implementation_artifacts}/ directory (from config.yaml)</step>
```

### Fix 4: Document Integration Test Patterns

**Create:** `_bmad-output/implementation-artifacts/integration-test-patterns.md`

**Content:**

- How to set up real services for integration tests
- Integration test fixtures and patterns
- Examples from existing integration tests

**Reference in:** Dev agent principles or `testing-strategy.mdc`

---

## 6. Questions for Team Review

### Question 1: Verification Document Workflow

**Current Gap:** Verification docs created in `_bmad-output/` but need to be in `docs/` for attachment.

**Question:** Should we:

- **Option A:** Create directly in `docs/` (simpler, but breaks architecture)
- **Option B:** Create in `_bmad-output/`, copy to `docs/`, attach to OpenProject (maintains architecture)
- **Option C:** Create in `_bmad-output/`, attach directly from there (requires OpenProject API support)

**BMad Master Recommendation:** **Option B** - Maintains architecture, clear separation of concerns.

### Question 2: Integration Test Knowledge Source

**Current Gap:** Dev agent needs integration test patterns but they're project-specific.

**Question:** Where should integration test patterns live?

- **Option A:** `_bmad-output/implementation-artifacts/integration-test-patterns.md` (project-specific)
- **Option B:** `docs/integration-test-patterns.md` (for attachment to Feature/Story)
- **Option C:** Reference existing integration tests as examples

**BMad Master Recommendation:** **Option A + C** - Patterns in `_bmad-output/`, reference existing tests.

### Question 3: Test Team Workflow Trigger

**Current State:** Test team validates when work package is "In testing" (79).

**Question:** Should test-validation workflow be:

- **Option A:** Manual trigger (current)
- **Option B:** Automatic trigger when status changes to "In testing" (79)
- **Option C:** Scheduled/periodic validation

**BMad Master Recommendation:** **Option A** - Manual trigger maintains control, but document clearly in workflow.

---

## 7. Summary & Recommendations

### ✅ AGREEMENT

**BMad Master fully agrees with the proposed architecture:**

- `_bmad/` = Agent behavior and rules ✅
- `_bmad-output/` = Project technical information ✅
- `docs/` = OpenProject attachments only ✅

### ⚠️ GAPS TO FIX

1. **CRITICAL:** Update workflow references (broken links to moved files)
2. **HIGH:** Add verification doc workflow step (create → copy → attach)
3. **MEDIUM:** Add PM agent activation step (story file location)
4. **MEDIUM:** Document integration test patterns

### 📋 PROCESS STATUS

**Concept → Production Flow:**

- ✅ Concept → Planning: NO GAPS
- ⚠️ Planning → Implementation: MINOR GAP (documentation clarity)
- ⚠️ Implementation → Testing: GAP (verification doc workflow)
- ✅ Testing → Production: NO GAPS (assuming fixes applied)

### 🎯 NEXT STEPS

1. Fix broken workflow references (Fix 1)
2. Add verification doc workflow step (Fix 2)
3. Add PM agent activation step (Fix 3)
4. Document integration test patterns (Fix 4)
5. Team review of questions (Section 6)

---

**BMad Master Status:** ✅ **AGREEMENT WITH PROPOSAL** + **GAPS IDENTIFIED FOR RESOLUTION**

