# Test Team Instructions: Validation & Bug Management

**Last Updated:** 2026-01-06  
**Agent:** Test Team  
**Status:** MANDATORY INSTRUCTIONS

## Overview

The Test Team is responsible for validating tasks and stories, creating bugs for failures, validating bug fixes, and closing stories/epics only after all work is validated.

## Test Team Responsibilities

### 1. Task Validation

**When:** Task is marked "In testing" (79)

**Process:**
1. Review task implementation
2. Run test suite for task
3. Verify acceptance criteria met
4. Verify code quality standards
5. Update task status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bug

```python
# Validate task
if task_validation_passes:
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
    # Create bug (see Bug Creation below)
```

### 2. Story Validation

**When:** All tasks are "Closed" (82) and story is "In testing" (79)

**Prerequisites:**
- ✅ All tasks "Closed" (82)
- ✅ All bugs "Closed" (82)

**Process:**
1. Review all task implementations
2. Run full story test suite
3. Verify all acceptance criteria met
4. Verify integration with other stories
5. Update story status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bugs

```python
# Verify prerequisites
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]
bugs = [c for c in children["children"] if c["type"] == "Bug"]

all_tasks_closed = all(task["status"] == "Closed" for task in tasks)
all_bugs_closed = all(bug["status"] == "Closed" for bug in bugs)

if not (all_tasks_closed and all_bugs_closed):
    raise Exception("Cannot validate story: tasks or bugs not closed")

# Validate story
if story_validation_passes:
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=82,  # Closed
        description="Story validated. All acceptance criteria met."
    )
else:
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=81,  # Test failed
        description="Story validation failed. Bugs created."
    )
    # Create bugs (see Bug Creation below)
```

### 3. Bug Creation

**When:** Task or story validation fails

**Process:**
1. Create bug work package
2. Link bug to story (parent relationship)
3. Add detailed bug description
4. Set bug priority
5. Assign bug to dev
6. Set bug status to "New" (71)

```python
# Create bug
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

### 4. Bug Fix Validation

**When:** Bug is marked "In testing" (79) after dev fix

**Process:**
1. Review fix
2. Re-run tests
3. Verify bug is resolved
4. Verify no regressions
5. Update bug status:
   - **"Closed" (82)** if fix validated
   - **"Test failed" (81)** if fix incomplete → Iterate

```python
# Validate bug fix
if bug_fix_validated:
    mcp_openproject_update_work_package(
        work_package_id=bug_id,
        status_id=82,  # Closed
        description="Bug fix validated. Performance requirement met (35ms < 50ms)."
    )
    
    # Re-validate story if all bugs closed
    children = mcp_openproject_get_work_package_children(parent_id=story_id)
    bugs = [c for c in children["children"] if c["type"] == "Bug"]
    all_bugs_closed = all(bug["status"] == "Closed" for bug in bugs)
    
    if all_bugs_closed:
        # Re-validate story
        mcp_openproject_update_work_package(
            work_package_id=story_id,
            status_id=79,  # In testing (re-validate)
            description="All bugs fixed. Re-validating story."
        )
else:
    mcp_openproject_update_work_package(
        work_package_id=bug_id,
        status_id=81,  # Test failed
        description="Bug fix incomplete. Additional fixes needed."
    )
    # Iterate: Dev fixes again
```

### 5. Story Closure

**Prerequisites:**
- ✅ All tasks "Closed" (82)
- ✅ All bugs "Closed" (82)
- ✅ Story validation passed

**Process:**
1. Verify all prerequisites
2. Close story (status 82)

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

### 6. Epic Closure

**Prerequisites:**
- ✅ All stories "Closed" (82)
- ✅ All tasks in all stories "Closed" (82)
- ✅ All bugs in all stories "Closed" (82)

**Process:**
1. Verify all prerequisites
2. Run epic-level integration tests
3. Close epic (status 82)

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

## Test Team Checklist

### Task Validation Checklist

- [ ] Task implementation reviewed
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Acceptance criteria met
- [ ] Code quality standards met
- [ ] Task status updated (Closed or Test failed)

### Story Validation Checklist

- [ ] All tasks closed
- [ ] All bugs closed
- [ ] All acceptance criteria met
- [ ] Integration tests pass
- [ ] No regressions
- [ ] Code follows architecture patterns
- [ ] Story status updated (Closed or Test failed)

### Bug Creation Checklist

- [ ] Bug description includes expected vs actual
- [ ] Steps to reproduce included
- [ ] Acceptance criteria violated identified
- [ ] Test results included
- [ ] Bug linked to story (parent relationship)
- [ ] Bug priority set
- [ ] Bug assigned to dev

### Bug Fix Validation Checklist

- [ ] Fix reviewed
- [ ] Tests re-run
- [ ] Bug resolved
- [ ] No regressions
- [ ] Bug status updated (Closed or Test failed)

### Story Closure Checklist

- [ ] All tasks closed
- [ ] All bugs closed
- [ ] Story validation passed
- [ ] All acceptance criteria met
- [ ] Story status "Closed" (82)

### Epic Closure Checklist

- [ ] All stories closed
- [ ] All tasks in all stories closed
- [ ] All bugs in all stories closed
- [ ] Epic validation passed
- [ ] Epic status "Closed" (82)

## References

- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **Test Validation Workflow:** `@bmad/bmm/workflows/test-validation`





