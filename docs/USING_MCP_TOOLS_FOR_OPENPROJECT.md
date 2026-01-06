# Using MCP Tools Directly for OpenProject

## Overview

You can use MCP tools directly to create and manage work packages in OpenProject. This document shows how to use the available MCP tools.

## Available MCP Tools

### Creating Work Packages

```python
# Create Epic
mcp_openproject_create_work_package(
    project_id=8,
    subject="Epic 1: Secure Platform Foundation",
    type_id=40,  # Epic
    description="Platform operators can deploy a secure, auditable RAG system..."
)

# Create User Story
mcp_openproject_create_work_package(
    project_id=8,
    subject="Story 1.1: Project Structure & Development Environment Setup",
    type_id=41,  # User Story
    description="As a Developer, I want..."
)

# Create Task
mcp_openproject_create_work_package(
    project_id=8,
    subject="Task 1: Create Project Directory Structure",
    type_id=36,  # Task
    description="Create root directory structure..."
)
```

### Work Package Type IDs

- **Epic**: `type_id=40`
- **Feature**: `type_id=39`
- **User Story**: `type_id=41`
- **Task**: `type_id=36`
- **Summary task**: `type_id=38` (fallback if Epic not enabled)

### Setting Parent-Child Relationships

**Note**: The MCP `update_work_package` tool doesn't directly support `parent_id`. Use one of these approaches:

1. **Use the parent relationship script** (Recommended):
   ```bash
   python scripts/set_openproject_parents.py
   ```

2. **Use direct API calls** (if needed):
   ```python
   # See scripts/set_openproject_parents.py for implementation
   ```

### Updating Work Package Types

To update existing work packages to correct types:

```python
# Update story from Task (36) to User Story (41)
mcp_openproject_update_work_package(
    work_package_id=181,
    type_id=41  # Note: Check if MCP tool supports type_id parameter
)
```

**Note**: If the MCP tool doesn't support `type_id` in `update_work_package`, use:
```bash
python scripts/fix_and_update_openproject.py
```

## Example: Complete Workflow

### Step 1: Create Epic

```python
epic = mcp_openproject_create_work_package(
    project_id=8,
    subject="Epic 1: Secure Platform Foundation",
    type_id=40,
    description="Platform operators can deploy..."
)
epic_id = epic["work_package"]["id"]  # e.g., 172
```

### Step 2: Create Story Under Epic

```python
story = mcp_openproject_create_work_package(
    project_id=8,
    subject="Story 1.1: Project Structure & Development Environment Setup",
    type_id=41,  # User Story
    description="As a Developer, I want..."
)
story_id = story["work_package"]["id"]  # e.g., 181
```

### Step 3: Set Parent Relationship

```bash
# Use the script to set Story 1.1 as child of Epic 1
python scripts/set_openproject_parents.py
```

Or manually via API (see `scripts/set_openproject_parents.py`).

### Step 4: Create Tasks Under Story

```python
task = mcp_openproject_create_work_package(
    project_id=8,
    subject="Task 1: Create Project Directory Structure",
    type_id=36,  # Task
    description="Create root directory structure..."
)
task_id = task["work_package"]["id"]
```

### Step 5: Set Task Parent Relationship

```bash
# Use the script to set Task as child of Story
python scripts/set_openproject_parents.py
```

## Batch Operations

For batch operations (creating many epics/stories/tasks), you have two options:

### Option 1: Use MCP Tools in a Loop

```python
# Example: Create all epics
epics = [
    {"number": 1, "title": "Secure Platform Foundation", "description": "..."},
    {"number": 2, "title": "Tenant Onboarding & Configuration", "description": "..."},
    # ... more epics
]

for epic in epics:
    mcp_openproject_create_work_package(
        project_id=8,
        subject=f"Epic {epic['number']}: {epic['title']}",
        type_id=40,
        description=epic['description']
    )
```

### Option 2: Use Sync Scripts

The sync scripts (`scripts/sync_epics_to_openproject.py`) use direct API calls for efficiency, but you can adapt them to use MCP tools if preferred.

## Current Status

✅ **Epics Created**: All 9 epics created with correct type (40)
- Epic 1: ID 172
- Epic 2: ID 173
- Epic 3: ID 174
- Epic 4: ID 175
- Epic 5: ID 176
- Epic 6: ID 177
- Epic 7: ID 178
- Epic 8: ID 179
- Epic 9: ID 180

✅ **Stories Created**: Story 1.1 created (ID 181) with correct type (41)

⏳ **Next Steps**:
1. Create remaining stories under each epic
2. Set parent-child relationships
3. Create tasks under stories
4. Update any existing work packages with wrong types

## Tips

1. **Always use correct type_id**: Epic=40, Feature=39, User Story=41, Task=36
2. **Set parent relationships**: Use `scripts/set_openproject_parents.py` after creating work packages
3. **Verify types**: Run `python scripts/fix_and_update_openproject.py --dry-run` to check types
4. **Create tasks from artifacts**: Use `scripts/create_tasks_from_stories.py` to create tasks from implementation artifacts

## Troubleshooting

### Type Not Available Error

If you get "Type is not set to one of the allowed values":
- Check project settings in OpenProject UI
- Enable Epic, Feature, User Story types for the project
- Or use fallback types (Summary task for Epic, Task for Story)

### Parent Relationship Not Working

- Use `scripts/set_openproject_parents.py` to set relationships
- Or set manually in OpenProject UI
- Verify work package IDs are correct

### MCP Tool Limitations

Some operations may not be directly supported by MCP tools:
- Setting parent relationships (use script or direct API)
- Bulk type updates (use script or direct API)
- Complex queries (use direct API)

In these cases, use the provided scripts which use direct API calls but follow the same patterns as MCP tools.








