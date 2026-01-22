---
date: 2026-01-15
author: RagLeader
feature: tenant-specific-mcp-configuration
status: draft
---

# Product Brief: Multi-Tenant MCP Client & Server Pattern

## Executive Summary

**Multi-Tenant MCP Client & Server Pattern** standardizes the multi-tenant pattern across all MCP clients and servers in the system. Following the existing `genImage` pattern, all MCP clients will accept `tenant_id` as a parameter and pass it through to MCP servers in tool call arguments, enabling consistent multi-tenant isolation across all external MCP dependencies.

**Key Innovation**: This feature ensures all MCP clients and servers follow a consistent multi-tenant pattern where:

- **Consistent Pattern**: All MCP clients accept `tenant_id` as a parameter (like `genImage` does)
- **Automatic Propagation**: `tenant_id` from config/context is automatically passed to all MCP tool calls
- **Server-Side Isolation**: MCP servers use `tenant_id` in arguments for multi-tenant data isolation
- **Unified Architecture**: Single pattern applied across Postgres, MinIO, AI-MCP-Server, and all other MCP clients

## Problem Statement

### Current State

- **Inconsistent Pattern**: Only some MCP clients (like `genImage`) follow the multi-tenant pattern
- **Missing tenant_id**: Many MCP clients (Postgres, MinIO, AI-MCP-Server) don't accept or pass `tenant_id`
- **Manual Configuration**: `tenant_id` must be manually provided in config, not automatically extracted from context
- **Pattern Fragmentation**: Different MCP clients use different approaches for tenant isolation

### Problem Impact

- **Inconsistent Behavior**: Some MCP clients support multi-tenancy, others don't
- **Manual Overhead**: Developers must manually pass `tenant_id` to each MCP client call
- **Error-Prone**: Easy to forget passing `tenant_id`, leading to data leakage or isolation failures
- **Maintenance Burden**: Different patterns across MCP clients make maintenance and onboarding difficult

### Who Experiences This Problem

- **Developers**: Must remember to pass `tenant_id` manually to each MCP client
- **Platform Operators**: Inconsistent multi-tenant support across different MCP dependencies
- **Tenant Organizations**: Risk of data leakage when `tenant_id` is not properly propagated

## Solution Vision

### Core Capability

The system will standardize the multi-tenant pattern across all MCP clients and servers:

1. **Automatic tenant_id Extraction**: `tenant_id` is automatically extracted from context (middleware) or config
2. **Consistent Client Interface**: All MCP clients accept `tenant_id` as a parameter (following `genImage` pattern)
3. **Automatic Propagation**: `tenant_id` is automatically included in all MCP tool call arguments
4. **Server-Side Support**: All MCP servers (internal and external) accept `tenant_id` in tool arguments for isolation

### Key Features

- **Standardized Client Pattern**: All MCP clients follow the same pattern as `genImage` (accept `tenant_id`, pass in arguments)
- **Automatic Context Extraction**: `tenant_id` automatically extracted from middleware context or config
- **MCP Tool Updates**: All internal MCP tools updated to accept `tenant_id` parameter
- **External MCP Server Support**: Pattern works with external MCP servers that support `tenant_id` in arguments

## User Value Proposition

### For Developers

- **Consistent Pattern**: Single, predictable pattern for all MCP client calls
- **Automatic Handling**: `tenant_id` automatically extracted and propagated, no manual passing required
- **Reduced Errors**: Eliminates risk of forgetting to pass `tenant_id`
- **Easier Onboarding**: Clear, consistent pattern makes it easy for new developers

### For Platform Operators

- **Unified Architecture**: Consistent multi-tenant support across all MCP dependencies
- **Reduced Maintenance**: Single pattern to maintain instead of multiple approaches
- **Better Isolation**: Guaranteed tenant isolation across all MCP clients
- **Scalability**: Pattern scales to any number of MCP clients and servers

### For Tenant Organizations

- **Guaranteed Isolation**: `tenant_id` always passed, ensuring proper data isolation
- **Consistent Behavior**: Same multi-tenant behavior across all MCP dependencies
- **Compliance Support**: Proper tenant isolation supports compliance requirements

## Success Metrics

### Technical Metrics

- **Pattern Coverage**: 100% of MCP clients follow the multi-tenant pattern
- **Automatic Extraction**: 100% of `tenant_id` values automatically extracted from context/config
- **Tool Call Success**: >99% success rate for MCP tool calls with `tenant_id`
- **Performance Impact**: <5ms overhead for automatic `tenant_id` extraction and propagation

### Business Metrics

- **Developer Productivity**: 50% reduction in manual `tenant_id` passing
- **Error Reduction**: 90% reduction in tenant isolation errors
- **Onboarding Time**: 30% reduction in time for new developers to understand MCP client usage
- **Consistency**: 100% of MCP clients use the same pattern

## Technical Approach

### Architecture Changes

1. **MCP Client Standardization**: Update all MCP clients to accept `tenant_id` parameter (following `genImage` pattern)
2. **Automatic tenant_id Extraction**: Extract `tenant_id` from middleware context or config automatically
3. **Tool Argument Propagation**: Automatically include `tenant_id` in all MCP tool call arguments
4. **MCP Tool Updates**: Update all internal MCP tools to accept `tenant_id` parameter

### Integration Points

- **Tenant Middleware**: Extract `tenant_id` from context (already exists)
- **MCP Client Services**: Postgres, MinIO, AI-MCP-Server clients accept `tenant_id` and pass in arguments
- **MCP Tools**: All internal MCP tools accept `tenant_id` parameter
- **Config Support**: `tenant_id` can be provided via config for external MCP server calls

### Pattern Example (Following genImage)

```python
# MCP Client Pattern (like genImage)
def generate_embeddings(
    tenant_id: str,  # <-- tenant_id as parameter
    texts: List[str]
) -> List[List[float]]:
    tool_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "embeddings_generate",
            "arguments": {
                "tenant_id": tenant_id,  # <-- tenant_id in arguments
                "texts": texts
            }
        }
    }
    # ... call MCP server
```

### Automatic tenant_id Extraction

```python
# From middleware context (preferred)
tenant_id = get_tenant_id_from_context()  # Already available

# From config (fallback for external MCP servers)
tenant_id = config.get("tenant_id")
```

## Out of Scope (Initial Release)

- Tenant-specific MCP server endpoints (this is about pattern, not endpoints)
- Multi-region MCP server support
- MCP server health monitoring per tenant
- Automatic failover between tenant MCP servers
- MCP server usage analytics per tenant

## Next Steps

1. **Product Requirements Document (PRD)**: Detailed requirements and acceptance criteria
2. **Technical Architecture**: Design standardized MCP client pattern and automatic `tenant_id` extraction
3. **Implementation Plan**: Phased approach to update all MCP clients and tools
4. **Testing Strategy**: Unit and integration tests for multi-tenant pattern across all MCP clients

## External Dependencies Analysis

### Overview

The system integrates with multiple external dependencies, some via MCP protocol and others via direct connections. This section details each dependency and how the multi-tenant pattern will be applied.

### MCP-Based Dependencies (Require Pattern Application)

#### 1. **AI-MCP-Server** (Embedding Generation) ✅ Multi-Tenant Support

- **Purpose**: Generate embeddings for vector search with multi-tenant support
- **Current State**: Uses MCP protocol with multi-tenant capabilities, but doesn't pass `tenant_id` in tool calls yet
- **Location**: `app/services/gpu_ai_client.py`, `app/services/gpu_ai_sse_client.py` (to be renamed/refactored)
- **MCP Endpoint**: Configurable per tenant (supports multi-tenant setup)
- **Transport**: HTTP/SSE (Server-Sent Events)
- **Tools Used**: `embeddings_generate`, `embeddings_get_status`
- **Multi-Tenant Support**: AI-MCP-Server allows for multi-tenant setup, enabling tenant-specific configurations
- **Pattern Application**:
  - Update `GPUAIClient.generate_embeddings()` to accept `tenant_id` parameter
  - Pass `tenant_id` in MCP tool call arguments
  - Extract `tenant_id` from context or config automatically
  - Leverage AI-MCP-Server's native multi-tenant capabilities for tenant-specific embedding generation

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

### MCP Client Dependencies (All via MCP Protocol)

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
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically

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
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically

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
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically

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
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically

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
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically

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
  - Pass `tenant_id` in all MCP tool call arguments
  - Extract `tenant_id` from context or config automatically

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

   - AI-MCP-Server Client - Update to accept and pass `tenant_id` (leverages native multi-tenant support)
   - PostgreSQL MCP Client - Create new MCP client, migrate from direct connection
   - Redis MCP Client - Create new MCP client, migrate from direct connection
   - MinIO MCP Client - Create new MCP client, migrate from direct connection
   - Meilisearch MCP Client - Create new MCP client, migrate from direct connection
   - Mem0 MCP Client - Create new MCP client, migrate from direct SDK
   - Langfuse MCP Client - Create new MCP client, migrate from direct SDK

2. **Medium Priority** (Future MCP Servers):

   - Any new MCP servers should follow the pattern from day one
   - All dependencies MUST use MCP clients (no direct connections allowed)

## Reference: Existing Pattern (GenImage)

The `genImage` MCP client already follows this pattern:

- Accepts `tenant_id` as a function parameter
- Passes `tenant_id` in MCP tool call arguments
- MCP server uses `tenant_id` for multi-tenant isolation

This feature will apply the same pattern to all MCP clients and servers in the system.
