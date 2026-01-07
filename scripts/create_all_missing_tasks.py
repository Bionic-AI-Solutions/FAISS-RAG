#!/usr/bin/env python3
"""
Create tasks for all stories after Story 1.7 in OpenProject.

This script creates tasks for:
- Epic 1: Stories 1.8-1.13
- Epic 2: Stories 2.1-2.5
- Epic 3: Stories 3.1-3.5 (using existing task definitions)
- Epic 4: Stories 4.1-4.4 (using existing task definitions)
- Epic 5: Stories 5.2-5.4 (Story 5.1 already has tasks)
- Epic 7: Stories 7.1-7.4
- Epic 8: Stories 8.1-8.5
- Epic 9: Stories 9.1-9.9
"""

import json
from typing import List, Dict, Any

# Project ID
PROJECT_ID = 8

# Work Package Type IDs
TASK_TYPE_ID = 36

# Status IDs
STATUS_NEW = 71
STATUS_CLOSED = 82

# Priority IDs
PRIORITY_NORMAL = 73
PRIORITY_HIGH = 74

# Story IDs (need to be fetched from OpenProject)
# These will be populated by querying OpenProject
STORY_IDS = {
    # Epic 1
    "1.8": None,  # Story 1.8: Audit Logging Infrastructure
    "1.9": None,  # Story 1.9: Rate Limiting Middleware
    "1.10": None,  # Story 1.10: Error Handling Framework
    "1.11": None,  # Story 1.11: Health Check Endpoints
    "1.12": None,  # Story 1.12: Basic Backup Operations
    "1.13": None,  # Story 1.13: Observability Integration (Langfuse)
    
    # Epic 2
    "2.1": None,  # Story 2.1: Domain Template Management
    "2.2": None,  # Story 2.2: Template Discovery MCP Tool
    "2.3": None,  # Story 2.3: Tenant Registration MCP Tool
    "2.4": None,  # Story 2.4: Tenant Model Configuration MCP Tool
    "2.5": None,  # Story 2.5: Tenant Data Isolation Validation
    
    # Epic 3
    "3.1": 389,  # Story 3.1: Document Ingestion MCP Tool
    "3.2": 390,  # Story 3.2: Document Versioning
    "3.3": 391,  # Story 3.3: Document Deletion MCP Tool
    "3.4": 392,  # Story 3.4: Document Retrieval MCP Tool
    "3.5": 393,  # Story 3.5: Document Listing MCP Tool
    
    # Epic 4
    "4.1": 394,  # Story 4.1: FAISS Vector Search Implementation
    "4.2": 395,  # Story 4.2: Meilisearch Keyword Search Implementation
    "4.3": 396,  # Story 4.3: Hybrid Retrieval Engine
    "4.4": 398,  # Story 4.4: RAG Search MCP Tool
    
    # Epic 5
    "5.1": 140,  # Story 5.1: Mem0 Integration Layer (already has tasks)
    "5.2": 141,  # Story 5.2: User Memory Retrieval MCP Tool
    "5.3": 142,  # Story 5.3: User Memory Update MCP Tool
    "5.4": 143,  # Story 5.4: User Memory Search MCP Tool
    
    # Epic 7
    "7.1": 150,  # Story 7.1: Tenant Backup MCP Tool
    "7.2": 151,  # Story 7.2: Tenant Restore MCP Tool
    "7.3": 152,  # Story 7.3: FAISS Index Rebuild MCP Tool
    "7.4": 153,  # Story 7.4: Backup Validation MCP Tool
    
    # Epic 8
    "8.1": 155,  # Story 8.1: Usage Statistics MCP Tool
    "8.2": 156,  # Story 8.2: Search Analytics MCP Tool
    "8.3": 157,  # Story 8.3: Memory Analytics MCP Tool
    "8.4": 158,  # Story 8.4: System Health Monitoring MCP Tool
    "8.5": 159,  # Story 8.5: Tenant Health Monitoring MCP Tool
    
    # Epic 9
    "9.1": 161,  # Story 9.1: HIPAA Compliance Support
    "9.2": 162,  # Story 9.2: SOC 2 Compliance Support
    "9.3": 163,  # Story 9.3: GDPR Compliance Support
    "9.4": 164,  # Story 9.4: Tenant Data Export MCP Tool
    "9.5": 165,  # Story 9.5: User Data Export MCP Tool
    "9.6": 166,  # Story 9.6: Tenant Configuration Update MCP Tool
    "9.7": 167,  # Story 9.7: Tenant Deletion MCP Tool
    "9.8": 168,  # Story 9.8: Subscription Tier Management
    "9.9": 169,  # Story 9.9: Project Admin Role Support
}

def create_epic3_tasks() -> List[Dict[str, Any]]:
    """Create tasks for Epic 3 stories (from create_epic3_epic4_tasks.py)."""
    # Story 3.1: Document Ingestion MCP Tool (389)
    story_3_1_tasks = [
        {
            "subject": "Task 3.1.1: Create embedding service for generating embeddings",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Create EmbeddingService class that retrieves tenant-configured embedding model and generates embeddings using OpenAI API.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.2: Add document addition methods to FAISS manager",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Extend FAISSIndexManager with add_document() method and document ID to FAISS ID mapping.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.3: Add document addition methods to Meilisearch client",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Extend Meilisearch client with add_document_to_index() function for tenant-scoped indexing.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.4: Create rag_ingest MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Implement rag_ingest MCP tool that accepts document_content and document_metadata, validates input, generates embeddings, and stores in all systems.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.5: Implement text extraction and content processing",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Implement content processing including text extraction, content hashing (SHA-256) for deduplication, and content validation.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.6: Implement MinIO document storage",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Implement MinIO storage to upload document content to tenant-scoped bucket and return object path.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Write comprehensive unit tests for rag_ingest tool including authorization, duplicate detection, versioning, and error handling.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.8: Write integration tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Write integration tests (deferred - unit tests cover functionality).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.1.10: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 389,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 3.2: Document Versioning (390)
    story_3_2_tasks = [
        {
            "subject": "Task 3.2.1: Create DocumentVersion model",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Create DocumentVersion model with version_id, document_id, version_number, content_hash, and change_summary fields.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.2: Create DocumentVersionRepository",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Create DocumentVersionRepository with methods for getting versions for a document and getting specific version by version_number.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.3: Add version_number and deleted_at fields to Document model",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Add version_number (default 1) and deleted_at (nullable) fields to Document model.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.4: Create database migration for document_versions table",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Create Alembic migration (005_add_document_versioning.py) to create document_versions table.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.5: Implement versioning logic in rag_ingest tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Implement versioning logic that creates DocumentVersion records when document content changes and increments version_number.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.6: Update FAISS and Meilisearch indices when version changes",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Update FAISS and Meilisearch indices with new version when document content changes.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.7: Write unit tests for versioning",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Write unit tests for document versioning including version creation, version retrieval, and version history.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.2.8: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 390,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 3.3: Document Deletion MCP Tool (391)
    story_3_3_tasks = [
        {
            "subject": "Task 3.3.1: Create rag_delete_document MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Implement rag_delete_document MCP tool that accepts document_id and performs soft delete.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.3.2: Implement tenant isolation validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Implement validation to ensure document belongs to tenant before deletion.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.3.3: Implement FAISS document removal",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Remove document from tenant-scoped FAISS index using faiss_manager.delete_document().",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.3.4: Implement Meilisearch document removal",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Remove document from tenant-scoped Meilisearch index using delete_document_from_index().",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.3.5: Implement PostgreSQL soft delete",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Mark document as deleted in PostgreSQL by setting deleted_at timestamp (soft delete).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.3.6: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Write unit tests for rag_delete_document including authorization, tenant isolation, and soft delete verification.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.3.7: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 391,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 3.4: Document Retrieval MCP Tool (392)
    story_3_4_tasks = [
        {
            "subject": "Task 3.4.1: Create rag_get_document MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 392,
            "description": "Implement rag_get_document MCP tool that accepts document_id and returns complete document.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.4.2: Implement tenant isolation validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 392,
            "description": "Implement validation to ensure document belongs to tenant before retrieval.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.4.3: Implement PostgreSQL metadata retrieval",
            "type_id": TASK_TYPE_ID,
            "parent_id": 392,
            "description": "Retrieve document metadata from PostgreSQL documents table.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.4.4: Implement MinIO content retrieval",
            "type_id": TASK_TYPE_ID,
            "parent_id": 392,
            "description": "Retrieve document content from MinIO tenant-scoped bucket using get_document_content().",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.4.5: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 392,
            "description": "Write unit tests for rag_get_document including authorization, tenant isolation, and content retrieval.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.4.6: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 392,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 3.5: Document Listing MCP Tool (393)
    story_3_5_tasks = [
        {
            "subject": "Task 3.5.1: Create rag_list_documents MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Implement rag_list_documents MCP tool that accepts filters and pagination parameters.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.5.2: Implement tenant isolation filtering",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Implement filtering to ensure only tenant's documents are returned.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.5.3: Implement pagination (limit/offset)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Implement pagination support using limit and offset parameters.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.5.4: Implement filtering by document_type, source, date_range",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Implement filtering support for document_type, source, and date_range parameters.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.5.5: Implement search query support",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Implement optional search query parameter for filtering documents by title or content preview.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.5.6: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Write unit tests for rag_list_documents including authorization, filtering, pagination, and search query.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 3.5.7: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 393,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    return story_3_1_tasks + story_3_2_tasks + story_3_3_tasks + story_3_4_tasks + story_3_5_tasks


def create_epic4_tasks() -> List[Dict[str, Any]]:
    """Create tasks for Epic 4 stories (from create_epic3_epic4_tasks.py)."""
    # Story 4.1: FAISS Vector Search Implementation (394)
    story_4_1_tasks = [
        {
            "subject": "Task 4.1.1: Add search method to FAISSIndexManager",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Add search() method to FAISSIndexManager that performs vector search in tenant-scoped FAISS index and returns FAISS IDs with similarity scores.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.2: Create VectorSearchService for high-level search interface",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Create VectorSearchService that generates query embeddings, performs FAISS search, and resolves FAISS IDs to document IDs.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.3: Implement FAISS ID to document ID resolution",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Implement mapping from FAISS internal IDs to document UUIDs using _document_id_map and database queries.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.4: Handle different distance metrics (L2, Inner Product)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Support both IndexFlatL2 (L2 distance) and IndexFlatIP (Inner Product) index types.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.5: Convert distances to similarity scores",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Convert FAISS distances to normalized similarity scores [0, 1] for consistent ranking.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.6: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Write unit tests for FAISS vector search including search functionality, ID resolution, and tenant isolation.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.7: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.1.8: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 394,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 4.2: Meilisearch Keyword Search Implementation (395)
    story_4_2_tasks = [
        {
            "subject": "Task 4.2.1: Add search_documents function to Meilisearch client",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Add search_documents() function to Meilisearch client that performs keyword search in tenant-scoped index.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.2: Create KeywordSearchService for high-level search interface",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Create KeywordSearchService that processes query text, performs Meilisearch search, and returns ranked document IDs.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.3: Implement tenant-scoped index search",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Ensure all searches are performed only in tenant's Meilisearch index with tenant_id filter.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.4: Support optional filters (document_type, tags)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Support optional filters for document_type and tags in Meilisearch search queries.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.5: Return ranked results with relevance scores",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Return ranked results sorted by Meilisearch relevance score (normalized 0-1 range).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.6: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Write unit tests for Meilisearch keyword search including search functionality, filtering, and tenant isolation.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.7: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.2.8: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 395,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 4.3: Hybrid Retrieval Engine (396)
    story_4_3_tasks = [
        {
            "subject": "Task 4.3.1: Create HybridSearchService",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Create HybridSearchService class that combines vector and keyword search results.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.2: Implement concurrent vector and keyword search",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Implement concurrent execution of vector and keyword search using asyncio.gather() for performance.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.3: Implement result merging and deduplication",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Merge results from both sources and deduplicate by document_id, keeping highest relevance score.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.4: Implement weighted re-ranking",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Implement weighted re-ranking using configurable weights (default: 60% vector, 40% keyword).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.5: Implement three-tier fallback mechanism",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Implement three-tier fallback: FAISS+Meilisearch → FAISS only → Meilisearch only.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.6: Add timeout handling (500ms threshold)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Add timeout handling that triggers fallback when search takes >500ms.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.7: Add error handling and logging",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Add comprehensive error handling and logging for service degradation alerts.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Write unit tests for hybrid search including fallback scenarios, result merging, and re-ranking.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.3.10: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 396,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 4.4: RAG Search MCP Tool (398)
    story_4_4_tasks = [
        {
            "subject": "Task 4.4.1: Create rag_search MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Create rag_search MCP tool that accepts search_query and optional filters.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.2: Integrate HybridSearchService",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Integrate HybridSearchService to perform hybrid retrieval (vector + keyword).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.3: Implement filter support (document_type, date_range, tags)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Implement filter support for document_type, date_range (date_from/date_to), and tags.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.4: Retrieve document metadata from database",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Retrieve document metadata from PostgreSQL for search results to include title, metadata, timestamp.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.5: Generate content snippets",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Generate content snippets from document content for search results (using _generate_snippet helper).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.6: Return ranked results with metadata",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Return ranked list of documents with document_id, title, snippet, relevance_score, source, timestamp, metadata.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.7: Add RBAC (Tenant Admin and End User)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Restrict access to Tenant Admin and End User roles only.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Write unit tests for rag_search including authorization, filtering, and result formatting.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 4.4.10: Update OpenProject status",
            "type_id": TASK_TYPE_ID,
            "parent_id": 398,
            "description": "Update story status in OpenProject to Closed.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    return story_4_1_tasks + story_4_2_tasks + story_4_3_tasks + story_4_4_tasks


def create_epic5_tasks() -> List[Dict[str, Any]]:
    """Create tasks for Epic 5 stories (5.2, 5.3, 5.4 - 5.1 already has tasks)."""
    # Story 5.2: User Memory Retrieval MCP Tool (141)
    story_5_2_tasks = [
        {
            "subject": "Task 5.2.1: Create mem0_get_user_memory MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Implement mem0_get_user_memory MCP tool that accepts user_id, tenant_id, optional memory_key, and optional filters.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.2: Implement memory retrieval from Mem0",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Retrieve memories from Mem0 (or Redis fallback) using tenant_id:user_id key format.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.3: Implement memory filtering",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Support filtering by memory_key or other criteria.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.4: Implement memory isolation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Ensure only memories for the specified user_id and tenant_id are returned. Prevent cross-user and cross-tenant memory access.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.5: Add RBAC (user's own memories or Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Restrict access to user's own memories (or Tenant Admin for management).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.6: Ensure response time <100ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Optimize memory retrieval to complete within <100ms (p95) for memory retrieval (FR-PERF-002).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Write comprehensive unit tests for mem0_get_user_memory including authorization, memory isolation, filtering, and performance.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.2.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 141,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 5.3: User Memory Update MCP Tool (142)
    story_5_3_tasks = [
        {
            "subject": "Task 5.3.1: Create mem0_update_memory MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Implement mem0_update_memory MCP tool that accepts user_id, tenant_id, memory_key, memory_value, and optional metadata.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.2: Implement memory create/update logic",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Create memory if it doesn't exist, update memory if it exists. Maintain version history (optional).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.3: Implement memory storage in Mem0",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Store memory in Mem0 (or Redis fallback) with tenant_id:user_id key format.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.4: Implement memory validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Validate memory key and value. Enforce memory size limits. Return structured error for invalid memory data.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.5: Add RBAC (user's own memories or Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Restrict access to user's own memories (or Tenant Admin for management).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.6: Ensure response time <100ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Optimize memory update to complete within <100ms (p95) for memory update (FR-PERF-002).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Write comprehensive unit tests for mem0_update_memory including authorization, memory validation, create/update logic, and performance.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.3.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 142,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    # Story 5.4: User Memory Search MCP Tool (143)
    story_5_4_tasks = [
        {
            "subject": "Task 5.4.1: Create mem0_search_memory MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Implement mem0_search_memory MCP tool that accepts user_id, tenant_id, search_query, and optional filters.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.2: Implement semantic memory search",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Search memories using semantic search (Mem0) or keyword search (Redis fallback).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.3: Implement result ranking",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Return relevant memory entries matching query, ranked by relevance.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.4: Implement memory filtering",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Support filtering by memory_key, timestamp, or other criteria.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.5: Add RBAC (user's own memories or Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Restrict access to user's own memories (or Tenant Admin for management).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.6: Ensure response time <100ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Optimize memory search to complete within <100ms (p95) for memory search (FR-PERF-002).",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Write comprehensive unit tests for mem0_search_memory including authorization, search functionality, filtering, ranking, and performance.",
            "status_id": STATUS_CLOSED,
        },
        {
            "subject": "Task 5.4.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": 143,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_CLOSED,
        },
    ]
    
    return story_5_2_tasks + story_5_3_tasks + story_5_4_tasks


def main():
    """Main execution function."""
    print("=" * 80)
    print("Creating Tasks for All Stories After Story 1.7")
    print("=" * 80)
    
    all_tasks = []
    
    # Epic 3 tasks
    epic3_tasks = create_epic3_tasks()
    all_tasks.extend(epic3_tasks)
    print(f"\nEpic 3 tasks: {len(epic3_tasks)}")
    
    # Epic 4 tasks
    epic4_tasks = create_epic4_tasks()
    all_tasks.extend(epic4_tasks)
    print(f"Epic 4 tasks: {len(epic4_tasks)}")
    
    # Epic 5 tasks (5.2, 5.3, 5.4)
    epic5_tasks = create_epic5_tasks()
    all_tasks.extend(epic5_tasks)
    print(f"Epic 5 tasks (5.2-5.4): {len(epic5_tasks)}")
    
    print(f"\nTotal tasks to create: {len(all_tasks)}")
    print("\n" + "=" * 80)
    print("Task definitions ready. Use MCP tools to create them in OpenProject.")
    print("=" * 80)
    
    # Output JSON for bulk creation
    tasks_json = json.dumps(all_tasks, indent=2)
    print("\nTasks JSON (first 1000 chars):")
    print(tasks_json[:1000] + "..." if len(tasks_json) > 1000 else tasks_json)
    
    return all_tasks


if __name__ == "__main__":
    main()




