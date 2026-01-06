# Archon External Knowledge Search Workflow

This workflow defines how BMAD agents use Archon for **searching external knowledge only**.

## CRITICAL: Archon Scope

✅ **USE Archon For:**

- Searching external library documentation
- Finding code examples from public sources
- Researching industry best practices
- Looking up framework references

❌ **DO NOT USE Archon For:**

- Storing project documents (use OpenProject attachments)
- PRDs, architecture docs (use OpenProject attachments)
- Any project-specific artifacts (use OpenProject attachments)

**All project documents must be stored as OpenProject attachments at the appropriate work package level.**

## Core Principle: Research External Knowledge

**RULE:** Search external knowledge bases before implementing new features.

```
┌─────────────────────────────────────────────────────────────────┐
│              EXTERNAL KNOWLEDGE RESEARCH WORKFLOW                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. IDENTIFY NEED                                                │
│     └── What EXTERNAL knowledge do I need?                      │
│                                                                  │
│  2. SEARCH KNOWLEDGE BASE                                        │
│     └── mcp_archon_rag_search_knowledge_base(query, ...)        │
│                                                                  │
│  3. FIND CODE EXAMPLES                                           │
│     └── mcp_archon_rag_search_code_examples(query, ...)         │
│                                                                  │
│  4. READ DETAILED CONTENT                                        │
│     └── mcp_archon_rag_read_full_page(page_id)                  │
│                                                                  │
│  5. IMPLEMENT WITH CONTEXT                                       │
│     └── Use external knowledge in implementation                 │
│                                                                  │
│  6. DOCUMENT IN OPENPROJECT                                      │
│     └── Store project docs as OpenProject attachments           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## What External Knowledge Is Available

Archon indexes external documentation sources such as:

- **Framework Docs**: React, FastAPI, Express, Django, etc.
- **Library Docs**: PostgreSQL, Redis, OpenAI, etc.
- **Platform Docs**: AWS, GCP, Azure, Kubernetes, etc.
- **Best Practices**: Security guidelines, design patterns, etc.

### Getting Available Sources

```python
# List all indexed external documentation
sources = mcp_archon_rag_get_available_sources()

# Returns:
# {
#   "sources": [
#     {"id": "src_abc123", "title": "React Documentation", "url": "..."},
#     {"id": "src_def456", "title": "FastAPI Docs", "url": "..."},
#     ...
#   ]
# }
```

## Research Workflow Patterns

### Pattern 1: General Knowledge Search

When you need to find information on a topic:

```python
# Search across all external knowledge
results = mcp_archon_rag_search_knowledge_base(
    query="authentication JWT",  # Keep queries SHORT (2-5 words)
    match_count=5
)

# Read full content of relevant pages
for result in results["results"][:2]:
    full_content = mcp_archon_rag_read_full_page(
        page_id=result["page_id"]
    )
```

### Pattern 2: Targeted Documentation Search

When you need information from specific documentation:

```python
# Step 1: Get available sources
sources = mcp_archon_rag_get_available_sources()

# Step 2: Find the source ID for React docs (example)
react_source_id = "src_abc123"  # From sources list

# Step 3: Search within that source only
results = mcp_archon_rag_search_knowledge_base(
    query="hooks state management",
    source_id=react_source_id,  # Filter to React docs only
    match_count=5
)
```

### Pattern 3: Find Code Examples

When you need implementation patterns:

```python
# Search for code examples
examples = mcp_archon_rag_search_code_examples(
    query="FastAPI dependency injection",
    match_count=5
)

# Examples include code snippets with context
for example in examples["results"]:
    print(f"Example: {example['title']}")
    print(f"Code: {example['content']}")
```

### Pattern 4: Browse Documentation Structure

When you want to explore a documentation source:

```python
# List all pages in a documentation source
pages = mcp_archon_rag_list_pages_for_source(
    source_id="src_abc123"
)

# Optionally filter by section
pages = mcp_archon_rag_list_pages_for_source(
    source_id="src_abc123",
    section="# Getting Started"
)

# Read specific pages
for page in pages["pages"][:5]:
    content = mcp_archon_rag_read_full_page(page_id=page["id"])
```

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
    query="how to implement vector search with pgvector in PostgreSQL for semantic similarity"
)

# Too many terms
mcp_archon_rag_search_code_examples(
    query="React hooks useState useEffect useContext useReducer useMemo useCallback"
)
```

## Agent-Specific Research Patterns

### Dev Agent

```python
# Before implementing a feature, research external patterns
knowledge = mcp_archon_rag_search_knowledge_base(
    query="authentication patterns",
    match_count=5
)

examples = mcp_archon_rag_search_code_examples(
    query="JWT middleware Python",
    match_count=3
)

# After implementation, store docs in OpenProject (NOT Archon)
# → Attach implementation notes to Task work package
```

### Architect Agent

```python
# Research architecture patterns from external sources
patterns = mcp_archon_rag_search_knowledge_base(
    query="microservices event driven",
    match_count=5
)

# Store architecture decisions in OpenProject (NOT Archon)
# → Attach architecture doc to Feature work package
```

### TEA Agent

```python
# Research testing patterns
test_patterns = mcp_archon_rag_search_knowledge_base(
    query="pytest fixtures async",
    match_count=5
)

test_examples = mcp_archon_rag_search_code_examples(
    query="integration testing FastAPI",
    match_count=3
)

# Store test documentation in OpenProject (NOT Archon)
# → Attach test strategy to Feature work package
```

## Document Storage Reminder

**Where to Store Project Documents:**

| Document Type        | Storage Location                             |
| -------------------- | -------------------------------------------- |
| Product Brief        | OpenProject → Project level attachment       |
| PRD                  | OpenProject → Project/Epic level attachment  |
| Architecture Doc     | OpenProject → Feature level attachment       |
| Technical Spec       | OpenProject → Feature/Story level attachment |
| Implementation Notes | OpenProject → Task level attachment          |
| Test Strategy        | OpenProject → Feature level attachment       |
| Test Cases           | OpenProject → Story level attachment         |

**Remember:** Archon is for SEARCHING external knowledge. OpenProject is for STORING project documents.

## Best Practices Summary

1. **Search First**: Always search external knowledge before implementing
2. **Short Queries**: Use 2-5 keywords for best results
3. **Source Filtering**: Use `source_id` when you know which docs to search
4. **Read Full Pages**: Get complete context with `rag_read_full_page`
5. **Store in OpenProject**: All project documents go to OpenProject attachments
6. **Never Store in Archon**: Don't use Archon for project-specific documents
