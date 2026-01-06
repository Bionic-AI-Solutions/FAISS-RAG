# Archon Integration for BMAD

This module provides integration with Archon as an **external knowledge repository only**.

## Overview

Archon is used **ONLY** for searching external knowledge:

✅ **USE Archon For:**
- External library documentation (React, FastAPI, PostgreSQL, etc.)
- Framework references and guides
- Code examples from public repositories
- Industry best practices and standards
- Research findings from external sources

❌ **DO NOT USE Archon For:**
- Project documents (use OpenProject attachments)
- PRDs, architecture docs (use OpenProject attachments)
- Technical specifications (use OpenProject attachments)
- Any project-specific artifacts (use OpenProject attachments)

**All project documents must be stored as OpenProject attachments at the appropriate work package level.**

## Quick Setup

Archon requires minimal setup since it's only used for searching existing knowledge sources.

### 1. Get Available Knowledge Sources

```python
# List available external documentation sources
sources = mcp_archon_rag_get_available_sources()
# Note the source IDs for documentation you frequently reference
```

### 2. Update Configuration (Optional)

Edit `_bmad/_config/project-config.yaml`:

```yaml
archon:
  enabled: true
  
  rag:
    default_match_count: 5
    preferred_sources:               # ← Sources you use frequently
      - "src_abc123"                 # e.g., React docs
      - "src_def456"                 # e.g., FastAPI docs
```

## Files in This Module

| File | Purpose |
|------|---------|
| `tools.md` | Complete MCP tool reference for knowledge search |
| `workflow.md` | Research-first development workflow |
| `README.md` | This setup guide |

## Core Workflow: Research External Knowledge

```
1. IDENTIFY    → What EXTERNAL knowledge do I need?
2. SEARCH      → mcp_archon_rag_search_knowledge_base(query, ...)
3. EXAMPLES    → mcp_archon_rag_search_code_examples(query, ...)
4. READ        → mcp_archon_rag_read_full_page(page_id)
5. IMPLEMENT   → Use external knowledge in implementation
6. DOCUMENT    → Store project docs in OpenProject (NOT Archon)
```

## System Responsibilities

| System | Responsibility |
|--------|----------------|
| **OpenProject** | Work management + ALL project documents (attachments) |
| **Archon** | Search EXTERNAL knowledge only (no project storage) |

## Common Tasks

### Search External Documentation
```python
# Search for library/framework documentation
results = mcp_archon_rag_search_knowledge_base(
    query="authentication JWT",  # Keep queries SHORT (2-5 words)
    match_count=5
)
```

### Find Code Examples
```python
# Find implementation patterns from external sources
examples = mcp_archon_rag_search_code_examples(
    query="FastAPI middleware",
    match_count=3
)
```

### Search Specific Documentation Source
```python
# Get available sources
sources = mcp_archon_rag_get_available_sources()

# Search within specific documentation
results = mcp_archon_rag_search_knowledge_base(
    query="hooks state",
    source_id="src_react_docs",  # Filter to React docs only
    match_count=5
)
```

## What NOT To Do

```python
# ❌ WRONG - Don't store project documents in Archon
mcp_archon_manage_document(
    action="create",
    project_id=archon_id,
    title="My Project Architecture",  # DON'T DO THIS
    content={"markdown": "..."}
)

# ✅ CORRECT - Store project documents as OpenProject attachments
# Upload architecture doc to Feature work package in OpenProject
```

## Troubleshooting

### Poor Search Results

- **Shorten your query** to 2-5 keywords
- Try different keyword combinations
- Use source filtering if you know which documentation to search

### Source ID Not Working

- Source IDs are internal identifiers (e.g., "src_abc123")
- NOT URLs or domain names
- Run `mcp_archon_rag_get_available_sources()` to get current IDs

## Related Documentation

- See `workflow.md` for research workflow patterns
- See `tools.md` for complete tool reference
- See `_bmad/integrations/openproject/` for work management AND document storage
