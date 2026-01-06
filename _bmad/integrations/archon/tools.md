# Archon MCP Tools Reference

This document provides the reference for Archon MCP tools used for **searching external knowledge** in BMAD workflows.

## CRITICAL: Archon Scope

✅ **USE Archon For (Search Only):**

- External library documentation
- Framework references and guides
- Code examples from public repositories
- Industry best practices
- Research from external sources

❌ **DO NOT USE Archon For:**

- Storing project documents (use OpenProject attachments)
- PRDs, architecture docs (use OpenProject attachments)
- Any project-specific artifacts (use OpenProject attachments)

**All project documents must be stored as OpenProject attachments at the appropriate work package level.**

## Configuration

Archon settings in `_bmad/_config/project-config.yaml`:

```yaml
archon:
  enabled: true
  rag:
    default_match_count: 5
    preferred_sources: [] # Source IDs for frequently used docs
```

**Setup:** Get knowledge sources with `mcp_archon_rag_get_available_sources()`

## Tool Categories

### Health & Session

| Tool                        | Description             |
| --------------------------- | ----------------------- |
| `mcp_archon_health_check()` | Check MCP server health |
| `mcp_archon_session_info()` | Get session information |

### Document Management (NOT FOR PROJECT DOCS)

⚠️ **WARNING:** These tools exist but should NOT be used for project documents. Store project documents as OpenProject attachments instead.

| Tool                                                  | Description                   | Parameters                      |
| ----------------------------------------------------- | ----------------------------- | ------------------------------- |
| `mcp_archon_find_documents(project_id, ...)`          | List/search/get documents     | `project_id` required           |
| `mcp_archon_manage_document(action, project_id, ...)` | Create/update/delete document | `action`, `project_id` required |

**Use Case:** Only for managing curated external reference materials, NOT project-specific documents.

### RAG Knowledge Base

| Tool                                                   | Description            | Parameters           |
| ------------------------------------------------------ | ---------------------- | -------------------- |
| `mcp_archon_rag_get_available_sources()`               | List knowledge sources | None                 |
| `mcp_archon_rag_search_knowledge_base(query, ...)`     | Search knowledge       | `query` required     |
| `mcp_archon_rag_search_code_examples(query, ...)`      | Find code examples     | `query` required     |
| `mcp_archon_rag_list_pages_for_source(source_id, ...)` | List pages in source   | `source_id` required |
| `mcp_archon_rag_read_full_page(page_id, url)`          | Get full page content  | `page_id` or `url`   |

### Version Management

| Tool                                                             | Description            | Parameters                                    |
| ---------------------------------------------------------------- | ---------------------- | --------------------------------------------- |
| `mcp_archon_find_versions(project_id, ...)`                      | List version history   | `project_id` required                         |
| `mcp_archon_manage_version(action, project_id, field_name, ...)` | Create/restore version | `action`, `project_id`, `field_name` required |

### Feature Tracking

| Tool                                          | Description          | Parameters            |
| --------------------------------------------- | -------------------- | --------------------- |
| `mcp_archon_get_project_features(project_id)` | Get project features | `project_id` required |

## RAG Search Best Practices

### CRITICAL: Keep Queries Short!

Vector search works best with **2-5 keywords**, not long sentences.

**✅ GOOD Queries:**

```python
mcp_archon_rag_search_knowledge_base(query="vector search pgvector")
mcp_archon_rag_search_knowledge_base(query="authentication JWT")
mcp_archon_rag_search_code_examples(query="React useState")
mcp_archon_rag_search_code_examples(query="FastAPI middleware")
```

**❌ BAD Queries:**

```python
# Too long - won't return good results
mcp_archon_rag_search_knowledge_base(
    query="how to implement vector search with pgvector in PostgreSQL for semantic similarity matching with OpenAI embeddings"
)

# Too many terms - pick the most important 2-5
mcp_archon_rag_search_code_examples(
    query="React hooks useState useEffect useContext useReducer useMemo useCallback"
)
```

### Searching Specific Sources

When you need documentation from a specific source:

```python
# Step 1: Get available sources
sources = mcp_archon_rag_get_available_sources()

# Step 2: Find the source ID you need
# Example: Looking for "Supabase" docs → find "src_abc123"

# Step 3: Search with source filter
results = mcp_archon_rag_search_knowledge_base(
    query="vector functions",
    source_id="src_abc123",  # Filter to specific source
    match_count=5
)
```

### Reading Full Pages

After searching, get complete page content:

```python
# From search results, get page_id
results = mcp_archon_rag_search_knowledge_base(query="authentication")

# Read full page content
full_page = mcp_archon_rag_read_full_page(
    page_id=results["results"][0]["page_id"]
)
```

## Document Management Patterns

### Creating Project Documentation

```python
# Create knowledge project (if not exists)
project = mcp_archon_manage_project(
    action="create",
    title="My Project - Knowledge Base",
    description="Technical documentation and research",
    github_repo="https://github.com/org/repo"
)
archon_project_id = project["project"]["id"]

# Store architecture document
mcp_archon_manage_document(
    action="create",
    project_id=archon_project_id,
    title="Architecture Document",
    document_type="spec",
    content={"markdown": "# Architecture\n\n..."},
    tags=["architecture", "technical-design"]
)
```

### Linking to OpenProject

When storing documents, include OpenProject references:

```python
mcp_archon_manage_document(
    action="create",
    project_id=archon_project_id,
    title="Epic 1: Technical Specification",
    document_type="spec",
    content={
        "markdown": f"""
        # Technical Specification

        {spec_content}

        ---

        **OpenProject References:**
        - Project ID: {op_project_id}
        - Epic Work Package: {epic_id}
        - Related Stories: {story_ids}
        """
    },
    tags=["epic-1", "architecture", "openproject-linked"]
)
```

### Updating Documents

```python
# Find existing document
docs = mcp_archon_find_documents(
    project_id=archon_project_id,
    query="Architecture"
)

# Update with new content
mcp_archon_manage_document(
    action="update",
    project_id=archon_project_id,
    document_id=docs["documents"][0]["id"],
    content={"markdown": "# Updated Architecture\n\n..."}
)
```

## Common Usage Patterns

### Research Before Implementation

```python
# 1. Search knowledge base for relevant info
research = mcp_archon_rag_search_knowledge_base(
    query="authentication patterns",
    match_count=5
)

# 2. Find code examples
examples = mcp_archon_rag_search_code_examples(
    query="JWT middleware",
    match_count=3
)

# 3. Read full pages for detailed information
for result in research["results"][:2]:
    full_content = mcp_archon_rag_read_full_page(
        page_id=result["page_id"]
    )
    # Use content for implementation
```

### Documenting Implementation Decisions

```python
# Store technical decision
mcp_archon_manage_document(
    action="create",
    project_id=archon_project_id,
    title="ADR-001: Database Selection",
    document_type="note",
    content={
        "markdown": """
        # ADR-001: Database Selection

        ## Context
        We need to choose a database for...

        ## Decision
        We will use PostgreSQL because...

        ## Consequences
        - Benefit 1
        - Trade-off 1
        """
    },
    tags=["adr", "database", "architecture-decision"]
)
```

### Browsing Documentation Structure

```python
# List all pages in a knowledge source
pages = mcp_archon_rag_list_pages_for_source(
    source_id="src_abc123",
    section="# Getting Started"  # Optional filter
)

# Read specific pages
for page in pages["pages"]:
    content = mcp_archon_rag_read_full_page(page_id=page["id"])
```

## Integration with BMAD Agents

| Agent           | Archon Usage                                   |
| --------------- | ---------------------------------------------- |
| **PM**          | Store product briefs, PRDs, research findings  |
| **Architect**   | Store architecture docs, technical specs, ADRs |
| **Dev**         | Search code examples, reference documentation  |
| **Tech Writer** | Create and update project documentation        |
| **TEA**         | Store test strategies, test case documentation |

## Troubleshooting

### No Results from Search

- **Shorten your query** to 2-5 keywords
- Check if source exists: `mcp_archon_rag_get_available_sources()`
- Try different keyword combinations

### Source ID Not Found

- Run `mcp_archon_rag_get_available_sources()` to get current source IDs
- Source IDs are NOT URLs - they're internal identifiers like "src_abc123"

### Document Not Saving

- Ensure you have a valid `project_id` (UUID format)
- Check the `content` field is a dict with "markdown" key
- Verify `document_type` is valid: spec/design/note/prp/api/guide
