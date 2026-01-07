#!/usr/bin/env python3
"""
Create missing Epic 3, Epic 4 epics, their stories, and all tasks for Epics 3, 4, 5, and 6.

This script:
1. Creates Epic 3 and Epic 4 epics (if they don't exist)
2. Creates all stories for Epic 3 and Epic 4 (if they don't exist)
3. Creates all tasks for Epic 3, 4, 5, and 6 stories
"""

import json
import sys
from typing import List, Dict, Any

# Project ID
PROJECT_ID = 8

# Work Package Type IDs
EPIC_TYPE_ID = 40
STORY_TYPE_ID = 41
TASK_TYPE_ID = 36

# Status IDs
STATUS_NEW = 71
STATUS_CLOSED = 82

# Priority IDs
PRIORITY_NORMAL = 73
PRIORITY_HIGH = 74


def create_epic_3_stories() -> List[Dict[str, Any]]:
    """Return Epic 3 story definitions."""
    return [
        {
            "subject": "Story 3.1: Document Ingestion MCP Tool",
            "type_id": STORY_TYPE_ID,
            "description": """As a **Tenant Admin**,
I want **to ingest documents into the knowledge base**,
So that **documents become searchable and available for RAG operations**.

**Acceptance Criteria:**
- Tool accepts: document_content (text, images, tables), document_metadata (title, source, type), tenant_id, optional document_id
- Tool extracts text content from documents
- Tool generates embeddings using tenant-configured embedding model
- Tool stores document in PostgreSQL documents table
- Tool stores document content in MinIO (tenant-scoped bucket)
- Tool indexes document in FAISS (tenant-scoped index)
- Tool indexes document in Meilisearch (tenant-scoped index)
- Tool returns document_id and ingestion status
- Access is restricted to Tenant Admin and End User roles
- Ingestion completes within <2s for typical documents""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_HIGH,
        },
        {
            "subject": "Story 3.2: Document Versioning",
            "type_id": STORY_TYPE_ID,
            "description": """As a **Tenant Admin**,
I want **documents to be versioned when updated**,
So that **I can track document changes and maintain history**.

**Acceptance Criteria:**
- New version is created with incremented version number
- Previous version is retained in document_versions table
- Document metadata includes current version number
- Version history is queryable
- FAISS and Meilisearch indices are updated with new version
- Old version embeddings are marked as deprecated""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_NORMAL,
        },
        {
            "subject": "Story 3.3: Document Deletion MCP Tool",
            "type_id": STORY_TYPE_ID,
            "description": """As a **Tenant Admin**,
I want **to delete documents from the knowledge base**,
So that **I can remove outdated or incorrect documents**.

**Acceptance Criteria:**
- Tool accepts: document_id, tenant_id
- Tool validates document belongs to tenant (tenant isolation)
- Tool removes document from FAISS index (tenant-scoped)
- Tool removes document from Meilisearch index (tenant-scoped)
- Tool marks document as deleted in PostgreSQL (soft delete)
- Tool retains document in MinIO for recovery period (30 days)
- Access is restricted to Tenant Admin role only
- Deletion completes within <500ms""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_NORMAL,
        },
        {
            "subject": "Story 3.4: Document Retrieval MCP Tool",
            "type_id": STORY_TYPE_ID,
            "description": """As a **User**,
I want **to retrieve specific documents from the knowledge base**,
So that **I can access document content and metadata**.

**Acceptance Criteria:**
- Tool accepts: document_id, tenant_id
- Tool validates document belongs to tenant (tenant isolation)
- Tool retrieves document metadata from PostgreSQL
- Tool retrieves document content from MinIO
- Tool returns complete document with metadata and content
- Access is available to Tenant Admin and End User roles
- Retrieval completes within <200ms (p95)""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_NORMAL,
        },
        {
            "subject": "Story 3.5: Document Listing MCP Tool",
            "type_id": STORY_TYPE_ID,
            "description": """As a **User**,
I want **to list documents in the knowledge base**,
So that **I can browse and discover available documents**.

**Acceptance Criteria:**
- Tool accepts: tenant_id, optional filters (document_type, source, date_range), pagination parameters
- Tool returns list of documents with metadata
- Tool supports pagination (cursor-based or limit/offset)
- Tool filters results by tenant_id (tenant isolation)
- Tool supports filtering by document_type, source, date_range
- Access is available to Tenant Admin and End User roles
- Listing completes within <200ms (p95)""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_NORMAL,
        },
    ]


def create_epic_4_stories() -> List[Dict[str, Any]]:
    """Return Epic 4 story definitions."""
    return [
        {
            "subject": "Story 4.1: FAISS Vector Search Implementation",
            "type_id": STORY_TYPE_ID,
            "description": """As a **User**,
I want **semantic vector search using FAISS**,
So that **I can find documents based on semantic similarity**.

**Acceptance Criteria:**
- Search query is converted to embedding using tenant-configured embedding model
- Embedding is searched in tenant-scoped FAISS index
- Results are ranked by cosine similarity (or configured distance metric)
- Top K results are returned (default K=10, configurable)
- Response time is <150ms (p95) for vector search
- Search accuracy is >90% (relevant results in top 5)""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_HIGH,
        },
        {
            "subject": "Story 4.2: Meilisearch Keyword Search Implementation",
            "type_id": STORY_TYPE_ID,
            "description": """As a **User**,
I want **keyword search using Meilisearch**,
So that **I can find documents using exact keyword matching**.

**Acceptance Criteria:**
- Search query is sent to tenant-scoped Meilisearch index
- Meilisearch performs full-text search with ranking
- Results are ranked by relevance score
- Top K results are returned (default K=10, configurable)
- Response time is <100ms (p95) for keyword search""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_HIGH,
        },
        {
            "subject": "Story 4.3: Hybrid Retrieval Engine",
            "type_id": STORY_TYPE_ID,
            "description": """As a **User**,
I want **hybrid retrieval combining vector and keyword search**,
So that **I get the best results from both semantic and keyword matching**.

**Acceptance Criteria:**
- Vector search results are retrieved from FAISS
- Keyword search results are retrieved from Meilisearch
- Results are merged and deduplicated by document_id
- Results are re-ranked using combined relevance score (weighted combination)
- Final ranked results are returned
- Response time is <200ms (p95) for hybrid search
- Three-tier fallback: FAISS + Meilisearch → FAISS only → Meilisearch only""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_HIGH,
        },
        {
            "subject": "Story 4.4: RAG Search MCP Tool",
            "type_id": STORY_TYPE_ID,
            "description": """As a **User**,
I want **to search the knowledge base via MCP tool**,
So that **I can retrieve relevant documents for RAG operations**.

**Acceptance Criteria:**
- Tool accepts: search_query (text), tenant_id, user_id, optional filters
- Tool performs hybrid retrieval (vector + keyword)
- Tool returns ranked list of relevant documents with metadata
- Tool supports optional filters for document_type, date_range, tags
- Access is available to Tenant Admin and End User roles
- Response time is <200ms (p95) for voice interactions
- Search accuracy is >90% (relevant results in top 5)""",
            "status_id": STATUS_CLOSED,
            "priority_id": PRIORITY_HIGH,
        },
    ]


def main():
    """Main execution function."""
    print("=" * 80)
    print("Creating Missing Epics, Stories, and Tasks for Epics 3, 4, 5, and 6")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Create Epic 3 and Epic 4 epics")
    print("2. Create all stories for Epic 3 and Epic 4")
    print("3. Create all tasks for Epic 3, 4, 5, and 6 stories")
    print("\nNote: This script uses MCP tools. Run it from within a context that has")
    print("access to mcp_openproject_* tools.")
    print("\n" + "=" * 80)
    
    # Note: This script needs to be executed in a context with MCP tools available
    # The actual creation will be done via MCP tool calls, not direct API calls
    print("\n⚠️  This script defines the structure but requires MCP tool execution.")
    print("   Please use the MCP tools directly or adapt this script to use")
    print("   the OpenProject API client.")
    
    # Print story definitions for reference
    print("\nEpic 3 Stories:")
    for i, story in enumerate(create_epic_3_stories(), 1):
        print(f"  {i}. {story['subject']}")
    
    print("\nEpic 4 Stories:")
    for i, story in enumerate(create_epic_4_stories(), 1):
        print(f"  {i}. {story['subject']}")
    
    print("\n" + "=" * 80)
    print("Script structure ready. Execute via MCP tools or API client.")


if __name__ == "__main__":
    main()








