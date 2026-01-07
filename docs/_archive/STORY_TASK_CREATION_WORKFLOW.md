# Story Task Creation Workflow

**Last Updated:** 2026-01-06  
**Status:** MANDATORY WORKFLOW  
**Applies To:** All Stories (Epic 3+)

## Overview

**CRITICAL:** Before starting ANY story implementation, tasks MUST be created in OpenProject. This ensures:
- Proper task tracking and progress visibility
- Clear breakdown of work
- Ability to update task status as work progresses
- Traceability from story → tasks → implementation

## Workflow: Story → Tasks → Implementation

### Phase 1: Story Grooming (PM/Architect)

**Step 1: Review Story Acceptance Criteria**

- Read story acceptance criteria from `epics.md` or story file
- Understand all requirements and dependencies

**Step 2: Break Down Story into Tasks**

- Create task breakdown based on acceptance criteria
- Each task should be:
  - **Specific**: Clear, actionable work item
  - **Measurable**: Can verify completion
  - **Achievable**: 30 minutes to 4 hours of work
  - **Relevant**: Directly contributes to story acceptance criteria
  - **Time-bound**: Clear completion criteria

**Step 3: Create Tasks in OpenProject**

```python
# Example: Creating tasks for Story 3.1
story_id = 129  # Story 3.1: Document Ingestion MCP Tool

tasks = [
    {
        "subject": "Task 3.1.1: Create embedding service for generating embeddings",
        "description": """
        Create EmbeddingService class that:
        - Retrieves tenant-configured embedding model from TenantConfig
        - Generates embeddings using OpenAI API (or tenant-configured provider)
        - Handles errors and retries
        - Returns normalized embedding vectors
        
        **Acceptance Criteria:**
        - Service retrieves model from tenant configuration
        - Embeddings generated successfully
        - Error handling for API failures
        """,
        "type_id": 36,  # Task
    },
    {
        "subject": "Task 3.1.2: Add document addition methods to FAISS manager",
        "description": """
        Extend FAISSIndexManager with:
        - add_document() method
        - Document ID to FAISS ID mapping
        - Tenant-scoped index access
        
        **Acceptance Criteria:**
        - Documents can be added to tenant FAISS index
        - Document IDs mapped to FAISS internal IDs
        - Tenant isolation enforced
        """,
        "type_id": 36,
    },
    {
        "subject": "Task 3.1.3: Add document addition methods to Meilisearch client",
        "description": """
        Extend Meilisearch client with:
        - add_document_to_index() function
        - Tenant-scoped index creation
        - Document metadata indexing
        
        **Acceptance Criteria:**
        - Documents indexed in tenant Meilisearch index
        - Metadata searchable
        - Tenant isolation enforced
        """,
        "type_id": 36,
    },
    {
        "subject": "Task 3.1.4: Create rag_ingest MCP tool",
        "description": """
        Implement rag_ingest MCP tool that:
        - Accepts document_content and document_metadata
        - Validates input (title required, content not empty)
        - Generates embeddings
        - Stores in PostgreSQL, MinIO, FAISS, Meilisearch
        - Returns document_id and ingestion status
        
        **Acceptance Criteria:**
        - Tool accepts required parameters
        - Document stored in all systems
        - Returns success status
        - RBAC: Tenant Admin and End User only
        """,
        "type_id": 36,
    },
    {
        "subject": "Task 3.1.5: Implement text extraction and content processing",
        "description": """
        Implement content processing:
        - Text extraction from document_content
        - Content hashing (SHA-256) for deduplication
        - Content validation
        
        **Acceptance Criteria:**
        - Text extracted correctly
        - Content hash generated
        - Duplicate detection works
        """,
        "type_id": 36,
    },
    {
        "subject": "Task 3.1.6: Implement MinIO document storage",
        "description": """
        Implement MinIO storage:
        - Upload document content to tenant-scoped bucket
        - Store with document_id as object name
        - Return object path
        
        **Acceptance Criteria:**
        - Content stored in tenant bucket
        - Object path returned
        - Tenant isolation enforced
        """,
        "type_id": 36,
    },
    {
        "subject": "Task 3.1.7: Write unit tests",
        "description": """
        Write comprehensive unit tests:
        - Test rag_ingest tool with various inputs
        - Test authorization (Tenant Admin, End User, Uber Admin rejection)
        - Test duplicate detection
        - Test document versioning
        - Test error handling
        
        **Acceptance Criteria:**
        - All unit tests pass
        - Coverage >80%
        - All acceptance criteria tested
        """,
        "type_id": 36,
    },
    {
        "subject": "Task 3.1.8: Create verification documentation",
        "description": """
        Create verification document:
        - Document all acceptance criteria
        - Verify each criterion met
        - Include test results
        - Attach to OpenProject story
        
        **Acceptance Criteria:**
        - Verification document created
        - All criteria verified
        - Document attached to story
        """,
        "type_id": 36,
    },
]

# Create tasks in OpenProject
for task_data in tasks:
    task = mcp_openproject_create_work_package(
        project_id=8,
        subject=task_data["subject"],
        type_id=task_data["type_id"],
        description=task_data["description"],
        parent_id=story_id,  # Link to story
        status_id=71,  # New
    )
    print(f"Created task: {task['work_package']['id']} - {task_data['subject']}")
```

**Step 4: Verify Tasks Created**

```python
# Verify all tasks created
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]

print(f"Created {len(tasks)} tasks for story {story_id}")
for task in tasks:
    print(f"  - {task['id']}: {task['subject']}")
```

### Phase 2: Implementation (Dev)

**CRITICAL:** Do NOT start implementation until tasks are created!

**Step 1: Verify Tasks Exist**

```python
# ALWAYS verify tasks exist before starting
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]

if not tasks:
    raise Exception(
        f"❌ ERROR: No tasks found for story {story_id}. "
        "Tasks must be created BEFORE implementation starts. "
        "Request PM to groom story and create tasks first."
    )

print(f"✅ Found {len(tasks)} tasks. Proceeding with implementation.")
```

**Step 2: Implement Each Task**

For each task:

```python
# 1. Start Task
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=77,  # In progress
)

# 2. Implement task
# ... write code ...
# ... run tests ...

# 3. Mark Task Complete
mcp_openproject_update_work_package(
    work_package_id=task_id,
    status_id=79,  # In testing
)

# 4. Add completion comment
mcp_openproject_add_work_package_comment(
    work_package_id=task_id,
    comment=f"""
    **Task Complete:**
    
    - Implementation: ✅ Complete
    - Unit tests: ✅ Passed (X/X)
    - Integration tests: ✅ Passed (Y/Y)
    - Ready for test team validation
    """
)
```

**Step 3: Update Story File**

```markdown
## Implementation Tasks

- [x] Task 3.1.1: Create embedding service for generating embeddings
- [x] Task 3.1.2: Add document addition methods to FAISS manager
- [x] Task 3.1.3: Add document addition methods to Meilisearch client
- [x] Task 3.1.4: Create rag_ingest MCP tool
- [x] Task 3.1.5: Implement text extraction and content processing
- [x] Task 3.1.6: Implement MinIO document storage
- [x] Task 3.1.7: Write unit tests
- [x] Task 3.1.8: Create verification documentation
```

### Phase 3: Story Completion

**When all tasks are complete:**

```python
# Verify all tasks closed
children = mcp_openproject_get_work_package_children(parent_id=story_id)
tasks = [c for c in children["children"] if c["type"] == "Task"]

all_tasks_closed = all(task["status"] == "Closed" for task in tasks)

if all_tasks_closed:
    # Mark story ready for test
    mcp_openproject_update_work_package(
        work_package_id=story_id,
        status_id=79,  # In testing
    )
```

## Task Naming Convention

**Format:** `Task X.Y.Z: [Brief Description]`

- **X**: Epic number
- **Y**: Story number within epic
- **Z**: Task number within story

**Examples:**
- `Task 3.1.1: Create embedding service for generating embeddings`
- `Task 3.1.2: Add document addition methods to FAISS manager`
- `Task 4.1.1: Add search method to FAISSIndexManager`
- `Task 4.1.2: Create VectorSearchService for high-level search interface`

## Task Description Template

```markdown
**Objective:**
[What this task accomplishes]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Dependencies:**
- [List any dependencies on other tasks]

**Estimated Time:**
[30 minutes - 4 hours]

**Files to Create/Modify:**
- `path/to/file1.py`
- `path/to/file2.py`

**Tests Required:**
- Unit tests: [description]
- Integration tests: [description]
```

## Common Mistakes to Avoid

### ❌ DON'T: Start Implementation Without Tasks

```python
# WRONG - Starting implementation without tasks
# ... start coding immediately ...
```

### ✅ DO: Create Tasks First

```python
# CORRECT - Create tasks first
tasks = create_tasks_for_story(story_id)
# Then start implementation
```

### ❌ DON'T: Track Tasks Only in Markdown

```markdown
# WRONG - Tasks only in markdown file
## Implementation Tasks
- [x] Task 1: ...
- [x] Task 2: ...
```

### ✅ DO: Create Tasks in OpenProject

```python
# CORRECT - Create tasks in OpenProject
for task in tasks:
    mcp_openproject_create_work_package(
        project_id=8,
        subject=task["subject"],
        type_id=36,  # Task
        parent_id=story_id,
    )
```

### ❌ DON'T: Skip Task Status Updates

```python
# WRONG - Not updating task status
# ... implement task ...
# ... mark story complete ...
```

### ✅ DO: Update Task Status as Work Progresses

```python
# CORRECT - Update task status
mcp_openproject_update_work_package(task_id, status_id=77)  # Start
# ... implement ...
mcp_openproject_update_work_package(task_id, status_id=79)  # Complete
```

## Retroactive Task Creation

**For Epic 3 and Epic 4 stories that were implemented without tasks:**

These stories should have tasks created retroactively for:
- Documentation purposes
- Future reference
- Completing the workflow

**However:** Going forward, ALL stories MUST have tasks created BEFORE implementation starts.

## Checklist: Before Starting Story Implementation

- [ ] Story acceptance criteria reviewed
- [ ] Tasks broken down (in markdown or planning doc)
- [ ] Tasks created in OpenProject
- [ ] Tasks linked to story (parent_id set)
- [ ] Tasks verified (get_work_package_children returns tasks)
- [ ] Task descriptions include acceptance criteria
- [ ] Ready to start implementation

## References

- **Dev Agent Instructions:** `docs/DEV_AGENT_INSTRUCTIONS.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **Task Management Process:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **OpenProject Integration:** See workspace rules for OpenProject MCP tools

## Enforcement

**This workflow is MANDATORY for all stories starting from Epic 5.**

**Violations:**
- If implementation starts without tasks → STOP and create tasks first
- If tasks are tracked only in markdown → Create them in OpenProject
- If task status is not updated → Update status as work progresses

**Exception:** Epic 3 and Epic 4 stories are exempt (retroactive task creation acceptable), but going forward this workflow must be followed.







