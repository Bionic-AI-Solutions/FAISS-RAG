---
date: 2026-01-15
author: RagLeader
feature: tenant-specific-mcp-configuration
status: draft
---

# Product Brief: Multi-Tenant MCP Client & Server Pattern

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

## External Dependencies Analysis

### MCP Client Dependencies (All via MCP Protocol)

#### 1. **AI-MCP-Server** (Embedding Generation) ✅ Multi-Tenant Support

- **Purpose**: Generate embeddings for vector search with multi-tenant support
- **Current State**: Uses MCP protocol with multi-tenant capabilities, but doesn't pass `tenant_id` in tool calls yet
- **Location**: `app/services/gpu_ai_client.py`, `app/services/gpu_ai_sse_client.py` (to be renamed/refactored)
- **MCP Endpoint**: Configurable per tenant (supports multi-tenant setup)
- **Transport**: HTTP/SSE (Server-Sent Events)
- **Tools Used**: `embeddings_generate`, `embeddings_get_status`
- **Multi-Tenant Support**: AI-MCP-Server allows for multi-tenant setup, enabling tenant-specific configurations and endpoint routing
- **Pattern Application**:
  - Create AI-MCP-Server MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

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
- **Location**: `app/services/postgres_mcp_client.py` (to be created)
- **Connection**: **MCP client** (replaces direct `asyncpg` connection)
- **MCP Endpoint**: Configurable per tenant
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `postgres_query`, `postgres_execute`, `postgres_transaction` (MCP tools)
- **Pattern Application**:
  - Create PostgreSQL MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

#### 4. **Redis MCP Server** (Caching & Session Storage)

- **Purpose**: Caching, rate limiting, session storage, Mem0 fallback
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/redis_mcp_client.py` (to be created)
- **Connection**: **MCP client** (replaces direct `aioredis` connection)
- **MCP Endpoint**: Configurable per tenant
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `redis_get`, `redis_set`, `redis_delete`, `redis_keys` (MCP tools)
- **Pattern Application**:
  - Create Redis MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

#### 5. **MinIO MCP Server** (S3-Compatible Object Storage)

- **Purpose**: Store documents, embeddings, files
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/minio_mcp_client.py` (to be created)
- **Connection**: **MCP client** (replaces direct `minio` Python SDK)
- **MCP Endpoint**: Configurable per tenant
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `minio_put_object`, `minio_get_object`, `minio_delete_object`, `minio_list_objects` (MCP tools)
- **Pattern Application**:
  - Create MinIO MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

#### 6. **Meilisearch MCP Server** (Keyword Search Engine)

- **Purpose**: Keyword search and hybrid retrieval
- **Current State**: Currently uses direct connection, **MUST migrate to MCP client**
- **Location**: `app/services/meilisearch_mcp_client.py` (to be created)
- **Connection**: **MCP client** (replaces direct `meilisearch` Python SDK)
- **MCP Endpoint**: Configurable per tenant
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `meilisearch_search`, `meilisearch_index`, `meilisearch_delete` (MCP tools)
- **Pattern Application**:
  - Create Meilisearch MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

#### 7. **Mem0 MCP Server** (Memory Management)

- **Purpose**: Long-term memory for conversational context
- **Current State**: Currently uses direct SDK connection, **MUST migrate to MCP client**
- **Location**: `app/services/mem0_mcp_client.py` (to be created)
- **Connection**: **MCP client** (replaces direct Python SDK)
- **MCP Endpoint**: Configurable per tenant
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `mem0_get_memory`, `mem0_create_memory`, `mem0_update_memory`, `mem0_search_memory` (MCP tools)
- **Pattern Application**:
  - Create Mem0 MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

#### 8. **Langfuse MCP Server** (Observability)

- **Purpose**: LLM observability, tool call tracking, analytics
- **Current State**: Currently uses direct SDK connection, **MUST migrate to MCP client**
- **Location**: `app/services/langfuse_mcp_client.py` (to be created)
- **Connection**: **MCP client** (replaces direct `langfuse` Python SDK)
- **MCP Endpoint**: Configurable per tenant
- **Transport**: HTTP/SSE (MCP protocol)
- **Tools Used**: `langfuse_trace`, `langfuse_span`, `langfuse_generation` (MCP tools)
- **Pattern Application**:
  - Create Langfuse MCP client following `genImage` pattern
  - Pass `tenant_id="rag"` in all MCP tool call arguments
  - Extract `tenant_id="rag"` from config automatically

### Dependency Summary

| Dependency        | Type       | Current State                    | Pattern Application Needed                                     |
| ----------------- | ---------- | -------------------------------- | -------------------------------------------------------------- |
| **AI-MCP-Server** | MCP Client | ❌ No `tenant_id`                | ✅ **Yes** - Add `tenant_id` parameter (supports multi-tenant) |
| **GenImage**      | MCP Client | ✅ Has `tenant_id`               | ✅ **Reference** - Already follows pattern                     |
| **PostgreSQL**    | MCP Client | ❌ Direct connection (migrate)   | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Redis**         | MCP Client | ❌ Direct connection (migrate)   | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **MinIO**         | MCP Client | ❌ Direct connection (migrate)   | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Meilisearch**   | MCP Client | ❌ Direct connection (migrate)   | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Mem0**          | MCP Client | ❌ Direct SDK (migrate)          | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |
| **Langfuse**      | MCP Client | ❌ Direct SDK (migrate)          | ✅ **Yes** - Create MCP client, add `tenant_id` parameter      |

### Implementation Priority

1. **High Priority** (Core MCP Clients - All Dependencies):

   - AI-MCP-Server Client - Update to accept and pass `tenant_id="rag"` (leverages native multi-tenant support)
   - PostgreSQL MCP Client - Create new MCP client, migrate from direct connection
   - Redis MCP Client - Create new MCP client, migrate from direct connection
   - MinIO MCP Client - Create new MCP client, migrate from direct connection
   - Meilisearch MCP Client - Create new MCP client, migrate from direct connection
   - Mem0 MCP Client - Create new MCP client, migrate from direct SDK
   - Langfuse MCP Client - Create new MCP client, migrate from direct SDK

2. **Medium Priority** (Future MCP Servers):

   - Any new MCP servers should follow the pattern from day one
   - All dependencies MUST use MCP clients (no direct connections allowed)

## Success Criteria

### Technical Success

- ✅ 100% of MCP clients follow the multi-tenant pattern with `tenant_id="rag"`
- ✅ 100% of dependencies accessed via MCP clients (no direct connections)
- ✅ >99% success rate for MCP tool calls with `tenant_id="rag"`
- ✅ <5ms overhead per MCP call (acceptable cumulative impact for sequential calls)
- ✅ Circuit breakers prevent cascading failures

### Business Success

- ✅ Consistent pattern across all MCP clients
- ✅ Leverage downstream MCP server multi-tenant capabilities
- ✅ Reduced architecture complexity through standardized client pattern
- ✅ Improved scalability through MCP server tenant routing

## Next Steps

1. **Technical Architecture** (HOW): Design standardized MCP client pattern following Archon MCP server documentation, circuit breaker implementation, service layer integration patterns
2. **Implementation** (Artifacts): Create/update all MCP clients with `tenant_id="rag"` pattern
3. **Testing** (Artifacts): Unit and integration tests with test tenant model using `tenant_id="rag"`
4. **Documentation** (Artifacts): MCP client development guide referencing Archon MCP server documentation
