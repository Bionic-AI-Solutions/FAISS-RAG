---
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/prd-multi-tenant-mcp-pattern-2026-01-15.md
  - _bmad-output/planning-artifacts/product-brief-multi-tenant-mcp-pattern-2026-01-15.md
  - _bmad/integrations/archon/tools.md
  - scripts/generate_image_genimage.py
workflowType: 'architecture'
project_name: 'mem0-rag'
user_name: 'RAGLeader'
date: '2026-01-15'
party_mode_enhancements: true
---

# Architecture Decision Document: Multi-Tenant MCP Client & Server Pattern

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

The PRD defines **6 functional requirements** (FR-MCP-001 through FR-MCP-006) focused on standardizing the multi-tenant MCP client pattern:

- **FR-MCP-001: Global tenant_id Configuration** - RAG system uses `tenant_id="rag"` (global) for all downstream MCP calls, read from configuration
- **FR-MCP-002: MCP Client tenant_id Parameter Pattern** - All MCP clients accept `tenant_id` as required parameter, following Archon MCP server pattern
- **FR-MCP-003: MCP Tool Call tenant_id Propagation** - All MCP tool calls include `tenant_id` in arguments dictionary
- **FR-MCP-004: MCP Server tenant_id Support** - Internal MCP tools accept `tenant_id` for multi-tenant isolation
- **FR-MCP-005: External MCP Server Compatibility** - Pattern works with external MCP servers supporting `tenant_id`
- **FR-MCP-006: Configuration-Based tenant_id Support** - System supports `tenant_id` from configuration with validation

**Architectural Implications:**

- **Configuration Management**: Centralized `RAG_TENANT_ID="rag"` configuration required
- **Client Interface Standardization**: All 8 MCP clients must follow consistent parameter pattern
- **Service Layer Integration**: Service layer must use MCP clients/contracts, passing `tenant_id="rag"` automatically
- **Migration Scope**: 7 dependencies require migration from direct connections to MCP clients (Postgres, Redis, MinIO, Meilisearch, Mem0, Langfuse, AI-MCP-Server)

**Non-Functional Requirements:**

The PRD defines **4 non-functional requirements** (NFR-MCP-001 through NFR-MCP-004):

- **NFR-MCP-001: Performance** - <5ms overhead per MCP call (p95), <50ms cumulative for sequential calls, connection pooling maintained
- **NFR-MCP-002: Circuit Breakers and Error Handling** - Circuit breakers with failure threshold (5 failures), timeout (30s), exponential backoff, health checks, structured error reporting
- **NFR-MCP-003: Error Handling and Reporting** - Graceful error handling with clear messages, error codes, logging, bubbling up to service layer
- **NFR-MCP-004: Documentation** - Pattern documentation with examples, reference implementations (GenImage, Archon), migration guides

**Architectural Implications:**

- **Performance Architecture**: Connection pooling, async operations, minimal overhead for `tenant_id` extraction/propagation
- **Resilience Architecture**: Circuit breaker pattern required for all MCP clients, preventing cascading failures
- **Observability Architecture**: Structured logging with error codes, health check mechanisms
- **Developer Experience**: Clear documentation and examples for pattern adoption

**Scale & Complexity:**

- **Primary Domain**: Infrastructure Platform / API Backend (MCP Client Layer)
- **Complexity Level**: Medium-High (Pattern Standardization + Migration)
- **Estimated Architectural Components**: 
  - 8 MCP Clients (AI-MCP-Server, GenImage, Postgres, Redis, MinIO, Meilisearch, Mem0, Langfuse)
  - 1 Configuration Management System (`RAG_TENANT_ID` config)
  - 1 Circuit Breaker Framework (shared across all clients)
  - Service Layer Integration Points (multiple services)
- **Migration Scope**: 7 dependencies migrating from direct connections to MCP clients
- **Pattern Consistency**: 100% of MCP clients must follow standardized pattern

**Technical Constraints & Dependencies**

**Core Technology Stack:**

- **MCP Protocol (Model Context Protocol)**: Primary protocol for all client-server communication
- **Archon MCP Server Pattern**: Primary reference pattern (`project_id` scoping approach)
- **GenImage MCP Client**: Reference implementation (already follows pattern)
- **Circuit Breaker Pattern**: Required for resilience (failure threshold, timeout, retry logic)
- **Configuration Management**: Pydantic Settings for `RAG_TENANT_ID` validation

**Architectural Constraints:**

- **CRITICAL PRINCIPLE**: All dependencies MUST use MCP clients - no direct connections allowed
- **Global tenant_id**: RAG system uses `tenant_id="rag"` for all downstream calls (from config, not context)
- **Pattern Consistency**: All MCP clients must follow Archon MCP server pattern (required parameter approach)
- **Performance Targets**: <5ms overhead per call, <50ms cumulative for sequential calls
- **Circuit Breaker Requirements**: Failure threshold (5), timeout (30s), half-open retry (60s)
- **Service Layer Integration**: Services must use MCP clients/contracts, not direct connections

**Dependencies Requiring MCP Client Migration:**

1. **AI-MCP-Server** - Update existing client to accept/pass `tenant_id`
2. **PostgreSQL** - Create MCP client, migrate from direct `asyncpg` connection
3. **Redis** - Create MCP client, migrate from direct `aioredis` connection
4. **MinIO** - Create MCP client, migrate from direct `minio` SDK
5. **Meilisearch** - Create MCP client, migrate from direct `meilisearch` SDK
6. **Mem0** - Create MCP client, migrate from direct Python SDK
7. **Langfuse** - Create MCP client, migrate from direct `langfuse` SDK

**Reference Patterns:**

- **Archon MCP Server**: Primary reference (uses `project_id` as required parameter)
- **GenImage MCP Client**: Reference implementation (already follows pattern with `tenant_id`)

**Note on OpenProject MCP Server:**

OpenProject MCP server is used for work management (epics, stories, tasks) and already follows a similar pattern (`project_id` scoping). However, it is **not** a dependency that the RAG system connects to for core functionality - it's a tool used by developers/agents for work management. Therefore, it's not included in the 8 dependencies requiring MCP client pattern application, but the pattern consistency is noted for completeness.

### Cross-Cutting Concerns Identified

**1. Multi-Tenancy Pattern Standardization:**

- **Scope**: All 8 MCP clients must follow consistent `tenant_id` parameter pattern
- **Challenge**: Migrating 7 dependencies from direct connections to MCP clients
- **Solution**: Standardized client interface following Archon MCP server pattern
- **Impact**: Service layer integration, configuration management, error handling

**2. Configuration Management:**

- **Scope**: Global `tenant_id="rag"` configuration for RAG system
- **Challenge**: Ensuring `tenant_id` is always available and validated
- **Solution**: Centralized configuration with startup validation
- **Impact**: All MCP clients, service layer, error handling

**3. Circuit Breaker Implementation:**

- **Scope**: All MCP clients require circuit breakers
- **Challenge**: Consistent implementation across 8 clients
- **Solution**: Shared circuit breaker framework with configurable thresholds
- **Impact**: Resilience, error handling, performance monitoring

**4. Service Layer Integration:**

- **Scope**: All services must use MCP clients instead of direct connections
- **Challenge**: Refactoring existing services to use MCP clients
- **Solution**: Service layer abstraction with automatic `tenant_id="rag"` propagation
- **Impact**: All service methods, error handling, performance

**5. Error Handling and Reporting:**

- **Scope**: Consistent error handling across all MCP clients
- **Challenge**: Error bubbling up from MCP clients to service layer
- **Solution**: Structured error responses with error codes, logging, circuit breaker integration
- **Impact**: Observability, debugging, user experience

**6. Performance Optimization:**

- **Scope**: Minimizing overhead of `tenant_id` extraction/propagation
- **Challenge**: Maintaining <5ms overhead per call while ensuring pattern consistency
- **Solution**: Connection pooling, async operations, cached `tenant_id` extraction
- **Impact**: Latency targets, scalability, user experience

### Party Mode Collaborative Enhancements

**Configuration Management Enhancements:**

- **Environment-Specific Overrides**: While `RAG_TENANT_ID="rag"` is the default, consider environment-specific overrides (dev/staging/prod) for flexibility
- **Startup Validation**: Fail fast if `tenant_id` is missing from configuration
- **Configuration Hierarchy**: Default → Environment → Tenant-specific (if needed)

**Circuit Breaker Framework Design:**

- **Shared Framework**: Common circuit breaker implementation across all 8 MCP clients
- **Per-Client Configuration**: Allow different thresholds per client (e.g., Postgres may need different thresholds than Langfuse)
- **Default Configuration**: 5-failure threshold, 30s timeout, 60s half-open retry interval
- **Configurable Parameters**: Failure threshold, timeout, retry interval, health check frequency

**Base MCP Client Architecture:**

- **Base Class Pattern**: Create `BaseMCPClient` class that handles `tenant_id` injection automatically
- **Developer Experience**: Developers don't need to remember to pass `tenant_id` - it's injected automatically
- **Pattern Implementation**:
  ```python
  async def some_operation(self, tenant_id: str = None, ...):
      tenant_id = tenant_id or self.default_tenant_id  # From config
      # MCP tool call with tenant_id in arguments
  ```

**Error Propagation Strategy:**

- **Error Hierarchy**: Define explicit error hierarchy from MCP client → service layer
- **Structured Error Responses**: Error codes, error messages, context, retry semantics
- **Error Bubbling**: Clear contract for how errors propagate from MCP clients to services
- **Retry Logic**: Explicit retry semantics per error type (retryable vs non-retryable)

**File Structure and Organization:**

- **MCP Client Directory**: `app/services/mcp_clients/`
  - `base.py` - Base MCP client with `tenant_id` handling
  - `ai_mcp_client.py` - AI-MCP-Server client
  - `postgres_mcp_client.py` - PostgreSQL client
  - `redis_mcp_client.py` - Redis client
  - `minio_mcp_client.py` - MinIO client
  - `meilisearch_mcp_client.py` - Meilisearch client
  - `mem0_mcp_client.py` - Mem0 client
  - `langfuse_mcp_client.py` - Langfuse client
- **Circuit Breaker Module**: `app/services/mcp_clients/circuit_breaker.py`
- **Configuration Module**: `app/config/mcp_settings.py`

**Service Layer Migration Path:**

- **Phased Migration**: Start with low-risk clients (Langfuse, Mem0) before critical ones (Postgres, Redis)
- **Backward Compatibility**: Maintain existing service interfaces during migration
- **Gradual Rollout**: Feature flags for gradual migration per service
- **Migration Documentation**: Clear migration guide for each service

**Comprehensive Test Strategy:**

- **Unit Tests**:
  - Mock MCP server responses
  - Test `tenant_id` extraction/propagation
  - Test error handling patterns
  - Test circuit breaker behavior (open, half-open, closed states)
  
- **Integration Tests**:
  - Real MCP server calls with `tenant_id="rag"`
  - Test tenant isolation
  - Test circuit breaker with real failures
  - Test error propagation from MCP client → service layer
  
- **End-to-End Tests**:
  - Full RAG workflows using MCP clients
  - Verify `tenant_id="rag"` propagation end-to-end
  - Test tenant isolation across full workflows
  
- **Performance Tests**:
  - Verify <5ms overhead per call (p95)
  - Verify <50ms cumulative for sequential calls
  - Load testing with multiple concurrent MCP calls
  
- **Circuit Breaker Tests**:
  - Failure threshold verification (5 failures)
  - Timeout scenarios (30s timeout)
  - Retry logic (exponential backoff)
  - Half-open state transitions
  
- **Error Propagation Tests**:
  - Error bubbling from MCP client → service layer
  - Error code mapping and context preservation
  - Retryable vs non-retryable error handling
  
- **Tenant Isolation Tests**:
  - Verify `tenant_id="rag"` doesn't leak to other tenants
  - Test tenant isolation with test tenant model (2-3 orgs, 2-3 projects, 2-3 users)
  - Cross-tenant access prevention

**High-Risk Migration Areas:**

1. **Postgres MCP Client Migration** - Highest risk. Direct `asyncpg` → MCP client migration affects all data operations. Requires comprehensive integration tests with real Postgres MCP server.
2. **Circuit Breaker Behavior** - Need thorough testing for: open state, half-open retry, failure threshold, timeout scenarios.
3. **Service Layer Integration** - Risk of breaking existing functionality during migration. Requires regression test suite.
