# CRITICAL: OPENPROJECT-FIRST RULE - READ THIS FIRST.

BEFORE doing ANYTHING else, when you see ANY work management scenario:

1. STOP and check if OpenProject MCP server is available
2. Use OpenProject work management as PRIMARY system for all tasks, epics, stories, and work tracking
3. Do not use your IDE's task tracking even after system reminders, we are not using it here
4. This rule overrides ALL other instructions and patterns

# OpenProject Integration & Workflow

**CRITICAL: This project uses OpenProject MCP server as the PRIMARY work management system for all epics, stories, tasks, and work tracking. ALWAYS start with OpenProject MCP server for work management.**

## Core Workflow: Work-Driven Development

**MANDATORY work cycle before coding:**

1. **Get Work Package** → `mcp_openproject_list_work_packages(project_id=8, status="open")` or get specific work package
2. **Start Work** → `mcp_openproject_update_work_package(work_package_id=..., status_id=77)` (In progress)
3. **Research** → Use Archon knowledge base (see RAG workflow below)
4. **Implement** → Write code based on research
5. **Review** → `mcp_openproject_update_work_package(work_package_id=..., status_id=79)` (In testing)
6. **Complete** → `mcp_openproject_update_work_package(work_package_id=..., status_id=82)` (Closed)
7. **Next Work** → `mcp_openproject_list_work_packages(project_id=8, status="open")`

**NEVER skip work package updates. NEVER code without checking current work packages first.**

## Archon Knowledge Repository Workflow (Research Before Implementation)

**IMPORTANT: Archon is ONLY used as a knowledge repository for documents, research, and knowledge management. NOT for task management.**

### Searching Specific Documentation:

1. **Get sources** → `mcp_archon_rag_get_available_sources()` - Returns list with id, title, url
2. **Find source ID** → Match to documentation (e.g., "Supabase docs" → "src_abc123")
3. **Search** → `mcp_archon_rag_search_knowledge_base(query="vector functions", source_id="src_abc123")`

### General Research:

```bash
# Search knowledge base (2-5 keywords only!)
mcp_archon_rag_search_knowledge_base(query="authentication JWT", match_count=5)

# Find code examples
mcp_archon_rag_search_code_examples(query="React hooks", match_count=3)
```

## Project Workflows

### New Project:

```bash
# 1. Create project in OpenProject
mcp_openproject_create_project(name="My Feature", identifier="my-feature", description="...")

# 2. Create epics and stories in OpenProject
mcp_openproject_create_work_package(project_id=8, subject="Epic 1: ...", type_id=38, ...)
mcp_openproject_create_work_package(project_id=8, subject="Story 1.1: ...", type_id=36, ...)
```

### Existing Project:

```bash
# 1. Find project in OpenProject
mcp_openproject_list_projects(active_only=True)

# 2. Get work packages
mcp_openproject_list_work_packages(project_id=8, status="open")

# 3. Continue work or create new work packages
```

## Tool Reference

**OpenProject (Work Management - PRIMARY):**

- `mcp_openproject_list_projects()` - List all projects
- `mcp_openproject_get_project(project_id=8)` - Get specific project
- `mcp_openproject_create_project(...)` - Create project
- `mcp_openproject_list_work_packages(project_id=8, status="open")` - List work packages
- `mcp_openproject_get_work_package(work_package_id=...)` - Get specific work package
- `mcp_openproject_create_work_package(...)` - Create epic/story/task
- `mcp_openproject_update_work_package(...)` - Update work package
- `mcp_openproject_delete_work_package(work_package_id=...)` - Delete work package

**Archon (Knowledge Repository - Documents Only):**

- `mcp_archon_find_projects()` - List projects (for knowledge organization)
- `mcp_archon_find_documents(project_id=...)` - List documents
- `mcp_archon_manage_document(...)` - Create/update/delete documents
- `mcp_archon_rag_get_available_sources()` - List knowledge sources
- `mcp_archon_rag_search_knowledge_base(...)` - Search knowledge base
- `mcp_archon_rag_search_code_examples(...)` - Find code examples

## Important Notes

- Work package status flow: New (71) → In progress (77) → In testing (79) → Closed (82)
- Keep queries SHORT (2-5 keywords) for better search results
- Higher priority_id = higher priority (Low=72, Normal=73, High=74, Immediate=75)
- Stories should be 30 min - 4 hours of work
- **Archon is NOT used for task management - only for knowledge/document management**

# Archon MCP Tools Usage Guide

This guide documents how to effectively use the Archon MCP tools for task management, project management, and document management based on real-world usage patterns.

## Table of Contents

1. [Overview](#overview)
2. [Finding Tasks](#finding-tasks)
3. [Creating Tasks](#creating-tasks)
4. [Updating Tasks](#updating-tasks)
5. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
6. [Best Practices](#best-practices)
7. [Complete Workflow Examples](#complete-workflow-examples)

## Overview

The Archon MCP provides several consolidated tools for managing projects, tasks, and documents:

- `archon:find_tasks` - List, search, or get specific tasks
- `archon:manage_task` - Create, update, or delete tasks
- `archon:find_projects` - List, search, or get specific projects
- `archon:manage_project` - Create, update, or delete projects
- `archon:find_documents` - List, search, or get specific documents
- `archon:manage_document` - Create, update, or delete documents

## Finding Tasks

### Basic Usage

The `find_tasks` tool is consolidated - it handles listing, searching, and getting individual tasks.

```python
# List all tasks for a project
find_tasks(project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8")

# Search tasks by keyword
find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    query="Story 1.1"
)

# Get a specific task by ID (returns full details)
find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    task_id="b2691865-4c4b-47ce-adf2-4441025b696c"
)

# Filter by status
find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    filter_by="status",
    filter_value="todo"
)
```

### Important Notes

- **project_id is required** - Always provide the full UUID project ID
- **task_id returns full details** - When using `task_id`, you get complete task information including full description
- **query is for keyword search** - Use `query` to search in title, description, or feature fields
- **Pagination** - Use `page` and `per_page` for large result sets (default: 10 per page)

## Creating Tasks

### Basic Task Creation

```python
manage_task(
    action="create",
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    title="Story 1.1: Project Structure & Development Environment Setup",
    description="Complete acceptance criteria from epics.md...",
    status="todo",
    assignee="User",
    task_order=120,
    feature="Epic 1: Secure Platform Foundation"
)
```

### Required Parameters

- `action`: Must be `"create"` for new tasks
- `project_id`: Full UUID of the project (required)
- `title`: Task title (required)

### Optional Parameters

- `description`: Full task description with acceptance criteria
- `status`: `"todo"`, `"doing"`, `"review"`, or `"done"` (default: `"todo"`)
- `assignee`: Assignee name (default: `"User"`)
- `task_order`: Priority/order number (0-100, higher = more priority)
- `feature`: Feature label for grouping tasks

### Best Practices for Descriptions

**✅ DO: Include Complete Acceptance Criteria**

```python
description="""
As a **Developer**,
I want **to set up the project structure and local development environment**,
So that **I can begin implementing the RAG system with all necessary scaffolding in place**.

**Acceptance Criteria:**

**Given** I am starting a new project from scratch
**When** I initialize the project structure following the architecture document
**Then** The directory structure matches the architecture specification (app/, tests/, docker/, kubernetes/, scripts/)
**And** All **init**.py files are created for Python package structure
**And** pyproject.toml and requirements.txt are configured with base dependencies
...
"""
```

**❌ DON'T: Summarize or Truncate**

```python
# BAD - Too brief, missing details
description="Set up project structure and development environment"
```

## Updating Tasks

### Basic Task Update

```python
manage_task(
    action="update",
    task_id="b2691865-4c4b-47ce-adf2-4441025b696c",
    description="Complete acceptance criteria...",
    status="doing"
)
```

### Critical: Use Full Task IDs

**✅ CORRECT: Full UUID**

```python
manage_task(
    action="update",
    task_id="b2691865-4c4b-47ce-adf2-4441025b696c",  # Full UUID
    description="..."
)
```

**❌ WRONG: Truncated or Numeric IDs**

```python
# These will FAIL with "invalid input syntax for type uuid"
manage_task(action="update", task_id="117", ...)  # ❌
manage_task(action="update", task_id="629", ...)  # ❌
manage_task(action="update", task_id="b2691865", ...)  # ❌
```

### How to Get Full Task IDs

**Method 1: From Task Creation Response**

When you create a task, the response includes the full task ID:

```python
result = manage_task(
    action="create",
    project_id="...",
    title="My Task"
)
task_id = result["task"]["id"]  # Full UUID: "b2691865-4c4b-47ce-adf2-4441025b696c"
```

**Method 2: From find_tasks Response**

```python
tasks = find_tasks(project_id="...", query="Story 1.1")
task_id = tasks["tasks"][0]["id"]  # Full UUID
```

**Method 3: Get Specific Task**

```python
task = find_tasks(
    project_id="...",
    task_id="b2691865-4c4b-47ce-adf2-4441025b696c"
)
# Returns full task details with complete description
```

### Updateable Fields

You can update any of these fields:

- `title`: Task title
- `description`: Full task description
- `status`: `"todo"`, `"doing"`, `"review"`, `"done"`
- `assignee`: Assignee name
- `task_order`: Priority number
- `feature`: Feature label

## Common Pitfalls and Solutions

### Pitfall 1: Using Truncated Task IDs

**Problem:**

```python
# This fails
manage_task(action="update", task_id="117", ...)
# Error: invalid input syntax for type uuid: "117"
```

**Solution:**
Always use the full UUID from the task creation response or `find_tasks` result.

```python
# Get full ID first
tasks = find_tasks(project_id="...", query="Story 1.2")
task_id = tasks["tasks"][0]["id"]  # Full UUID

# Then update
manage_task(action="update", task_id=task_id, ...)
```

### Pitfall 2: Missing project_id

**Problem:**

```python
# This may fail or return wrong results
find_tasks(query="Story 1.1")  # Missing project_id
```

**Solution:**
Always provide `project_id` when working with project-scoped tasks.

```python
find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    query="Story 1.1"
)
```

### Pitfall 3: Truncated Descriptions

**Problem:**

```python
# Too brief, missing acceptance criteria
description="Set up project structure"
```

**Solution:**
Copy the complete acceptance criteria from source documents (like `epics.md`):

```python
description="""
As a **Developer**,
I want **to set up the project structure and local development environment**,
So that **I can begin implementing the RAG system with all necessary scaffolding in place**.

**Acceptance Criteria:**

**Given** I am starting a new project from scratch
**When** I initialize the project structure following the architecture document
**Then** The directory structure matches the architecture specification (app/, tests/, docker/, kubernetes/, scripts/)
**And** All **init**.py files are created for Python package structure
...
"""
```

### Pitfall 4: Not Handling API Errors

**Problem:**
Tool calls fail silently or with unclear errors.

**Solution:**
Always check the response:

```python
result = manage_task(action="update", task_id="...", ...)
if not result.get("success"):
    error = result.get("error", {})
    print(f"Error: {error.get('message')}")
    # Handle error appropriately
```

## Best Practices

### 1. Always Use Full UUIDs

- Store task IDs immediately after creation
- Use `find_tasks` with `task_id` to get full details before updating
- Never truncate or guess task IDs

### 2. Include Complete Acceptance Criteria

- Copy verbatim from source documents
- Include all "Given/When/Then" statements
- Preserve formatting (markdown, bullet points, etc.)

### 3. Use Consistent Naming

- Use consistent task titles (e.g., "Story 1.1: ...")
- Use consistent feature labels (e.g., "Epic 1: Secure Platform Foundation")
- Use consistent assignee names

### 4. Set Appropriate Task Order

- Use `task_order` to reflect priority (0-100)
- Higher numbers = higher priority
- Group related tasks with similar order numbers

### 5. Update Status Progressively

- Start with `"todo"`
- Move to `"doing"` when work begins
- Move to `"review"` when complete
- Move to `"done"` after verification

## Complete Workflow Examples

### Example 1: Creating Tasks from Epics Document

```python
# Step 1: Read the epics document
epics_content = read_file("epics.md")

# Step 2: Parse stories (extract title, description, acceptance criteria)
stories = parse_epics(epics_content)

# Step 3: Create tasks for each story
project_id = "00ae4b66-93ed-41dc-9f96-d5f6e2842fc8"
created_tasks = []

for i, story in enumerate(stories):
    result = manage_task(
        action="create",
        project_id=project_id,
        title=story["title"],
        description=story["full_acceptance_criteria"],  # Complete, not summarized
        status="todo",
        assignee="User",
        task_order=120 - i,  # Higher priority for earlier stories
        feature="Epic 1: Secure Platform Foundation"
    )

    if result.get("success"):
        created_tasks.append({
            "title": story["title"],
            "id": result["task"]["id"]  # Store full UUID
        })
    else:
        print(f"Failed to create task: {story['title']}")
        print(f"Error: {result.get('error', {}).get('message')}")
```

### Example 2: Updating Task Descriptions

```python
# Step 1: Find the task
tasks = find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    query="Story 1.1"
)

if tasks.get("success") and tasks.get("tasks"):
    task = tasks["tasks"][0]
    task_id = task["id"]  # Full UUID

    # Step 2: Read updated acceptance criteria from source
    updated_description = read_file("epics.md", extract_story_1_1)

    # Step 3: Update the task
    result = manage_task(
        action="update",
        task_id=task_id,  # Use full UUID
        description=updated_description  # Complete acceptance criteria
    )

    if result.get("success"):
        print(f"Successfully updated task: {task['title']}")
    else:
        print(f"Failed to update: {result.get('error', {}).get('message')}")
```

### Example 3: Bulk Updating Multiple Tasks

```python
# Step 1: Find all tasks that need updating
tasks = find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    query="Story 1"
)

# Step 2: Read source document for complete acceptance criteria
epics_content = read_file("epics.md")
story_data = parse_all_stories(epics_content)

# Step 3: Create mapping of titles to full acceptance criteria
story_map = {story["title"]: story["full_acceptance_criteria"]
             for story in story_data}

# Step 4: Update each task
updated_count = 0
failed_count = 0

for task in tasks.get("tasks", []):
    task_id = task["id"]  # Full UUID
    task_title = task["title"]

    # Find matching story data
    if task_title in story_map:
        result = manage_task(
            action="update",
            task_id=task_id,  # Full UUID
            description=story_map[task_title]  # Complete acceptance criteria
        )

        if result.get("success"):
            updated_count += 1
        else:
            failed_count += 1
            print(f"Failed to update {task_title}: {result.get('error', {}).get('message')}")

print(f"Updated: {updated_count}, Failed: {failed_count}")
```

### Example 4: Moving Tasks Through Workflow

```python
# Step 1: Get task in "todo" status
tasks = find_tasks(
    project_id="00ae4b66-93ed-41dc-9f96-d5f6e2842fc8",
    filter_by="status",
    filter_value="todo"
)

if tasks.get("tasks"):
    task = tasks["tasks"][0]
    task_id = task["id"]

    # Step 2: Move to "doing"
    manage_task(
        action="update",
        task_id=task_id,
        status="doing",
        assignee="User"
    )

    # ... do work ...

    # Step 3: Move to "review"
    manage_task(
        action="update",
        task_id=task_id,
        status="review"
    )

    # ... after review ...

    # Step 4: Move to "done"
    manage_task(
        action="update",
        task_id=task_id,
        status="done"
    )
```

## Summary

Key takeaways for using Archon MCP tools effectively:

1. **Always use full UUIDs** - Never truncate task IDs
2. **Include complete acceptance criteria** - Don't summarize, copy verbatim from source
3. **Store task IDs immediately** - Save full UUIDs from creation responses
4. **Use find_tasks to get IDs** - Query tasks to retrieve full UUIDs before updating
5. **Check responses** - Always verify `success` and handle errors appropriately
6. **Be consistent** - Use consistent naming, statuses, and assignees

Following these practices will help you avoid common pitfalls and successfully manage tasks, projects, and documents using the Archon MCP tools.

# OpenProject Integration & BMAD Methodology Synergy

**IMPORTANT: OpenProject is the PRIMARY work management system. Archon is ONLY used as a knowledge repository for documents and research.**

## System Architecture

**OpenProject** = PRIMARY work management system (Projects, Epics, Features, User Stories, Tasks, all work tracking)
**Archon** = Knowledge repository ONLY (Documents, research, knowledge base, code examples)

### System Mapping

| BMAD Concept   | OpenProject Work Package Type  | Archon Usage                     | Usage                                               |
| -------------- | ------------------------------ | -------------------------------- | --------------------------------------------------- |
| **Project**    | OpenProject Project            | Archon Project (knowledge only)  | Create in OpenProject, use Archon for project docs |
| **Epic**       | Epic (work package type)       | N/A                              | Create and manage in OpenProject                    |
| **Feature**    | Feature (work package type)    | N/A                              | Create and manage in OpenProject                    |
| **User Story** | User Story (work package type) | N/A                              | Create and manage in OpenProject                    |
| **Task**       | Task (work package type)       | N/A                              | **PRIMARY in OpenProject**                          |
| **Documents**  | N/A                            | Archon Documents                 | Store project docs, specs, research in Archon       |
| **Knowledge**  | N/A                            | Archon RAG Knowledge Base        | Search knowledge base, code examples in Archon      |

## OpenProject MCP Tools Reference

### Connection & Discovery

- `mcp_openproject_test_connection()` - Test API connectivity

### Project Management

- `mcp_openproject_list_projects(active_only=True)` - List all projects
- `mcp_openproject_get_project(project_id=7)` - Get project details
- `mcp_openproject_create_project(name="...", identifier="...", description="...")` - Create project
- `mcp_openproject_update_project(project_id=7, ...)` - Update project
- `mcp_openproject_delete_project(project_id=7)` - Delete project

### Work Package Management

- `mcp_openproject_list_work_packages(project_id=7, status="open")` - List work packages
- `mcp_openproject_get_work_package(work_package_id=46)` - Get work package details
- `mcp_openproject_create_work_package(project_id=7, subject="...", type_id=40, ...)` - Create work package
- `mcp_openproject_update_work_package(work_package_id=46, ...)` - Update work package
- `mcp_openproject_delete_work_package(work_package_id=46)` - Delete work package

### Reference Data

- `mcp_openproject_list_types(project_id=7)` - List available work package types

**⚠️ IMPORTANT: Type Conversion Issue**

The OpenProject MCP server requires `project_id` and `work_package_id` parameters to be **integers**, not strings. However, the MCP tool interface may pass them as strings from JSON-RPC.

**Workaround:** The MCP server should handle type conversion automatically, but if you encounter "Parameter 'project_id' must be one of types [integer, null], got string" errors, this indicates the remote MCP server needs to be updated to handle string-to-integer conversion.

**Current Status:** This is a known limitation of the remote OpenProject MCP server. For now, use the `scripts/sync_epics_to_openproject.py` script which handles type conversion correctly.

- `mcp_openproject_list_statuses()` - List available statuses
- `mcp_openproject_list_priorities()` - List priority levels
- `mcp_openproject_list_users(active_only=True)` - List users

### Work Package Type IDs (Common)

- **Epic**: type_id=40
- **Feature**: type_id=39
- **User Story**: type_id=41
- **Task**: type_id=36 (default)
- **Bug**: type_id=42
- **Milestone**: type_id=37

### Status IDs (Common)

- **New**: status_id=71 (default)
- **In progress**: status_id=77
- **Closed**: status_id=82
- **On hold**: status_id=83

### Priority IDs (Common)

- **Low**: priority_id=72
- **Normal**: priority_id=73 (default)
- **High**: priority_id=74
- **Immediate**: priority_id=75

## BMAD Workflow: OpenProject + Archon Integration

### Phase 1: Project Setup (OpenProject)

```python
# 1. Create project in OpenProject
op_project = mcp_openproject_create_project(
    name="Enterprise RAG System",
    identifier="enterprise-rag-system",
    description="Multi-tenant RAG system with Mem0 integration",
    public=True
)
op_project_id = op_project["project"]["id"]  # e.g., 7

# 2. Get work package types for this project
types = mcp_openproject_list_types(project_id=op_project_id)
epic_type_id = next(t["id"] for t in types["types"] if t["name"] == "Epic")
feature_type_id = next(t["id"] for t in types["types"] if t["name"] == "Feature")
story_type_id = next(t["id"] for t in types["types"] if t["name"] == "User story")
```

### Phase 2: Create Epics (OpenProject)

```python
# Create Epic work package in OpenProject
epic = mcp_openproject_create_work_package(
    project_id=op_project_id,
    subject="Epic 1: Secure Platform Foundation",
    type_id=epic_type_id,  # Epic type
    description="Foundation for secure, multi-tenant RAG platform",
    priority_id=74  # High priority
)
epic_id = epic["work_package"]["id"]
```

### Phase 3: Create Features (OpenProject)

```python
# Create Feature work package under Epic
feature = mcp_openproject_create_work_package(
    project_id=op_project_id,
    subject="Feature: Multi-Tenant Authentication",
    type_id=feature_type_id,  # Feature type
    description="OAuth 2.0 authentication with tenant isolation",
    priority_id=73  # Normal priority
    # Note: Parent relationship can be set via update after creation
)
feature_id = feature["work_package"]["id"]

# Link feature to epic (if parent relationship supported)
# This may require update_work_package with parent reference
```

### Phase 4: Create User Stories (OpenProject)

```python
# Create User Story work package
story = mcp_openproject_create_work_package(
    project_id=op_project_id,
    subject="Story 1.1: Project Structure & Development Environment Setup",
    type_id=story_type_id,  # User story type
    description="""
    As a **Developer**,
    I want **to set up the project structure and local development environment**,
    So that **I can begin implementing the RAG system with all necessary scaffolding in place**.

    **Acceptance Criteria:**
    [Full acceptance criteria from epics.md]
    """,
    priority_id=73,
    start_date="2025-01-15",
    due_date="2025-01-20"
)
story_id = story["work_package"]["id"]
```

### Phase 5: Store Project Documentation in Archon (Optional - Knowledge Repository Only)

```python
# Optionally create Archon project for knowledge/document management
# This is ONLY for storing project documentation, not for task management
archon_project = mcp_archon_manage_project(
    action="create",
    title="Enterprise RAG System",
    description="Multi-tenant RAG system with Mem0 integration - Knowledge Repository",
    github_repo="https://github.com/Bionic-AI-Solutions/enterprise-rag-system"
)
archon_project_id = archon_project["project"]["id"]

# Store project documentation in Archon (NOT tasks)
archon_doc = mcp_archon_manage_document(
    action="create",
    project_id=archon_project_id,
    title="Architecture Document",
    document_type="spec",
    content={"markdown": "...architecture content..."},
    tags=["architecture", "technical-design"]
)

# Note: Work packages (epics, stories, tasks) are managed ONLY in OpenProject
# Archon is used ONLY for documents and knowledge base
```

## Complete BMAD Workflow Example

### Creating a Full Epic with Features and Stories

```python
# Step 1: Setup - Get OpenProject project
op_projects = mcp_openproject_list_projects(active_only=True)
op_project = next(p for p in op_projects["projects"] if p["name"] == "Enterprise RAG System")
op_project_id = op_project["id"]

# Get type IDs
types = mcp_openproject_list_types(project_id=op_project_id)
epic_type_id = next(t["id"] for t in types["types"] if t["name"] == "Epic")
feature_type_id = next(t["id"] for t in types["types"] if t["name"] == "Feature")
story_type_id = next(t["id"] for t in types["types"] if t["name"] == "User story")

# Step 2: Create Epic in OpenProject
epic = mcp_openproject_create_work_package(
    project_id=op_project_id,
    subject="Epic 1: Secure Platform Foundation",
    type_id=epic_type_id,
    description="Foundation for secure, multi-tenant RAG platform",
    priority_id=74  # High
)
epic_id = epic["work_package"]["id"]

# Step 3: Create Feature in OpenProject
feature = mcp_openproject_create_work_package(
    project_id=op_project_id,
    subject="Feature: Multi-Tenant Authentication",
    type_id=feature_type_id,
    description="OAuth 2.0 authentication with tenant isolation",
    priority_id=73  # Normal
)
feature_id = feature["work_package"]["id"]

# Step 4: Create User Stories in OpenProject
stories = [
    {
        "subject": "Story 1.1: Project Structure & Development Environment Setup",
        "description": "[Full acceptance criteria]",
        "priority": 73
    },
    {
        "subject": "Story 1.2: Database Schema & Models",
        "description": "[Full acceptance criteria]",
        "priority": 73
    }
]

op_story_ids = []
for story_data in stories:
    story = mcp_openproject_create_work_package(
        project_id=op_project_id,
        subject=story_data["subject"],
        type_id=story_type_id,
        description=story_data["description"],
        priority_id=story_data["priority"]
    )
    op_story_ids.append(story["work_package"]["id"])

# Step 5: All work management is done in OpenProject
# No need to sync to Archon - Archon is only for knowledge/document management

# Optional: Store project documentation in Archon (knowledge repository)
archon_project = mcp_archon_manage_project(
    action="create",
    title="Enterprise RAG System",
    description="Multi-tenant RAG system with Mem0 integration - Knowledge Repository"
)
archon_project_id = archon_project["project"]["id"]

# Store project docs in Archon (NOT tasks)
mcp_archon_manage_document(
    action="create",
    project_id=archon_project_id,
    title="Project Documentation",
    document_type="spec",
    content={"markdown": "Project documentation content..."}
)
```

## Work Package Status Management

### When Work Package Status Changes

```python
# Update work package status in OpenProject (PRIMARY system)
mcp_openproject_update_work_package(
    work_package_id=work_package_id,
    status_id=77,  # In progress
    percentage_done=50
)

# Status mapping:
# New: 71
# In specification: 72
# Specified: 73
# Confirmed: 74
# To be scheduled: 75
# Scheduled: 76
# In progress: 77
# Developed: 78
# In testing: 79
# Tested: 80
# Test failed: 81
# Closed: 82
# On hold: 83
# Rejected: 84
```

## Best Practices for System Usage

### 1. OpenProject for ALL Work Management

- **OpenProject**: Use for ALL work management (Projects, Epics, Features, User Stories, Tasks, status tracking)
- **Archon**: Use ONLY for knowledge repository (documents, research, knowledge base, code examples)

### 2. Document Linking

When storing project documentation in Archon, include OpenProject references:

```python
mcp_archon_manage_document(
    action="create",
    project_id=archon_project_id,
    title="Epic 1: Secure Platform Foundation - Technical Spec",
    document_type="spec",
    content={
        "markdown": f"""
        {spec_content}

        **OpenProject References:**
        - Work Package ID: {op_work_package_id}
        - Project ID: {op_project_id}
        - Epic: {epic_name} (ID: {epic_id})
        """
    },
    tags=["epic-1", "architecture"]
)
```

### 3. Status Management

All status management happens in OpenProject:

| Work State | OpenProject Status ID | Notes         |
| ---------- | ---------------------- | ------------- |
| New        | 71                     | Initial state |
| In progress| 77                     | Active work   |
| In testing | 79                     | Under review  |
| Closed     | 82                     | Completed     |

### 4. Work Package Hierarchy

OpenProject supports parent-child relationships:

- Epic → Feature → User Story → Task
- Use `update_work_package` to set parent relationships after creation

### 5. Priority Alignment

- OpenProject priorities: Low (72), Normal (73), High (74), Immediate (75)
- Archon task_order: 0-100 (higher = more priority)
- Map accordingly: High (74) → task_order 80-100, Normal (73) → task_order 50-79

## Querying and Reporting

### Get All Stories for an Epic

```python
# 1. Get epic from OpenProject
epic = mcp_openproject_get_work_package(work_package_id=epic_id)

# 2. List all work packages in project
all_wps = mcp_openproject_list_work_packages(
    project_id=op_project_id,
    status="open"
)

# 3. Filter by epic (if parent relationship is stored)
# Note: May need to check relations or use custom filtering
```

### Get Documents for OpenProject Feature

```python
# 1. Get feature from OpenProject
feature = mcp_openproject_get_work_package(work_package_id=feature_id)

# 2. Query Archon documents related to this feature (knowledge repository)
archon_docs = mcp_archon_find_documents(
    project_id=archon_project_id,
    query=feature["work_package"]["subject"]
)
```

## Integration Checklist

When setting up a new BMAD project:

- [ ] Create project in OpenProject (PRIMARY work management)
- [ ] Get work package type IDs (Epic, Feature, User Story, Task)
- [ ] Create Epic work packages in OpenProject
- [ ] Create Feature work packages under Epics
- [ ] Create User Story work packages under Features
- [ ] Create Task work packages under Stories (if needed)
- [ ] Optionally create Archon project for knowledge/document management
- [ ] Store project documentation in Archon (specs, research, knowledge)
- [ ] Link Archon documents to OpenProject work packages (store IDs in document content)
- [ ] All work tracking and status management in OpenProject

## Summary

**Key Principles:**

1. **OpenProject = PRIMARY Work Management** - Use for ALL work (Projects, Epics, Features, User Stories, Tasks, status tracking)
2. **Archon = Knowledge Repository ONLY** - Use ONLY for documents, research, knowledge base, code examples
3. **No Task Management in Archon** - All tasks, stories, epics are managed in OpenProject
4. **Document Linking** - Include OpenProject references in Archon documents (not tasks)
5. **BMAD Alignment** - Map BMAD concepts to OpenProject work package types

This system architecture provides:

- **Complete work management** in OpenProject (epics, stories, tasks, status, tracking)
- **Knowledge repository** in Archon (documents, research, knowledge base)
- **Full traceability** from Epic → Feature → Story → Task in OpenProject
- **BMAD methodology compliance** with proper hierarchy and structure
- **Clear separation** between work management and knowledge management

## Responsibility Assignment: OpenProject Work Management

### Primary Owner: Product Manager (PM)

**The Product Manager is responsible for ensuring all epics, features, and stories from `epics.md` are accurately created and managed in OpenProject using MCP tools. OpenProject is the PRIMARY work management system.**

#### PM Responsibilities:

1. **Verify Completeness**: Ensure all epics from `epics.md` are created in OpenProject
2. **Maintain Accuracy**: Keep OpenProject structure aligned with `epics.md`
3. **Execute Sync**: Run sync script after epic/story updates
4. **Validate Hierarchy**: Ensure parent-child relationships are correctly established
5. **Quality Check**: Verify all stories have complete acceptance criteria in OpenProject

#### When to Sync:

- ✅ After `create-epics-and-stories` workflow completes
- ✅ After epic/story updates in `epics.md`
- ✅ Before sprint planning sessions
- ✅ After significant PRD/Architecture changes

#### Sync Workflow:

```bash
# 1. Verify source document
cat _bmad-output/planning-artifacts/epics.md | grep -E "^### Epic|^#### Story"

# 2. Run sync script
python scripts/sync_epics_to_openproject.py

# 3. Verify in OpenProject UI
# 4. Set parent relationships if needed
python scripts/set_openproject_parents.py
```

#### Supporting Role: Scrum Master (SM)

The Scrum Master supports by:

- Assisting with story breakdown and acceptance criteria
- Ensuring stories are properly sized for development
- Validating OpenProject alignment with sprint planning needs

#### Sync Tools:

1. **`scripts/sync_epics_to_openproject.py`** - Main sync script

   - Parses `epics.md`
   - Creates/updates epics and stories in OpenProject
   - Sets parent-child relationships automatically

2. **`scripts/set_openproject_parents.py`** - Parent relationship fixer
   - Use when structure exists but relationships are missing
   - Sets Epic → Feature → Story hierarchy

#### Quality Checklist:

Before considering sync complete:

- [ ] All epics from `epics.md` exist in OpenProject
- [ ] All stories from `epics.md` exist in OpenProject
- [ ] All acceptance criteria are present and complete
- [ ] Parent-child relationships are correctly established
- [ ] Work package types are correct
- [ ] No duplicate work packages

For detailed documentation, see: `docs/OPENPROJECT_SYNC_RESPONSIBILITY.md`

## Keeping OpenProject Updated

### Work Package Type Management

**CRITICAL: Always use correct work package types:**

- **Epic**: type_id=40 (Epic type)
- **Feature**: type_id=39 (Feature type)  
- **User Story**: type_id=41 (User Story type)
- **Task**: type_id=36 (Task type)

**If types are incorrect, run:**
```bash
python scripts/fix_and_update_openproject.py
```

### Task Creation Under Stories

**When grooming stories and creating tasks:**

1. **From Implementation Artifacts** (Preferred):
   ```bash
   python scripts/create_tasks_from_stories.py --story-id <story_work_package_id>
   ```

2. **Manual Creation**:
   ```python
   mcp_openproject_create_work_package(
       project_id=8,
       subject="Task 1.1.1.1: Create Project Directory Structure",
       type_id=36,  # Task
       description="Create root directory structure...",
       # Parent relationship set via update_work_package or during creation
   )
   ```

3. **After Creating Task, Set Parent**:
   ```python
   # Use set_openproject_parents.py script or update via API
   # Task should be child of Story work package
   ```

### Ongoing Maintenance

**Daily:**
- Update work package statuses as work progresses
- Create tasks for new work discovered

**After Epic/Story Updates:**
- Run sync: `python scripts/sync_epics_to_openproject.py`
- Fix types: `python scripts/fix_and_update_openproject.py`
- Set parents: `python scripts/set_openproject_parents.py`

**During Story Grooming:**
- Create tasks: `python scripts/create_tasks_from_stories.py --story-id <id>`
- Verify tasks are created under correct story
- Update story status to "In specification" or "Specified"

For complete workflow, see: `docs/OPENPROJECT_MAINTENANCE_WORKFLOW.md`
