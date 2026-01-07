# BMAD Workflow Quick Reference

**Last Updated:** 2026-01-06  
**For:** Action Owners (PM, Dev, Test Team, SM, PM)

## Key Principles

1. **Action Owner Responsibility:** Each person updating a work package status MUST immediately update parent status if conditions are met
2. **Immediate Status Transitions:** All status transitions happen IMMEDIATELY when conditions are met
3. **No Duplicate Documentation:** Use existing documents in `_bmad-output/` and attach as needed
4. **Features Optional:** Features are recommended for new epics but NOT retroactively created for existing work

## Work Package Hierarchy

```
Project
└── Epic (type_id=40)
    └── Feature (type_id=39, OPTIONAL but RECOMMENDED for new epics)
        └── User Story (type_id=41)
            └── Task (type_id=36) / Bug (type_id=42)
```

## Status Transition Rules

### Epic Status Transitions

| When                             | Epic Status               | Action Owner | Helper Function                                |
| -------------------------------- | ------------------------- | ------------ | ---------------------------------------------- |
| First story → "In progress" (77) | Epic → "In progress" (77) | PM/Dev       | `update_epic_status_based_on_stories(epic_id)` |
| Last story → "Closed" (82)       | Epic → "Closed" (82)      | Test Team    | `update_epic_status_based_on_stories(epic_id)` |

### Story Status Transitions

| When                                                   | Story Status               | Action Owner  | Helper Function                                                    |
| ------------------------------------------------------ | -------------------------- | ------------- | ------------------------------------------------------------------ |
| First task → "In progress" (77)                        | Story → "In progress" (77) | Dev           | `update_story_status_based_on_tasks(story_id)`                     |
| Test task → "In testing" (79) + all other tasks closed | Story → "In testing" (79)  | Dev           | `update_story_status_when_test_task_ready(story_id, test_task_id)` |
| All tasks + bugs → "Closed" (82)                       | Story → "Closed" (82)      | Dev/Test Team | `update_story_status_when_all_tasks_closed(story_id)`              |

## Action Owner Checklists

### PM: Epic Creation

- [ ] Create epic with comprehensive description (business goal, scope, success criteria, dependencies, technical considerations, timeline)
- [ ] Add story breakdown to epic description
- [ ] Create epic test story with validation tasks
- [ ] Create epic design document in `_bmad-output/planning-artifacts/` or `_bmad-output/`
- [ ] Attach epic design document to epic work package
- [ ] For new epics: Create Features if appropriate (NOT retroactively for existing epics)

### PM: Story Grooming

- [ ] Create story with detailed description and acceptance criteria
- [ ] Create ALL tasks (including test task "Task X.Y.T") during grooming
- [ ] Link all tasks to story (parent relationships)
- [ ] For UI stories: Create UI design document and attach to story
- [ ] Verify all tasks created before marking story "In progress"

### Dev: Task Implementation

- [ ] Verify tasks exist before starting
- [ ] Update task status to "In progress" (77) when starting
- [ ] **IMMEDIATELY** call `update_story_status_based_on_tasks(story_id)` if first task
- [ ] Update task status to "In testing" (79) when complete
- [ ] For test task: Create story test document and attach to story
- [ ] **IMMEDIATELY** call `update_story_status_when_test_task_ready(story_id, test_task_id)` when test task ready
- [ ] Update task status to "Closed" (82) when validated
- [ ] **IMMEDIATELY** call `update_story_status_when_all_tasks_closed(story_id)` when closing task

### Test Team: Story Validation

- [ ] Validate tasks when marked "In testing" (79)
- [ ] Close tasks (82) that pass validation
- [ ] Create bugs for tasks that fail validation
- [ ] Validate story when marked "In testing" (79)
- [ ] Close story (82) when all tasks and bugs closed
- [ ] **IMMEDIATELY** call `update_epic_status_based_on_stories(epic_id)` when closing story

### Test Team: Epic Validation

- [ ] Validate epic test story
- [ ] Run epic-level integration tests
- [ ] Close epic (82) when all stories closed
- [ ] **IMMEDIATELY** verify epic status updated when last story closed

## Document Locations

**CRITICAL:** Never create duplicate documentation.

- **Primary Location:** `_bmad-output/planning-artifacts/` or `_bmad-output/`
- **Attachments:** Attach parts or whole documents to Epics/Features/Stories in OpenProject
- **No Duplicates:** Do NOT create duplicate documentation in `docs/` if it exists in `_bmad-output/`

**Document Types:**

- Epic Design: `_bmad-output/planning-artifacts/epic-X-design.md` or `_bmad-output/epic-X-design.md`
- Story UI Design: `_bmad-output/planning-artifacts/story-X-Y-ui-design.md` or `_bmad-output/story-X-Y-ui-design.md`
- Story Test Document: `_bmad-output/planning-artifacts/story-X-Y-test-document.md` or `_bmad-output/story-X-Y-test-document.md`

## Test Task Naming

**Format:** `Task X.Y.T: Story X.Y Testing and Validation`

- X = Epic number
- Y = Story number
- T = Test task identifier

Example: `Task 5.2.T: Story 5.2 Testing and Validation`

## Helper Functions

All helper functions are in `scripts/openproject_status_helpers.py`:

```python
from scripts.openproject_status_helpers import (
    update_epic_status_based_on_stories,
    update_story_status_based_on_tasks,
    update_story_status_when_test_task_ready,
    update_story_status_when_all_tasks_closed
)
```

**Note:** These functions use OpenProject MCP tools. Implement with actual MCP tool calls in your environment.

## Common Workflows

### Story Grooming → Implementation → Closure

1. **PM:** Create story with acceptance criteria
2. **PM:** Create all tasks (including test task) during grooming
3. **PM:** Mark story "In progress" (77) only after tasks created
4. **Dev:** Start first task → Story automatically moves to "In progress" (77)
5. **Dev:** Complete tasks → Mark "In testing" (79)
6. **Dev:** Complete test task → Create test document → Attach to story → Story automatically moves to "In testing" (79)
7. **Test Team:** Validate story → Close story (82) → Story automatically closes when all tasks/bugs closed
8. **Test Team:** Close last story in epic → Epic automatically closes (82)

### Epic Creation → Story Breakdown → Closure

1. **PM:** Create epic with comprehensive description
2. **PM:** Add story breakdown to epic description
3. **PM:** Create epic test story
4. **PM:** Create and attach epic design document
5. **PM:** Create all stories under epic
6. **Dev/Test:** Work on stories → Epic automatically moves to "In progress" when first story starts
7. **Test Team:** Close last story → Epic automatically closes (82)

## OpenProject MCP Tools Reference

All operations use OpenProject MCP server tools:

- `mcp_openproject_create_work_package()` - Create epics, stories, tasks
- `mcp_openproject_update_work_package()` - Update statuses and descriptions
- `mcp_openproject_get_work_package()` - Get work package details
- `mcp_openproject_get_work_package_children()` - Get children (stories, tasks)
- `mcp_openproject_set_work_package_parent()` - Set parent relationships
- `mcp_openproject_add_work_package_attachment()` - Attach documents
- `mcp_openproject_add_work_package_comment()` - Add comments

## Status IDs Reference

| Status      | ID  | Use Case                  |
| ----------- | --- | ------------------------- |
| New         | 71  | Initial state             |
| In progress | 77  | Active work               |
| In testing  | 79  | Ready for test validation |
| Closed      | 82  | Complete                  |

## Full Documentation

For complete workflow details, see:

- **Complete Workflow Requirements:** `docs/BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md`
- **Task Creation Workflow:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`


