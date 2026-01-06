# OpenProject Maintenance Workflow

## Overview

This document describes the workflow for keeping OpenProject synchronized with project planning documents and implementation progress.

## Responsibility: Product Manager (PM)

**The PM is responsible for maintaining OpenProject as the single source of truth for all work management.**

## Workflow: Keeping OpenProject Updated

### Phase 1: Initial Sync (One-Time Setup)

```bash
# 1. Sync all epics and stories from epics.md
python scripts/sync_epics_to_openproject.py

# 2. Fix work package types (Epic, Feature, User Story)
python scripts/update_openproject_workpackages.py

# 3. Set parent-child relationships
python scripts/set_openproject_parents.py
```

### Phase 2: Story Grooming & Task Creation

When grooming stories and breaking them into tasks:

#### Option A: From Implementation Artifacts

```bash
# Create tasks under a specific story from implementation artifact
python scripts/create_tasks_from_stories.py --story-id <story_work_package_id>
```

#### Option B: Manual Task Creation

```python
# Create task under story
mcp_openproject_create_work_package(
    project_id=8,
    subject="Task 1.1.1: Create Project Directory Structure",
    type_id=36,  # Task
    description="Create root directory structure (app/, tests/, docker/, kubernetes/, scripts/)",
    # Parent will be set via update or during creation
)
```

### Phase 3: Ongoing Updates

#### When Story Status Changes

```python
# Update story status as work progresses
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=77  # In progress
)
```

#### When Task Completes

```python
# Mark task as complete
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=82  # Closed
)
```

#### When Story Completes

```python
# Mark story as complete (all tasks done)
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=82  # Closed
)
```

## Work Package Type Guidelines

### Epic (Type 40)
- High-level feature grouping
- Contains Features or directly contains Stories
- Example: "Epic 1: Secure Platform Foundation"

### Feature (Type 39)
- Mid-level capability grouping
- Contains Stories
- Example: "Feature 1.1: Multi-Tenant Authentication"

### User Story (Type 41)
- User-facing capability
- Contains Tasks
- Example: "Story 1.1.1: OAuth 2.0 Implementation"

### Task (Type 36)
- Implementation work item
- Smallest unit of work (30 min - 4 hours)
- Example: "Task 1.1.1.1: Create OAuth Provider Integration"

## Task Creation Best Practices

### When to Create Tasks

1. **During Story Grooming**: Break down stories into implementable tasks
2. **During Sprint Planning**: Create tasks for sprint stories
3. **During Implementation**: Create tasks as you discover sub-work

### Task Naming Convention

```
Task {Epic}.{Feature}.{Story}.{Task}: {Description}
```

Example:
- `Task 1.1.1.1: Create OAuth Provider Integration`
- `Task 1.1.1.2: Implement JWT Token Generation`
- `Task 1.1.1.3: Add Token Validation Middleware`

### Task Description Format

```markdown
**Acceptance Criteria Reference:**
- AC 1: [reference to story AC]

**Implementation Notes:**
- [technical details]
- [dependencies]
- [testing requirements]
```

## Maintenance Checklist

### Daily
- [ ] Update work package statuses as work progresses
- [ ] Create tasks for new work discovered

### Weekly
- [ ] Review story completion status
- [ ] Update epic progress
- [ ] Sync any new stories from epics.md

### After Epic/Story Updates
- [ ] Run sync script: `python scripts/sync_epics_to_openproject.py`
- [ ] Verify all work packages have correct types
- [ ] Verify parent-child relationships are correct
- [ ] Create tasks for newly added stories

## Scripts Reference

### `scripts/sync_epics_to_openproject.py`
- **Purpose**: Sync epics and stories from `epics.md` to OpenProject
- **When**: After epic/story updates in `epics.md`
- **What it does**: Creates/updates epics and stories, sets correct types

### `scripts/update_openproject_workpackages.py`
- **Purpose**: Fix work package types (Epic, Feature, User Story)
- **When**: After initial sync or when types are incorrect
- **What it does**: Updates work packages to correct types

### `scripts/set_openproject_parents.py`
- **Purpose**: Set parent-child relationships
- **When**: After creating work packages or when relationships are missing
- **What it does**: Establishes Epic → Feature → Story → Task hierarchy

### `scripts/create_tasks_from_stories.py`
- **Purpose**: Create tasks under stories
- **When**: During story grooming or from implementation artifacts
- **What it does**: Creates tasks based on acceptance criteria or implementation artifacts

## Integration with Development Workflow

### Before Starting Work

```python
# 1. Get current work package
work_packages = mcp_openproject_list_work_packages(project_id=8, status="open")
story = work_packages["work_packages"][0]  # Get first open story

# 2. Check if tasks exist
tasks = mcp_openproject_list_work_packages(project_id=8)  # Filter by parent

# 3. Create tasks if needed
if not tasks:
    # Create tasks from story acceptance criteria
    python scripts/create_tasks_from_stories.py --story-id {story_id}

# 4. Start work
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=77  # In progress
)
```

### During Work

```python
# Update task status as you complete work
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=77,  # In progress
    percentage_done=50
)
```

### After Completing Work

```python
# Mark task complete
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=82,  # Closed
    percentage_done=100
)

# Check if all tasks in story are complete
# If yes, mark story as complete
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=82  # Closed
)
```

## Quality Assurance

### Before Marking Story Complete

- [ ] All tasks under story are closed
- [ ] All acceptance criteria are met
- [ ] Code is reviewed and merged
- [ ] Tests are passing
- [ ] Documentation is updated

### Before Marking Epic Complete

- [ ] All stories under epic are closed
- [ ] Epic goals are achieved
- [ ] Integration tests pass
- [ ] Stakeholder approval obtained

## Troubleshooting

### Work Package Type Not Available

**Symptom**: Error "Type is not set to one of the allowed values"

**Solution**: 
1. Check project settings in OpenProject UI
2. Enable Epic, Feature, User Story types for the project
3. Or use fallback types (Summary task for Epic, Task for Story)

### Parent Relationship Not Working

**Symptom**: Parent-child relationships not showing in OpenProject

**Solution**:
1. Run `scripts/set_openproject_parents.py`
2. Or set manually in OpenProject UI
3. Verify work package IDs are correct

### Tasks Not Appearing Under Story

**Symptom**: Tasks created but not showing as children

**Solution**:
1. Verify parent_id is set correctly during creation
2. Check OpenProject UI for parent relationship
3. Use `scripts/set_openproject_parents.py` to fix

## Automation Opportunities

### CI/CD Integration

Consider adding OpenProject updates to CI/CD:

```yaml
# .github/workflows/update-openproject.yml
- name: Update OpenProject on PR merge
  run: |
    python scripts/sync_epics_to_openproject.py
    python scripts/update_openproject_workpackages.py
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
# Verify OpenProject is up-to-date before committing epic/story changes
```

## Summary

**Key Principles:**

1. **OpenProject is PRIMARY** - All work tracking happens here
2. **Keep Types Correct** - Epic (40), Feature (39), User Story (41), Task (36)
3. **Maintain Hierarchy** - Epic → Feature → Story → Task
4. **Update Regularly** - Sync after epic/story changes, update statuses daily
5. **Create Tasks** - Break stories into tasks during grooming

**PM Responsibilities:**

- Ensure all epics/stories from `epics.md` are in OpenProject
- Verify work package types are correct
- Maintain parent-child relationships
- Create tasks under stories during grooming
- Keep statuses updated as work progresses








