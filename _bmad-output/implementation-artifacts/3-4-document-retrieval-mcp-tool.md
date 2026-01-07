# Story 3.4: Document Retrieval MCP Tool

**Story ID:** 132  
**Epic:** Epic 3: Knowledge Base Management  
**Status:** Done

## Acceptance Criteria

**Given** Document retrieval is required
**When** I implement rag_get_document MCP tool
**Then** Tool accepts: document_id, tenant_id (FR-KB-008)
**And** Tool validates document belongs to tenant (tenant isolation)
**And** Tool retrieves document metadata from PostgreSQL
**And** Tool retrieves document content from MinIO
**And** Tool returns complete document with metadata and content
**And** Access is available to Tenant Admin and End User roles
**And** Retrieval completes within <200ms (p95)

**Given** Document access control is required
**When** I retrieve a document
**Then** Tenant isolation is enforced (users can only access their tenant's documents)
**And** Role-based access is enforced (End Users have read-only access)
**And** Invalid access attempts return 403 Forbidden error

## Implementation Tasks

- [x] Task 1: Create rag_get_document MCP tool
- [x] Task 2: Implement tenant isolation validation
- [x] Task 3: Implement PostgreSQL metadata retrieval
- [x] Task 4: Implement MinIO content retrieval
- [x] Task 5: Write unit tests
- [x] Task 6: Update OpenProject status

## Implementation Summary

All tasks completed. The `rag_get_document` MCP tool has been implemented with:
- Tenant Admin and End User role access
- Tenant isolation validation
- PostgreSQL metadata retrieval
- MinIO content retrieval via `get_document_content`
- Comprehensive unit tests








