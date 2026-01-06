# CRITICAL WORKFLOW REQUIREMENT: Task Creation During Grooming

**Last Updated:** 2026-01-06  
**Status:** MANDATORY WORKFLOW RULE

## Overview

**ALL tasks for a story MUST be created in OpenProject during the GROOMING phase, BEFORE implementation begins.** This is a mandatory agile practice that must be followed by Product Managers (PM) and Developers (Dev).

## Workflow: Story Grooming → Task Creation → Implementation

### Phase 1: Story Grooming (PM Responsibility)

**When:** Before story moves to "In progress" status

**PM Actions:**
1. ✅ Review story acceptance criteria
2. ✅ Break down story into implementable tasks
3. ✅ Create tasks in OpenProject using `mcp_openproject_bulk_create_work_packages()`
4. ✅ Set parent relationships to story
5. ✅ Add task descriptions with acceptance criteria
6. ✅ Verify all tasks are created and linked
7. ✅ Update story status to "In progress" (77) only AFTER tasks are created

**Task Creation Requirements:**
- All tasks must be created BEFORE implementation starts
- Tasks should be granular (30 min - 4 hours of work)
- Each task should map to specific acceptance criteria
- Tasks should include detailed descriptions

### Phase 2: Implementation (Dev Responsibility)

**When:** After tasks are created and story is "In progress"

**Dev Actions:**
1. ✅ Start with first task (status: "In progress" 77)
2. ✅ Update task status as work progresses
3. ✅ Add comments to tasks documenting progress
4. ✅ Close tasks (status: "Closed" 82) when complete
5. ✅ Move to next task
6. ✅ Update story file to reflect task completion

**Task Status Updates:**
- "New" (71) → "In progress" (77) when starting work
- "In progress" (77) → "In testing" (79) when ready for testing
- "In testing" (79) → "Closed" (82) when complete

## Example: Story 1.5 Grooming Process

### Step 1: PM Reviews Story (Before Grooming)

```python
# PM reviews Story 1.5 acceptance criteria
story = mcp_openproject_get_work_package(work_package_id=113)
# Review acceptance criteria
# Break down into tasks
```

### Step 2: PM Creates Tasks (During Grooming)

```python
# PM creates all tasks BEFORE implementation
tasks = [
    {
        "subject": "Task 1: Implement OAuth 2.0 Token Validation",
        "type_id": 36,  # Task
        "description": "Create OAuth 2.0 token validation...",
        "status_id": 71  # New
    },
    # ... all 7 tasks
]

# Bulk create all tasks
mcp_openproject_bulk_create_work_packages(
    project_id=8,
    work_packages=tasks
)

# Set parent relationships
for task_id in [213, 214, 215, 216, 217, 218, 219]:
    mcp_openproject_set_work_package_parent(
        work_package_id=task_id,
        parent_id=113  # Story 1.5
    )
```

### Step 3: PM Updates Story Status

```python
# Only AFTER all tasks are created
mcp_openproject_update_work_package(
    work_package_id=113,
    status_id=77  # In progress
)
```

### Step 4: Dev Begins Implementation

```python
# Dev starts with first task
mcp_openproject_update_work_package(
    work_package_id=213,  # Task 1
    status_id=77  # In progress
)

# Work on task...
# Update task when complete
mcp_openproject_update_work_package(
    work_package_id=213,
    status_id=82  # Closed
)
```

## PM Checklist: Story Grooming

**Before marking story as "In progress":**

- [ ] Story acceptance criteria reviewed
- [ ] Story broken down into tasks (7 tasks for Story 1.5)
- [ ] All tasks created in OpenProject
- [ ] All tasks linked to story (parent relationship set)
- [ ] Task descriptions include acceptance criteria
- [ ] Story file created in `_bmad-output/implementation-artifacts/`
- [ ] Story file includes all tasks with checkboxes
- [ ] Story status updated to "In progress" (77)

## Dev Checklist: Implementation

**Before starting implementation:**

- [ ] Verify all tasks exist in OpenProject
- [ ] Verify all tasks are linked to story
- [ ] Review task descriptions and acceptance criteria
- [ ] Start with first task (update status to "In progress")

**During implementation:**

- [ ] Update task status as work progresses
- [ ] Add comments to tasks documenting progress
- [ ] Update story file to mark tasks complete
- [ ] Close tasks when complete

## Violations and Corrections

### What Happened with Stories 1.3 and 1.4

**Issue:** Tasks were created retroactively after implementation was complete.

**Correction Applied (2026-01-06):**
- ✅ Created all tasks for Story 1.3 (7 tasks, IDs 201-207)
- ✅ Created all tasks for Story 1.4 (5 tasks, IDs 208-212)
- ✅ Marked all tasks as "Closed" (82) to reflect completion
- ✅ Set parent relationships correctly
- ✅ Documented retroactive creation in comments

**Going Forward:**
- ✅ Story 1.5 tasks created during grooming (before implementation)
- ✅ All future stories will follow this process

## BMAD Workflow Integration

### PM Agent Workflow

**When using `create-story` workflow:**
1. Create story file with tasks
2. **IMMEDIATELY create tasks in OpenProject**
3. Set parent relationships
4. Mark story as ready for implementation

**When using `sprint-planning` workflow:**
1. Review stories for sprint
2. **Groom each story: create tasks in OpenProject**
3. Verify all tasks are created
4. Mark stories as ready for sprint

### Dev Agent Workflow

**When using `dev-story` workflow:**
1. **Verify tasks exist in OpenProject** (if not, request PM to create them)
2. Start with first task
3. Update task status as work progresses
4. Close tasks when complete

## OpenProject Task Creation Template

```python
def create_story_tasks(story_id: int, tasks: list[dict]):
    """
    Create all tasks for a story during grooming phase.
    
    Args:
        story_id: OpenProject work package ID for the story
        tasks: List of task definitions with:
            - subject: Task title
            - description: Task description with acceptance criteria
            - type_id: 36 (Task)
            - status_id: 71 (New)
    """
    # Create all tasks
    result = mcp_openproject_bulk_create_work_packages(
        project_id=8,
        work_packages=tasks
    )
    
    # Set parent relationships
    for task in result["created"]:
        mcp_openproject_set_work_package_parent(
            work_package_id=task["id"],
            parent_id=story_id
        )
    
    # Verify all tasks are created
    children = mcp_openproject_get_work_package_children(parent_id=story_id)
    assert len(children["children"]) == len(tasks), "Not all tasks created"
    
    return result
```

## References

- **BMAD Workflow:** `@bmad/bmm/workflows/create-story` - Story creation workflow
- **BMAD Workflow:** `@bmad/bmm/workflows/sprint-planning` - Sprint planning workflow
- **BMAD Workflow:** `@bmad/bmm/workflows/dev-story` - Story development workflow
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md` - Detailed task management process

## Enforcement

**This is a MANDATORY workflow requirement.** Stories should NOT be marked as "In progress" until all tasks are created in OpenProject during the grooming phase.

**PM Responsibility:** Create tasks during grooming, before story moves to "In progress"  
**Dev Responsibility:** Verify tasks exist before starting implementation, update task statuses during work

## Related Workflows

- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md` - Complete testing and validation process
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md` - Detailed task management process

