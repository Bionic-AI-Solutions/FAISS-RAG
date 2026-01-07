# Desired OpenProject MCP Tools - Functional Specification

## Overview

Based on experience using OpenProject MCP tools and analyzing the OpenProject API v3 capabilities, this document articulates desired MCP tools that would significantly improve workflow efficiency and completeness.

## Current MCP Tools (Already Available)

### ✅ Project Management
- `mcp_openproject_test_connection()` - Test API connectivity
- `mcp_openproject_list_projects(active_only=True)` - List projects
- `mcp_openproject_get_project(project_id)` - Get project details
- `mcp_openproject_create_project(...)` - Create project
- `mcp_openproject_update_project(...)` - Update project
- `mcp_openproject_delete_project(project_id)` - Delete project

### ✅ Work Package Management (Basic)
- `mcp_openproject_list_work_packages(project_id, status, ...)` - List work packages
- `mcp_openproject_get_work_package(work_package_id)` - Get work package details
- `mcp_openproject_create_work_package(...)` - Create work package
- `mcp_openproject_update_work_package(...)` - Update work package
- `mcp_openproject_delete_work_package(work_package_id)` - Delete work package

### ✅ Reference Data
- `mcp_openproject_list_types(project_id)` - List work package types
- `mcp_openproject_list_statuses()` - List statuses
- `mcp_openproject_list_priorities()` - List priorities
- `mcp_openproject_list_users(active_only=True)` - List users

---

## Desired MCP Tools - Critical Gaps

### 🔴 Priority 1: Hierarchy & Relationships

#### 1.1 Set Work Package Parent
**Current Gap**: Must use direct API calls or scripts to set parent-child relationships.

**Desired Tool**:
```python
mcp_openproject_set_work_package_parent(
    work_package_id: int,
    parent_id: int,
    lock_version: Optional[int] = None  # Auto-fetch if not provided
) -> Dict
```

**Use Cases**:
- Set Story as child of Epic
- Set Task as child of Story
- Reorganize work package hierarchy
- Bulk hierarchy setup

**API Endpoint**: `PATCH /api/v3/work_packages/{id}` with `_links.parent`

---

#### 1.2 Get Work Package Children
**Current Gap**: Cannot easily query children of a work package.

**Desired Tool**:
```python
mcp_openproject_get_work_package_children(
    parent_id: int,
    project_id: Optional[int] = None,
    type_id: Optional[int] = None,  # Filter by type
    status: Optional[str] = None,  # Filter by status
    include_closed: bool = False
) -> Dict
```

**Use Cases**:
- List all stories under an epic
- List all tasks under a story
- Check if story has tasks before closing
- Generate progress reports

**API Endpoint**: `GET /api/v3/work_packages` with filter `parent={parent_id}`

---

#### 1.3 Get Work Package Hierarchy
**Desired Tool**:
```python
mcp_openproject_get_work_package_hierarchy(
    work_package_id: int,
    include_ancestors: bool = True,
    include_descendants: bool = True,
    max_depth: Optional[int] = None
) -> Dict
```

**Use Cases**:
- Visualize full hierarchy (Epic → Feature → Story → Task)
- Understand work package context
- Generate tree views

**API Endpoint**: Uses `GET /api/v3/work_packages/{id}` and recursive queries

---

### 🔴 Priority 2: Bulk Operations

#### 2.1 Bulk Create Work Packages
**Current Gap**: Must create work packages one-by-one, which is slow for large batches.

**Desired Tool**:
```python
mcp_openproject_bulk_create_work_packages(
    project_id: int,
    work_packages: List[Dict],  # List of work package definitions
    continue_on_error: bool = False
) -> Dict
```

**Work Package Definition**:
```python
{
    "subject": "Story 1.1: ...",
    "type_id": 41,
    "description": "...",
    "parent_id": 172,  # Optional
    "status_id": 71,
    "priority_id": 73,
    "assignee_id": None,
    # ... other fields
}
```

**Use Cases**:
- Sync all epics/stories from `epics.md` in one operation
- Create multiple tasks under a story
- Import work packages from external systems

**API Endpoint**: `POST /api/v3/work_packages` (multiple calls, but tool handles batching)

---

#### 2.2 Bulk Update Work Packages
**Desired Tool**:
```python
mcp_openproject_bulk_update_work_packages(
    updates: List[Dict]  # List of {work_package_id, updates}
) -> Dict
```

**Use Cases**:
- Update types for all stories (Task → User Story)
- Set parent relationships for multiple work packages
- Update statuses in bulk

**API Endpoint**: Multiple `PATCH /api/v3/work_packages/{id}` calls

---

### 🟡 Priority 3: Enhanced Querying & Filtering

#### 3.1 Advanced Work Package Query
**Current Gap**: `list_work_packages` has limited filtering options.

**Desired Tool**:
```python
mcp_openproject_query_work_packages(
    project_id: Optional[int] = None,
    filters: Dict = {},  # Flexible filter structure
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    page: int = 1,
    page_size: int = 20,
    include: Optional[List[str]] = None  # Include relations, watchers, etc.
) -> Dict
```

**Filter Examples**:
```python
filters = {
    "type": {"operator": "=", "values": [41]},  # User Story
    "status": {"operator": "!=", "values": [82]},  # Not closed
    "parent": {"operator": "=", "values": [172]},  # Under Epic 1
    "subject": {"operator": "~", "values": ["Story 1"]},  # Contains
    "created_at": {"operator": ">=", "values": ["2026-01-01"]}
}
```

**Use Cases**:
- Find all open stories under Epic 1
- Find all tasks assigned to a user
- Search work packages by subject pattern
- Complex reporting queries

**API Endpoint**: `GET /api/v3/work_packages` with advanced filters

---

#### 3.2 Search Work Packages
**Desired Tool**:
```python
mcp_openproject_search_work_packages(
    query: str,  # Full-text search
    project_id: Optional[int] = None,
    type_ids: Optional[List[int]] = None,
    limit: int = 20
) -> Dict
```

**Use Cases**:
- Quick search for work packages by subject/description
- Find work packages containing specific keywords
- User-friendly search interface

**API Endpoint**: `GET /api/v3/work_packages` with text search

---

### 🟡 Priority 4: Work Package Relations

#### 4.1 Create Work Package Relation
**Current Gap**: Cannot create relations (blocks, follows, relates to, etc.) via MCP.

**Desired Tool**:
```python
mcp_openproject_create_work_package_relation(
    work_package_id: int,
    related_work_package_id: int,
    relation_type: str,  # "blocks", "follows", "relates", "duplicates", "blocks", "precedes"
    description: Optional[str] = None
) -> Dict
```

**Use Cases**:
- Link blocking tasks
- Create dependency chains
- Relate duplicate work packages
- Track related work

**API Endpoint**: `POST /api/v3/work_packages/{id}/relations`

---

#### 4.2 List Work Package Relations
**Desired Tool**:
```python
mcp_openproject_list_work_package_relations(
    work_package_id: int,
    relation_type: Optional[str] = None
) -> Dict
```

**Use Cases**:
- View all dependencies
- Check for blocking work packages
- Understand work package relationships

**API Endpoint**: `GET /api/v3/work_packages/{id}/relations`

---

### 🟡 Priority 5: Activities & Comments

#### 5.1 Add Work Package Comment
**Current Gap**: Cannot add comments/activities via MCP.

**Desired Tool**:
```python
mcp_openproject_add_work_package_comment(
    work_package_id: int,
    comment: str,
    notify: bool = True
) -> Dict
```

**Use Cases**:
- Add progress updates
- Document decisions
- Communicate with team
- Track work package history

**API Endpoint**: `POST /api/v3/work_packages/{id}/activities`

---

#### 5.2 List Work Package Activities
**Desired Tool**:
```python
mcp_openproject_list_work_package_activities(
    work_package_id: int,
    limit: int = 20
) -> Dict
```

**Use Cases**:
- View work package history
- Review comments
- Track changes

**API Endpoint**: `GET /api/v3/work_packages/{id}/activities`

---

### 🟢 Priority 6: Watchers & Assignments

#### 6.1 Add Work Package Watcher
**Desired Tool**:
```python
mcp_openproject_add_work_package_watcher(
    work_package_id: int,
    user_id: int
) -> Dict
```

**Use Cases**:
- Subscribe users to work package updates
- Notify stakeholders
- Track who's watching

**API Endpoint**: `POST /api/v3/work_packages/{id}/watchers`

---

#### 6.2 Assign Work Package
**Desired Tool**:
```python
mcp_openproject_assign_work_package(
    work_package_id: int,
    assignee_id: Optional[int] = None,  # None to unassign
    responsible_id: Optional[int] = None
) -> Dict
```

**Use Cases**:
- Assign tasks to developers
- Set responsible person
- Reassign work packages

**API Endpoint**: `PATCH /api/v3/work_packages/{id}` with assignee/responsible

---

### 🟢 Priority 7: Time Tracking

#### 7.1 Log Time on Work Package
**Desired Tool**:
```python
mcp_openproject_log_time(
    work_package_id: int,
    hours: float,
    activity_id: Optional[int] = None,  # Default activity
    spent_on: Optional[str] = None,  # Date, defaults to today
    comment: Optional[str] = None
) -> Dict
```

**Use Cases**:
- Track time spent on tasks
- Generate time reports
- Monitor effort

**API Endpoint**: `POST /api/v3/time_entries`

---

#### 7.2 Get Work Package Time Entries
**Desired Tool**:
```python
mcp_openproject_get_work_package_time_entries(
    work_package_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict
```

**Use Cases**:
- View logged time
- Calculate total effort
- Generate time reports

**API Endpoint**: `GET /api/v3/time_entries` with work package filter

---

### 🟢 Priority 8: Attachments

#### 8.1 Add Work Package Attachment
**Desired Tool**:
```python
mcp_openproject_add_work_package_attachment(
    work_package_id: int,
    file_path: str,  # Local file path
    description: Optional[str] = None
) -> Dict
```

**Use Cases**:
- Attach screenshots
- Upload documents
- Share files

**API Endpoint**: `POST /api/v3/work_packages/{id}/attachments`

---

#### 8.2 List Work Package Attachments
**Desired Tool**:
```python
mcp_openproject_list_work_package_attachments(
    work_package_id: int
) -> Dict
```

**Use Cases**:
- View attached files
- Download attachments
- Manage files

**API Endpoint**: `GET /api/v3/work_packages/{id}/attachments`

---

### 🟢 Priority 9: Custom Fields & Metadata

#### 9.1 Update Work Package Custom Fields
**Desired Tool**:
```python
mcp_openproject_update_work_package_custom_fields(
    work_package_id: int,
    custom_fields: Dict  # {custom_field_id: value}
) -> Dict
```

**Use Cases**:
- Set custom field values
- Track additional metadata
- Extend work package data

**API Endpoint**: `PATCH /api/v3/work_packages/{id}` with custom fields

---

#### 9.2 List Project Custom Fields
**Desired Tool**:
```python
mcp_openproject_list_custom_fields(
    project_id: Optional[int] = None
) -> Dict
```

**Use Cases**:
- Discover available custom fields
- Understand field types
- Configure custom fields

**API Endpoint**: `GET /api/v3/custom_fields`

---

### 🟢 Priority 10: Workflow & Status Management

#### 10.1 Get Available Status Transitions
**Desired Tool**:
```python
mcp_openproject_get_available_status_transitions(
    work_package_id: int
) -> Dict
```

**Use Cases**:
- Determine valid next statuses
- Build status transition UI
- Validate status changes

**API Endpoint**: `GET /api/v3/work_packages/{id}/available_relations` or schema

---

#### 10.2 Update Work Package Status
**Enhanced Version**:
```python
mcp_openproject_update_work_package_status(
    work_package_id: int,
    status_id: int,
    comment: Optional[str] = None  # Optional status change comment
) -> Dict
```

**Use Cases**:
- Change status with context
- Document status transitions
- Track status history

**API Endpoint**: `PATCH /api/v3/work_packages/{id}` with status + activity

---

## Implementation Notes

### Type Conversion
**Issue**: MCP tools should handle string-to-integer conversion automatically for `project_id` and `work_package_id` parameters.

**Recommendation**: MCP server should accept both strings and integers, converting strings to integers internally.

### Error Handling
**Desired**: All tools should return structured errors:
```python
{
    "success": false,
    "error": {
        "code": "WORK_PACKAGE_NOT_FOUND",
        "message": "Work package 123 not found",
        "details": {...}
    }
}
```

### Batch Operations
**Recommendation**: For bulk operations, tools should:
- Process in batches (e.g., 10-20 at a time)
- Return partial results on errors
- Provide detailed error reporting per item

### Pagination
**Recommendation**: All list/query tools should support:
- `page` and `page_size` parameters
- Return `total`, `count`, `offset` in response
- Support cursor-based pagination for large datasets

---

## Summary: Most Critical Tools

### Must Have (🔴 Priority 1-2)
1. **Set Work Package Parent** - Critical for hierarchy management
2. **Get Work Package Children** - Essential for queries
3. **Bulk Create Work Packages** - Needed for efficient syncing

### Should Have (🟡 Priority 3-4)
4. **Advanced Query** - Flexible filtering
5. **Create Relations** - Dependency management
6. **Add Comments** - Team communication

### Nice to Have (🟢 Priority 5-10)
7. **Time Tracking** - Effort tracking
8. **Attachments** - File management
9. **Watchers** - Notification management
10. **Custom Fields** - Extended metadata

---

## Example: Complete Workflow with Desired Tools

```python
# 1. Create Epic
epic = mcp_openproject_create_work_package(
    project_id=8,
    subject="Epic 1: Secure Platform Foundation",
    type_id=40,
    description="..."
)
epic_id = epic["work_package"]["id"]

# 2. Create Story
story = mcp_openproject_create_work_package(
    project_id=8,
    subject="Story 1.1: Project Structure",
    type_id=41,
    description="..."
)
story_id = story["work_package"]["id"]

# 3. Set Parent (NEW TOOL)
mcp_openproject_set_work_package_parent(
    work_package_id=story_id,
    parent_id=epic_id
)

# 4. Create Tasks in Bulk (NEW TOOL)
tasks = mcp_openproject_bulk_create_work_packages(
    project_id=8,
    work_packages=[
        {
            "subject": "Task 1: Create Directory Structure",
            "type_id": 36,
            "description": "...",
            "parent_id": story_id
        },
        {
            "subject": "Task 2: Configure Python Files",
            "type_id": 36,
            "description": "...",
            "parent_id": story_id
        }
    ]
)

# 5. Query Children (NEW TOOL)
children = mcp_openproject_get_work_package_children(
    parent_id=story_id,
    type_id=36  # Tasks only
)

# 6. Add Comment (NEW TOOL)
mcp_openproject_add_work_package_comment(
    work_package_id=story_id,
    comment="Tasks created and ready for development"
)

# 7. Assign (NEW TOOL)
mcp_openproject_assign_work_package(
    work_package_id=story_id,
    assignee_id=user_id
)
```

This workflow would be **significantly more efficient** than current approach!














