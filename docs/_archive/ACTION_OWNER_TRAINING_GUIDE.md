# Action Owner Training Guide

**Date:** 2026-01-06  
**Purpose:** Training guide for action owners (PM, Dev, Test Team) on immediate status transition responsibilities

## Overview

This guide explains the **IMMEDIATE** status transition responsibilities for all action owners. When you update a work package status, you MUST immediately check and update parent work package statuses if conditions are met.

## Core Principle

**IMMEDIATE = When conditions are met, update parent status RIGHT AWAY, not later.**

---

## Status Transition Rules

### Epic Status Transitions

| When | Epic Status | Action Owner | Action Required |
|------|-------------|--------------|-----------------|
| First story → "In progress" (77) | Epic → "In progress" (77) | PM/Dev | **IMMEDIATE** - Update epic status |
| Last story → "Closed" (82) | Epic → "Closed" (82) | Test Team | **IMMEDIATE** - Update epic status |

### Story Status Transitions

| When | Story Status | Action Owner | Action Required |
|------|-------------|--------------|-----------------|
| First task → "In progress" (77) | Story → "In progress" (77) | Dev | **IMMEDIATE** - Update story status |
| Test task → "In testing" (79) + all other tasks closed | Story → "In testing" (79) | Dev | **IMMEDIATE** - Update story status |
| All tasks + bugs → "Closed" (82) | Story → "Closed" (82) | Dev/Test Team | **IMMEDIATE** - Update story status |

---

## Action Owner Responsibilities

### Product Manager (PM)

**When Creating Epics:**
1. Create epic with comprehensive description
2. Include story breakdown in description
3. Create test story (Story X.T)
4. Attach design document

**When Grooming Stories:**
1. Create story with acceptance criteria
2. Break down into tasks
3. **CRITICAL:** Check for existing tasks (use `status="all"`) before creating
4. Create test task (Task X.Y.T)
5. Attach UI documents for UI stories

**Status Updates:**
- When creating epics/stories, no immediate status updates needed (they start as "New")
- When stories move to "In progress", check if epic should also move to "In progress"

### Developer (Dev)

**When Starting a Task:**
1. Update task status to "In progress" (77)
2. **IMMEDIATE:** Check if this is the first task for the story
3. **IMMEDIATE:** If first task, update story status to "In progress" (77)
4. **IMMEDIATE:** Check if story is first story for epic
5. **IMMEDIATE:** If first story, update epic status to "In progress" (77)

**When Completing a Task:**
1. Update task status to "In testing" (79)
2. **IMMEDIATE:** If this is the test task (Task X.Y.T), check if all other tasks are closed
3. **IMMEDIATE:** If test task ready and all other tasks closed, update story status to "In testing" (79)

**When Closing a Task:**
1. Update task status to "Closed" (82)
2. **IMMEDIATE:** Check if all tasks and bugs for the story are closed
3. **IMMEDIATE:** If all closed, update story status to "Closed" (82)
4. **IMMEDIATE:** Check if all stories for the epic are closed
5. **IMMEDIATE:** If all stories closed, update epic status to "Closed" (82)

**Example Workflow:**

```python
# Step 1: Start task
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=77  # In progress
)

# Step 2: IMMEDIATE - Update story if first task
from scripts.openproject_status_helpers import update_story_status_based_on_tasks
update_story_status_based_on_tasks(story_id)

# Step 3: IMMEDIATE - Update epic if first story
# (This is handled by the helper function if epic is parent)

# ... implement task ...

# Step 4: Complete task
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=79  # In testing
)

# Step 5: IMMEDIATE - Update story if test task ready
if ".T:" in task_subject:
    from scripts.openproject_status_helpers import update_story_status_when_test_task_ready
    update_story_status_when_test_task_ready(story_id, task_id)

# Step 6: After test validation, close task
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=82  # Closed
)

# Step 7: IMMEDIATE - Update story if all tasks closed
from scripts.openproject_status_helpers import update_story_status_when_all_tasks_closed
update_story_status_when_all_tasks_closed(story_id)
```

### Test Team

**When Validating Tasks:**
1. Review task implementation
2. Run test suite
3. Verify acceptance criteria
4. Update task status:
   - "Closed" (82) if validation passes
   - "Test failed" (81) if validation fails → Create bug
5. **IMMEDIATE:** If task closed, check if all tasks/bugs for story are closed
6. **IMMEDIATE:** If all closed, update story status to "Closed" (82)

**When Validating Stories:**
1. Review all task implementations
2. Run full story test suite
3. Verify all acceptance criteria met
4. Update story status:
   - "Closed" (82) if validation passes
   - "Test failed" (81) if validation fails → Create bugs
5. **IMMEDIATE:** If story closed, check if all stories for epic are closed
6. **IMMEDIATE:** If all stories closed, update epic status to "Closed" (82)

**When Closing Epics:**
1. Verify all stories closed
2. Verify all tasks closed
3. Verify all bugs closed
4. Run epic-level integration tests
5. Close epic (status 82)

**Example Workflow:**

```python
# Step 1: Validate task
if validation_passes:
    mcp_openproject_update_work_package(
        work_package_id=task_id,
        status_id=82  # Closed
    )
    
    # Step 2: IMMEDIATE - Check if story should close
    from scripts.openproject_status_helpers import update_story_status_when_all_tasks_closed
    update_story_status_when_all_tasks_closed(story_id)
else:
    # Create bug
    bug = mcp_openproject_create_work_package(
        project_id=8,
        subject=f"Bug: {task_subject}",
        type_id=42,  # Bug
        description="Task validation failed..."
    )
    mcp_openproject_set_work_package_parent(
        work_package_id=bug["work_package"]["id"],
        parent_id=story_id
    )

# Step 3: Validate story
if all_tasks_closed and all_bugs_closed:
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=82  # Closed
    )
    
    # Step 4: IMMEDIATE - Check if epic should close
    from scripts.openproject_status_helpers import update_epic_status_based_on_stories
    # Get epic from story hierarchy
    hierarchy = mcp_openproject_get_work_package_hierarchy(work_package_id=story_id)
    epic = next((a for a in hierarchy.get("ancestors", []) if a["type"]["id"] == 40), None)
    if epic:
        update_epic_status_based_on_stories(epic["id"])
```

---

## Helper Functions

**Location:** `scripts/openproject_status_helpers.py`

**Available Functions:**
- `update_epic_status_based_on_stories(epic_id)` - Update epic status based on story statuses
- `update_story_status_based_on_tasks(story_id)` - Update story status when first task starts
- `update_story_status_when_test_task_ready(story_id, test_task_id)` - Update story status when test task ready
- `update_story_status_when_all_tasks_closed(story_id)` - Update story status when all tasks closed

**Usage:**
```python
from scripts.openproject_status_helpers import (
    update_epic_status_based_on_stories,
    update_story_status_based_on_tasks,
    update_story_status_when_test_task_ready,
    update_story_status_when_all_tasks_closed
)

# Call immediately after updating work package status
update_story_status_based_on_tasks(story_id)
```

---

## Common Mistakes to Avoid

### ❌ WRONG: Delayed Updates

```python
# BAD - Update task, forget to update story
mcp_openproject_update_work_package(work_package_id=task_id, status_id=77)
# ... later, maybe update story ...
```

### ✅ CORRECT: Immediate Updates

```python
# GOOD - Update task, immediately update story
mcp_openproject_update_work_package(work_package_id=task_id, status_id=77)
update_story_status_based_on_tasks(story_id)  # IMMEDIATE
```

### ❌ WRONG: Manual Checking

```python
# BAD - Manually checking conditions
if some_condition:
    # Maybe update later...
    pass
```

### ✅ CORRECT: Use Helper Functions

```python
# GOOD - Use helper functions that check conditions
update_story_status_based_on_tasks(story_id)  # Helper checks conditions
```

---

## Status IDs Reference

| Status | ID | Use Case |
|--------|-----|----------|
| New | 71 | Initial state |
| In progress | 77 | Active work |
| In testing | 79 | Ready for test validation |
| Closed | 82 | Complete |
| Test failed | 81 | Validation failed |

---

## Type IDs Reference

| Type | ID | Use Case |
|------|-----|----------|
| Epic | 40 | High-level feature grouping |
| Feature | 39 | Optional intermediate grouping |
| User Story | 41 | User-facing functionality |
| Task | 36 | Implementation work item |
| Bug | 42 | Defect or issue |

---

## Checklist for Action Owners

### Before Starting Work

- [ ] Understand which work package you're working on
- [ ] Know the parent work package (story/epic)
- [ ] Know the helper functions available
- [ ] Know when to call helper functions

### During Work

- [ ] Update work package status as work progresses
- [ ] **IMMEDIATE:** Call helper function after status update
- [ ] Verify parent status was updated correctly
- [ ] Add comments documenting progress

### After Completing Work

- [ ] Verify all statuses are correct
- [ ] Verify parent statuses are correct
- [ ] Verify helper functions were called
- [ ] Document any issues or blockers

---

## Questions?

**For Workflow Questions:**
- See: `@bmad/bmm/workflows/epic-story-lifecycle`
- See: `docs/BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md`

**For Technical Questions:**
- See: `scripts/openproject_status_helpers.py`
- See: `docs/USING_MCP_TOOLS_FOR_OPENPROJECT.md`

**For Process Questions:**
- Contact: Scrum Master (SM)
- Contact: Product Manager (PM)

---

**Remember: IMMEDIATE means RIGHT AWAY, not later!**


