# Task Management Process

**Last Updated:** 2026-01-06

## ⚠️ CRITICAL WORKFLOW REQUIREMENT

**ALL tasks for a story MUST be created in OpenProject during the GROOMING phase, BEFORE implementation begins.**

This is a mandatory agile practice:

- **PM Responsibility:** Create tasks during story grooming, before story moves to "In progress"
- **Dev Responsibility:** Verify tasks exist before starting implementation, update task statuses during work

**See:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md` for complete workflow requirements.

## Overview

All stories must have their tasks created and tracked in OpenProject. Tasks should be created during the **grooming phase**, before implementation starts.

## Process

### 1. Story Grooming Phase (PM Responsibility) - BEFORE Implementation

**This phase happens BEFORE the story moves to "In progress":**

1. **Create Story File** in `_bmad-output/implementation-artifacts/`
2. **Break Down Tasks** in the story file (map to acceptance criteria)
3. **⚠️ Check for Existing Tasks** - Query OpenProject with `status="all"` to check for existing tasks (including closed stories) to avoid duplicates
4. **Create Tasks in OpenProject** using `mcp_openproject_bulk_create_work_packages()` (only create tasks that don't already exist)
5. **Set Parent Relationships** using `mcp_openproject_set_work_package_parent()`
6. **Verify All Tasks Created** - Check that all tasks are linked to story
7. **Update Story Status** to "In progress" (77) - ONLY after tasks are created

**⚠️ CRITICAL:** 
- Story should NOT be marked "In progress" until all tasks are created in OpenProject.
- **Always check for existing tasks first** - Some stories may be closed and won't appear in default views. Use `status="all"` when querying to include closed stories/tasks.

### 2. During Implementation

1. **Update Task Status** as you complete each task:

   - "In progress" (77) - When starting work
   - "In testing" (79) - When ready for testing
   - "Closed" (82) - When complete

2. **Add Comments** to tasks documenting:

   - What was implemented
   - Test results
   - Any issues encountered
   - Verification steps

3. **Update Story File** to mark tasks as complete

### 3. Task Validation (Test Team)

**When:** Task is marked "In testing" (79)

**Test Team Actions:**

1. Review task implementation
2. Run test suite
3. Verify acceptance criteria met
4. Update task status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bug

### 4. Story Validation (Test Team)

**When:** All tasks are "Closed" (82) and story is marked "In testing" (79)

**Test Team Actions:**

1. Review all task implementations
2. Run full story test suite
3. Verify all acceptance criteria met
4. Update story status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bugs

### 5. Bug Management (Test Team → Dev → Test Team)

**When:** Task or story validation fails

**Process:**

1. Test team creates bug, links to story, assigns to dev
2. Dev fixes bug, marks "In testing" (79)
3. Test team validates fix:
   - **"Closed" (82)** if fix validated
   - **"Test failed" (81)** if fix incomplete → Iterate
4. Repeat until bug is "Closed" (82)

**Only after all bugs closed:** Story can be closed

### 6. Story Closure (Test Team)

**Prerequisites:**

- ✅ All tasks "Closed" (82)
- ✅ All bugs "Closed" (82)
- ✅ Story validation passed

**Test Team Actions:**

1. Verify all tasks closed
2. Verify all bugs closed
3. Run final story validation
4. Close story (status 82)

### 7. Epic Closure (Test Team)

**Prerequisites:**

- ✅ All stories "Closed" (82)
- ✅ All tasks in all stories "Closed" (82)
- ✅ All bugs in all stories "Closed" (82)

**Test Team Actions:**

1. Verify all stories closed
2. Verify all tasks closed
3. Verify all bugs closed
4. Run epic-level integration tests
5. Close epic (status 82)

**See:** `docs/QA_TESTING_WORKFLOW.md` for complete QA/testing workflow

## Task Status Flow

```
New (71) → In progress (77) → In testing (79) → Closed (82)
```

## Example: Story 1.5 Task Creation

```python
# Create tasks for Story 1.5
tasks = [
    {
        "subject": "Task 1: Implement OAuth 2.0 Token Validation",
        "type_id": 36,  # Task
        "description": "Create OAuth 2.0 token validation function...",
        "status_id": 71  # New
    },
    # ... more tasks
]

# Bulk create
mcp_openproject_bulk_create_work_packages(
    project_id=8,
    work_packages=tasks
)

# Set parent relationships
for task_id in [213, 214, ...]:
    mcp_openproject_set_work_package_parent(
        work_package_id=task_id,
        parent_id=113  # Story 1.5
    )
```

## Retroactive Task Creation

**Stories 1.3 and 1.4:** Tasks were created retroactively on 2026-01-06:

- Story 1.3: 7 tasks created (201-207)
- Story 1.4: 5 tasks created (208-212)
- All tasks marked as Closed (82) to reflect completion

## Going Forward

**For Story 1.5 and all future stories:**

- ✅ Create tasks in OpenProject when starting the story
- ✅ Update task statuses as work progresses
- ✅ Add comments to tasks documenting progress
- ✅ Close tasks when complete
- ✅ Update story file to reflect task completion

## OpenProject Task IDs Reference

### Story 1.3 Tasks (Work Package 111)

- 201: Task 1: Create Database Models
- 202: Task 2: Set Up Alembic Migrations
- 203: Task 3: Configure Row Level Security (RLS)
- 204: Task 4: Enhance Database Connection Management
- 205: Task 5: Create Database Repositories
- 206: Task 6: Add Database Tests
- 207: Task 7: Verify Story Implementation

### Story 1.4 Tasks (Work Package 112)

- 208: Task 1: Initialize FastMCP Server
- 209: Task 2: Implement rag_list_tools MCP Tool
- 210: Task 3: Implement Context Validation Middleware
- 211: Task 4: Integrate FastMCP with FastAPI
- 212: Task 5: Verify Story Implementation

### Story 1.5 Tasks (Work Package 113)

- 213: Task 1: Implement OAuth 2.0 Token Validation
- 214: Task 2: Implement API Key Authentication
- 215: Task 3: Create Authentication Middleware
- 216: Task 4: Integrate Audit Logging for Authentication
- 217: Task 5: Add Authentication Configuration
- 218: Task 6: Add Authentication Tests
- 219: Task 7: Verify Story Implementation
