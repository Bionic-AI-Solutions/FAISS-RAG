# Complete Agile Workflow: Grooming → Implementation → Testing → Closure

**Last Updated:** 2026-01-06  
**Status:** MANDATORY WORKFLOW

## Overview

This document provides the complete end-to-end agile workflow from story grooming through epic closure, including all quality gates and validation steps.

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: STORY GROOMING (PM)                               │
├─────────────────────────────────────────────────────────────┤
│ 1. Review story acceptance criteria                         │
│ 2. Break down into tasks                                    │
│ 3. Create story file                                        │
│ 4. Create ALL tasks in OpenProject                         │
│ 5. Set parent relationships                                 │
│ 6. Mark story "In progress" (77)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: TASK IMPLEMENTATION (Dev)                         │
├─────────────────────────────────────────────────────────────┤
│ For each task:                                              │
│ 1. Start task → Status "In progress" (77)                  │
│ 2. Implement task                                           │
│ 3. Run tests                                                │
│ 4. Mark task "In testing" (79)                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: TASK VALIDATION (Test Team)                       │
├─────────────────────────────────────────────────────────────┤
│ For each task:                                              │
│ 1. Review implementation                                    │
│ 2. Run test suite                                           │
│ 3. Verify acceptance criteria                               │
│ 4. Update status:                                           │
│    - "Closed" (82) if passes                                │
│    - "Test failed" (81) if fails → Create bug               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: BUG FIX ITERATION (Dev ↔ Test Team)               │
├─────────────────────────────────────────────────────────────┤
│ If bugs created:                                            │
│ 1. Test team creates bug, assigns to dev                    │
│ 2. Dev fixes bug → Status "In testing" (79)                 │
│ 3. Test validates fix:                                     │
│    - "Closed" (82) if validated                             │
│    - "Test failed" (81) if incomplete → Iterate             │
│ 4. Repeat until all bugs "Closed" (82)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: STORY VALIDATION (Test Team)                      │
├─────────────────────────────────────────────────────────────┤
│ Prerequisites:                                              │
│ - All tasks "Closed" (82)                                   │
│ - All bugs "Closed" (82)                                    │
│                                                             │
│ Process:                                                    │
│ 1. Dev marks story "In testing" (79)                        │
│ 2. Test team validates story                               │
│ 3. Update status:                                           │
│    - "Closed" (82) if passes                                │
│    - "Test failed" (81) if fails → Create bugs → Iterate    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: STORY CLOSURE (Test Team)                         │
├─────────────────────────────────────────────────────────────┤
│ Prerequisites:                                              │
│ - All tasks "Closed" (82)                                   │
│ - All bugs "Closed" (82)                                    │
│ - Story validation passed                                   │
│                                                             │
│ Process:                                                    │
│ 1. Verify all prerequisites                                 │
│ 2. Close story (status 82)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: EPIC CLOSURE (Test Team)                          │
├─────────────────────────────────────────────────────────────┤
│ Prerequisites:                                              │
│ - All stories "Closed" (82)                                 │
│ - All tasks in all stories "Closed" (82)                    │
│ - All bugs in all stories "Closed" (82)                     │
│                                                             │
│ Process:                                                    │
│ 1. Verify all prerequisites                                 │
│ 2. Run epic-level integration tests                         │
│ 3. Close epic (status 82)                                   │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Phase Descriptions

### Phase 1: Story Grooming (PM)

**Timing:** Before story moves to "In progress"

**PM Checklist:**
- [ ] Review story acceptance criteria
- [ ] Break down into implementable tasks (30 min - 4 hours each)
- [ ] Create story file in `_bmad-output/implementation-artifacts/`
- [ ] Create ALL tasks in OpenProject using `mcp_openproject_bulk_create_work_packages()`
- [ ] Set parent relationships for all tasks
- [ ] Verify all tasks are created and linked
- [ ] Mark story "In progress" (77) ONLY after tasks created

**Outputs:**
- Story file with tasks
- All tasks created in OpenProject
- Story ready for implementation

### Phase 2: Task Implementation (Dev)

**Timing:** After story is "In progress" and tasks are created

**Dev Checklist (Per Task):**
- [ ] Verify task exists in OpenProject
- [ ] Start task → Status "In progress" (77)
- [ ] Implement task according to acceptance criteria
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Update story file to mark task complete
- [ ] Mark task "In testing" (79)
- [ ] Add comment with test results

**Outputs:**
- Task implementation complete
- Tests passing
- Task ready for test validation

### Phase 3: Task Validation (Test Team)

**Timing:** When task is "In testing" (79)

**Test Team Checklist (Per Task):**
- [ ] Review task implementation
- [ ] Run test suite for task
- [ ] Verify acceptance criteria met
- [ ] Verify code quality standards
- [ ] Update task status:
  - "Closed" (82) if validation passes
  - "Test failed" (81) if validation fails → Create bug

**Outputs:**
- Task validated and closed, OR
- Bug created for task issues

### Phase 4: Bug Fix Iteration (Dev ↔ Test Team)

**Timing:** When task or story validation fails

**Iteration Process:**
1. **Test Team:** Create bug, link to story, assign to dev
2. **Dev:** Fix bug → Status "In testing" (79)
3. **Test Team:** Validate fix:
   - "Closed" (82) if validated
   - "Test failed" (81) if incomplete → Iterate
4. **Repeat** until bug is "Closed" (82)

**Outputs:**
- All bugs closed
- Story ready for re-validation

### Phase 5: Story Validation (Test Team)

**Timing:** When all tasks are "Closed" (82)

**Prerequisites:**
- ✅ All tasks "Closed" (82)
- ✅ All bugs "Closed" (82)
- ✅ Story marked "In testing" (79) by dev

**Test Team Checklist:**
- [ ] Verify all tasks closed
- [ ] Verify all bugs closed
- [ ] Run full story test suite
- [ ] Verify all acceptance criteria met
- [ ] Verify integration with other stories
- [ ] Update story status:
  - "Closed" (82) if validation passes
  - "Test failed" (81) if validation fails → Create bugs → Iterate

**Outputs:**
- Story validated and closed, OR
- Bugs created for story issues

### Phase 6: Story Closure (Test Team)

**Timing:** After story validation passes

**Prerequisites:**
- ✅ All tasks "Closed" (82)
- ✅ All bugs "Closed" (82)
- ✅ Story validation passed

**Test Team Actions:**
1. Verify all prerequisites
2. Close story (status 82)
3. Add final comment summarizing completion

**Outputs:**
- Story closed
- Ready for epic closure

### Phase 7: Epic Closure (Test Team)

**Timing:** When all stories in epic are "Closed" (82)

**Prerequisites:**
- ✅ All stories "Closed" (82)
- ✅ All tasks in all stories "Closed" (82)
- ✅ All bugs in all stories "Closed" (82)

**Test Team Actions:**
1. Verify all prerequisites
2. Run epic-level integration tests
3. Close epic (status 82)

**Outputs:**
- Epic closed
- Feature complete

## Status Transitions

### Task Status Flow

```
New (71) 
    ↓ [Dev starts]
In progress (77)
    ↓ [Dev completes]
In testing (79)
    ↓ [Test validates]
Closed (82) OR Test failed (81) → Create bug
```

### Story Status Flow

```
New (71)
    ↓ [PM grooms, creates tasks]
In progress (77)
    ↓ [All tasks closed, dev marks ready]
In testing (79)
    ↓ [Test validates]
Closed (82) OR Test failed (81) → Create bugs
```

### Bug Status Flow

```
New (71) [Test team creates]
    ↓ [Dev fixes]
In progress (77)
    ↓ [Dev completes fix]
In testing (79)
    ↓ [Test validates]
Closed (82) OR Test failed (81) → Iterate
```

## Role Responsibilities Summary

### Product Manager (PM)

**Grooming Phase:**
- Create story file
- Break down into tasks
- Create ALL tasks in OpenProject
- Verify tasks created
- Mark story "In progress" only after tasks created

### Developer (Dev)

**Implementation Phase:**
- Verify tasks exist before starting
- Update task status as work progresses
- Mark tasks "In testing" when complete
- Fix bugs assigned by test team
- Mark story "In testing" when all tasks complete

**Bug Fix Phase:**
- Fix bugs assigned by test team
- Mark bugs "In testing" after fix
- Iterate until bugs closed

### Test Team

**Validation Phase:**
- Validate each task when "In testing"
- Close tasks that pass validation
- Create bugs for tasks that fail validation
- Validate story when all tasks complete
- Validate bug fixes
- Close story when all tasks and bugs closed
- Close epic when all stories closed

## Quality Gates

### Task Quality Gate

**Before task can be closed:**
- ✅ Implementation complete
- ✅ Unit tests pass
- ✅ Integration tests pass
- ✅ Acceptance criteria met
- ✅ Test team validation passed

### Story Quality Gate

**Before story can be closed:**
- ✅ All tasks closed
- ✅ All bugs closed
- ✅ All acceptance criteria met
- ✅ Story integration tests pass
- ✅ Test team validation passed

### Epic Quality Gate

**Before epic can be closed:**
- ✅ All stories closed
- ✅ All tasks in all stories closed
- ✅ All bugs in all stories closed
- ✅ Epic integration tests pass
- ✅ Test team validation passed

## OpenProject Work Package Types

| Type | ID | Description |
|------|-----|-------------|
| Task | 36 | Implementation task |
| Bug | 42 | Bug/defect |
| User story | 41 | User story |
| Epic | 40 | Epic/feature |

## Example: Complete Story Lifecycle

### Story 1.5: Authentication Middleware

**Phase 1: Grooming (PM)**
- PM creates story file with 7 tasks
- PM creates tasks 213-219 in OpenProject
- PM marks story "In progress" (77)

**Phase 2: Implementation (Dev)**
- Dev implements Task 213 → "In testing" (79)
- Test validates Task 213 → "Closed" (82)
- Repeat for Tasks 214-219
- All tasks closed → Story "In testing" (79)

**Phase 3: Story Validation (Test Team)**
- Test validates story
- Finds bug: OAuth validation >50ms
- Creates Bug #220, links to Story 1.5
- Story "Test failed" (81)

**Phase 4: Bug Fix (Dev ↔ Test Team)**
- Dev fixes bug → Bug "In testing" (79)
- Test validates fix → Bug "Closed" (82)
- Story re-validated → Story "Closed" (82)

**Phase 5: Epic Closure (Test Team)**
- All stories in Epic 1 closed
- Epic validation passes
- Epic "Closed" (82)

## Integration with BMAD Workflows

### PM Workflows

- **create-story:** Creates story, then calls groom-story
- **groom-story:** Creates tasks in OpenProject (NEW workflow)
- **sprint-planning:** Grooms stories for sprint, creates tasks

### Dev Workflows

- **dev-story:** Verifies tasks exist, implements story, updates task statuses

### Test Team Workflows

- **test-validation:** Validates tasks and stories (NEW workflow)
- **bug-management:** Creates bugs, validates fixes (NEW workflow)

## References

- **Task Creation Requirement:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md`
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`





