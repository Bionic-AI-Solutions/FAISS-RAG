# Story 3.3: Document Deletion MCP Tool

**Story ID:** 131  
**Epic:** Epic 3: Knowledge Base Management  
**Status:** Done

## Acceptance Criteria

**Given** Document deletion is required
**When** I implement rag_delete_document MCP tool
**Then** Tool accepts: document_id, tenant_id (FR-KB-007)
**And** Tool validates document belongs to tenant (tenant isolation)
**And** Tool removes document from FAISS index (tenant-scoped)
**And** Tool removes document from Meilisearch index (tenant-scoped)
**And** Tool marks document as deleted in PostgreSQL (soft delete)
**And** Tool retains document in MinIO for recovery period (30 days)
**And** Access is restricted to Tenant Admin role only
**And** Deletion completes within <500ms

**Given** Soft delete recovery is required
**When** I delete a document
**Then** Document can be restored within recovery period
**And** Document metadata is retained for audit purposes
**And** Deleted documents are excluded from search results

## Implementation Tasks

- [x] Task 1: Create rag_delete_document MCP tool
- [x] Task 2: Implement tenant isolation validation
- [x] Task 3: Implement FAISS document removal
- [x] Task 4: Implement Meilisearch document removal
- [x] Task 5: Implement PostgreSQL soft delete
- [x] Task 6: Write unit tests
- [x] Task 7: Update OpenProject status

## Implementation Summary

All tasks completed. The `rag_delete_document` MCP tool has been implemented with:
- Tenant Admin role restriction
- Tenant isolation validation
- Soft delete in PostgreSQL (sets `deleted_at` timestamp)
- FAISS document removal via `faiss_manager.delete_document`
- Meilisearch document removal via `delete_document_from_index`
- Comprehensive unit tests

