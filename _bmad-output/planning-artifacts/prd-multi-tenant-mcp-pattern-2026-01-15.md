---
date: 2026-01-15
author: RagLeader
feature: tenant-specific-mcp-configuration
status: draft
workflowType: "prd"
stepsCompleted: [1]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-multi-tenant-mcp-pattern-2026-01-15.md
---

# Product Requirements Document: Multi-Tenant MCP Client & Server Pattern

**Author:** RagLeader  
**Date:** 2026-01-15  
**Status:** Draft

## Executive Summary

**Multi-Tenant MCP Client & Server Pattern** standardizes the multi-tenant pattern across all MCP clients in the RAG system. The RAG system acts as a **CLIENT** for downstream MCP servers, using a global `tenant_id="rag"` for all downstream calls. RAG maintains internal tenant isolation, while downstream MCP servers are shared multi-tenant services that route requests based on `tenant_id` to preconfigured end systems.

Following the existing `genImage` pattern and learning from Archon MCP server's `project_id` scoping approach, all MCP clients will pass `tenant_id="rag"` in tool call arguments, enabling consistent connectivity to downstream MCP servers.

**Key Innovation**: This feature ensures all MCP clients follow a consistent pattern where:

- RAG system uses `tenant_id="rag"` (global) for all downstream MCP calls
- RAG maintains internal tenant isolation (PostgreSQL RLS, tenant-scoped buckets, etc.)
- Downstream MCP servers are shared multi-tenant services with preconfigured tenant routing
- All MCP clients follow the Archon MCP server pattern for consistency

## Problem Statement

### Current State

- **Inconsistent Pattern**: Only some MCP clients (like `genImage`) follow the multi-tenant pattern
- **Missing tenant_id**: Many MCP clients (AI-MCP-Server) don't accept or pass `tenant_id`
- **Direct Connections**: Current implementation uses direct connections to dependencies (Postgres, Redis, MinIO, etc.) instead of MCP clients
- **Pattern Fragmentation**: Different MCP clients use different approaches for tenant isolation
- **No Standardized Client Pattern**: No consistent pattern for RAG system to connect to downstream MCP servers

### Problem Impact

- **Inconsistent Behavior**: Some MCP clients support multi-tenancy, others don't
- **Architecture Complexity**: Direct connections make it difficult to manage tenant routing at MCP server level
- **Error-Prone**: Easy to forget passing `tenant_id`, leading to connection failures
- **Maintenance Burden**: Different patterns across MCP clients make maintenance and onboarding difficult
- **Limited Scalability**: Direct connections prevent leveraging MCP server multi-tenant capabilities

### Who Experiences This Problem

- **Developers**: Must remember to pass `tenant_id` manually to each MCP client
- **Platform Operators**: Inconsistent multi-tenant support across different MCP dependencies
- **RAG System Operators**: Cannot leverage downstream MCP server multi-tenant routing capabilities

## Solution Vision

### Architecture Model

**RAG System as Client**: The RAG system acts as a **CLIENT** for downstream MCP servers. All downstream MCP calls use `tenant_id="rag"` (global tenant ID for RAG system).

**Tenant Isolation Boundaries**:

- **RAG System**: Maintains internal tenant isolation using PostgreSQL RLS, tenant-scoped buckets, tenant-scoped indexes, etc.
- **Downstream MCP Servers**: Shared multi-tenant services that route requests based on `tenant_id` to preconfigured end systems
- **End Systems**: Preconfigured connections at MCP server level based on `tenant_id`

### Core Capability

The system will standardize the multi-tenant pattern across all MCP clients:

1. **Global tenant_id**: RAG system uses `tenant_id="rag"` for all downstream MCP calls (from config or hardcoded)
2. **Consistent Client Interface**: All MCP clients accept `tenant_id` as a parameter (following Archon MCP server pattern)
3. **MCP Tool Call Pattern**: `tenant_id="rag"` is included in all MCP tool call arguments
4. **Service Layer Integration**: Service layer uses MCP clients/contracts to connect to downstream systems
5. **Circuit Breakers**: Circuit breakers with error reporting and bubbling up for resilience

### Architecture Model

**RAG System as Client**: The RAG system acts as a **CLIENT** for downstream MCP servers. This architecture model clarifies the tenant isolation boundaries and connection patterns.

**Architecture Flow:**

```
RAG System (Client)
  ↓ tenant_id="rag" (global)
Downstream MCP Servers (Shared Multi-Tenant Services)
  ↓ tenant_id routing to preconfigured connections
End Systems (Postgres, Redis, MinIO, etc.)
```

**Tenant Isolation Boundaries:**

1. **RAG System Internal Isolation**:

   - PostgreSQL RLS policies enforce tenant isolation
   - Tenant-scoped buckets in MinIO
   - Tenant-scoped indexes in Meilisearch
   - Tenant-scoped keys in Redis
   - All internal operations maintain tenant isolation

2. **Downstream MCP Servers**:

   - Shared multi-tenant services
   - Receive `tenant_id="rag"` from RAG system
   - Route requests to preconfigured end systems based on `tenant_id`
   - Other clients (besides RAG) can also use these MCP servers with their own `tenant_id`

3. **End Systems**:
   - Preconfigured connections at MCP server level
   - MCP server knows which end system to connect to based on `tenant_id`
   - RAG system's `tenant_id="rag"` routes to RAG's preconfigured end systems

### Reference Patterns

#### Pattern 1: Archon MCP Server (Primary Reference) ✅

Archon MCP server uses `project_id` as a scoping parameter, demonstrating the pattern we follow:

```python
# Archon pattern: project_id as required parameter
mcp_archon_find_documents(project_id="...", ...)  # project_id required
mcp_archon_manage_document(action="create", project_id="...", ...)  # project_id required
mcp_archon_find_tasks(project_id="...", ...)  # project_id required
```

**Key Learnings from Archon:**

- **Required Parameter**: `project_id` is always required in tool calls
- **Scoping Isolation**: All operations are scoped to `project_id`
- **Consistent Pattern**: All tools follow the same pattern
- **Explicit Parameter**: `project_id` must be explicitly provided

**Our Adaptation:**

- Use `tenant_id="rag"` instead of `project_id` (semantic difference, same pattern)
- `tenant_id="rag"` comes from configuration (not context extraction)
- Apply same required parameter pattern to all MCP clients
- Reference: `_bmad/integrations/archon/tools.md`

#### Pattern 2: GenImage (Additional Reference) ✅

```python
def generate_image(tenant_id: str, prompt: str):
    tool_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "gi_generate_image",
            "arguments": {
                "tenant_id": tenant_id,  # ✅ Pattern applied
                "prompt": prompt
            }
        }
    }
```

**Key Characteristics:**

- `tenant_id` is a required function parameter
- `tenant_id` is passed in MCP tool call arguments
- MCP server uses `tenant_id` for multi-tenant isolation

## Functional Requirements

### FR-MCP-001: Global tenant_id Configuration

**Requirement**: The RAG system must use `tenant_id="rag"` (global) for all downstream MCP calls.

**Acceptance Criteria:**

- **Given** RAG system needs to call a downstream MCP server
- **When** the MCP client is initialized
- **Then** `tenant_id="rag"` is read from configuration (e.g., `RAG_TENANT_ID="rag"`)
- **And** `tenant_id="rag"` is used for all downstream MCP tool calls
- **And** configuration is validated at startup
- **And** error is returned if `tenant_id` is missing from config

**Priority**: High  
**Dependencies**: Configuration management (`app/config/settings.py`)

**Configuration Example:**

```python
# app/config/settings.py
RAG_TENANT_ID: str = "rag"  # Global tenant ID for RAG system
```

### FR-MCP-002: MCP Client tenant_id Parameter Pattern

**Requirement**: All MCP clients must accept `tenant_id` as a required parameter, following the Archon MCP server pattern.

**Acceptance Criteria:**

- **Given** an MCP client method (e.g., `generate_embeddings`)
- **When** the method is called
- **Then** `tenant_id` is a required parameter (defaults to `"rag"` from config)
- **And** `tenant_id` is passed in all MCP tool call arguments
- **And** all MCP clients follow the same pattern as Archon MCP server
- **And** pattern is documented with examples referencing Archon MCP server documentation

**Priority**: High  
**Dependencies**: FR-MCP-001

**Reference**: Archon MCP server pattern (`_bmad/integrations/archon/tools.md`)

**Affected Clients:**

- AI-MCP-Server Client (`app/services/gpu_ai_client.py`) - to be refactored/renamed
- AI-MCP-Server SSE Client (`app/services/gpu_ai_sse_client.py`) - to be refactored/renamed
- PostgreSQL MCP Client (to be created)
- Redis MCP Client (to be created)
- MinIO MCP Client (to be created)
- Meilisearch MCP Client (to be created)
- Mem0 MCP Client (to be created)
- Langfuse MCP Client (to be created)

### FR-MCP-003: MCP Tool Call tenant_id Propagation

**Requirement**: All MCP tool calls must include `tenant_id` in the tool arguments.

**Acceptance Criteria:**

- **Given** an MCP client makes a tool call
- **When** the tool call is constructed
- **Then** `tenant_id` is included in the `arguments` dictionary
- **And** `tenant_id` is passed as a string (UUID format)
- **And** tool call format follows JSON-RPC 2.0 specification
- **And** pattern matches `genImage` implementation

**Priority**: High  
**Dependencies**: FR-MCP-002

**Example:**

```python
# RAG system uses tenant_id="rag" for all downstream calls
tenant_id = "rag"  # From config: RAG_TENANT_ID

tool_payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "embeddings_generate",
        "arguments": {
            "tenant_id": tenant_id,  # ✅ Always "rag" for RAG system
            "texts": texts,
            "normalize": normalize
        }
    },
    "id": message_id
}
```

### FR-MCP-004: MCP Server tenant_id Support

**Requirement**: All internal MCP tools must accept `tenant_id` as a parameter for multi-tenant isolation.

**Acceptance Criteria:**

- **Given** an internal MCP tool (e.g., `rag_search`, `rag_ingest`)
- **When** the tool is called
- **Then** `tenant_id` is extracted from tool arguments or context
- **And** `tenant_id` is validated against user's tenant membership
- **And** operations are scoped to the specified `tenant_id`
- **And** error is returned if `tenant_id` is missing or invalid

**Priority**: Medium  
**Dependencies**: Existing tenant middleware

**Note**: Most internal MCP tools already extract `tenant_id` from context. This requirement ensures consistency and explicit parameter support.

### FR-MCP-005: External MCP Server Compatibility

**Requirement**: The pattern must work with external MCP servers that support `tenant_id` in tool arguments.

**Acceptance Criteria:**

- **Given** an external MCP server (e.g., AI-MCP-Server, GenImage)
- **When** the MCP client calls the external server
- **Then** `tenant_id` is included in tool call arguments
- **And** external server can use `tenant_id` for multi-tenant isolation
- **And** pattern is compatible with MCP protocol specification
- **And** fallback behavior is defined if external server doesn't support `tenant_id`

**Priority**: High  
**Dependencies**: FR-MCP-003

### FR-MCP-006: Configuration-Based tenant_id Support

**Requirement**: The system must support `tenant_id` provided via configuration for external MCP server calls.

**Acceptance Criteria:**

- **Given** `tenant_id` is provided in config (e.g., `.env` or `tenant_config.json`)
- **When** an MCP client needs `tenant_id` and context extraction fails
- **Then** `tenant_id` is read from configuration
- **And** configuration format is documented
- **And** configuration validation ensures `tenant_id` is valid UUID format
- **And** error is returned if `tenant_id` is missing from both context and config

**Priority**: Medium  
**Dependencies**: FR-MCP-001

**Configuration Format:**

```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Non-Functional Requirements

### NFR-MCP-001: Performance

**Requirement**: MCP client calls and `tenant_id` propagation must not significantly impact performance.

**Acceptance Criteria:**

- **Given** a request requires downstream MCP calls
- **When** MCP clients are called sequentially (worst case)
- **Then** cumulative overhead is acceptable (<50ms for sequential calls)
- **And** individual MCP call overhead is <5ms (p95)
- **And** connection pooling is maintained for MCP clients
- **And** performance remains within acceptable parameters even with sequential calls

**Priority**: High

**Note**: Sequential MCP calls are acceptable worst case. Performance targets account for cumulative impact.

### NFR-MCP-002: Circuit Breakers and Error Handling

**Requirement**: All MCP clients must implement circuit breakers with error reporting and bubbling up.

**Acceptance Criteria:**

- **Given** an MCP server is unavailable or returns errors
- **When** the MCP client attempts to call the server
- **Then** circuit breaker opens after threshold failures
- **And** error is reported with detailed context
- **And** error bubbles up to service layer with clear error messages
- **And** retry logic uses exponential backoff
- **And** health check mechanisms monitor MCP server availability

**Priority**: High

**Circuit Breaker Configuration:**

- Failure threshold: 5 consecutive failures
- Timeout: 30 seconds
- Half-open retry interval: 60 seconds
- Error reporting: Structured logging with error codes

### NFR-MCP-003: Error Handling and Reporting

**Requirement**: The system must handle MCP client errors gracefully with proper reporting and bubbling up.

**Acceptance Criteria:**

- **Given** `tenant_id` is missing from config
- **When** an MCP client attempts to make a tool call
- **Then** a clear error message is returned
- **And** error code follows existing error code pattern (e.g., `FR-ERROR-003`)
- **And** error is logged for debugging with full context
- **And** error bubbles up to service layer with actionable information
- **And** circuit breaker prevents cascading failures

**Priority**: High

### NFR-MCP-004: Documentation

**Requirement**: The multi-tenant pattern must be fully documented with examples.

**Acceptance Criteria:**

- **Given** a developer wants to create a new MCP client
- **When** they read the documentation
- **Then** pattern is clearly explained with examples
- **And** `genImage` is referenced as the reference implementation
- **And** common pitfalls are documented
- **And** migration guide is provided for existing clients

**Priority**: Medium

## External Dependencies Analysis

**CRITICAL ARCHITECTURAL PRINCIPLE**: All external dependencies (Postgres, Redis, MinIO, Meilisearch, Mem0, Langfuse, AI-MCP-Server, GenImage) must be accessed through MCP clients using the `tenant_id` pattern. This ensures consistent multi-tenant isolation and standardized connectivity across all dependencies.

### All Dependencies via MCP Clients (Require Pattern Application)

#### 1. **AI-MCP-Server** (Embedding Generation) ✅ Multi-Tenant Support

- **Purpose**: Generate embeddings for vector search with multi-tenant support
- **Current State**: Uses MCP protocol with multi-tenant capabilities, but doesn't pass `tenant_id` in tool calls yet
- **Location**: `app/services/gpu_ai_client.py`, `app/services/gpu_ai_sse_client.py` (to be renamed/refactored)
- **MCP Endpoint**: Configurable per tenant (supports multi-tenant setup via `AI_MCP_SERVER_BASE_URL` or tenant-specific config)
- **Transport**: HTTP/SSE (Server-Sent Events)
- **Tools Used**: `embeddings_generate`, `embeddings_get_status`
- **Multi-Tenant Support**: AI-MCP-Server allows for multi-tenant setup, enabling tenant-specific configurations and endpoint routing
- **Pattern Application**:
  - Update `GPUAIClient.generate_embeddings()` to accept `tenant_id` parameter
  - Update `GPUAISSEClient.generate_embeddings()` to accept `tenant_id` parameter
  - Pass `tenant_id` in MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
  - Leverage AI-MCP-Server's native multi-tenant capabilities for tenant-specific embedding generation
- **Priority**: High

#### 2. **GenImage MCP Server** (Image Generation) ✅ Reference Pattern

- **Purpose**: Generate images using AI image generation service
- **Current State**: **Already follows the pattern** (reference implementation)
- **Location**: `scripts/generate_image_genimage.py`
- **MCP Endpoint**: Configurable (example: GenImage MCP server endpoint)
- **Transport**: HTTP with SSE support
- **Tools Used**: `gi_generate_image`, `genimage_generate_image`, `generate_image` (tool name varies)
- **Pattern Example**:
  ```python
  def generate_image(tenant_id: str, prompt: str):
      tool_payload = {
          "jsonrpc": "2.0",
          "method": "tools/call",
          "params": {
              "name": "gi_generate_image",
              "arguments": {
                  "tenant_id": tenant_id,  # ✅ Pattern applied
                  "prompt": prompt
              }
          }
      }
  ```
- **Status**: Reference implementation - all other MCP clients should follow this pattern

#### 3. **PostgreSQL MCP Server** (Primary Database)

- **Purpose**: Store tenant data, configurations, audit logs
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/postgres_mcp_client.py` (to be created), `app/db/connection.py` (to be refactored)
- **Connection**: **MCP client** (replaces direct `asyncpg` connection)
- **MCP Endpoint**: Configurable per tenant (e.g., `POSTGRES_MCP_SERVER_URL`)
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `postgres_query`, `postgres_execute`, `postgres_transaction` (MCP tools)
- **Tenant Isolation**:
  - `tenant_id` passed in MCP tool call arguments
  - PostgreSQL RLS policies enforce tenant isolation based on `tenant_id` from MCP arguments
  - MCP server sets session variable `app.current_tenant_id` for RLS enforcement
- **Configuration**: `POSTGRES_MCP_SERVER_URL`, `POSTGRES_MCP_SERVER_API_KEY` (per tenant)
- **Pattern Application**:
  - Create PostgreSQL MCP client following `genImage` pattern
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
- **Priority**: High

#### 4. **Redis MCP Server** (Caching & Session Storage)

- **Purpose**: Caching, rate limiting, session storage, Mem0 fallback
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/redis_mcp_client.py` (to be created), `app/services/redis_client.py` (to be refactored)
- **Connection**: **MCP client** (replaces direct `aioredis` connection)
- **MCP Endpoint**: Configurable per tenant (e.g., `REDIS_MCP_SERVER_URL`)
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `redis_get`, `redis_set`, `redis_delete`, `redis_keys` (MCP tools)
- **Tenant Isolation**:
  - `tenant_id` passed in MCP tool call arguments
  - Key prefixes: `tenant:{tenant_id}:{key}` (enforced by MCP server)
  - Memory keys: `tenant:{tenant_id}:user:{user_id}:memory:{memory_id}`
- **Configuration**: `REDIS_MCP_SERVER_URL`, `REDIS_MCP_SERVER_API_KEY` (per tenant)
- **Pattern Application**:
  - Create Redis MCP client following `genImage` pattern
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
- **Priority**: High

#### 5. **MinIO MCP Server** (S3-Compatible Object Storage)

- **Purpose**: Store documents, embeddings, files
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/minio_mcp_client.py` (to be created), `app/services/minio_client.py` (to be refactored)
- **Connection**: **MCP client** (replaces direct `minio` Python SDK)
- **MCP Endpoint**: Configurable per tenant (e.g., `MINIO_MCP_SERVER_URL`)
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `minio_put_object`, `minio_get_object`, `minio_delete_object`, `minio_list_objects` (MCP tools)
- **Tenant Isolation**:
  - `tenant_id` passed in MCP tool call arguments
  - Tenant-scoped buckets: `tenant-{tenant_id}` (enforced by MCP server)
  - Bucket validation ensures tenant isolation
- **Configuration**: `MINIO_MCP_SERVER_URL`, `MINIO_MCP_SERVER_ACCESS_KEY`, `MINIO_MCP_SERVER_SECRET_KEY` (per tenant)
- **Pattern Application**:
  - Create MinIO MCP client following `genImage` pattern
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
- **Priority**: High

#### 6. **Meilisearch MCP Server** (Keyword Search Engine)

- **Purpose**: Keyword search and hybrid retrieval
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/meilisearch_mcp_client.py` (to be created), `app/services/meilisearch_client.py` (to be refactored)
- **Connection**: **MCP client** (replaces direct `meilisearch` Python SDK)
- **MCP Endpoint**: Configurable per tenant (e.g., `MEILISEARCH_MCP_SERVER_URL`)
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `meilisearch_search`, `meilisearch_index`, `meilisearch_delete` (MCP tools)
- **Tenant Isolation**:
  - `tenant_id` passed in MCP tool call arguments
  - Tenant-scoped indexes: `tenant-{tenant_id}` (enforced by MCP server)
  - Filterable attribute `tenant_id` for additional isolation
- **Configuration**: `MEILISEARCH_MCP_SERVER_URL`, `MEILISEARCH_MCP_SERVER_API_KEY` (per tenant)
- **Pattern Application**:
  - Create Meilisearch MCP client following `genImage` pattern
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
- **Priority**: High

#### 7. **Mem0 MCP Server** (Memory Management)

- **Purpose**: Long-term memory for conversational context
- **Current State**: Currently uses direct SDK connection, **MUST migrate to MCP client**
- **Location**: `app/services/mem0_mcp_client.py` (to be created), `app/services/mem0_client.py` (to be refactored)
- **Connection**: **MCP client** (replaces direct Python SDK)
- **MCP Endpoint**: Configurable per tenant (e.g., `MEM0_MCP_SERVER_URL`)
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `mem0_get_memory`, `mem0_create_memory`, `mem0_update_memory`, `mem0_search_memory` (MCP tools)
- **Tenant Isolation**:
  - `tenant_id` passed in MCP tool call arguments
  - MCP server uses `tenant_id` for memory isolation
  - Redis fallback key prefixes: `tenant:{tenant_id}:mem0:write_queue` (enforced by MCP server)
- **Configuration**: `MEM0_MCP_SERVER_URL`, `MEM0_MCP_SERVER_API_KEY` (per tenant)
- **Pattern Application**:
  - Create Mem0 MCP client following `genImage` pattern
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
- **Priority**: High

#### 8. **Langfuse MCP Server** (Observability)

- **Purpose**: LLM observability, tool call tracking, analytics
- **Current State**: Currently uses direct SDK connection, **MUST migrate to MCP client**
- **Location**: `app/services/langfuse_mcp_client.py` (to be created), `app/integrations/langfuse_client.py` (to be refactored)
- **Connection**: **MCP client** (replaces direct `langfuse` Python SDK)
- **MCP Endpoint**: Configurable per tenant (e.g., `LANGFUSE_MCP_SERVER_URL`)
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `langfuse_trace`, `langfuse_span`, `langfuse_generation` (MCP tools)
- **Tenant Isolation**:
  - `tenant_id` passed in MCP tool call arguments
  - MCP server includes `tenant_id` in observability metadata
  - Tenant-scoped tracking and analytics
- **Configuration**: `LANGFUSE_MCP_SERVER_URL`, `LANGFUSE_MCP_SERVER_PUBLIC_KEY`, `LANGFUSE_MCP_SERVER_SECRET_KEY` (per tenant)
- **Pattern Application**:
  - Create Langfuse MCP client following `genImage` pattern
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
- **Priority**: Medium

### Dependency Summary

**ALL dependencies must use MCP clients with `tenant_id` pattern:**

| Dependency        | Type       | Current State                  | Pattern Application Needed                                     |
| ----------------- | ---------- | ------------------------------ | -------------------------------------------------------------- |
| **AI-MCP-Server** | MCP Client | ❌ No `tenant_id`              | ✅ **Yes** - Add `tenant_id` parameter (supports multi-tenant) |
| **GenImage**      | MCP Client | ✅ Has `tenant_id`             | ✅ **Reference** - Already follows pattern                     |
| **PostgreSQL**    | MCP Client | ❌ Direct connection (migrate) | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Redis**         | MCP Client | ❌ Direct connection (migrate) | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **MinIO**         | MCP Client | ❌ Direct connection (migrate) | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Meilisearch**   | MCP Client | ❌ Direct connection (migrate) | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Mem0**          | MCP Client | ❌ Direct SDK (migrate)        | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Langfuse**      | MCP Client | ❌ Direct SDK (migrate)        | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |

## Reference Patterns

### Pattern 1: Archon MCP Server (Primary Reference)

Archon MCP server uses `project_id` as a scoping parameter, demonstrating the pattern we follow:

```python
# Archon pattern: project_id as required parameter
mcp_archon_find_documents(project_id="...", ...)  # project_id required
mcp_archon_manage_document(action="create", project_id="...", ...)  # project_id required
mcp_archon_find_tasks(project_id="...", ...)  # project_id required
```

**Key Learnings from Archon:**

- **Required Parameter**: `project_id` is always required in tool calls
- **Scoping Isolation**: All operations are scoped to `project_id`
- **Consistent Pattern**: All tools follow the same pattern
- **Explicit Parameter**: `project_id` must be explicitly provided

**Our Adaptation:**

- Use `tenant_id="rag"` instead of `project_id` (semantic difference, same pattern)
- `tenant_id="rag"` comes from configuration (RAG_TENANT_ID="rag")
- Apply same required parameter pattern to all MCP clients
- Reference: `_bmad/integrations/archon/tools.md`

### Pattern 2: GenImage (Additional Reference)

The `genImage` MCP client already follows this pattern:

```python
def generate_image(tenant_id: str, prompt: str):
    """
    Generate an image using genimage tool.

    Args:
        tenant_id: Tenant ID for multi-tenant isolation (RAG uses "rag")
        prompt: Text prompt describing the image
    """
    tool_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "gi_generate_image",
            "arguments": {
                "tenant_id": tenant_id,  # ✅ Pattern applied (RAG uses "rag")
                "prompt": prompt
            }
        },
        "id": 2
    }
    # ... call MCP server
```

**Key Characteristics:**

- `tenant_id` is a required function parameter
- `tenant_id` is passed in MCP tool call arguments
- MCP server uses `tenant_id` for multi-tenant isolation
- RAG system uses `tenant_id="rag"` for all calls

## Implementation Approach

### Phase 1: Core MCP Client Updates (High Priority)

**Goal**: Update all MCP clients to follow the multi-tenant pattern with `tenant_id` parameter.

#### 1.1 AI-MCP-Server Client Updates

**Tasks:**

1. Update `GPUAIClient.generate_embeddings()` to accept `tenant_id` parameter
2. Update `GPUAISSEClient.generate_embeddings()` to accept `tenant_id` parameter
3. Add automatic `tenant_id` extraction from context
4. Include `tenant_id` in MCP tool call arguments
5. Update `_wait_for_embeddings()` to pass `tenant_id` in status check calls
6. Leverage AI-MCP-Server's multi-tenant setup for tenant-specific endpoint routing (if configured)
7. Add unit tests for `tenant_id` parameter handling
8. Add integration tests for AI-MCP-Server calls with `tenant_id`

**Files to Modify:**

- `app/services/gpu_ai_client.py` (consider renaming to `ai_mcp_client.py`)
- `app/services/gpu_ai_sse_client.py` (consider renaming to `ai_mcp_sse_client.py`)
- `tests/unit/services/test_gpu_ai_client.py` (create if needed, consider renaming)
- `tests/integration/test_ai_mcp_server.py` (create if needed)

#### 1.2 PostgreSQL MCP Client Creation

**Tasks:**

1. Create `PostgresMCPClient` class following `genImage` pattern
2. Implement MCP tool calls: `postgres_query`, `postgres_execute`, `postgres_transaction`
3. Accept `tenant_id` as parameter in all methods
4. Pass `tenant_id` in MCP tool call arguments
5. Replace direct `asyncpg` connections with MCP client calls
6. Add unit and integration tests

**Files to Create:**

- `app/services/postgres_mcp_client.py`
- `tests/unit/services/test_postgres_mcp_client.py`
- `tests/integration/test_postgres_mcp.py`

#### 1.3 Redis MCP Client Creation

**Tasks:**

1. Create `RedisMCPClient` class following `genImage` pattern
2. Implement MCP tool calls: `redis_get`, `redis_set`, `redis_delete`, `redis_keys`
3. Accept `tenant_id` as parameter in all methods
4. Pass `tenant_id` in MCP tool call arguments
5. Replace direct `aioredis` connections with MCP client calls
6. Add unit and integration tests

**Files to Create:**

- `app/services/redis_mcp_client.py`
- `tests/unit/services/test_redis_mcp_client.py`
- `tests/integration/test_redis_mcp.py`

#### 1.4 MinIO MCP Client Creation

**Tasks:**

1. Create `MinIOMCPClient` class following `genImage` pattern
2. Implement MCP tool calls: `minio_put_object`, `minio_get_object`, `minio_delete_object`, `minio_list_objects`
3. Accept `tenant_id` as parameter in all methods
4. Pass `tenant_id` in MCP tool call arguments
5. Replace direct `minio` SDK calls with MCP client calls
6. Add unit and integration tests

**Files to Create:**

- `app/services/minio_mcp_client.py`
- `tests/unit/services/test_minio_mcp_client.py`
- `tests/integration/test_minio_mcp.py`

#### 1.5 Meilisearch MCP Client Creation

**Tasks:**

1. Create `MeilisearchMCPClient` class following `genImage` pattern
2. Implement MCP tool calls: `meilisearch_search`, `meilisearch_index`, `meilisearch_delete`
3. Accept `tenant_id` as parameter in all methods
4. Pass `tenant_id` in MCP tool call arguments
5. Replace direct `meilisearch` SDK calls with MCP client calls
6. Add unit and integration tests

**Files to Create:**

- `app/services/meilisearch_mcp_client.py`
- `tests/unit/services/test_meilisearch_mcp_client.py`
- `tests/integration/test_meilisearch_mcp.py`

#### 1.6 Mem0 MCP Client Creation

**Tasks:**

1. Create `Mem0MCPClient` class following `genImage` pattern
2. Implement MCP tool calls: `mem0_get_memory`, `mem0_create_memory`, `mem0_update_memory`, `mem0_search_memory`
3. Accept `tenant_id` as parameter in all methods
4. Pass `tenant_id` in MCP tool call arguments
5. Replace direct Mem0 SDK calls with MCP client calls
6. Add unit and integration tests

**Files to Create:**

- `app/services/mem0_mcp_client.py`
- `tests/unit/services/test_mem0_mcp_client.py`
- `tests/integration/test_mem0_mcp.py`

#### 1.7 Langfuse MCP Client Creation

**Tasks:**

1. Create `LangfuseMCPClient` class following `genImage` pattern
2. Implement MCP tool calls: `langfuse_trace`, `langfuse_span`, `langfuse_generation`
3. Accept `tenant_id` as parameter in all methods
4. Pass `tenant_id` in MCP tool call arguments
5. Replace direct Langfuse SDK calls with MCP client calls
6. Add unit and integration tests

**Files to Create:**

- `app/services/langfuse_mcp_client.py`
- `tests/unit/services/test_langfuse_mcp_client.py`
- `tests/integration/test_langfuse_mcp.py`

### Phase 2: Service Layer Integration (High Priority)

**Goal**: Update service layer to use MCP clients/contracts for downstream connections.

**Tasks:**

1. Update `EmbeddingService` to use `AIMCPClient` instead of direct `gpu_ai_client`
2. Update all services to use MCP clients instead of direct connections
3. Ensure all service methods pass `tenant_id="rag"` to MCP clients
4. Add circuit breaker integration at service layer
5. Add error handling and bubbling up

**Files to Modify:**

- `app/services/embedding_service.py`
- All service files that use direct connections

**Reference**: Archon MCP server documentation (`_bmad/integrations/archon/tools.md`) for MCP client pattern

### Phase 3: Documentation and Examples (Medium Priority)

**Goal**: Document the multi-tenant pattern with examples.

**Tasks:**

1. Create MCP client development guide
2. Document Archon MCP server pattern as reference
3. Document `genImage` as additional reference
4. Add code examples showing `tenant_id="rag"` usage
5. Document service layer integration patterns

**Files to Create:**

- `docs/development/mcp-client-pattern.md` (reference Archon MCP server docs)
- `docs/development/mcp-multi-tenant-guide.md`
- `docs/development/service-layer-mcp-integration.md`

### Phase 4: Future MCP Clients (Low Priority)

**Goal**: Ensure all future MCP clients follow the pattern from day one.

**Tasks:**

1. Update MCP client template/boilerplate
2. Add pattern validation in code review checklist
3. Document pattern in onboarding materials

## Testing Requirements

### Unit Tests

- Test `tenant_id` extraction from context
- Test `tenant_id` extraction from config (fallback)
- Test `tenant_id` parameter validation
- Test MCP tool call argument construction with `tenant_id`
- Test error handling for missing `tenant_id`

### Integration Tests

**Test Tenant Model**: All tests use `tenant_id="rag"` from RAG system perspective.

**Test Data Structure**:

- **RAG System**: Uses `tenant_id="rag"` for all downstream calls
- **Internal RAG Tenants**: 2-3 Organizations, each with 2-3 Projects, each with 2-3 Users
- **Tenant Isolation**: Each user has clean access to their projects/data only

**Test Scenarios**:

1. **Tenant Isolation Tests**:

   - User A in Org 1, Project 1 can only access their data
   - User B in Org 1, Project 2 cannot access User A's data
   - User C in Org 2 cannot access Org 1 data
   - All downstream calls use `tenant_id="rag"`

2. **MCP Client Tests**:

   - Test AI-MCP-Server client with `tenant_id="rag"`
   - Test PostgreSQL MCP client with `tenant_id="rag"`
   - Test Redis MCP client with `tenant_id="rag"`
   - Test MinIO MCP client with `tenant_id="rag"`
   - Test Meilisearch MCP client with `tenant_id="rag"`
   - Test Mem0 MCP client with `tenant_id="rag"`
   - Test Langfuse MCP client with `tenant_id="rag"`

3. **End-to-End Tests**:
   - Test RAG → MCP Server (tenant_id="rag") → End System flow
   - Test tenant isolation within RAG system
   - Test that downstream calls use correct `tenant_id="rag"`
   - Test circuit breakers and error handling
   - Test end-to-end workflows using all MCP clients with `tenant_id="rag"`

### Performance Tests

- Measure overhead of automatic `tenant_id` extraction
- Measure overhead of `tenant_id` propagation in tool calls
- Ensure <5ms overhead (p95)

## Success Criteria

### Technical Success

- ✅ 100% of MCP clients follow the multi-tenant pattern
- ✅ 100% of `tenant_id` values automatically extracted from context/config
- ✅ >99% success rate for MCP tool calls with `tenant_id`
- ✅ <5ms overhead for automatic `tenant_id` extraction and propagation
- ✅ All unit and integration tests passing

### Business Success

- ✅ 50% reduction in manual `tenant_id` passing
- ✅ 90% reduction in tenant isolation errors
- ✅ 30% reduction in onboarding time for new developers
- ✅ 100% consistency across all MCP clients

## Out of Scope

- **User Stories**: User stories will be created after Technical Architecture documentation (BMAD methodology)
- **Migration Strategy**: This is a greenfield system - no migration from existing code needed
- **Tenant-Specific MCP Server Endpoints**: MCP servers have preconfigured connections per `tenant_id` - endpoint configuration is out of scope
- Multi-region MCP server support
- MCP server health monitoring per tenant (circuit breakers provide basic health checks)
- Automatic failover between tenant MCP servers
- MCP server usage analytics per tenant
- Direct connection fallbacks (all dependencies MUST use MCP clients)

## Dependencies

- Existing tenant middleware (`app/mcp/middleware/tenant.py`)
- Existing context extraction functions (`get_tenant_id_from_context()`)
- GenImage MCP client (reference implementation)
- Archon MCP server pattern (inspiration for scoping approach)

## Risks and Mitigations

### Risk 1: External MCP Servers Don't Support tenant_id

**Mitigation**:

- Document which external MCP servers support `tenant_id`
- Provide fallback behavior for servers that don't support it
- Add configuration flag to enable/disable `tenant_id` passing per server

### Risk 2: Performance Impact

**Mitigation**:

- Measure and optimize `tenant_id` extraction overhead
- Use connection pooling to minimize impact
- Cache `tenant_id` in request context to avoid repeated extraction

### Risk 3: Breaking Changes

**Mitigation**:

- Maintain backward compatibility with automatic extraction
- Provide migration guide for existing MCP clients
- Use feature flags for gradual rollout

## Next Steps

1. **Technical Architecture** (HOW): Design standardized MCP client pattern following Archon MCP server documentation, circuit breaker implementation, service layer integration patterns
2. **Implementation** (Artifacts): Phase 1 - Create/update all MCP clients (AI-MCP-Server, Postgres, Redis, MinIO, Meilisearch, Mem0, Langfuse) with `tenant_id="rag"` pattern
3. **Testing** (Artifacts): Unit and integration tests with test tenant model (2-3 orgs, 2-3 projects, 2-3 users) using `tenant_id="rag"`
4. **Documentation** (Artifacts): MCP client development guide referencing Archon MCP server documentation, service layer integration examples

**Note**: User stories will be created after Technical Architecture documentation per BMAD methodology.
