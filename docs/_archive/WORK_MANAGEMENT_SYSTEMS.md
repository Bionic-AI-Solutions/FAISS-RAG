# Work Management Systems - mem0-rag Project

## System Architecture

This project uses a clear separation between work management and knowledge management:

### OpenProject - PRIMARY Work Management System

**Purpose**: All work tracking, epics, stories, tasks, status management

**Used For:**
- Project creation and management
- Epic creation and tracking
- Feature creation and tracking
- User Story creation and tracking
- Task creation and tracking
- Work package status updates
- Priority management
- Assignment and workload tracking
- Sprint planning
- Progress reporting

**MCP Tools:**
- `mcp_openproject_list_projects()` - List projects
- `mcp_openproject_create_project()` - Create project
- `mcp_openproject_list_work_packages()` - List work packages
- `mcp_openproject_create_work_package()` - Create epic/story/task
- `mcp_openproject_update_work_package()` - Update work package
- `mcp_openproject_get_work_package()` - Get work package details
- `mcp_openproject_delete_work_package()` - Delete work package

### Archon - Knowledge Repository ONLY

**Purpose**: Documents, research, knowledge base, code examples

**Used For:**
- Project documentation storage
- Technical specifications
- Architecture documents
- Research notes
- Knowledge base search
- Code example search
- Document versioning

**NOT Used For:**
- ❌ Task management
- ❌ Work tracking
- ❌ Status management
- ❌ Epic/story management

**MCP Tools:**
- `mcp_archon_find_projects()` - List projects (for knowledge organization)
- `mcp_archon_find_documents()` - List documents
- `mcp_archon_manage_document()` - Create/update/delete documents
- `mcp_archon_rag_get_available_sources()` - List knowledge sources
- `mcp_archon_rag_search_knowledge_base()` - Search knowledge base
- `mcp_archon_rag_search_code_examples()` - Find code examples

## Workflow Guidelines

### Creating New Work

1. **Create in OpenProject** (PRIMARY)
   ```python
   # Create epic
   mcp_openproject_create_work_package(
       project_id=8,
       subject="Epic 1: Secure Platform Foundation",
       type_id=38,  # Summary task (Epic)
       description="...",
       priority_id=74  # High
   )
   
   # Create story
   mcp_openproject_create_work_package(
       project_id=8,
       subject="Story 1.1: Project Structure Setup",
       type_id=36,  # Task (Story)
       description="...",
       priority_id=73  # Normal
   )
   ```

2. **Optionally Store Documentation in Archon** (Knowledge Repository)
   ```python
   # Store related documentation
   mcp_archon_manage_document(
       action="create",
       project_id=archon_project_id,
       title="Epic 1: Technical Specification",
       document_type="spec",
       content={"markdown": "..."},
       tags=["epic-1"]
   )
   ```

### Updating Work Status

**ALWAYS update in OpenProject:**

```python
# Update work package status
mcp_openproject_update_work_package(
    work_package_id=work_package_id,
    status_id=77,  # In progress
    percentage_done=50
)
```

### Research Before Implementation

**Use Archon knowledge base:**

```python
# Search knowledge base
mcp_archon_rag_search_knowledge_base(
    query="authentication JWT",
    match_count=5
)

# Find code examples
mcp_archon_rag_search_code_examples(
    query="FastAPI middleware",
    match_count=3
)
```

## Team Member Responsibilities

### Product Manager (PM)
- ✅ Create and manage epics in OpenProject
- ✅ Create and manage stories in OpenProject
- ✅ Sync epics.md to OpenProject
- ✅ Track work progress in OpenProject
- ✅ Store project documentation in Archon (optional)

### Scrum Master (SM)
- ✅ Manage sprint planning in OpenProject
- ✅ Track story status in OpenProject
- ✅ Coordinate work assignments in OpenProject
- ✅ Use Archon for research and knowledge base

### Developer (Dev)
- ✅ Get work packages from OpenProject
- ✅ Update work package status in OpenProject
- ✅ Research using Archon knowledge base
- ✅ Store technical documentation in Archon (optional)

### Architect
- ✅ Review epics/stories in OpenProject
- ✅ Store architecture documents in Archon
- ✅ Search knowledge base in Archon for patterns

## Key Principles

1. **OpenProject = ALL Work Management** - Everything related to work tracking goes here
2. **Archon = Knowledge Repository ONLY** - Documents, research, knowledge base
3. **No Task Management in Archon** - All tasks are in OpenProject
4. **Clear Separation** - Work management vs. knowledge management
5. **BMAD Compliance** - Follow BMAD methodology using OpenProject work packages

## Migration Notes

**Previous System (Deprecated):**
- Archon was used for task management
- OpenProject was used for high-level planning only

**Current System:**
- OpenProject is PRIMARY for all work management
- Archon is ONLY for knowledge/document management
- No task synchronization needed
- Clear separation of concerns















