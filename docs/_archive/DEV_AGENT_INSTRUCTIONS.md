# Dev Agent Instructions: Task Implementation & Status Updates

**Last Updated:** 2026-01-06  
**Agent:** Dev  
**Status:** MANDATORY INSTRUCTIONS

## Overview

The Dev agent is responsible for implementing tasks, updating task statuses, fixing bugs, and ensuring all tasks are complete before marking story ready for test validation.

**CRITICAL: Workflow Continuity**

- **DO NOT ask for permission after completing each task** - Continue automatically to the next task
- **DO NOT pause between tasks** - Proceed seamlessly through all tasks in a story
- **Only stop if:** You encounter a blocker, need clarification, or reach the end of the story
- **Always test before proceeding** - Run tests after each implementation (see `docs/DEV_TESTING_RULE.md`)

## Dev Responsibilities

### 1. Verify Tasks Exist (BEFORE Starting)

**CRITICAL:** Before starting implementation, verify all tasks are created in OpenProject.

**MANDATORY WORKFLOW:**

1. **Tasks MUST be created in OpenProject BEFORE implementation starts**
2. **Tasks MUST be linked to story (parent_id set)**
3. **Tasks MUST have clear descriptions with acceptance criteria**
4. **See `docs/STORY_TASK_CREATION_WORKFLOW.md` for complete workflow**

```python
# ALWAYS verify tasks exist before starting
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]

if not tasks:
    raise Exception(
        f"❌ ERROR: No tasks found for story {story_id}. "
        "Tasks must be created BEFORE implementation starts. "
        "Request PM to groom story and create tasks first. "
        "See docs/STORY_TASK_CREATION_WORKFLOW.md for workflow."
    )

print(f"✅ Found {len(tasks)} tasks. Proceeding with implementation.")
```

### 2. Task Implementation Process

**For each task:**

**Step 1: Start Task**

```python
# Mark task as in progress
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=77  # In progress
)
```

**Step 2: Implement Task**

- Write code according to acceptance criteria
- **CRITICAL**: Tests must align with desired functionality, not broken implementations
  - See `docs/TESTING_PRINCIPLES.md` for detailed guidelines
  - Fix implementation when tests fail, don't change tests to pass broken code
- Run unit tests
- Run integration tests
- Verify all acceptance criteria are tested
- Update story file to mark task complete

**Step 3: Mark Task Ready for Test**

```python
# Mark task ready for test team validation
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=79,  # In testing
    description="Task complete. Tests passed. Ready for test team validation."
)

# Add comment with test results
mcp_openproject_add_work_package_comment(
    work_package_id=task_id,
    comment="""
    **Implementation Complete:**

    - OAuth 2.0 token validation implemented
    - Unit tests: 12/12 passed
    - Integration tests: 5/5 passed
    - Performance: 35ms (meets <50ms requirement)
    - Ready for test team validation
    """
)
```

**Step 4: Update Story File**

- Mark task as complete in story file
- Update task status in `_bmad-output/implementation-artifacts/[story].md`

**Step 5: Add Verification Documents to OpenProject (When Story Complete)**

When all tasks are complete and story verification is done:

```python
import base64

# Read and encode verification document
with open("docs/STORY_X_Y_VERIFICATION.md", "rb") as f:
    verification_content = base64.b64encode(f.read()).decode("utf-8")

mcp_openproject_add_work_package_attachment(
    work_package_id=story_id,
    file_data=verification_content,
    filename="STORY_X_Y_VERIFICATION.md",
    content_type="text/markdown",
    description="Story verification report with acceptance criteria validation"
)

# Add test alignment verification if created
if os.path.exists("docs/STORY_X_Y_TEST_ALIGNMENT_VERIFICATION.md"):
    with open("docs/STORY_X_Y_TEST_ALIGNMENT_VERIFICATION.md", "rb") as f:
        alignment_content = base64.b64encode(f.read()).decode("utf-8")

    mcp_openproject_add_work_package_attachment(
        work_package_id=story_id,
        file_data=alignment_content,
        filename="STORY_X_Y_TEST_ALIGNMENT_VERIFICATION.md",
        content_type="text/markdown",
        description="Test alignment verification ensuring tests validate desired functionality"
    )
```

**Note:** Verification documents provide traceability and support test team validation. Always create and attach them when a story is complete.

### 3. Bug Fix Process

**When bug is created by test team:**

**Step 1: Review Bug**

```python
# Get bug details
bug = mcp_openproject_get_work_package(work_package_id=bug_id)
```

**Step 2: Fix Bug**

```python
# Mark bug as in progress
mcp_openproject_update_work_package(
    work_package_id=bug_id,
    status_id=77  # In progress
)

# ... fix bug ...

# Mark bug ready for test
mcp_openproject_update_work_package(
    work_package_id=bug_id,
    status_id=79,  # In testing
    description="Bug fixed. Ready for test team validation."
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

**Step 3: Iterate if Needed**

- If test team marks bug "Test failed" (81), fix again
- Repeat until bug is "Closed" (82)

### 4. Mark Story Ready for Test

**When all tasks are closed:**

```python
# Verify all tasks closed
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]
bugs = [c for c in children["children"] if c["type"] == "Bug"]

all_tasks_closed = all(task["status"] == "Closed" for task in tasks)
all_bugs_closed = all(bug["status"] == "Closed" for bug in bugs)

if all_tasks_closed and all_bugs_closed:
    # Mark story ready for test
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=79,  # In testing
        description="All tasks complete. All bugs fixed. Story ready for test team validation."
    )
```

## Dev Checklist

### Before Starting Implementation

- [ ] **CRITICAL:** Verify all tasks exist in OpenProject (MUST exist before starting)
- [ ] Verify all tasks are linked to story (parent_id set)
- [ ] Review task descriptions and acceptance criteria
- [ ] Review story acceptance criteria
- [ ] If tasks don't exist → STOP and request PM to create tasks first
- [ ] See `docs/STORY_TASK_CREATION_WORKFLOW.md` for complete workflow

### During Implementation

- [ ] Update task status as work progresses
- [ ] Add comments to tasks documenting progress
- [ ] Update story file to mark tasks complete
- [ ] Run tests before marking task "In testing"
- [ ] Fix bugs assigned by test team
- [ ] Iterate on bug fixes until closed

### Before Marking Story Ready for Test

- [ ] All tasks are "Closed" (82)
- [ ] All bugs are "Closed" (82)
- [ ] Story marked "In testing" (79)

## Task Status Updates

**Always update task status as work progresses:**

1. **Start Task:** "In progress" (77)
2. **Complete Task:** "In testing" (79)
3. **Task Validated:** "Closed" (82) - Test team does this
4. **Task Failed:** "Test failed" (81) - Test team does this → Create bug

## Bug Status Updates

**When fixing bugs:**

1. **Start Fix:** "In progress" (77)
2. **Complete Fix:** "In testing" (79)
3. **Fix Validated:** "Closed" (82) - Test team does this
4. **Fix Incomplete:** "Test failed" (81) - Test team does this → Iterate

## Common Mistakes to Avoid

### ❌ DON'T: Start Implementation Without Tasks

```python
# WRONG - Starting without verifying tasks exist
# ... start coding immediately ...
```

### ✅ DO: Verify Tasks Exist First (MANDATORY)

```python
# CORRECT - Verify tasks exist before starting
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]

if not tasks:
    raise Exception(
        f"❌ ERROR: No tasks found for story {story_id}. "
        "Tasks must be created BEFORE implementation starts. "
        "Request PM to groom story and create tasks first. "
        "See docs/STORY_TASK_CREATION_WORKFLOW.md for workflow."
    )

print(f"✅ Found {len(tasks)} tasks. Proceeding with implementation.")
```

**See `docs/STORY_TASK_CREATION_WORKFLOW.md` for complete workflow and examples.**

### ❌ DON'T: Skip Task Status Updates

Always update task status as work progresses.

### ✅ DO: Update Task Status Regularly

```python
# Start task
mcp_openproject_update_work_package(task_id, status_id=77)

# ... work on task ...

# Complete task
mcp_openproject_update_work_package(task_id, status_id=79)
```

## References

- **Story Task Creation Workflow:** `docs/STORY_TASK_CREATION_WORKFLOW.md` ⚠️ **MANDATORY**
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **Testing Principles:** `docs/TESTING_PRINCIPLES.md`
- **Dev Story Workflow:** `@bmad/bmm/workflows/dev-story`
