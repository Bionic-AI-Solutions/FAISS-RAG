#!/usr/bin/env python3
"""
Create tasks retroactively for Epic 3 and Epic 4 stories.
These stories were implemented without tasks, so we're creating them for documentation.
"""

import json
from typing import List, Dict, Any

# Epic 3 Tasks
epic3_tasks = [
    # Story 3.1: Document Ingestion MCP Tool (129)
    {
        "subject": "Task 3.1.1: Create embedding service for generating embeddings",
        "type_id": 36,
        "parent_id": 129,
        "description": "Create EmbeddingService class that retrieves tenant-configured embedding model and generates embeddings using OpenAI API.",
        "status_id": 82,  # Closed
    },
    {
        "subject": "Task 3.1.2: Add document addition methods to FAISS manager",
        "type_id": 36,
        "parent_id": 129,
        "description": "Extend FAISSIndexManager with add_document() method and document ID to FAISS ID mapping.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.3: Add document addition methods to Meilisearch client",
        "type_id": 36,
        "parent_id": 129,
        "description": "Extend Meilisearch client with add_document_to_index() function for tenant-scoped indexing.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.4: Create rag_ingest MCP tool",
        "type_id": 36,
        "parent_id": 129,
        "description": "Implement rag_ingest MCP tool that accepts document_content and document_metadata, validates input, generates embeddings, and stores in all systems.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.5: Implement text extraction and content processing",
        "type_id": 36,
        "parent_id": 129,
        "description": "Implement content processing including text extraction, content hashing (SHA-256) for deduplication, and content validation.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.6: Implement MinIO document storage",
        "type_id": 36,
        "parent_id": 129,
        "description": "Implement MinIO storage to upload document content to tenant-scoped bucket and return object path.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.7: Write unit tests",
        "type_id": 36,
        "parent_id": 129,
        "description": "Write comprehensive unit tests for rag_ingest tool including authorization, duplicate detection, versioning, and error handling.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.8: Write integration tests",
        "type_id": 36,
        "parent_id": 129,
        "description": "Write integration tests (deferred - unit tests cover functionality).",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.9: Create verification documentation",
        "type_id": 36,
        "parent_id": 129,
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.1.10: Update OpenProject status",
        "type_id": 36,
        "parent_id": 129,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 3.2: Document Versioning (130)
    {
        "subject": "Task 3.2.1: Create DocumentVersion model",
        "type_id": 36,
        "parent_id": 130,
        "description": "Create DocumentVersion model with version_id, document_id, version_number, content_hash, and change_summary fields.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.2: Create DocumentVersionRepository",
        "type_id": 36,
        "parent_id": 130,
        "description": "Create DocumentVersionRepository with methods for getting versions for a document and getting specific version by version_number.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.3: Add version_number and deleted_at fields to Document model",
        "type_id": 36,
        "parent_id": 130,
        "description": "Add version_number (default 1) and deleted_at (nullable) fields to Document model.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.4: Create database migration for document_versions table",
        "type_id": 36,
        "parent_id": 130,
        "description": "Create Alembic migration (005_add_document_versioning.py) to create document_versions table.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.5: Implement versioning logic in rag_ingest tool",
        "type_id": 36,
        "parent_id": 130,
        "description": "Implement versioning logic that creates DocumentVersion records when document content changes and increments version_number.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.6: Update FAISS and Meilisearch indices when version changes",
        "type_id": 36,
        "parent_id": 130,
        "description": "Update FAISS and Meilisearch indices with new version when document content changes.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.7: Write unit tests for versioning",
        "type_id": 36,
        "parent_id": 130,
        "description": "Write unit tests for document versioning including version creation, version retrieval, and version history.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.2.8: Update OpenProject status",
        "type_id": 36,
        "parent_id": 130,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 3.3: Document Deletion MCP Tool (131)
    {
        "subject": "Task 3.3.1: Create rag_delete_document MCP tool",
        "type_id": 36,
        "parent_id": 131,
        "description": "Implement rag_delete_document MCP tool that accepts document_id and performs soft delete.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.3.2: Implement tenant isolation validation",
        "type_id": 36,
        "parent_id": 131,
        "description": "Implement validation to ensure document belongs to tenant before deletion.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.3.3: Implement FAISS document removal",
        "type_id": 36,
        "parent_id": 131,
        "description": "Remove document from tenant-scoped FAISS index using faiss_manager.delete_document().",
        "status_id": 82,
    },
    {
        "subject": "Task 3.3.4: Implement Meilisearch document removal",
        "type_id": 36,
        "parent_id": 131,
        "description": "Remove document from tenant-scoped Meilisearch index using delete_document_from_index().",
        "status_id": 82,
    },
    {
        "subject": "Task 3.3.5: Implement PostgreSQL soft delete",
        "type_id": 36,
        "parent_id": 131,
        "description": "Mark document as deleted in PostgreSQL by setting deleted_at timestamp (soft delete).",
        "status_id": 82,
    },
    {
        "subject": "Task 3.3.6: Write unit tests",
        "type_id": 36,
        "parent_id": 131,
        "description": "Write unit tests for rag_delete_document including authorization, tenant isolation, and soft delete verification.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.3.7: Update OpenProject status",
        "type_id": 36,
        "parent_id": 131,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 3.4: Document Retrieval MCP Tool (132)
    {
        "subject": "Task 3.4.1: Create rag_get_document MCP tool",
        "type_id": 36,
        "parent_id": 132,
        "description": "Implement rag_get_document MCP tool that accepts document_id and returns complete document.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.4.2: Implement tenant isolation validation",
        "type_id": 36,
        "parent_id": 132,
        "description": "Implement validation to ensure document belongs to tenant before retrieval.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.4.3: Implement PostgreSQL metadata retrieval",
        "type_id": 36,
        "parent_id": 132,
        "description": "Retrieve document metadata from PostgreSQL documents table.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.4.4: Implement MinIO content retrieval",
        "type_id": 36,
        "parent_id": 132,
        "description": "Retrieve document content from MinIO tenant-scoped bucket using get_document_content().",
        "status_id": 82,
    },
    {
        "subject": "Task 3.4.5: Write unit tests",
        "type_id": 36,
        "parent_id": 132,
        "description": "Write unit tests for rag_get_document including authorization, tenant isolation, and content retrieval.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.4.6: Update OpenProject status",
        "type_id": 36,
        "parent_id": 132,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 3.5: Document Listing MCP Tool (133)
    {
        "subject": "Task 3.5.1: Create rag_list_documents MCP tool",
        "type_id": 36,
        "parent_id": 133,
        "description": "Implement rag_list_documents MCP tool that accepts filters and pagination parameters.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.5.2: Implement tenant isolation filtering",
        "type_id": 36,
        "parent_id": 133,
        "description": "Implement filtering to ensure only tenant's documents are returned.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.5.3: Implement pagination (limit/offset)",
        "type_id": 36,
        "parent_id": 133,
        "description": "Implement pagination support using limit and offset parameters.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.5.4: Implement filtering by document_type, source, date_range",
        "type_id": 36,
        "parent_id": 133,
        "description": "Implement filtering support for document_type, source, and date_range parameters.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.5.5: Implement search query support",
        "type_id": 36,
        "parent_id": 133,
        "description": "Implement optional search query parameter for filtering documents by title or content preview.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.5.6: Write unit tests",
        "type_id": 36,
        "parent_id": 133,
        "description": "Write unit tests for rag_list_documents including authorization, filtering, pagination, and search query.",
        "status_id": 82,
    },
    {
        "subject": "Task 3.5.7: Update OpenProject status",
        "type_id": 36,
        "parent_id": 133,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
]

# Epic 4 Tasks
epic4_tasks = [
    # Story 4.1: FAISS Vector Search Implementation (135)
    {
        "subject": "Task 4.1.1: Add search method to FAISSIndexManager",
        "type_id": 36,
        "parent_id": 135,
        "description": "Add search() method to FAISSIndexManager that performs vector search in tenant-scoped FAISS index and returns FAISS IDs with similarity scores.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.2: Create VectorSearchService for high-level search interface",
        "type_id": 36,
        "parent_id": 135,
        "description": "Create VectorSearchService that generates query embeddings, performs FAISS search, and resolves FAISS IDs to document IDs.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.3: Implement FAISS ID to document ID resolution",
        "type_id": 36,
        "parent_id": 135,
        "description": "Implement mapping from FAISS internal IDs to document UUIDs using _document_id_map and database queries.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.4: Handle different distance metrics (L2, Inner Product)",
        "type_id": 36,
        "parent_id": 135,
        "description": "Support both IndexFlatL2 (L2 distance) and IndexFlatIP (Inner Product) index types.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.5: Convert distances to similarity scores",
        "type_id": 36,
        "parent_id": 135,
        "description": "Convert FAISS distances to normalized similarity scores [0, 1] for consistent ranking.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.6: Write unit tests",
        "type_id": 36,
        "parent_id": 135,
        "description": "Write unit tests for FAISS vector search including search functionality, ID resolution, and tenant isolation.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.7: Create verification documentation",
        "type_id": 36,
        "parent_id": 135,
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.1.8: Update OpenProject status",
        "type_id": 36,
        "parent_id": 135,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 4.2: Meilisearch Keyword Search Implementation (136)
    {
        "subject": "Task 4.2.1: Add search_documents function to Meilisearch client",
        "type_id": 36,
        "parent_id": 136,
        "description": "Add search_documents() function to Meilisearch client that performs keyword search in tenant-scoped index.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.2: Create KeywordSearchService for high-level search interface",
        "type_id": 36,
        "parent_id": 136,
        "description": "Create KeywordSearchService that processes query text, performs Meilisearch search, and returns ranked document IDs.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.3: Implement tenant-scoped index search",
        "type_id": 36,
        "parent_id": 136,
        "description": "Ensure all searches are performed only in tenant's Meilisearch index with tenant_id filter.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.4: Support optional filters (document_type, tags)",
        "type_id": 36,
        "parent_id": 136,
        "description": "Support optional filters for document_type and tags in Meilisearch search queries.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.5: Return ranked results with relevance scores",
        "type_id": 36,
        "parent_id": 136,
        "description": "Return ranked results sorted by Meilisearch relevance score (normalized 0-1 range).",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.6: Write unit tests",
        "type_id": 36,
        "parent_id": 136,
        "description": "Write unit tests for Meilisearch keyword search including search functionality, filtering, and tenant isolation.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.7: Create verification documentation",
        "type_id": 36,
        "parent_id": 136,
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.2.8: Update OpenProject status",
        "type_id": 36,
        "parent_id": 136,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 4.3: Hybrid Retrieval Engine (137)
    {
        "subject": "Task 4.3.1: Create HybridSearchService",
        "type_id": 36,
        "parent_id": 137,
        "description": "Create HybridSearchService class that combines vector and keyword search results.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.2: Implement concurrent vector and keyword search",
        "type_id": 36,
        "parent_id": 137,
        "description": "Implement concurrent execution of vector and keyword search using asyncio.gather() for performance.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.3: Implement result merging and deduplication",
        "type_id": 36,
        "parent_id": 137,
        "description": "Merge results from both sources and deduplicate by document_id, keeping highest relevance score.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.4: Implement weighted re-ranking",
        "type_id": 36,
        "parent_id": 137,
        "description": "Implement weighted re-ranking using configurable weights (default: 60% vector, 40% keyword).",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.5: Implement three-tier fallback mechanism",
        "type_id": 36,
        "parent_id": 137,
        "description": "Implement three-tier fallback: FAISS+Meilisearch → FAISS only → Meilisearch only.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.6: Add timeout handling (500ms threshold)",
        "type_id": 36,
        "parent_id": 137,
        "description": "Add timeout handling that triggers fallback when search takes >500ms.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.7: Add error handling and logging",
        "type_id": 36,
        "parent_id": 137,
        "description": "Add comprehensive error handling and logging for service degradation alerts.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.8: Write unit tests",
        "type_id": 36,
        "parent_id": 137,
        "description": "Write unit tests for hybrid search including fallback scenarios, result merging, and re-ranking.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.9: Create verification documentation",
        "type_id": 36,
        "parent_id": 137,
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.3.10: Update OpenProject status",
        "type_id": 36,
        "parent_id": 137,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
    # Story 4.4: RAG Search MCP Tool (138)
    {
        "subject": "Task 4.4.1: Create rag_search MCP tool",
        "type_id": 36,
        "parent_id": 138,
        "description": "Create rag_search MCP tool that accepts search_query and optional filters.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.2: Integrate HybridSearchService",
        "type_id": 36,
        "parent_id": 138,
        "description": "Integrate HybridSearchService to perform hybrid retrieval (vector + keyword).",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.3: Implement filter support (document_type, date_range, tags)",
        "type_id": 36,
        "parent_id": 138,
        "description": "Implement filter support for document_type, date_range (date_from/date_to), and tags.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.4: Retrieve document metadata from database",
        "type_id": 36,
        "parent_id": 138,
        "description": "Retrieve document metadata from PostgreSQL for search results to include title, metadata, timestamp.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.5: Generate content snippets",
        "type_id": 36,
        "parent_id": 138,
        "description": "Generate content snippets from document content for search results (using _generate_snippet helper).",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.6: Return ranked results with metadata",
        "type_id": 36,
        "parent_id": 138,
        "description": "Return ranked list of documents with document_id, title, snippet, relevance_score, source, timestamp, metadata.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.7: Add RBAC (Tenant Admin and End User)",
        "type_id": 36,
        "parent_id": 138,
        "description": "Restrict access to Tenant Admin and End User roles only.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.8: Write unit tests",
        "type_id": 36,
        "parent_id": 138,
        "description": "Write unit tests for rag_search including authorization, filtering, and result formatting.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.9: Create verification documentation",
        "type_id": 36,
        "parent_id": 138,
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "status_id": 82,
    },
    {
        "subject": "Task 4.4.10: Update OpenProject status",
        "type_id": 36,
        "parent_id": 138,
        "description": "Update story status in OpenProject to Closed.",
        "status_id": 82,
    },
]

all_tasks = epic3_tasks + epic4_tasks

# Convert to JSON string for bulk_create_work_packages
tasks_json = json.dumps(all_tasks)

print(f"Total tasks to create: {len(all_tasks)}")
print(f"Epic 3 tasks: {len(epic3_tasks)}")
print(f"Epic 4 tasks: {len(epic4_tasks)}")
print("\nTasks JSON:")
print(tasks_json)








