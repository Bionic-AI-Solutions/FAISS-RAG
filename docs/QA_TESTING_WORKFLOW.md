# QA Testing & Story Closure Workflow

**Last Updated:** 2026-01-06  
**Status:** MANDATORY WORKFLOW

## Overview

This workflow defines the complete process for task validation, story validation, bug management, and story/epic closure. It ensures quality gates are met before stories and epics are closed.

## Complete Workflow: Task → Story → Epic Closure

```
Task Implementation
    ↓
Task Testing (Dev)
    ↓
Task Validation (Test Team)
    ↓
All Tasks Complete?
    ↓ YES
Story Testing (Dev)
    ↓
Story Validation (Test Team)
    ↓
Bugs Found?
    ↓ YES → Create Bug → Assign to Dev → Fix → Test Validate (Iterate)
    ↓ NO
Close Story
    ↓
All Stories Complete?
    ↓ YES
Close Epic/Feature
```

## Phase 1: Task Validation

### Step 1: Dev Completes Task

**Dev Actions:**
1. Complete task implementation
2. Run unit tests
3. Run integration tests
4. Update task status to "In testing" (79)
5. Add comment with test results

```python
# Dev marks task ready for testing
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=79,  # In testing
    description="Task complete. Tests passed. Ready for test team validation."
)
```

### Step 2: Test Team Validates Task

**Test Team Actions:**
1. Review task implementation
2. Run test suite for task
3. Verify acceptance criteria met
4. Verify code quality standards
5. Update task status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bug

```python
# Test team validates task
if validation_passes:
    mcp_openproject_update_work_package(
        work_package_id=task_id,
        status_id=82,  # Closed
        description="Task validated. All acceptance criteria met."
    )
else:
    mcp_openproject_update_work_package(
        work_package_id=task_id,
        status_id=81,  # Test failed
        description="Task validation failed. Bug created."
    )
    # Create bug (see Phase 3)
```

## Phase 2: Story Validation

### Step 1: All Tasks Complete

**Prerequisites:**
- All tasks in story are "Closed" (82)
- All task validations passed

**Check:**
```python
# Verify all tasks are closed
children = mcp_openproject_get_work_package_children(parent_id=story_id)
all_closed = all(
    task["status"] == "Closed" 
    for task in children["children"]
)
```

### Step 2: Dev Marks Story Ready for Testing

**Dev Actions:**
1. Verify all tasks are closed
2. Run full story test suite
3. Update story status to "In testing" (79)
4. Add comment with test results

```python
# Dev marks story ready for testing
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=79,  # In testing
    description="All tasks complete. Story ready for test team validation."
)
```

### Step 3: Test Team Validates Story

**Test Team Actions:**
1. Review all task implementations
2. Run full story test suite
3. Verify all acceptance criteria met
4. Verify integration with other stories
5. Verify code quality and architecture patterns
6. Update story status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bug

```python
# Test team validates story
if story_validation_passes:
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=82,  # Closed
        description="Story validated. All acceptance criteria met. All tasks complete."
    )
else:
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=81,  # Test failed
        description="Story validation failed. Bugs created."
    )
    # Create bugs (see Phase 3)
```

## Phase 3: Bug Management & Iteration

### Step 1: Create Bug (Test Team)

**When:** Task or story validation fails

**Test Team Actions:**
1. Create bug work package in OpenProject
2. Link bug to story (parent relationship)
3. Add detailed bug description:
   - What was expected
   - What actually happened
   - Steps to reproduce
   - Test results
   - Acceptance criteria violated
4. Set bug priority (High 74, Normal 73, Low 72)
5. Assign bug to Dev
6. Set bug status to "New" (71)

```python
# Test team creates bug
bug = mcp_openproject_create_work_package(
    project_id=8,
    subject="Bug: [Brief Description]",
    type_id=42,  # Bug
    description="""
    **Bug Report:**
    
    **Story:** Story 1.5: Authentication Middleware
    **Task:** Task 1: Implement OAuth 2.0 Token Validation
    
    **Expected Behavior:**
    OAuth 2.0 token validation should complete within <50ms (FR-AUTH-001)
    
    **Actual Behavior:**
    Token validation takes 120ms, exceeding performance requirement
    
    **Steps to Reproduce:**
    1. Send request with valid OAuth token
    2. Measure authentication time
    3. Observe 120ms response time
    
    **Acceptance Criteria Violated:**
    - FR-AUTH-001: Authentication completes within <50ms
    
    **Test Results:**
    - Unit tests: Pass
    - Performance tests: Fail (120ms > 50ms)
    """,
    priority_id=74,  # High
    status_id=71  # New
)

# Link bug to story
mcp_openproject_set_work_package_parent(
    work_package_id=bug["work_package"]["id"],
    parent_id=story_id
)

# Assign to dev (if assignee_id available)
# mcp_openproject_assign_work_package(
#     work_package_id=bug["work_package"]["id"],
#     assignee_id=dev_user_id
# )
```

### Step 2: Dev Fixes Bug

**Dev Actions:**
1. Review bug description
2. Investigate issue
3. Implement fix
4. Run tests
5. Update bug status to "In testing" (79)
6. Add comment with fix details

```python
# Dev fixes bug
mcp_openproject_update_work_package(
    work_package_id=bug_id,
    status_id=77,  # In progress
    description="Bug fix in progress..."
)

# After fix
mcp_openproject_update_work_package(
    work_package_id=bug_id,
    status_id=79,  # In testing
    description="Bug fixed. Performance optimized to 35ms. Ready for test validation."
)

# Add comment
mcp_openproject_add_work_package_comment(
    work_package_id=bug_id,
    comment="""
    **Fix Applied:**
    
    - Optimized JWT token validation
    - Added caching for token claims
    - Reduced validation time from 120ms to 35ms
    
    **Tests:**
    - Unit tests: Pass
    - Performance tests: Pass (35ms < 50ms)
    - Integration tests: Pass
    """
)
```

### Step 3: Test Team Validates Bug Fix

**Test Team Actions:**
1. Review fix
2. Re-run tests
3. Verify bug is resolved
4. Verify no regressions
5. Update bug status:
   - **"Closed" (82)** if fix validated
   - **"Test failed" (81)** if fix incomplete → Iterate

```python
# Test team validates bug fix
if bug_fix_validated:
    mcp_openproject_update_work_package(
        work_package_id=bug_id,
        status_id=82,  # Closed
        description="Bug fix validated. Performance requirement met (35ms < 50ms)."
    )
    
    # Re-validate story
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=79,  # In testing (re-validate story)
        description="Bug fixed. Re-validating story."
    )
else:
    mcp_openproject_update_work_package(
        work_package_id=bug_id,
        status_id=81,  # Test failed
        description="Bug fix incomplete. Additional fixes needed."
    )
    # Iterate: Dev fixes again
```

### Step 4: Iterate Until All Bugs Fixed

**Process:**
1. Test team validates bug fix
2. If validation fails → Bug status "Test failed" (81)
3. Dev fixes again → Bug status "In testing" (79)
4. Test team validates again
5. Repeat until bug is "Closed" (82)

**Only after all bugs are closed:**
- Story can be re-validated
- Story can be closed

## Phase 4: Story Closure

### Prerequisites for Story Closure

**All of the following must be true:**
1. ✅ All tasks are "Closed" (82)
2. ✅ All bugs are "Closed" (82)
3. ✅ Story validation passed
4. ✅ All acceptance criteria met
5. ✅ Test team approval

### Story Closure Process

**Test Team Actions:**
1. Verify all tasks closed
2. Verify all bugs closed
3. Run final story validation
4. Verify all acceptance criteria met
5. Close story

```python
# Verify prerequisites
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]
bugs = [c for c in children["children"] if c["type"] == "Bug"]

all_tasks_closed = all(task["status"] == "Closed" for task in tasks)
all_bugs_closed = all(bug["status"] == "Closed" for bug in bugs)

if all_tasks_closed and all_bugs_closed and story_validation_passes:
    # Close story
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=82,  # Closed
        description="""
        **Story Closed:**
        
        ✅ All tasks complete and validated
        ✅ All bugs fixed and validated
        ✅ All acceptance criteria met
        ✅ Story validation passed
        ✅ Ready for epic closure
        """
    )
```

## Phase 5: Epic/Feature Closure

### Prerequisites for Epic Closure

**All of the following must be true:**
1. ✅ All stories in epic are "Closed" (82)
2. ✅ All tasks in all stories are "Closed" (82)
3. ✅ All bugs in all stories are "Closed" (82)
4. ✅ Epic validation passed

### Epic Closure Process

**Test Team Actions:**
1. Verify all stories closed
2. Verify all tasks closed
3. Verify all bugs closed
4. Run epic-level integration tests
5. Close epic

```python
# Verify all stories are closed
epic = mcp_openproject_get_work_package(work_package_id=epic_id)
children = mcp_openproject_get_work_package_children(parent_id=epic_id)
stories = [c for c in children["children"] if c["type"] == "User story"]

all_stories_closed = all(story["status"] == "Closed" for story in stories)

# Verify all tasks and bugs in all stories are closed
for story in stories:
    story_children = mcp_openproject_get_work_package_children(parent_id=story["id"])
    tasks = [c for c in story_children["children"] if c["type"] == "Task"]
    bugs = [c for c in story_children["children"] if c["type"] == "Bug"]
    
    all_tasks_closed = all(task["status"] == "Closed" for task in tasks)
    all_bugs_closed = all(bug["status"] == "Closed" for bug in bugs)
    
    if not (all_tasks_closed and all_bugs_closed):
        raise Exception(f"Story {story['id']} has unclosed tasks or bugs")

if all_stories_closed and epic_validation_passes:
    # Close epic
    mcp_openproject_update_work_package(
        work_package_id=epic_id,
        status_id=82,  # Closed
        description="""
        **Epic Closed:**
        
        ✅ All stories complete and validated
        ✅ All tasks complete and validated
        ✅ All bugs fixed and validated
        ✅ Epic validation passed
        """
    )
```

## Status Flow Diagrams

### Task Status Flow

```
New (71) 
    ↓
In progress (77) [Dev starts work]
    ↓
In testing (79) [Dev completes, ready for test]
    ↓
Closed (82) [Test validates] OR Test failed (81) [Create bug]
```

### Story Status Flow

```
New (71)
    ↓
In progress (77) [PM grooms, creates tasks]
    ↓
In testing (79) [All tasks closed, ready for test]
    ↓
Closed (82) [Test validates] OR Test failed (81) [Create bugs]
```

### Bug Status Flow

```
New (71) [Test team creates]
    ↓
In progress (77) [Dev fixes]
    ↓
In testing (79) [Dev completes fix]
    ↓
Closed (82) [Test validates] OR Test failed (81) [Iterate]
```

## Role Responsibilities

### Product Manager (PM)

**During Grooming:**
- Create story file
- Break down into tasks
- Create tasks in OpenProject
- Verify tasks are created
- Mark story "In progress" only after tasks created

### Developer (Dev)

**During Implementation:**
- Verify tasks exist before starting
- Update task status as work progresses
- Mark tasks "In testing" when complete
- Fix bugs assigned by test team
- Mark bugs "In testing" after fix
- Mark story "In testing" when all tasks complete

### Test Team

**During Validation:**
- Validate each task when marked "In testing"
- Close tasks that pass validation
- Create bugs for tasks that fail validation
- Validate story when all tasks complete
- Validate bug fixes
- Close story when all tasks and bugs closed
- Close epic when all stories closed

## OpenProject Status IDs Reference

| Status | ID | Description | Use Case |
|--------|-----|-------------|----------|
| New | 71 | Initial state | New tasks, stories, bugs |
| In specification | 72 | Being specified | Story specification |
| Specified | 73 | Specification complete | Story ready for grooming |
| Confirmed | 74 | Confirmed for sprint | Story confirmed |
| To be scheduled | 75 | Awaiting scheduling | Story scheduling |
| Scheduled | 76 | Scheduled for sprint | Story scheduled |
| In progress | 77 | Active work | Dev working on task/story/bug |
| Developed | 78 | Development complete | Dev work done |
| In testing | 79 | Ready for test | Task/story/bug ready for test validation |
| Tested | 80 | Testing complete | Test validation done |
| Test failed | 81 | Validation failed | Test validation failed → Create bug |
| Closed | 82 | Complete | Task/story/bug/epic closed |
| On hold | 83 | Temporarily paused | Work paused |
| Rejected | 84 | Rejected | Work rejected |

## Example: Complete Story Lifecycle

### Story 1.5: Authentication Middleware

**Phase 1: Grooming (PM)**
1. PM creates story file
2. PM creates 7 tasks in OpenProject (213-219)
3. PM marks story "In progress" (77)

**Phase 2: Implementation (Dev)**
1. Dev starts Task 213 → Status "In progress" (77)
2. Dev completes Task 213 → Status "In testing" (79)
3. Test validates Task 213 → Status "Closed" (82)
4. Repeat for Tasks 214-219
5. All tasks closed → Story status "In testing" (79)

**Phase 3: Story Validation (Test Team)**
1. Test validates story
2. Finds bug: OAuth validation >50ms
3. Creates Bug #220, links to Story 1.5
4. Story status "Test failed" (81)

**Phase 4: Bug Fix (Dev)**
1. Dev fixes bug → Bug status "In testing" (79)
2. Test validates fix → Bug status "Closed" (82)
3. Story re-validated → Story status "In testing" (79)
4. Story validation passes → Story status "Closed" (82)

**Phase 5: Epic Closure (Test Team)**
1. All stories in Epic 1 closed
2. Epic validation passes
3. Epic status "Closed" (82)

## Checklist Templates

### Task Validation Checklist (Test Team)

- [ ] Task implementation reviewed
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Acceptance criteria met
- [ ] Code quality standards met
- [ ] Task status updated (Closed or Test failed)

### Story Validation Checklist (Test Team)

- [ ] All tasks closed
- [ ] All acceptance criteria met
- [ ] Integration tests pass
- [ ] No regressions
- [ ] Code follows architecture patterns
- [ ] Story status updated (Closed or Test failed)

### Bug Creation Checklist (Test Team)

- [ ] Bug description includes expected vs actual
- [ ] Steps to reproduce included
- [ ] Acceptance criteria violated identified
- [ ] Test results included
- [ ] Bug linked to story (parent relationship)
- [ ] Bug priority set
- [ ] Bug assigned to dev

### Story Closure Checklist (Test Team)

- [ ] All tasks closed
- [ ] All bugs closed
- [ ] Story validation passed
- [ ] All acceptance criteria met
- [ ] Story status "Closed" (82)

### Epic Closure Checklist (Test Team)

- [ ] All stories closed
- [ ] All tasks in all stories closed
- [ ] All bugs in all stories closed
- [ ] Epic validation passed
- [ ] Epic status "Closed" (82)

## Integration with OpenProject

### Querying Tasks and Bugs

```python
# Get all tasks for a story
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]
bugs = [c for c in children["children"] if c["type"] == "Bug"]

# Check if all tasks closed
all_tasks_closed = all(task["status"] == "Closed" for task in tasks)

# Check if all bugs closed
all_bugs_closed = all(bug["status"] == "Closed" for bug in bugs)
```

### Creating Bugs

```python
# Create bug linked to story
bug = mcp_openproject_create_work_package(
    project_id=8,
    subject="Bug: [Description]",
    type_id=42,  # Bug
    description="...",
    priority_id=74  # High
)

# Link to story
mcp_openproject_set_work_package_parent(
    work_package_id=bug["work_package"]["id"],
    parent_id=story_id
)
```

## References

- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **Workflow Requirement:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md`
- **OpenProject MCP Tools:** OpenProject integration documentation





