# PM Agent Instructions: Story Grooming & Task Creation

**Last Updated:** 2026-01-06  
**Agent:** PM (Product Manager)  
**Status:** MANDATORY INSTRUCTIONS

## Overview

The PM agent is responsible for grooming stories and creating ALL tasks in OpenProject BEFORE the story moves to "In progress". This is a mandatory agile practice.

## PM Responsibilities

### 1. Story Grooming (MANDATORY)

**When:** Before story moves to "In progress"

**PM MUST:**

1. ✅ Review story acceptance criteria
2. ✅ Break down story into implementable tasks (30 min - 4 hours each)
3. ✅ Create story file in `_bmad-output/implementation-artifacts/`
4. ✅ Create ALL tasks in OpenProject using `mcp_openproject_bulk_create_work_packages()`
5. ✅ Set parent relationships for all tasks
6. ✅ Verify all tasks are created and linked
7. ✅ Mark story "In progress" (77) ONLY after tasks created

**CRITICAL:** Story should NOT be marked "In progress" until all tasks are created in OpenProject.

### 2. Task Creation Process

**Step 1: Break Down Story**

Review acceptance criteria and break down into tasks:

```python
# Example: Story 1.5 has 7 tasks
tasks = [
    "Task 1: Implement OAuth 2.0 Token Validation",
    "Task 2: Implement API Key Authentication",
    "Task 3: Create Authentication Middleware",
    "Task 4: Integrate Audit Logging for Authentication",
    "Task 5: Add Authentication Configuration",
    "Task 6: Add Authentication Tests",
    "Task 7: Verify Story Implementation",
]
```

**Step 2: Create Tasks in OpenProject**

```python
# Create all tasks
task_definitions = [
    {
        "subject": "Task 1: Implement OAuth 2.0 Token Validation",
        "type_id": 36,  # Task
        "description": """
        **Task Description:**

        Create OAuth 2.0 token validation function with the following:
        - Extract Bearer token from Authorization header
        - Validate JWT token signature and expiration
        - Extract user_id and tenant_id from token claims
        - Implement user profile lookup fallback if claims missing
        - Add performance monitoring (<50ms requirement)
        - Return structured error (FR-ERROR-003) for invalid tokens

        **Acceptance Criteria:**
        - Bearer tokens extracted from Authorization header
        - Tokens validated against OAuth provider
        - User_id and tenant_id extracted from token claims
        - Authentication completes within <50ms (FR-AUTH-001)
        - Invalid tokens return 401 Unauthorized with structured error (FR-ERROR-003)
        """,
        "status_id": 71  # New
    },
    # ... all tasks
]

# Bulk create
result = mcp_openproject_bulk_create_work_packages(
    project_id=8,
    work_packages=task_definitions
)
```

**Step 3: Set Parent Relationships**

```python
# Link all tasks to story
for task in result["created"]:
    mcp_openproject_set_work_package_parent(
        work_package_id=task["id"],
        parent_id=story_id
    )
```

**Step 4: Verify Tasks Created**

```python
# Verify all tasks are created and linked
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]

assert len(tasks) == len(task_definitions), "Not all tasks created"
assert all(task["parent_id"] == story_id for task in tasks), "Tasks not linked to story"
```

**Step 5: Mark Story In Progress**

```python
# ONLY after all tasks are created
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=77  # In progress
)
```

### 3. Story File Creation

**Create story file in `_bmad-output/implementation-artifacts/`:**

```markdown
# Story 1.5: Authentication Middleware

Status: in-progress

## Story

[Story description]

## Acceptance Criteria

[All acceptance criteria]

## Tasks / Subtasks

- [ ] Task 1: Implement OAuth 2.0 Token Validation (AC: OAuth 2.0)
  - [ ] Create OAuth 2.0 token validation function
  - [ ] Extract Bearer token from Authorization header
  - [ ] ...
- [ ] Task 2: Implement API Key Authentication (AC: API key)
  - [ ] ...
```

## PM Checklist: Story Grooming

**Before marking story as "In progress":**

- [ ] Story acceptance criteria reviewed
- [ ] Story broken down into tasks (7 tasks for Story 1.5)
- [ ] Story file created with all tasks
- [ ] All tasks created in OpenProject
- [ ] All tasks linked to story (parent relationship)
- [ ] Task descriptions include acceptance criteria
- [ ] Story status updated to "In progress" (77)

## Integration with Workflows

### create-story Workflow

When using `create-story` workflow:

1. Create story file
2. **IMMEDIATELY create tasks in OpenProject**
3. Set parent relationships
4. Mark story as ready for implementation

### sprint-planning Workflow

When using `sprint-planning` workflow:

1. Review stories for sprint
2. **Groom each story: create tasks in OpenProject**
3. Verify all tasks are created
4. Mark stories as ready for sprint

## Common Mistakes to Avoid

### ❌ DON'T: Mark Story "In Progress" Before Tasks Created

```python
# WRONG - Story marked in progress before tasks created
mcp_openproject_update_work_package(work_package_id=story_id, status_id=77)
# ... later create tasks ...
```

### ✅ DO: Create Tasks First, Then Mark In Progress

```python
# CORRECT - Tasks created first
mcp_openproject_bulk_create_work_packages(...)
mcp_openproject_set_work_package_parent(...)
# ... verify tasks created ...
mcp_openproject_update_work_package(work_package_id=story_id, status_id=77)
```

### ❌ DON'T: Create Tasks During Implementation

Tasks should be created during grooming, not during implementation.

### ✅ DO: Create Tasks During Grooming

All tasks must be created before story moves to "In progress".

## References

- **Workflow Requirement:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **Groom Story Workflow:** `@bmad/bmm/workflows/groom-story`




