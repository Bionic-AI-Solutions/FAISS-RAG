# OpenProject Work-Driven Development Workflow

This workflow defines how BMAD agents interact with OpenProject for work management and document storage.

## Core Principle: OpenProject-First

**CRITICAL RULE:** OpenProject is the PRIMARY system for BOTH work management AND document storage.

### Work Management

Before coding ANY functionality:

1. Check OpenProject for current work packages
2. Update work package status when starting work
3. Update status when work is complete
4. NEVER code without an associated work package

### Document Storage

ALL project artifacts must be stored as OpenProject attachments at the appropriate level:

- **Project-level**: Product briefs, project overview docs
- **Epic-level**: Epic specifications, business cases
- **Feature-level**: Feature architecture, technical designs
- **Story-level**: Story specifications, acceptance criteria docs
- **Task-level**: Implementation notes, technical details

**DO NOT store project documents in Archon.** Archon is ONLY for searching external knowledge.

## Mandatory Work Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORK-DRIVEN DEVELOPMENT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. GET WORK                                                     │
│     └── mcp_openproject_list_work_packages(project_id, "open")  │
│                                                                  │
│  2. START WORK                                                   │
│     └── mcp_openproject_update_work_package(id, status=77)      │
│                                                                  │
│  3. RESEARCH (via Archon - see archon/workflow.md)              │
│     └── mcp_archon_rag_search_knowledge_base(...)               │
│                                                                  │
│  4. IMPLEMENT                                                    │
│     └── Write code based on research and requirements           │
│                                                                  │
│  5. REVIEW                                                       │
│     └── mcp_openproject_update_work_package(id, status=79)      │
│                                                                  │
│  6. COMPLETE                                                     │
│     └── mcp_openproject_update_work_package(id, status=82)      │
│                                                                  │
│  7. NEXT WORK                                                    │
│     └── Return to step 1                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Work Package Hierarchy

OpenProject supports a hierarchical structure that aligns with BMAD:

```
Project
└── Epic (type_id from config)
    └── Feature (type_id from config)
        └── User Story (type_id from config)
            └── Task (type_id from config)
```

### Creating Work Package Hierarchy

**Step 1: Create Epic**

```python
epic = mcp_openproject_create_work_package(
    project_id={config.openproject.project_id},
    subject="Epic 1: {Epic Name}",
    type_id={config.openproject.types.epic},
    description="Business goal and scope",
    priority_id={config.openproject.priorities.high}
)
```

**Step 2: Create Features under Epic**

```python
feature = mcp_openproject_create_work_package(
    project_id={config.openproject.project_id},
    subject="Feature: {Feature Name}",
    type_id={config.openproject.types.feature},
    description="Functional capability"
)
# Set parent relationship
mcp_openproject_set_work_package_parent(
    work_package_id=feature["work_package"]["id"],
    parent_id=epic_id
)
```

**Step 3: Create User Stories under Features**

```python
story = mcp_openproject_create_work_package(
    project_id={config.openproject.project_id},
    subject="Story X.Y: {Story Name}",
    type_id={config.openproject.types.user_story},
    description="""
    As a {persona},
    I want {goal},
    So that {benefit}.

    **Acceptance Criteria:**
    - Given... When... Then...
    """
)
mcp_openproject_set_work_package_parent(
    work_package_id=story["work_package"]["id"],
    parent_id=feature_id
)
```

**Step 4: Create Tasks under Stories**

```python
task = mcp_openproject_create_work_package(
    project_id={config.openproject.project_id},
    subject="Task X.Y.Z: {Task Name}",
    type_id={config.openproject.types.task},
    description="Specific implementation work"
)
mcp_openproject_set_work_package_parent(
    work_package_id=task["work_package"]["id"],
    parent_id=story_id
)
```

## Status Workflow

### Standard Status Flow

```
New (71)
  ↓
In specification (72)  ← Requirements being defined
  ↓
Specified (73)         ← Requirements complete
  ↓
Confirmed (74)         ← Approved for work
  ↓
Scheduled (76)         ← In sprint backlog
  ↓
In progress (77)       ← Active development
  ↓
Developed (78)         ← Code complete
  ↓
In testing (79)        ← Under review/testing
  ↓
Tested (80)            ← Testing passed
  ↓
Closed (82)            ← Complete

Alternative paths:
  - On hold (83)       ← Paused
  - Rejected (84)      ← Not proceeding
  - Test failed (81)   ← Back to In progress
```

### Simplified Status Flow (Recommended)

For most development workflows, use this simplified flow:

```
New (71) → In progress (77) → In testing (79) → Closed (82)
```

## Document Storage Workflow

### Principle: Store Documents at Appropriate Level

All project documents are stored as OpenProject attachments. Choose the correct work package level:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENT STORAGE HIERARCHY                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PROJECT LEVEL                                                   │
│  └── Product briefs, project overview, high-level specs         │
│                                                                  │
│  EPIC LEVEL                                                      │
│  └── Epic specifications, business cases, epic architecture     │
│                                                                  │
│  FEATURE LEVEL                                                   │
│  └── Feature architecture, technical designs, API specs         │
│                                                                  │
│  STORY LEVEL                                                     │
│  └── Story specs, detailed acceptance criteria, test cases      │
│                                                                  │
│  TASK LEVEL                                                      │
│  └── Implementation notes, code documentation, technical notes  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Document Types and Storage Location

| Document Type           | Storage Level   | Rationale                 |
| ----------------------- | --------------- | ------------------------- |
| Product Brief           | Project         | Applies to entire project |
| PRD                     | Project or Epic | Requirements scope        |
| Architecture Overview   | Project         | System-wide architecture  |
| Feature Architecture    | Feature         | Feature-specific design   |
| Technical Specification | Feature/Story   | Implementation details    |
| API Documentation       | Feature         | API is feature-level      |
| Acceptance Criteria Doc | Story           | Story-specific criteria   |
| Test Strategy           | Feature         | Feature-level testing     |
| Test Cases              | Story           | Story-specific tests      |
| Implementation Notes    | Task            | Task-specific details     |
| Code Documentation      | Task            | Implementation reference  |

### Attaching Documents

1. **Via OpenProject UI**: Upload directly to work package
2. **Via API**: Use OpenProject attachment API
3. **Link in Description**: Reference document location in work package description

### Document Naming Convention

```
{WorkPackageID}-{DocumentType}-{Version}.{ext}

Examples:
- WP-123-architecture-v1.md
- WP-456-acceptance-criteria-v2.md
- WP-789-implementation-notes.md
```

## Agent Integration Points

### PM Agent

- **Creates:** Epics, Features, User Stories (from PRD)
- **Updates:** Story acceptance criteria, priorities
- **Queries:** Sprint backlog, story status
- **Documents:** Stores product briefs at Project level, PRDs at Epic level

### Dev Agent

- **Queries:** Assigned work packages, task details
- **Updates:** Task status (In progress → Developed)
- **Creates:** Sub-tasks for implementation breakdown
- **Documents:** Stores implementation notes at Task level

### SM Agent

- **Queries:** Sprint progress, blockers
- **Updates:** Sprint assignments, priorities
- **Reports:** Sprint status, velocity
- **Documents:** Sprint reports at Project level

### Architect Agent

- **Creates:** Technical tasks from architecture decisions
- **Links:** Stories to technical specifications
- **Documents:** Stores architecture docs at Feature level, system architecture at Project level

### TEA Agent

- **Creates:** Test-related tasks
- **Updates:** Test status, bug reports
- **Links:** Test cases to stories
- **Documents:** Stores test strategies at Feature level, test cases at Story level

## Sprint Planning Workflow

### 1. Backlog Grooming

```python
# Get unscheduled stories
backlog = mcp_openproject_query_work_packages(
    project_id={config.openproject.project_id},
    filters='[{"type":{"operator":"=","values":["{config.openproject.types.user_story}"]}},{"status":{"operator":"=","values":["71","72","73","74"]}}]'
)
```

### 2. Sprint Assignment

```python
# Move story to sprint
mcp_openproject_update_work_package(
    work_package_id=story_id,
    status_id=76  # Scheduled
)
```

### 3. Task Breakdown

```python
# Create implementation tasks under story
for task_def in story_tasks:
    task = mcp_openproject_create_work_package(
        project_id={config.openproject.project_id},
        subject=task_def["subject"],
        type_id={config.openproject.types.task},
        description=task_def["description"]
    )
    mcp_openproject_set_work_package_parent(
        work_package_id=task["work_package"]["id"],
        parent_id=story_id
    )
```

## Reporting Queries

### Sprint Status

```python
# Get all in-progress work
in_progress = mcp_openproject_list_work_packages(
    project_id={config.openproject.project_id},
    status="open"
)

# Get completed this sprint
completed = mcp_openproject_query_work_packages(
    project_id={config.openproject.project_id},
    filters='[{"status":{"operator":"=","values":["82"]}},{"updatedAt":{"operator":">t-","values":["14"]}}]'
)
```

### Blockers

```python
# Find blocked items
blocked = mcp_openproject_query_work_packages(
    project_id={config.openproject.project_id},
    filters='[{"status":{"operator":"=","values":["83"]}}]'
)

# Find items with blocking relations
relations = mcp_openproject_list_work_package_relations(
    relation_type="blocked"
)
```

## Best Practices

### 1. Always Use Full Work Package Cycle

- Never code without checking current work packages
- Always update status when starting/completing work
- Document blockers and decisions in comments

### 2. Maintain Hierarchy

- Stories should always link to Features/Epics
- Tasks should always link to Stories
- Use consistent naming: "Epic N:", "Story N.M:", "Task N.M.P:"

### 3. Keep Acceptance Criteria Complete

- Include full Given/When/Then statements
- Link to technical specifications
- Include test requirements

### 4. Use Comments for Context

```python
mcp_openproject_add_work_package_comment(
    work_package_id=task_id,
    comment="Implementation decision: Using approach X because...",
    notify=True
)
```

### 5. Log Time for Planning

```python
mcp_openproject_log_time(
    work_package_id=task_id,
    hours=2.5,
    comment="Implemented feature X"
)
```
