---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
workflowType: 'architecture'
project_name: 'new-rag'
user_name: 'RagLeader'
date: '2026-01-04'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- **45+ functional requirements** organized across 14 capability categories:
  - **Knowledge Base Operations (9 FRs)**: Document search, ingestion, management, versioning, deletion, retrieval, listing
  - **Memory Operations (5 FRs)**: User memory management (get, update, search), session context storage, memory isolation
  - **Tenant Management (8 FRs)**: Tenant onboarding, template management, configuration, data isolation, subscription tiers
  - **Authentication & Authorization (6 FRs)**: OAuth 2.0, tenant-based API keys, RBAC (4-tier), role-based data access
  - **Search Capabilities (5 FRs)**: Vector search (FAISS), keyword search (Meilisearch), hybrid retrieval, cross-modal search (Phase 2)
  - **Session Management (3 FRs)**: Session continuity, context-aware search, returning user recognition
  - **Compliance & Audit (5 FRs)**: Comprehensive audit logging, HIPAA, PCI DSS, SOC 2, GDPR compliance
  - **Monitoring & Analytics (6 FRs)**: Usage statistics, search analytics, memory analytics, health monitoring
  - **Data Management (4 FRs)**: Tenant-level and user-level data isolation, data export (GDPR)
  - **Performance & Optimization (4 FRs)**: Latency targets (<200ms search, <100ms memory, <500ms cold start), caching
  - **Error Handling & Recovery (4 FRs)**: Graceful degradation, fallback mechanisms, structured error responses, rate limit handling
  - **Integration & Protocol Support (3 FRs)**: MCP server implementation, tool discovery, context validation
  - **Backup & Recovery (5 FRs)**: Backup operations, restore, index rebuild, backup validation
  - **Rate Limiting (2 FRs)**: Per-tenant rate limiting, tier-based limits

**Non-Functional Requirements:**
- **50+ non-functional requirements** across 9 quality attribute categories:
  - **Performance**: <200ms p95 search latency, <100ms memory operations, <500ms cold start, >80% cache hit rate
  - **Scalability**: 200 tenants (MVP), 200 concurrent users/tenant, horizontal scaling, 40K requests/minute (MVP)
  - **Reliability**: >95% uptime (MVP), >99.9% (Phase 3), RTO <4h, RPO <1h, fault tolerance, graceful degradation
  - **Security**: AES-256 encryption at rest, TLS 1.3 in transit, RBAC, tenant isolation, vulnerability management
  - **Compliance**: HIPAA (healthcare), PCI DSS (fintech), SOC 2, GDPR, comprehensive audit logging
  - **Observability**: Langfuse integration (MVP requirement), monitoring, structured logging, distributed tracing (Phase 2), alerting
  - **Maintainability**: >80% test coverage, clean architecture, comprehensive documentation
  - **Deployability**: CI/CD pipelines, zero-downtime deployments, Infrastructure as Code
  - **Usability**: Clear MCP tool interfaces, comprehensive API documentation, <5min integration time

**Scale & Complexity:**
- **Primary Domain**: Infrastructure Platform (SaaS B2B) / API Backend
- **Complexity Level**: High/Enterprise
- **Estimated Architectural Components**: 7+ core services
  - MCP Server Layer (primary interface)
  - Mem0 Integration Layer (memory management)
  - FAISS Vector Store (vector search)
  - Hybrid Retrieval Engine (vector + keyword search)
  - Multi-Modal Processing Pipeline (text, images, audio, video - Phase 2)
  - Data Persistence Layer (PostgreSQL, MinIO)
  - Performance Layer (Redis caching, rate limiting)
- **Multi-Service Distributed Architecture**: Kubernetes orchestration with pod autoscaling
- **Multi-Tenant Architecture**: Strict data isolation, tenant-scoped resources
- **Multi-Modal Processing**: Priority-based processing pipeline
- **Real-Time Performance**: Sub-200ms latency requirements with optimization

### Technical Constraints & Dependencies

**Core Technology Stack:**
- **MCP Protocol (Model Context Protocol)**: Primary interface, standardized protocol for LLM tool consumption
- **Langfuse**: Observability and tool call tracking (MVP requirement) - integrated as middleware in MCP server layer
- **Mem0**: Memory management service integration with fallback to Redis
- **FAISS**: Vector search library with tenant-partitioned indices
- **PostgreSQL**: Relational database for tenant data, configurations, audit logs, metadata
- **Redis**: Caching layer, rate limiting, session storage, fallback memory store
- **MinIO**: Object storage for documents, images, audio, video
- **Meilisearch**: Keyword search engine for hybrid retrieval
- **Kubernetes**: Container orchestration, horizontal scaling, service management
- **Compliance Frameworks**: HIPAA, PCI DSS, SOC 2, GDPR - built into architecture

**Architectural Constraints:**
- **MCP-Native Interface**: All capabilities must be exposed via MCP tools (no REST API for core functionality)
- **Multi-Tenant Isolation**: Complete data isolation at every layer (database, vector indices, memory, storage)
- **Performance Targets**: Sub-200ms latency (p95) requires caching, connection pooling, async operations
- **Compliance Requirements**: Encryption, audit logging, access controls built into every component
- **Observability Requirement**: Langfuse integration must be non-intrusive, async logging to avoid latency impact

### Cross-Cutting Concerns Identified

**1. Multi-Tenancy:**
- **Data Isolation**: PostgreSQL RLS with tenant_id policies, tenant-scoped FAISS indices, tenant-prefixed Redis keys
- **Resource Isolation**: Each tenant gets isolated resources (indices, memory stores, storage buckets)
- **Configuration Isolation**: Tenant configurations stored separately, template-based onboarding
- **Access Control**: Tenant_id validation at every layer, cross-tenant access prevention

**2. Performance Optimization:**
- **Caching Strategy**: Multi-level caching (Redis for memory, search results, document metadata)
- **Connection Pooling**: Database connections, service connections (Mem0, FAISS, etc.)
- **Async Operations**: Async/await for I/O operations, parallel processing where possible
- **Query Optimization**: Vector search optimization, keyword search optimization, hybrid retrieval merging

**3. Security & Compliance:**
- **Encryption**: AES-256 at rest for all data stores, TLS 1.3 in transit for all communications
- **Access Control**: RBAC enforced at MCP server layer, validated before tool execution
- **Audit Logging**: Mandatory comprehensive audit logs for all operations, stored in PostgreSQL with indexed fields
- **Data Protection**: PII protection, secure data handling, vulnerability management

**4. Observability (Langfuse Integration - MVP Requirement):**
- **Tool Call Tracking**: All MCP tool calls logged to Langfuse with user, tenant, timestamp, action
- **Metrics Collection**: Tool execution time, cache hit rates, error rates per tenant
- **Async Logging**: Langfuse integration as middleware in MCP server, async logging to avoid latency impact
- **Structured Logging**: JSON format logs with tenant_id in all entries
- **Health Monitoring**: System health, component health, tenant health monitoring
- **Alerting**: Proactive alerts on degradation, errors, compliance violations

**5. Error Handling & Resilience:**
- **Graceful Degradation**: Fallback mechanisms (Mem0 → Redis, FAISS+Meilisearch → FAISS only → Meilisearch only)
- **Circuit Breakers**: Prevent cascade failures, service isolation
- **Fault Tolerance**: Zero user-facing errors on service failures, partial functionality maintenance
- **Recovery**: RTO <4h, RPO <1h, automated backup/restore, disaster recovery procedures

**6. Backup & Recovery:**
- **Backup Strategy**: PostgreSQL (WAL archiving, daily backups), FAISS indices (daily snapshots), Mem0 memory (daily snapshots)
- **Data Reconstruction**: FAISS index rebuild from PostgreSQL embeddings, memory store rebuild from backups/audit logs
- **Disaster Recovery**: Point-in-time recovery, sequential component restore, data structure validation

**7. Integration & Protocol Support:**
- **MCP Server Implementation**: Protocol handling, tool discovery, request/response, context validation
- **Service Integration**: Mem0, FAISS, PostgreSQL, Redis, MinIO, Meilisearch integration with connection pooling
- **Tool-Based Architecture**: Each capability exposed as MCP tool with standardized interface

### Architectural Implications

**Service Architecture:**
- **Distributed Microservices**: Clear service boundaries with isolation and fault tolerance
- **MCP Server Layer**: Primary interface layer handling protocol, tool execution, observability (Langfuse integration)
- **Service Layer**: Mem0 Integration, FAISS Vector Store, Hybrid Retrieval Engine, Multi-Modal Processing Pipeline
- **Data Layer**: PostgreSQL (relational data, audit logs), Redis (caching, rate limiting), MinIO (object storage)
- **Observability Layer**: Langfuse integrated as middleware in MCP server (non-intrusive, async)

**Multi-Tenant Architecture:**
- **Complete Data Isolation**: Every service enforces tenant_id boundaries
- **Tenant-Scoped Resources**: Isolated indices, memory stores, storage buckets per tenant
- **Configuration Isolation**: Tenant configurations stored separately, template-based onboarding
- **Resource Quotas**: Per-tenant rate limiting, storage quotas, subscription tier management

**Performance Architecture:**
- **Multi-Level Caching**: Redis caching for memory, search results, document metadata
- **Connection Pooling**: Database and service connection pools for performance
- **Async Operations**: Non-blocking I/O operations, parallel processing
- **Query Optimization**: Vector search, keyword search, hybrid retrieval optimization

**Compliance Architecture:**
- **Built-In Security**: Encryption, access control, audit logging in every component
- **Compliance Frameworks**: HIPAA, PCI DSS, SOC 2, GDPR requirements built into architecture
- **Audit Trail**: Comprehensive audit logging for all operations, queryable via MCP tool

**Observability Architecture:**
- **Langfuse Integration**: MVP requirement, integrated as middleware in MCP server layer
- **Non-Intrusive Design**: Async logging to avoid latency impact on MCP tool execution
- **Comprehensive Tracking**: All MCP tool calls tracked with user, tenant, timestamp, action, metrics
- **Metrics & Alerting**: Tool execution time, cache hit rates, error rates per tenant, proactive alerting

## Starter Template Evaluation

### Primary Technology Domain

**API/Backend Infrastructure Platform** - Python/FastAPI backend with MCP server interface

Based on project requirements analysis:
- **Primary Interface**: MCP Protocol (Model Context Protocol) - standardized LLM tool consumption
- **Backend Framework**: FastAPI (async Python web framework)
- **MCP Implementation**: FastMCP (Python framework for building MCP servers)
- **Deployment**: ASGI application (Uvicorn/Gunicorn compatible)
- **Architecture Pattern**: Multi-tenant SaaS infrastructure platform

### Starter Options Considered

**Option A: Generic FastAPI Cookiecutters**
- **Evaluation**: Most FastAPI starters assume REST-first architecture
- **Limitation**: Our system is MCP-first, which fundamentally changes the structure
- **Gap**: Multi-tenant patterns need to be foundational, not added later
- **Verdict**: Would require significant modification and removal of REST-focused code

**Option B: FastMCP Simple Server Pattern**
- **Evaluation**: FastMCP supports single-file server initialization
- **Limitation**: Insufficient for enterprise-scale multi-tenant system
- **Gap**: Missing service layer abstraction, middleware patterns, compliance infrastructure
- **Verdict**: Too simple for our complexity requirements

**Option C: Custom FastMCP + FastAPI Structure (SELECTED)**
- **Evaluation**: Leverages FastMCP's HTTP transport and FastAPI integration capabilities
- **Advantage**: MCP-first architecture with FastAPI for admin/health endpoints
- **Advantage**: Built-in middleware support for multi-tenant isolation and compliance
- **Advantage**: Modular structure from day one, optimized for our specific requirements
- **Verdict**: Best fit for our architecture needs

### Selected Approach: Custom FastMCP + FastAPI Structure

**Rationale for Selection:**

1. **MCP-Native Interface**: FastMCP provides native MCP protocol implementation with HTTP transport support, enabling multi-client concurrent access (unlike stdio transport)

2. **FastAPI Integration**: FastMCP's `http_app()` method returns an ASGI application that can be mounted into FastAPI, allowing us to:
   - Serve MCP endpoints at `/mcp/` as primary interface
   - Add optional REST endpoints for admin operations, health checks, monitoring
   - Leverage FastAPI's middleware ecosystem for cross-cutting concerns

3. **Middleware Architecture**: FastMCP supports middleware patterns that enable:
   - Authentication (OAuth 2.0, API key validation)
   - Tenant extraction and isolation
   - Authorization (RBAC enforcement)
   - Audit logging (comprehensive compliance tracking)
   - Observability (Langfuse integration)

4. **Multi-Tenant Foundation**: Custom structure allows us to build tenant isolation into every layer from the start, rather than retrofitting it

5. **Service Integration Patterns**: Modular structure supports clean integration with:
   - Mem0 (memory management)
   - FAISS (vector search)
   - Meilisearch (keyword search)
   - PostgreSQL (relational data)
   - Redis (caching, rate limiting)
   - MinIO (object storage)
   - Langfuse (observability)

6. **Compliance-First Design**: Structure enables built-in compliance (HIPAA, PCI DSS, SOC 2, GDPR) at every layer

**Initialization Approach:**

Start from scratch rather than modifying a cookiecutter template:
- Less code to remove/modify = faster to MVP
- Full control over architecture patterns
- No assumptions to override
- Clean foundation for multi-tenant, compliance-first architecture

### Project Structure

**Complete Directory Structure:**

```
rag-system/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + FastMCP mounting, combined lifespan
│   │
│   ├── mcp/                       # MCP Server Layer (Primary Interface)
│   │   ├── __init__.py
│   │   ├── server.py              # FastMCP server instance initialization
│   │   ├── tools/                 # MCP Tools (RAG Operations)
│   │   │   ├── __init__.py
│   │   │   ├── knowledge_base.py  # Knowledge base operations (search, ingest, etc.)
│   │   │   ├── memory.py          # Memory operations (get, update, search)
│   │   │   ├── tenant.py          # Tenant management operations
│   │   │   ├── session.py         # Session management operations
│   │   │   ├── audit.py           # Audit log query operations
│   │   │   └── templates.py       # Template management operations
│   │   ├── resources/             # MCP Resources (if needed)
│   │   │   └── __init__.py
│   │   └── middleware/            # MCP Middleware Stack
│   │       ├── __init__.py
│   │       ├── auth.py            # Authentication middleware (OAuth, API keys)
│   │       ├── tenant.py          # Tenant extraction and isolation middleware
│   │       ├── authorization.py   # RBAC authorization middleware
│   │       ├── audit.py            # Audit logging middleware
│   │       ├── observability.py   # Langfuse integration middleware
│   │       └── rate_limit.py       # Rate limiting middleware
│   │
│   ├── api/                       # Optional REST API Endpoints
│   │   ├── __init__.py
│   │   ├── admin.py               # Admin operations (if needed)
│   │   ├── health.py              # Health check endpoints
│   │   └── monitoring.py          # Monitoring/metrics endpoints
│   │
│   ├── services/                  # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── knowledge_service.py   # Knowledge base business logic
│   │   ├── memory_service.py      # Memory management (Mem0 integration)
│   │   ├── search_service.py      # Hybrid search (FAISS + Meilisearch)
│   │   ├── vector_service.py      # FAISS vector operations
│   │   ├── keyword_service.py     # Meilisearch keyword operations
│   │   ├── tenant_service.py      # Tenant management logic
│   │   ├── session_service.py     # Session management logic
│   │   └── backup_service.py      # Backup and restore operations
│   │
│   ├── models/                    # Pydantic Models
│   │   ├── __init__.py
│   │   ├── knowledge.py           # Knowledge base models
│   │   ├── memory.py              # Memory models
│   │   ├── tenant.py              # Tenant models
│   │   ├── session.py             # Session models
│   │   └── audit.py               # Audit log models
│   │
│   ├── db/                        # Database Layer
│   │   ├── __init__.py
│   │   ├── database.py            # Database connection and session management
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── repositories/          # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── knowledge_repo.py
│   │   │   ├── memory_repo.py
│   │   │   ├── tenant_repo.py
│   │   │   └── audit_repo.py
│   │   └── migrations/            # Alembic migrations
│   │
│   ├── config/                     # Configuration Management
│   │   ├── __init__.py
│   │   ├── settings.py            # Pydantic Settings
│   │   ├── database.py            # Database configuration
│   │   ├── redis.py               # Redis configuration
│   │   ├── mem0.py                # Mem0 configuration
│   │   ├── faiss.py               # FAISS configuration
│   │   ├── meilisearch.py         # Meilisearch configuration
│   │   ├── minio.py               # MinIO configuration
│   │   └── langfuse.py            # Langfuse configuration
│   │
│   └── utils/                     # Utility Functions
│       ├── __init__.py
│       ├── encryption.py          # Encryption utilities
│       ├── validation.py          # Input validation
│       └── errors.py              # Error handling utilities
│
├── tests/                         # Test Suite
│   ├── __init__.py
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── e2e/                       # End-to-end tests
│   └── fixtures/                  # Test fixtures
│
├── docker/                        # Docker Configuration
│   ├── Dockerfile
│   └── docker-compose.yml         # Local development environment
│
├── kubernetes/                    # Kubernetes Manifests
│   ├── deployments/
│   ├── services/
│   └── configmaps/
│
├── scripts/                       # Utility Scripts
│   ├── backup.py                  # Backup script
│   ├── restore.py                 # Restore script
│   └── migrate.py                 # Migration script
│
├── pyproject.toml                 # Python project configuration
├── requirements.txt               # Python dependencies
├── .env.example                  # Environment variable template
└── README.md                      # Project documentation
```

**Key Architectural Decisions in Structure:**

1. **MCP-First Organization**: `app/mcp/` contains the primary interface layer, clearly separated from optional REST endpoints

2. **Middleware Stack**: `app/mcp/middleware/` contains all cross-cutting concerns in a clear, composable order

3. **Service Layer Abstraction**: `app/services/` provides business logic that MCP tools call, enabling testability and reusability

4. **Repository Pattern**: `app/db/repositories/` provides data access abstraction, enabling easy testing and database swapping

5. **Configuration Management**: `app/config/` centralizes all service configurations using Pydantic Settings

6. **Modular Tools**: `app/mcp/tools/` organized by domain (knowledge, memory, tenant, etc.) for maintainability

### Middleware Implementation Patterns

**Middleware Execution Order:**

The middleware stack executes in the following order for each MCP tool call:

```
1. Authentication Middleware
   ↓
2. Tenant Extraction Middleware
   ↓
3. Rate Limiting Middleware
   ↓
4. Authorization Middleware (RBAC)
   ↓
5. Audit Logging Middleware (Pre-execution)
   ↓
6. Observability Middleware (Langfuse - Pre-execution)
   ↓
7. [MCP Tool Execution]
   ↓
8. Observability Middleware (Langfuse - Post-execution)
   ↓
9. Audit Logging Middleware (Post-execution)
```

**1. Authentication Middleware (`app/mcp/middleware/auth.py`)**

**Purpose**: Validate authentication credentials (OAuth 2.0 tokens or API keys)

**Implementation Pattern:**
```python
from fastmcp import Context
from typing import Optional

async def authenticate_request(ctx: Context) -> Optional[str]:
    """
    Extract and validate authentication from request.
    Returns user_id if authenticated, None otherwise.
    """
    # Extract token from headers or context
    # Validate OAuth token or API key
    # Return user_id for downstream middleware
    pass
```

**Responsibilities:**
- Extract OAuth 2.0 Bearer tokens from Authorization header
- Validate API keys for tenant-based authentication
- Extract user identity from JWT tokens
- Reject unauthenticated requests with appropriate error

**2. Tenant Extraction Middleware (`app/mcp/middleware/tenant.py`)**

**Purpose**: Extract tenant_id from authenticated request and inject into context

**Implementation Pattern:**
```python
from fastmcp import Context
from typing import Optional

async def extract_tenant(ctx: Context, user_id: str) -> Optional[str]:
    """
    Extract tenant_id from user context or request.
    Injects tenant_id into context for downstream use.
    """
    # Query database for user's tenant_id
    # Validate tenant is active
    # Inject tenant_id into context
    ctx.state["tenant_id"] = tenant_id
    return tenant_id
```

**Responsibilities:**
- Extract tenant_id from user context (database lookup)
- Validate tenant is active and not suspended
- Inject tenant_id into FastMCP context for all downstream operations
- Ensure tenant_id is available to all services and repositories

**3. Rate Limiting Middleware (`app/mcp/middleware/rate_limit.py`)**

**Purpose**: Enforce per-tenant rate limits based on subscription tier

**Implementation Pattern:**
```python
from fastmcp import Context
from app.services.tenant_service import get_tenant_tier

async def check_rate_limit(ctx: Context, tenant_id: str) -> bool:
    """
    Check if tenant has exceeded rate limit.
    Returns True if allowed, False if rate limited.
    """
    # Get tenant subscription tier
    # Check Redis for current request count
    # Increment counter if under limit
    # Return True/False
    pass
```

**Responsibilities:**
- Retrieve tenant subscription tier (Free, Basic, Enterprise)
- Check Redis for current request count in time window
- Enforce per-tenant limits (e.g., 1000 requests/minute)
- Return rate limit error if exceeded

**4. Authorization Middleware (`app/mcp/middleware/authorization.py`)**

**Purpose**: Enforce RBAC (Role-Based Access Control) before tool execution

**Implementation Pattern:**
```python
from fastmcp import Context
from app.models.tenant import UserRole

async def authorize_tool_access(
    ctx: Context, 
    tenant_id: str, 
    user_id: str, 
    tool_name: str
) -> bool:
    """
    Check if user has permission to execute specific tool.
    Returns True if authorized, False otherwise.
    """
    # Get user role from context
    # Check RBAC policies for tool access
    # Validate role has permission for tool
    # Return True/False
    pass
```

**Responsibilities:**
- Retrieve user role (Uber Admin, Tenant Admin, Project Admin, End User)
- Check RBAC policies for specific tool access
- Validate role has permission for requested tool
- Enforce tenant-level and project-level access controls

**5. Audit Logging Middleware (`app/mcp/middleware/audit.py`)**

**Purpose**: Log all operations for compliance (HIPAA, PCI DSS, SOC 2, GDPR)

**Implementation Pattern:**
```python
from fastmcp import Context
from app.db.repositories.audit_repo import AuditRepository
from datetime import datetime

async def log_audit_event(
    ctx: Context,
    tenant_id: str,
    user_id: str,
    tool_name: str,
    action: str,
    status: str,
    metadata: dict
):
    """
    Log audit event to PostgreSQL with comprehensive metadata.
    Async logging to avoid latency impact.
    """
    audit_entry = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "tool_name": tool_name,
        "action": action,
        "timestamp": datetime.utcnow(),
        "status": status,
        "metadata": metadata,
        "ip_address": ctx.state.get("ip_address"),
        "user_agent": ctx.state.get("user_agent"),
    }
    # Async write to PostgreSQL
    await audit_repo.create(audit_entry)
```

**Responsibilities:**
- Log all MCP tool calls with comprehensive metadata
- Store audit logs in PostgreSQL with indexed fields (tenant_id, user_id, timestamp, tool_name)
- Include request metadata (IP address, user agent, request ID)
- Support querying via MCP tool (`rag_query_audit_logs`)
- Ensure audit logs are immutable and tamper-proof

**6. Observability Middleware (`app/mcp/middleware/observability.py`)**

**Purpose**: Integrate Langfuse for tool call tracking and observability (MVP requirement)

**Implementation Pattern:**
```python
from fastmcp import Context
from langfuse import Langfuse
from datetime import datetime
import asyncio

async def track_tool_call(
    ctx: Context,
    tenant_id: str,
    user_id: str,
    tool_name: str,
    execution_time: float,
    status: str,
    error: Optional[str] = None
):
    """
    Track MCP tool call in Langfuse.
    Async logging to avoid latency impact on tool execution.
    """
    langfuse = Langfuse()
    
    # Create trace for tool call
    trace = langfuse.trace(
        name=tool_name,
        user_id=user_id,
        metadata={
            "tenant_id": tenant_id,
            "tool_name": tool_name,
            "execution_time_ms": execution_time * 1000,
            "status": status,
        }
    )
    
    # Log asynchronously to avoid blocking
    asyncio.create_task(trace.flush())
```

**Responsibilities:**
- Track all MCP tool calls in Langfuse with user, tenant, timestamp
- Measure tool execution time for performance monitoring
- Log errors and exceptions for debugging
- Provide metrics for cache hit rates, error rates per tenant
- Async logging to ensure zero latency impact on tool execution

**Middleware Integration with FastMCP:**

FastMCP middleware is added to the server instance:

```python
from fastmcp import FastMCP
from app.mcp.middleware.auth import AuthMiddleware
from app.mcp.middleware.tenant import TenantMiddleware
from app.mcp.middleware.authorization import AuthorizationMiddleware
from app.mcp.middleware.audit import AuditMiddleware
from app.mcp.middleware.observability import ObservabilityMiddleware
from app.mcp.middleware.rate_limit import RateLimitMiddleware

mcp = FastMCP("RAG System")

# Add middleware in execution order
mcp.add_middleware(AuthMiddleware())
mcp.add_middleware(TenantMiddleware())
mcp.add_middleware(RateLimitMiddleware())
mcp.add_middleware(AuthorizationMiddleware())
mcp.add_middleware(AuditMiddleware())
mcp.add_middleware(ObservabilityMiddleware())
```

**Lifespan Management:**

FastAPI and FastMCP lifespans are combined for proper initialization:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.mcp.server import create_mcp_server

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup: Initialize database connections, Redis, etc.
    await initialize_database()
    await initialize_redis()
    await initialize_services()
    yield
    # Shutdown: Cleanup connections
    await cleanup_database()
    await cleanup_redis()

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    # Combine both lifespans with proper initialization order
    async with app_lifespan(app):
        mcp = create_mcp_server()
        mcp_app = mcp.http_app(path='/mcp')
        async with mcp_app.lifespan(app):
            yield

app = FastAPI(lifespan=combined_lifespan)
app.mount("/mcp", mcp_app)
```

**Note:** Project initialization using this structure should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- ORM/Database Access Layer (SQLAlchemy 2.0 async)
- Database Migration Tool (Alembic)
- OAuth 2.0 / JWT Library (python-jose + authlib)
- Encryption Library (cryptography)
- Password Hashing (argon2)
- Rate Limiting Library (slowapi)
- Configuration Management (Pydantic Settings)
- Logging Library (structlog)

**Important Decisions (Shape Architecture):**
- Error Handling Format (Standardized JSON structure)
- CI/CD Platform (GitHub Actions)
- Monitoring & Alerting (Prometheus + Grafana)
- Caching Strategy (Redis with tenant-scoped keys)

**Deferred Decisions (Post-MVP):**
- Advanced monitoring dashboards (Phase 2)
- Custom rate limiting algorithms (Phase 2)
- Alternative authentication providers (Phase 3)

### Data Architecture

#### ORM/Database Access Layer

**Decision:** SQLAlchemy 2.0 async

**Version:** SQLAlchemy 2.0+ (latest stable)

**Rationale:**
- Async-first design aligns with FastAPI's async architecture
- Mature, production-ready ORM with excellent FastAPI integration
- Native support for PostgreSQL Row-Level Security (RLS) for multi-tenant isolation
- Strong Alembic integration for database migrations
- Repository pattern support for clean data access abstraction
- Excellent documentation and community support

**Implementation Notes:**
- Use `AsyncSession` consistently throughout the application
- Repository pattern in `app/db/repositories/` for data access abstraction
- Connection pooling configured for performance (<200ms latency targets)
- RLS policies enforced at database level for tenant isolation

**Affects:**
- All database operations
- Repository implementations
- Service layer data access
- Multi-tenant data isolation

#### Database Migration Tool

**Decision:** Alembic

**Version:** Alembic (latest, compatible with SQLAlchemy 2.0)

**Rationale:**
- Standard migration tool for SQLAlchemy
- Integrated with SQLAlchemy models
- Version control for schema changes
- Supports tenant-specific migrations if needed
- Production-proven migration workflow

**Implementation Notes:**
- Migrations stored in `app/db/migrations/`
- All migrations must include tenant_id in relevant tables from the start
- Test migrations in CI/CD pipeline
- Validate tenant isolation in migration tests

**Affects:**
- Database schema evolution
- Deployment procedures
- Multi-tenant schema management

#### Data Validation Strategy

**Decision:** Pydantic models for API validation, SQLAlchemy models for database schema

**Rationale:**
- Pydantic already in use for FastAPI request/response validation
- Type-safe validation with excellent error messages
- Clear separation: SQLAlchemy for DB, Pydantic for API
- Conversion layer between models for clean architecture

**Implementation Notes:**
- SQLAlchemy models in `app/db/models.py`
- Pydantic schemas in `app/models/` (request/response models)
- Conversion utilities in repositories or services
- Validation happens at API boundary (MCP tools)

**Affects:**
- Request/response handling
- Data validation
- Type safety

#### Caching Strategy

**Decision:** Redis with tenant-scoped key patterns

**Key Pattern:** `{tenant_id}:{resource_type}:{resource_id}`

**TTL Strategy:**
- Default: 1 hour
- Configurable per resource type
- Cache-aside pattern for reads
- Write-through for critical data

**Rationale:**
- Tenant-scoped keys prevent cross-tenant cache access
- Redis performance supports <200ms latency targets
- Flexible TTL configuration per resource type
- Cache-aside pattern provides flexibility and fault tolerance

**Implementation Notes:**
- All Redis keys must include tenant_id prefix
- Cache invalidation on data updates
- Test cache isolation in integration tests
- Monitor cache hit rates (target: >80% per PRD)

**Affects:**
- Performance optimization
- Multi-tenant isolation
- Service layer caching logic

### Authentication & Security

#### OAuth 2.0 / JWT Library

**Decision:** python-jose + authlib

**Versions:**
- python-jose (latest stable)
- authlib (latest stable)

**Rationale:**
- python-jose provides excellent JWT validation, FastAPI-friendly
- authlib provides comprehensive OAuth 2.0 server/client implementation
- Both libraries have strong FastAPI integration
- Production-proven security libraries
- Support for token refresh and revocation

**Implementation Notes:**
- python-jose for JWT token validation in authentication middleware
- authlib for OAuth 2.0 server implementation
- Token refresh mechanism for long-lived sessions
- Token revocation support for security compliance
- Test OAuth flow using authlib test utilities or mocks

**Affects:**
- Authentication middleware
- OAuth 2.0 server endpoints
- JWT token handling
- Security compliance

#### Encryption Library

**Decision:** cryptography (Python standard library)

**Version:** cryptography (latest stable)

**Rationale:**
- Industry-standard encryption library
- AES-256 support for at-rest encryption (PRD requirement)
- Field-level encryption support for PII protection
- Key management integration support
- Production-proven security

**Implementation Notes:**
- AES-256 encryption for data at rest (PRD requirement)
- Field-level encryption for PII fields (HIPAA, PCI DSS compliance)
- Key management integration for secure key storage
- Encryption/decryption utilities in `app/utils/encryption.py`

**Affects:**
- Data encryption at rest
- PII protection
- Compliance (HIPAA, PCI DSS)

#### Password Hashing

**Decision:** argon2

**Version:** argon2-cffi (latest stable)

**Rationale:**
- More secure than bcrypt (GPU-resistant, memory-hard)
- OWASP recommended for password hashing
- Better security properties for compliance requirements
- Production-proven for enterprise applications

**Implementation Notes:**
- Use argon2 for all password hashing
- Configure appropriate time and memory parameters
- Store hash parameters with hashed passwords
- Password hashing utilities in authentication service

**Affects:**
- User authentication
- API key generation (if applicable)
- Security compliance

### API & Communication Patterns

#### Error Handling Format

**Decision:** Standardized JSON error response structure

**Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "tenant_id": "optional",
    "timestamp": "ISO8601"
  }
}
```

**Rationale:**
- Consistent error format across all MCP tools
- LLM-friendly error messages for MCP clients
- Tenant_id inclusion for multi-tenant debugging
- Structured details for programmatic error handling
- ISO8601 timestamps for audit compliance

**Implementation Notes:**
- Centralized error handling in middleware or exception handlers
- Error codes defined in `app/utils/errors.py`
- Ensure error messages are clear for LLM consumption
- Include tenant_id when available for debugging
- Map all exceptions to standardized format

**Affects:**
- All MCP tool error responses
- Error handling middleware
- Client error handling

#### Rate Limiting Library

**Decision:** slowapi

**Version:** slowapi (latest stable)

**Rationale:**
- FastAPI-native rate limiting library
- Simple integration with FastAPI applications
- Redis backend support for distributed rate limiting
- Custom key function support for per-tenant rate limiting
- Production-ready for enterprise applications

**Implementation Notes:**
- Use slowapi with Redis backend for distributed rate limiting
- Custom key function to include tenant_id: `f"{tenant_id}:{get_remote_address(request)}"`
- Per-tenant rate limits based on subscription tier (Free, Basic, Enterprise)
- Default: 1000 requests/minute per tenant (per PRD)
- Return 429 status with rate limit error message
- Test rate limiting per tenant in integration tests

**Implementation Pattern:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_rate_limit_key(request):
    tenant_id = request.state.get("tenant_id", "unknown")
    return f"{tenant_id}:{get_remote_address(request)}"

limiter = Limiter(key_func=get_rate_limit_key, storage_uri="redis://...")
```

**Affects:**
- Rate limiting middleware
- Per-tenant quota enforcement
- Subscription tier management

### Infrastructure & Deployment

#### CI/CD Platform

**Decision:** GitHub Actions

**Rationale:**
- Integrated with GitHub repositories
- Excellent Kubernetes deployment support
- Easy secrets management for production credentials
- Comprehensive workflow capabilities
- Free for public repositories, reasonable pricing for private

**Implementation Notes:**
- CI/CD workflows in `.github/workflows/`
- Automated testing on pull requests
- Automated deployment to Kubernetes on main branch
- Secrets management via GitHub Secrets
- Environment-specific configurations (dev, staging, prod)

**Affects:**
- Deployment automation
- Testing automation
- Release process

#### Configuration Management

**Decision:** Pydantic Settings

**Version:** Pydantic Settings (included with Pydantic)

**Rationale:**
- Type-safe configuration management
- Environment variable support out of the box
- Built-in validation for configuration values
- Already using Pydantic for models
- Excellent FastAPI integration

**Implementation Notes:**
- Use `BaseSettings` from Pydantic for all configuration
- Environment variables loaded from `.env` files
- Configuration classes in `app/config/` directory
- Per-service configuration (database, Redis, Mem0, FAISS, etc.)
- Validation on application startup

**Affects:**
- Application configuration
- Environment management
- Service integration configuration

#### Logging Library

**Decision:** structlog

**Version:** structlog (latest stable)

**Rationale:**
- Structured JSON logging for log aggregation
- Tenant_id injection in all log entries (audit compliance)
- Performance-friendly async logging
- Excellent for production log analysis
- Industry standard for structured logging

**Implementation Notes:**
- Configure structlog to output JSON format
- Inject tenant_id into all log entries via context
- Structured logging with consistent fields (tenant_id, user_id, action, timestamp)
- Integration with log aggregation systems (ELK, Loki, etc.)
- Test log output format in tests

**Affects:**
- All application logging
- Audit log compliance
- Log aggregation and analysis

#### Monitoring & Alerting

**Decision:** Prometheus + Grafana

**Rationale:**
- Industry standard for Kubernetes monitoring
- Kubernetes-native integration
- Custom metrics support for business metrics
- Comprehensive alerting via Alertmanager
- Production-proven for enterprise applications

**Implementation Notes:**
- Prometheus metrics exposed at `/metrics` endpoint
- Custom metrics for MCP tool execution times, cache hit rates, error rates per tenant
- Grafana dashboards for visualization
- Alertmanager for proactive alerting on degradation, errors, compliance violations
- Integration with Kubernetes service discovery

**Affects:**
- System monitoring
- Performance metrics
- Alerting and incident response

### Decision Impact Analysis

**Implementation Sequence:**

1. **Foundation Layer (Week 1-2):**
   - Set up project structure (from Step 3)
   - Configure Pydantic Settings for all services
   - Set up structlog with tenant_id injection
   - Configure SQLAlchemy 2.0 async with connection pooling

2. **Data Layer (Week 2-3):**
   - Define SQLAlchemy models with tenant_id
   - Set up Alembic migrations
   - Implement RLS policies in PostgreSQL
   - Create repository pattern implementations

3. **Security Layer (Week 3-4):**
   - Implement OAuth 2.0 server with authlib
   - Set up JWT validation with python-jose
   - Implement authentication middleware
   - Configure argon2 for password hashing
   - Set up encryption utilities with cryptography

4. **API Layer (Week 4-5):**
   - Implement error handling format
   - Set up rate limiting with slowapi (tenant-scoped)
   - Configure Redis caching with tenant-scoped keys
   - Implement remaining middleware stack

5. **Infrastructure Layer (Week 5-6):**
   - Set up GitHub Actions CI/CD
   - Configure Prometheus metrics
   - Set up Grafana dashboards
   - Configure monitoring

**Cross-Component Dependencies:**

- **Authentication → All Services:** All services depend on tenant_id from authentication middleware
- **Database → Repositories → Services:** Services use repositories which use SQLAlchemy async sessions
- **Caching → Services:** Services use Redis caching for performance optimization
- **Rate Limiting → Authentication:** Rate limiting requires tenant_id from authentication
- **Logging → All Components:** All components use structlog with tenant_id context
- **Monitoring → All Components:** All components expose Prometheus metrics

**Testing Dependencies:**

- **Database Tests:** Require test database with RLS policies
- **Cache Tests:** Require test Redis instance or mocks
- **Auth Tests:** Require OAuth test utilities or mocks
- **Rate Limiting Tests:** Require test Redis instance
- **Integration Tests:** Require full test environment (database, Redis, services)

**Validation from Party Mode Review:**

All decisions validated by team review:
- ✅ SQLAlchemy 2.0 async confirmed production-ready and multi-tenant friendly
- ✅ slowapi rate limiting confirmed to support per-tenant keys via custom key function
- ✅ Error messages confirmed to be LLM-friendly for MCP clients
- ✅ Multi-tenant isolation testing strategy defined
- ✅ No blocking dependencies identified
- ✅ All decisions support MVP timeline

**Additional Considerations Identified:**

- Verify slowapi supports per-tenant rate limiting via custom key function (confirmed)
- Test multi-tenant isolation at all layers (database, cache, storage)
- Ensure error messages are LLM-friendly for MCP clients
- Set up RLS policies in PostgreSQL for tenant isolation
- Include tenant_id in all log entries for audit compliance
- Test OAuth flow using authlib test utilities or mocks
- Monitor cache hit rates (target: >80% per PRD)

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
15+ areas where AI agents could make different choices, including naming conventions, async session management, connection pooling, transaction handling, and error recovery patterns.

### Naming Patterns

#### Database Naming Conventions

**Tables:**
- Format: `snake_case`, plural
- Examples: `users`, `knowledge_documents`, `tenant_configurations`, `audit_logs`
- Rationale: PostgreSQL convention, matches Python naming

**Columns:**
- Format: `snake_case`
- Examples: `user_id`, `tenant_id`, `created_at`, `updated_at`, `email_address`
- Rationale: Consistent with table naming, Python convention

**Foreign Keys:**
- Format: `{referenced_table}_id`
- Examples: `user_id`, `tenant_id`, `document_id`
- Rationale: Clear relationship, standard PostgreSQL pattern

**Indexes:**
- Format: `idx_{table}_{column(s)}`
- Examples: `idx_users_email`, `idx_documents_tenant_id_created_at`, `idx_audit_logs_tenant_id_timestamp`
- Rationale: Clear naming, easy to identify purpose

**Constraints:**
- Primary Key: `pk_{table}` (e.g., `pk_users`)
- Foreign Key: `fk_{table}_{referenced_table}` (e.g., `fk_documents_tenants`)
- Unique: `uq_{table}_{column}` (e.g., `uq_users_email`)

#### API Naming Conventions

**MCP Tools:**
- Format: `snake_case` with `rag_` prefix
- Examples: `rag_search`, `rag_ingest_document`, `rag_get_memory`, `rag_update_memory`
- Rationale: MCP convention, clear namespace

**MCP Resources:**
- Format: `snake_case` with `rag_` prefix
- Examples: `rag_document`, `rag_memory`, `rag_tenant_config`
- Rationale: Consistent with tool naming

**REST Endpoints (if applicable):**
- Format: `snake_case`, plural
- Examples: `/api/v1/health`, `/api/v1/admin/tenants`
- Rationale: RESTful convention

#### Code Naming Conventions

**Python Functions:**
- Format: `snake_case`
- Examples: `get_user_by_id`, `create_knowledge_document`, `search_documents`
- Rationale: PEP 8 Python convention

**Python Variables:**
- Format: `snake_case`
- Examples: `tenant_id`, `user_data`, `document_content`
- Rationale: PEP 8 Python convention

**Python Classes:**
- Format: `PascalCase`
- Examples: `UserRepository`, `KnowledgeService`, `TenantMiddleware`
- Rationale: PEP 8 Python convention

**Python Constants:**
- Format: `UPPER_SNAKE_CASE`
- Examples: `MAX_RATE_LIMIT`, `DEFAULT_CACHE_TTL`, `DEFAULT_POOL_SIZE`
- Rationale: PEP 8 Python convention

**File Naming:**
- Format: `snake_case.py`
- Examples: `user_repository.py`, `knowledge_service.py`, `tenant_middleware.py`
- Rationale: Python convention, matches module naming

**Test File Naming:**
- Format: `test_{module_name}.py`
- Examples: `test_user_repository.py`, `test_knowledge_service.py`
- Rationale: pytest convention, clear test organization

### Structure Patterns

#### Project Organization

**Test Organization:**
- Location: `tests/` directory at project root
- Structure: Mirror `app/` structure
- Examples:
  - `app/services/knowledge_service.py` → `tests/services/test_knowledge_service.py`
  - `app/db/repositories/user_repository.py` → `tests/db/repositories/test_user_repository.py`
- Rationale: Clear test organization, easy to find corresponding tests

**Test Naming:**
- Format: `test_{function_name}_{scenario}`
- Examples:
  - `test_get_user_by_id_success`
  - `test_get_user_by_id_not_found`
  - `test_create_document_with_invalid_tenant_id`
- Rationale: Clear test purpose, easy to identify test scenarios

**Service Layer Organization:**
- Location: `app/services/`
- Pattern: One service per domain
- Examples: `knowledge_service.py`, `memory_service.py`, `tenant_service.py`
- Rationale: Clear separation of concerns, single responsibility

**Repository Pattern:**
- Location: `app/db/repositories/`
- Pattern: One repository per entity
- Examples: `user_repository.py`, `document_repository.py`, `tenant_repository.py`
- Rationale: Data access abstraction, testability

### Format Patterns

#### API Response Formats

**Success Response:**
- Format: Direct data (no wrapper)
- Rationale: MCP tools return data directly, no need for wrapper
- Example:
```json
{
  "documents": [...],
  "total": 42
}
```

**Error Response:**
- Format: Standardized error structure (defined in Step 4)
- Structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "tenant_id": "optional",
    "timestamp": "ISO8601"
  }
}
```
- Rationale: Consistent error handling, LLM-friendly

**Date/Time Format:**
- Format: ISO8601 strings
- Examples: `"2026-01-04T12:34:56Z"`, `"2026-01-04T12:34:56.123Z"`
- Rationale: Standard format, timezone-aware

#### Data Exchange Formats

**JSON Field Naming:**
- Format: `snake_case` for all JSON fields
- Rationale: Python convention, consistent with database columns
- Examples: `user_id`, `tenant_id`, `created_at`, `document_content`

**Boolean Representations:**
- Format: `true`/`false` (JSON boolean)
- Rationale: Standard JSON, not `1`/`0`

**Null Handling:**
- Format: `null` (JSON null)
- Rationale: Standard JSON null representation

**Array vs Object:**
- Single item: Object (e.g., `{"id": 1, "name": "..."}`)
- Multiple items: Array (e.g., `[{"id": 1}, {"id": 2}]`)
- Rationale: Clear distinction, consistent API

#### Logging Format

**Structured Logging:**
- Format: JSON with structlog
- Required Fields: `tenant_id`, `user_id` (when available), `action`, `timestamp`, `level`
- Example:
```json
{
  "tenant_id": "t_123",
  "user_id": "u_456",
  "action": "rag_search",
  "timestamp": "2026-01-04T12:34:56Z",
  "level": "info",
  "message": "Search executed successfully",
  "query": "loan application",
  "result_count": 5
}
```
- Rationale: Structured logs for aggregation, audit compliance

### Communication Patterns

#### Async/Await Patterns

**General Rules:**
- All I/O operations use `async/await`
- Database operations: Use `AsyncSession` from SQLAlchemy
- Service methods: All async (`async def method_name()`)
- Repository methods: All async (`async def method_name()`)
- Rationale: Non-blocking I/O, performance optimization

**Session Management Pattern (CRITICAL - Prevents Connection Leaks):**

**FastAPI Dependency Injection:**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import Depends

# Engine configuration with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Base pool size
    max_overflow=10,        # Additional connections under load
    pool_timeout=30,        # Fail fast if pool exhausted
    pool_recycle=3600,      # Recycle connections hourly
    echo=False,             # Set to True for SQL logging in dev
)

# Session factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Prevent lazy loading issues
    class_=AsyncSession
)

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides database session.
    Automatically closes session on request completion or exception.
    """
    async with async_session() as session:
        yield session
```

**Usage in MCP Tools:**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@mcp.tool
async def rag_search(
    query: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    MCP tool that uses database session via dependency injection.
    Session automatically managed by FastAPI.
    """
    # Use session - automatically closed when function completes
    result = await db.execute(select(Document).where(...))
    return {"documents": result.scalars().all()}
```

**Usage in Services:**
```python
from sqlalchemy.ext.asyncio import AsyncSession

class KnowledgeService:
    async def search_documents(
        self,
        tenant_id: str,
        query: str,
        db: AsyncSession
    ) -> list[Document]:
        """
        Service method receives session as parameter.
        Session lifecycle managed by caller (FastAPI dependency).
        """
        # Short-lived operation - session closed by dependency
        result = await db.execute(
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .where(Document.content.contains(query))
        )
        return result.scalars().all()
```

**Transaction Pattern:**
```python
async def create_document_with_metadata(
    tenant_id: str,
    document_data: dict,
    db: AsyncSession
) -> Document:
    """
    Use async context manager for transactions.
    Automatically commits on success, rolls back on exception.
    """
    async with db.begin():
        # Create document
        document = Document(tenant_id=tenant_id, **document_data)
        db.add(document)
        await db.flush()  # Get document.id
        
        # Create metadata in same transaction
        metadata = DocumentMetadata(document_id=document.id, ...)
        db.add(metadata)
        
        # Transaction commits automatically on context exit
        return document
```

**Eager Loading Pattern (CRITICAL - Prevents Lazy Loading Issues):**
```python
from sqlalchemy.orm import selectinload, joinedload

# Use selectinload for one-to-many relationships
async def get_document_with_metadata(
    document_id: str,
    tenant_id: str,
    db: AsyncSession
) -> Document:
    """
    Use eager loading to avoid lazy loading issues in async context.
    """
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.tenant_id == tenant_id)
        .options(selectinload(Document.metadata))  # Eager load metadata
    )
    return result.scalar_one_or_none()

# Use joinedload for many-to-one relationships
async def get_documents_with_tenant(
    tenant_id: str,
    db: AsyncSession
) -> list[Document]:
    """
    Use joinedload for foreign key relationships.
    """
    result = await db.execute(
        select(Document)
        .where(Document.tenant_id == tenant_id)
        .options(joinedload(Document.tenant))  # Eager load tenant
    )
    return result.scalars().all()
```

**Background Task Pattern (For Long Operations):**
```python
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

@mcp.tool
async def rag_ingest_large_document(
    document_data: dict,
    tenant_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    For long-running operations, use background tasks.
    Returns immediately, processes in background.
    """
    # Create document record immediately
    document = Document(tenant_id=tenant_id, status="processing", ...)
    db.add(document)
    await db.commit()
    
    # Add background task for processing
    background_tasks.add_task(
        process_large_document,
        document_id=document.id,
        tenant_id=tenant_id
    )
    
    return {"document_id": document.id, "status": "processing"}

async def process_large_document(document_id: str, tenant_id: str):
    """
    Background task that processes document.
    Uses its own database session.
    """
    async with async_session() as session:
        # Long-running operation with dedicated session
        # Process document, update status, etc.
        pass
```

**Connection Pool Monitoring:**
```python
from sqlalchemy import event
from sqlalchemy.pool import Pool
import structlog

logger = structlog.get_logger()

@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log connection creation."""
    logger.info("database_connection_created")

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout."""
    logger.info("database_connection_checked_out", pool_size=connection_proxy._pool.size())

@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection checkin."""
    logger.info("database_connection_checked_in")
```

#### Database Transaction Patterns

**Transaction Scope:**
- Pattern: Short-lived, operation-scoped transactions
- Use `async with db.begin()` for explicit transactions
- Never hold sessions across multiple operations
- Rationale: Prevents connection pool exhaustion, ensures data consistency

**Transaction Example:**
```python
async def transfer_document_ownership(
    document_id: str,
    from_tenant_id: str,
    to_tenant_id: str,
    db: AsyncSession
) -> Document:
    """
    Transaction ensures atomicity of multi-step operation.
    """
    async with db.begin():
        # Step 1: Get document
        document = await db.get(Document, document_id)
        if document.tenant_id != from_tenant_id:
            raise ValueError("Document not owned by source tenant")
        
        # Step 2: Update ownership
        document.tenant_id = to_tenant_id
        await db.flush()
        
        # Step 3: Create audit log
        audit_log = AuditLog(
            action="document_transferred",
            tenant_id=to_tenant_id,
            document_id=document_id
        )
        db.add(audit_log)
        
        # Transaction commits automatically
        return document
```

#### Configuration Access Patterns

**Pydantic Settings Pattern:**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Database configuration."""
    database_url: str
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    
    class Config:
        env_prefix = "DB_"

@lru_cache()
def get_database_settings() -> DatabaseSettings:
    """Cached settings instance."""
    return DatabaseSettings()

# Usage
settings = get_database_settings()
engine = create_async_engine(settings.database_url, ...)
```

**Dependency Injection Pattern:**
```python
from fastapi import Depends

def get_settings() -> DatabaseSettings:
    """FastAPI dependency for settings."""
    return get_database_settings()

# Usage in endpoints
@mcp.tool
async def some_tool(
    settings: DatabaseSettings = Depends(get_settings)
):
    # Use settings
    pass
```

#### Tenant Isolation Patterns

**Tenant ID Extraction:**
- Pattern: Extracted in middleware, stored in `request.state["tenant_id"]`
- All service methods receive `tenant_id` as first parameter
- All repository methods filter by `tenant_id`
- All database queries include `tenant_id` in WHERE clause

**Service Pattern:**
```python
class KnowledgeService:
    async def search_documents(
        self,
        tenant_id: str,  # First parameter - always required
        query: str,
        db: AsyncSession
    ) -> list[Document]:
        """
        Service method always requires tenant_id.
        Enforces tenant isolation at service layer.
        """
        result = await db.execute(
            select(Document)
            .where(Document.tenant_id == tenant_id)  # Always filter by tenant
            .where(Document.content.contains(query))
        )
        return result.scalars().all()
```

**Repository Pattern:**
```python
class DocumentRepository:
    async def get_by_id(
        self,
        document_id: str,
        tenant_id: str,  # Always required
        db: AsyncSession
    ) -> Document | None:
        """
        Repository method always requires tenant_id.
        Enforces tenant isolation at data layer.
        """
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id)
            .where(Document.tenant_id == tenant_id)  # Always filter by tenant
        )
        return result.scalar_one_or_none()
```

**MCP Tool Pattern:**
```python
from fastmcp import Context

@mcp.tool
async def rag_search(
    query: str,
    ctx: Context
) -> dict:
    """
    MCP tool extracts tenant_id from context.
    Tenant_id injected by middleware.
    """
    tenant_id = ctx.state.get("tenant_id")
    if not tenant_id:
        raise ValueError("tenant_id required")
    
    service = KnowledgeService()
    documents = await service.search_documents(
        tenant_id=tenant_id,  # Passed from context
        query=query,
        db=await get_db()
    )
    return {"documents": documents}
```

### Process Patterns

#### Error Handling Patterns

**Exception Hierarchy:**
```python
# Base exception
class RAGSystemError(Exception):
    """Base exception for RAG system."""
    pass

# Domain-specific exceptions
class TenantNotFoundError(RAGSystemError):
    """Tenant not found."""
    pass

class DocumentNotFoundError(RAGSystemError):
    """Document not found."""
    pass

class UnauthorizedError(RAGSystemError):
    """Unauthorized access."""
    pass
```

**Error Handling in MCP Tools:**
```python
from app.utils.errors import (
    RAGSystemError,
    TenantNotFoundError,
    DocumentNotFoundError
)

@mcp.tool
async def rag_search(
    query: str,
    ctx: Context
) -> dict:
    """
    MCP tool with error handling.
    Converts exceptions to standardized error format.
    """
    try:
        tenant_id = ctx.state.get("tenant_id")
        if not tenant_id:
            raise UnauthorizedError("tenant_id required")
        
        service = KnowledgeService()
        documents = await service.search_documents(
            tenant_id=tenant_id,
            query=query,
            db=await get_db()
        )
        return {"documents": documents}
    
    except TenantNotFoundError as e:
        raise ValueError(f"Tenant not found: {e}")
    except DocumentNotFoundError as e:
        raise ValueError(f"Document not found: {e}")
    except RAGSystemError as e:
        raise ValueError(f"System error: {e}")
    except Exception as e:
        # Log unexpected errors
        logger.error("unexpected_error", error=str(e), tenant_id=tenant_id)
        raise ValueError("Internal server error")
```

**Error Handling in Services:**
```python
class KnowledgeService:
    async def get_document(
        self,
        tenant_id: str,
        document_id: str,
        db: AsyncSession
    ) -> Document:
        """
        Service method raises domain-specific exceptions.
        """
        document = await db.get(Document, document_id)
        if not document:
            raise DocumentNotFoundError(f"Document {document_id} not found")
        
        if document.tenant_id != tenant_id:
            raise UnauthorizedError("Document not accessible")
        
        return document
```

### Enforcement Guidelines

**All AI Agents MUST:**

1. **Use FastAPI dependency injection for database sessions:**
   - Always use `db: AsyncSession = Depends(get_db)` in MCP tools
   - Never create sessions manually outside of dependency injection
   - Never hold sessions across multiple operations

2. **Include tenant_id in all database queries:**
   - All service methods must accept `tenant_id` as first parameter
   - All repository methods must accept `tenant_id` as parameter
   - All database queries must filter by `tenant_id` in WHERE clause

3. **Use eager loading for relationships:**
   - Use `selectinload()` for one-to-many relationships
   - Use `joinedload()` for many-to-one relationships
   - Never rely on lazy loading in async context

4. **Follow naming conventions:**
   - Database: `snake_case` for tables, columns, indexes
   - Python code: `snake_case` for functions/variables, `PascalCase` for classes
   - MCP tools: `rag_{tool_name}` format

5. **Use structured logging:**
   - Always include `tenant_id` in log entries
   - Use structlog for all logging
   - Include relevant context in log entries

6. **Handle errors consistently:**
   - Raise domain-specific exceptions in services
   - Convert to standardized error format in MCP tools
   - Always log unexpected errors

7. **Keep database operations fast:**
   - Target <200ms per operation (per PRD)
   - Use background tasks for long operations
   - Use caching to reduce database load

**Pattern Enforcement:**

- **Code Review**: Check for dependency injection usage, tenant_id inclusion, eager loading
- **Linting**: Use ruff or black for code formatting, mypy for type checking
- **Testing**: Integration tests verify session management, connection pool usage
- **Monitoring**: Track connection pool metrics, session leaks, query performance

**Pattern Examples:**

**Good Example - Session Management:**
```python
@mcp.tool
async def rag_search(
    query: str,
    ctx: Context,
    db: AsyncSession = Depends(get_db)  # ✅ Dependency injection
) -> dict:
    tenant_id = ctx.state.get("tenant_id")
    service = KnowledgeService()
    documents = await service.search_documents(
        tenant_id=tenant_id,  # ✅ Tenant isolation
        query=query,
        db=db  # ✅ Session from dependency
    )
    return {"documents": documents}
# ✅ Session automatically closed by FastAPI
```

**Anti-Pattern - Manual Session:**
```python
@mcp.tool
async def rag_search(
    query: str,
    ctx: Context
) -> dict:
    # ❌ Manual session creation - risk of leaks
    async with async_session() as session:
        documents = await session.execute(...)
        return {"documents": documents}
    # ❌ Session management not integrated with FastAPI lifecycle
```

**Good Example - Eager Loading:**
```python
async def get_document_with_metadata(
    document_id: str,
    tenant_id: str,
    db: AsyncSession
) -> Document:
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.tenant_id == tenant_id)
        .options(selectinload(Document.metadata))  # ✅ Eager loading
    )
    return result.scalar_one_or_none()
```

**Anti-Pattern - Lazy Loading:**
```python
async def get_document_with_metadata(
    document_id: str,
    tenant_id: str,
    db: AsyncSession
) -> Document:
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.tenant_id == tenant_id)
        # ❌ No eager loading - will fail in async context
    )
    document = result.scalar_one_or_none()
    # ❌ Accessing document.metadata here will fail (lazy loading)
    return document
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
rag-system/
├── README.md                          # Project documentation
├── pyproject.toml                      # Python project configuration (Poetry/uv)
├── requirements.txt                   # Python dependencies (pip)
├── requirements-dev.txt               # Development dependencies
├── .env.example                       # Environment variable template
├── .env                               # Local environment variables (gitignored)
├── .gitignore                         # Git ignore patterns
├── .python-version                    # Python version specification
├── .pre-commit-config.yaml            # Pre-commit hooks configuration
├── ruff.toml                          # Ruff linter configuration
├── mypy.ini                            # MyPy type checker configuration
│
├── .github/                           # GitHub Configuration
│   └── workflows/
│       ├── ci.yml                     # Continuous Integration workflow
│       ├── cd.yml                     # Continuous Deployment workflow
│       └── security.yml               # Security scanning workflow
│
├── app/                               # Application Source Code
│   ├── __init__.py
│   ├── main.py                        # FastAPI app + FastMCP mounting, combined lifespan
│   │
│   ├── mcp/                           # MCP Server Layer (Primary Interface)
│   │   ├── __init__.py
│   │   ├── server.py                  # FastMCP server instance initialization
│   │   │
│   │   ├── tools/                     # MCP Tools (RAG Operations)
│   │   │   ├── __init__.py
│   │   │   ├── knowledge_base.py     # Knowledge base operations (search, ingest, delete, list)
│   │   │   ├── memory.py             # Memory operations (get, set, update, search)
│   │   │   ├── tenant.py             # Tenant management operations (register, configure, list)
│   │   │   ├── session.py            # Session management operations (create, get, resume)
│   │   │   ├── audit.py               # Audit log query operations
│   │   │   ├── templates.py          # Template management operations (list, get)
│   │   │   └── monitoring.py         # Monitoring operations (health, stats, analytics)
│   │   │
│   │   ├── resources/                 # MCP Resources (if needed)
│   │   │   ├── __init__.py
│   │   │   └── document_resource.py  # Document resource template
│   │   │
│   │   └── middleware/                # MCP Middleware Stack
│   │       ├── __init__.py
│   │       ├── auth.py                # Authentication middleware (OAuth, API keys)
│   │       ├── tenant.py              # Tenant extraction and isolation middleware
│   │       ├── authorization.py       # RBAC authorization middleware
│   │       ├── audit.py                # Audit logging middleware
│   │       ├── observability.py       # Langfuse integration middleware
│   │       └── rate_limit.py          # Rate limiting middleware
│   │
│   ├── api/                           # Optional REST API Endpoints
│   │   ├── __init__.py
│   │   ├── admin.py                   # Admin operations (if needed)
│   │   ├── health.py                  # Health check endpoints (/health, /ready, /live)
│   │   └── monitoring.py              # Monitoring/metrics endpoints (/metrics for Prometheus)
│   │
│   ├── services/                      # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── knowledge_service.py       # Knowledge base business logic
│   │   ├── memory_service.py          # Memory management (Mem0 integration)
│   │   ├── search_service.py          # Hybrid search (FAISS + Meilisearch)
│   │   ├── vector_service.py          # FAISS vector operations
│   │   ├── keyword_service.py         # Meilisearch keyword operations
│   │   ├── tenant_service.py          # Tenant management logic
│   │   ├── session_service.py         # Session management logic
│   │   ├── backup_service.py          # Backup and restore operations
│   │   └── embedding_service.py       # Text embedding generation (for vector search)
│   │
│   ├── models/                        # Pydantic Models (Request/Response)
│   │   ├── __init__.py
│   │   ├── knowledge.py               # Knowledge base models (Document, SearchRequest, etc.)
│   │   ├── memory.py                  # Memory models (Memory, MemoryUpdate, etc.)
│   │   ├── tenant.py                  # Tenant models (Tenant, TenantConfig, etc.)
│   │   ├── session.py                 # Session models (Session, SessionContext, etc.)
│   │   ├── audit.py                   # Audit log models (AuditLog, AuditQuery, etc.)
│   │   ├── template.py                # Template models (Template, TemplateConfig, etc.)
│   │   └── common.py                  # Common models (ErrorResponse, Pagination, etc.)
│   │
│   ├── db/                            # Database Layer
│   │   ├── __init__.py
│   │   ├── database.py                # Database connection and session management (get_db dependency)
│   │   ├── base.py                    # Base model class for SQLAlchemy models
│   │   │
│   │   ├── models/                    # SQLAlchemy ORM Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py                # User model
│   │   │   ├── tenant.py              # Tenant model
│   │   │   ├── document.py            # Document model
│   │   │   ├── memory.py              # Memory model
│   │   │   ├── session.py             # Session model
│   │   │   ├── audit_log.py           # AuditLog model
│   │   │   ├── template.py            # Template model
│   │   │   └── tenant_config.py       # TenantConfig model
│   │   │
│   │   ├── repositories/              # Data Access Layer
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py     # Base repository class
│   │   │   ├── user_repository.py     # User data access
│   │   │   ├── tenant_repository.py   # Tenant data access
│   │   │   ├── document_repository.py # Document data access
│   │   │   ├── memory_repository.py   # Memory data access
│   │   │   ├── session_repository.py  # Session data access
│   │   │   ├── audit_repository.py    # Audit log data access
│   │   │   └── template_repository.py  # Template data access
│   │   │
│   │   └── migrations/                # Alembic Migrations
│   │       ├── versions/              # Migration versions
│   │       ├── env.py                 # Alembic environment
│   │       └── script.py.mako         # Migration template
│   │
│   ├── config/                         # Configuration Management
│   │   ├── __init__.py
│   │   ├── settings.py                # Base Pydantic Settings
│   │   ├── database.py                # Database configuration
│   │   ├── redis.py                   # Redis configuration
│   │   ├── mem0.py                    # Mem0 configuration
│   │   ├── faiss.py                   # FAISS configuration
│   │   ├── meilisearch.py             # Meilisearch configuration
│   │   ├── minio.py                   # MinIO configuration
│   │   ├── langfuse.py                # Langfuse configuration
│   │   └── oauth.py                   # OAuth 2.0 configuration
│   │
│   ├── utils/                          # Utility Functions
│   │   ├── __init__.py
│   │   ├── encryption.py              # Encryption utilities (AES-256, field-level)
│   │   ├── validation.py              # Input validation utilities
│   │   ├── errors.py                  # Error handling utilities (exception classes)
│   │   ├── logging.py                 # Logging configuration (structlog setup)
│   │   └── tenant_context.py         # Tenant context utilities
│   │
│   └── integrations/                  # External Service Integrations
│       ├── __init__.py
│       ├── mem0_client.py             # Mem0 API client
│       ├── faiss_client.py            # FAISS index management
│       ├── meilisearch_client.py      # Meilisearch client
│       ├── minio_client.py            # MinIO client
│       └── langfuse_client.py         # Langfuse client
│
├── tests/                              # Test Suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest configuration and fixtures
│   │
│   ├── unit/                           # Unit Tests
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── test_knowledge_service.py
│   │   │   ├── test_memory_service.py
│   │   │   ├── test_search_service.py
│   │   │   └── test_tenant_service.py
│   │   ├── repositories/
│   │   │   ├── test_document_repository.py
│   │   │   ├── test_memory_repository.py
│   │   │   └── test_tenant_repository.py
│   │   ├── middleware/
│   │   │   ├── test_auth_middleware.py
│   │   │   ├── test_tenant_middleware.py
│   │   │   └── test_rate_limit_middleware.py
│   │   └── utils/
│   │       ├── test_encryption.py
│   │       └── test_validation.py
│   │
│   ├── integration/                    # Integration Tests
│   │   ├── __init__.py
│   │   ├── test_mcp_tools.py          # MCP tool integration tests
│   │   ├── test_services.py           # Service integration tests
│   │   ├── test_repositories.py       # Repository integration tests
│   │   ├── test_middleware_stack.py   # Middleware integration tests
│   │   └── test_multi_tenant_isolation.py  # Tenant isolation tests
│   │
│   ├── e2e/                            # End-to-End Tests
│   │   ├── __init__.py
│   │   ├── test_user_journeys.py      # User journey tests
│   │   ├── test_tenant_onboarding.py  # Tenant onboarding flow
│   │   └── test_backup_restore.py     # Backup/restore flow
│   │
│   └── fixtures/                       # Test Fixtures
│       ├── __init__.py
│       ├── database.py                # Database fixtures
│       ├── tenants.py                 # Tenant fixtures
│       ├── documents.py                # Document fixtures
│       └── mcp_client.py              # MCP client fixtures
│
├── docker/                             # Docker Configuration
│   ├── Dockerfile                      # Production Dockerfile
│   ├── Dockerfile.dev                  # Development Dockerfile
│   └── docker-compose.yml              # Local development environment
│
├── kubernetes/                         # Kubernetes Manifests
│   ├── base/                           # Base Kubernetes resources
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   └── secrets.yaml
│   ├── deployments/                    # Deployment manifests
│   │   ├── app-deployment.yaml
│   │   ├── postgres-deployment.yaml
│   │   ├── redis-deployment.yaml
│   │   └── mem0-deployment.yaml
│   ├── services/                       # Service manifests
│   │   ├── app-service.yaml
│   │   ├── postgres-service.yaml
│   │   └── redis-service.yaml
│   ├── ingress/                        # Ingress configuration
│   │   └── ingress.yaml
│   └── monitoring/                     # Monitoring resources
│       ├── prometheus-config.yaml
│       └── grafana-dashboard.yaml
│
├── scripts/                            # Utility Scripts
│   ├── backup.py                       # Backup script (PostgreSQL, FAISS, Mem0)
│   ├── restore.py                      # Restore script
│   ├── migrate.py                      # Migration helper script
│   ├── seed_data.py                    # Seed test data
│   └── health_check.py                 # Health check script
│
└── docs/                               # Documentation
    ├── api/                            # API documentation
    │   ├── mcp-tools.md                # MCP tools documentation
    │   └── rest-endpoints.md           # REST endpoints documentation
    ├── architecture/                   # Architecture documentation
    │   ├── overview.md
    │   └── data-flow.md
    ├── deployment/                     # Deployment documentation
    │   ├── kubernetes.md
    │   └── docker.md
    └── development/                    # Development documentation
        ├── setup.md
        └── contributing.md
```

### Architectural Boundaries

#### API Boundaries

**MCP Server Interface (Primary):**
- **Endpoint**: `/mcp/` (mounted FastMCP server)
- **Protocol**: MCP Protocol (Model Context Protocol)
- **Authentication**: OAuth 2.0 Bearer tokens or API keys
- **Entry Point**: `app/mcp/server.py` → `app/mcp/tools/`
- **Boundary**: All core functionality exposed via MCP tools

**REST API Interface (Optional/Admin):**
- **Endpoints**: `/api/v1/health`, `/api/v1/metrics`, `/api/v1/admin/*`
- **Protocol**: HTTP/REST
- **Authentication**: OAuth 2.0 or API keys
- **Entry Point**: `app/api/` → `app/services/`
- **Boundary**: Admin operations, health checks, monitoring only

**Internal Service Boundaries:**
- **Services → Repositories**: Services call repositories, never direct database access
- **MCP Tools → Services**: MCP tools call services, services handle business logic
- **Services → Integrations**: Services call integration clients (Mem0, FAISS, etc.)

#### Component Boundaries

**MCP Layer:**
- **Location**: `app/mcp/`
- **Responsibility**: MCP protocol handling, tool registration, middleware execution
- **Dependencies**: Services, Models, Config
- **Boundary**: No direct database access, no direct external service calls

**Service Layer:**
- **Location**: `app/services/`
- **Responsibility**: Business logic, orchestration, validation
- **Dependencies**: Repositories, Integration clients, Models
- **Boundary**: No direct database access, no MCP protocol knowledge

**Repository Layer:**
- **Location**: `app/db/repositories/`
- **Responsibility**: Data access, query construction, tenant filtering
- **Dependencies**: Database models, Database session
- **Boundary**: No business logic, no external service calls

**Integration Layer:**
- **Location**: `app/integrations/`
- **Responsibility**: External service clients (Mem0, FAISS, Meilisearch, MinIO, Langfuse)
- **Dependencies**: Config, Utils
- **Boundary**: No business logic, no database access

#### Data Boundaries

**Database Schema Boundaries:**
- **Location**: `app/db/models/`
- **Tenant Isolation**: All tables include `tenant_id` column
- **RLS Policies**: Row-Level Security policies enforce tenant isolation
- **Access Pattern**: All queries filtered by `tenant_id` at repository layer

**Caching Boundaries:**
- **Location**: Redis (external service)
- **Key Pattern**: `{tenant_id}:{resource_type}:{resource_id}`
- **Access Pattern**: Services access cache, repositories don't
- **Boundary**: Cache-aside pattern, services handle cache logic

**Object Storage Boundaries:**
- **Location**: MinIO (external service)
- **Bucket Pattern**: Tenant-scoped buckets or tenant-prefixed paths
- **Access Pattern**: Services access MinIO via integration client
- **Boundary**: Services handle storage logic, repositories don't

**Vector Store Boundaries:**
- **Location**: FAISS indices (tenant-partitioned)
- **Index Pattern**: One index per tenant
- **Access Pattern**: Vector service manages indices, search service queries
- **Boundary**: Vector service handles FAISS operations, services use vector service

### Requirements to Structure Mapping

#### Functional Requirements Mapping

**Knowledge Base Operations (9 FRs) → `app/mcp/tools/knowledge_base.py`, `app/services/knowledge_service.py`, `app/db/repositories/document_repository.py`**
- `rag_search` → `app/mcp/tools/knowledge_base.py::rag_search()`
- `rag_ingest_document` → `app/mcp/tools/knowledge_base.py::rag_ingest_document()`
- `rag_delete_document` → `app/mcp/tools/knowledge_base.py::rag_delete_document()`
- `rag_list_documents` → `app/mcp/tools/knowledge_base.py::rag_list_documents()`
- Document versioning → `app/services/knowledge_service.py::version_document()`
- Document retrieval → `app/services/knowledge_service.py::get_document()`

**Memory Operations (5 FRs) → `app/mcp/tools/memory.py`, `app/services/memory_service.py`, `app/integrations/mem0_client.py`**
- `rag_get_memory` → `app/mcp/tools/memory.py::rag_get_memory()`
- `rag_set_memory` → `app/mcp/tools/memory.py::rag_set_memory()`
- `rag_update_memory` → `app/mcp/tools/memory.py::rag_update_memory()`
- `rag_search_memory` → `app/mcp/tools/memory.py::rag_search_memory()`
- Session context storage → `app/services/session_service.py::store_context()`

**Tenant Management (8 FRs) → `app/mcp/tools/tenant.py`, `app/services/tenant_service.py`, `app/db/repositories/tenant_repository.py`**
- `rag_register_tenant` → `app/mcp/tools/tenant.py::rag_register_tenant()`
- `rag_list_templates` → `app/mcp/tools/templates.py::rag_list_templates()`
- `rag_get_template` → `app/mcp/tools/templates.py::rag_get_template()`
- Tenant configuration → `app/services/tenant_service.py::configure_tenant()`
- Data isolation → `app/db/repositories/*` (all repositories filter by tenant_id)

**Authentication & Authorization (6 FRs) → `app/mcp/middleware/auth.py`, `app/mcp/middleware/authorization.py`, `app/config/oauth.py`**
- OAuth 2.0 authentication → `app/mcp/middleware/auth.py::authenticate_request()`
- API key validation → `app/mcp/middleware/auth.py::validate_api_key()`
- RBAC enforcement → `app/mcp/middleware/authorization.py::authorize_tool_access()`
- Role-based data access → `app/services/*` (all services check roles)

**Search Capabilities (5 FRs) → `app/services/search_service.py`, `app/services/vector_service.py`, `app/services/keyword_service.py`**
- Vector search (FAISS) → `app/services/vector_service.py::search()`
- Keyword search (Meilisearch) → `app/services/keyword_service.py::search()`
- Hybrid retrieval → `app/services/search_service.py::hybrid_search()`
- Cross-modal search (Phase 2) → `app/services/search_service.py::cross_modal_search()`

**Session Management (3 FRs) → `app/mcp/tools/session.py`, `app/services/session_service.py`, `app/db/repositories/session_repository.py`**
- Session continuity → `app/services/session_service.py::resume_session()`
- Context-aware search → `app/services/search_service.py::context_aware_search()`
- Returning user recognition → `app/services/session_service.py::recognize_user()`

**Compliance & Audit (5 FRs) → `app/mcp/middleware/audit.py`, `app/mcp/tools/audit.py`, `app/db/repositories/audit_repository.py`**
- Comprehensive audit logging → `app/mcp/middleware/audit.py::log_audit_event()`
- `rag_query_audit_logs` → `app/mcp/tools/audit.py::rag_query_audit_logs()`
- HIPAA compliance → `app/utils/encryption.py` (field-level encryption)
- PCI DSS compliance → `app/utils/encryption.py` (data encryption)
- GDPR compliance → `app/services/tenant_service.py::export_data()`

**Monitoring & Analytics (6 FRs) → `app/mcp/tools/monitoring.py`, `app/mcp/middleware/observability.py`, `app/api/monitoring.py`**
- Usage statistics → `app/mcp/tools/monitoring.py::rag_get_usage_stats()`
- Search analytics → `app/services/search_service.py::get_analytics()`
- Memory analytics → `app/services/memory_service.py::get_analytics()`
- Health monitoring → `app/api/health.py::health_check()`
- Langfuse integration → `app/mcp/middleware/observability.py::track_tool_call()`
- Prometheus metrics → `app/api/monitoring.py::metrics()`

**Backup & Recovery (5 FRs) → `app/services/backup_service.py`, `scripts/backup.py`, `scripts/restore.py`**
- Backup operations → `app/services/backup_service.py::backup_tenant_data()`
- Restore operations → `app/services/backup_service.py::restore_tenant_data()`
- Index rebuild → `app/services/backup_service.py::rebuild_index()`
- Backup validation → `app/services/backup_service.py::validate_backup()`

#### Cross-Cutting Concerns Mapping

**Multi-Tenancy:**
- **Data Isolation**: `app/db/models/*` (all models include tenant_id), `app/db/repositories/*` (all queries filter by tenant_id)
- **Resource Isolation**: `app/services/vector_service.py` (tenant-scoped FAISS indices), `app/services/memory_service.py` (tenant-scoped memory stores)
- **Configuration Isolation**: `app/db/models/tenant_config.py`, `app/services/tenant_service.py`

**Authentication & Security:**
- **OAuth 2.0**: `app/mcp/middleware/auth.py`, `app/config/oauth.py`
- **Encryption**: `app/utils/encryption.py`
- **Password Hashing**: `app/utils/encryption.py` (argon2)
- **API Keys**: `app/mcp/middleware/auth.py::validate_api_key()`

**Observability:**
- **Langfuse Integration**: `app/mcp/middleware/observability.py`
- **Structured Logging**: `app/utils/logging.py` (structlog configuration)
- **Metrics**: `app/api/monitoring.py` (Prometheus metrics)
- **Health Checks**: `app/api/health.py`

**Error Handling:**
- **Exception Classes**: `app/utils/errors.py`
- **Error Formatting**: `app/mcp/tools/*` (all tools use standardized error format)
- **Error Logging**: `app/utils/logging.py` (error logging utilities)

### Integration Points

#### Internal Communication

**MCP Tools → Services:**
- **Pattern**: MCP tools call service methods
- **Example**: `app/mcp/tools/knowledge_base.py::rag_search()` → `app/services/knowledge_service.py::search_documents()`
- **Data Flow**: Request → Service → Repository → Database

**Services → Repositories:**
- **Pattern**: Services call repository methods with tenant_id
- **Example**: `app/services/knowledge_service.py::get_document()` → `app/db/repositories/document_repository.py::get_by_id()`
- **Data Flow**: Service → Repository → Database (with tenant filtering)

**Services → Integration Clients:**
- **Pattern**: Services call integration clients for external services
- **Example**: `app/services/memory_service.py::get_memory()` → `app/integrations/mem0_client.py::get_memory()`
- **Data Flow**: Service → Integration Client → External Service

**Middleware → Services:**
- **Pattern**: Middleware injects context (tenant_id, user_id) into request state
- **Example**: `app/mcp/middleware/tenant.py` → extracts tenant_id → stores in `ctx.state["tenant_id"]`
- **Data Flow**: Request → Middleware Stack → MCP Tool → Service

#### External Integrations

**Mem0 Integration:**
- **Client**: `app/integrations/mem0_client.py`
- **Service**: `app/services/memory_service.py`
- **Configuration**: `app/config/mem0.py`
- **Fallback**: Redis (if Mem0 unavailable)

**FAISS Integration:**
- **Client**: `app/integrations/faiss_client.py`
- **Service**: `app/services/vector_service.py`
- **Configuration**: `app/config/faiss.py`
- **Storage**: Tenant-partitioned indices

**Meilisearch Integration:**
- **Client**: `app/integrations/meilisearch_client.py`
- **Service**: `app/services/keyword_service.py`
- **Configuration**: `app/config/meilisearch.py`
- **Storage**: Tenant-scoped indexes

**MinIO Integration:**
- **Client**: `app/integrations/minio_client.py`
- **Service**: `app/services/knowledge_service.py` (for document storage)
- **Configuration**: `app/config/minio.py`
- **Storage**: Tenant-scoped buckets

**Langfuse Integration:**
- **Client**: `app/integrations/langfuse_client.py`
- **Middleware**: `app/mcp/middleware/observability.py`
- **Configuration**: `app/config/langfuse.py`
- **Tracking**: All MCP tool calls logged to Langfuse

**PostgreSQL Integration:**
- **Connection**: `app/db/database.py` (AsyncSession, connection pooling)
- **Models**: `app/db/models/`
- **Repositories**: `app/db/repositories/`
- **Migrations**: `app/db/migrations/`

**Redis Integration:**
- **Client**: Redis client (via config)
- **Usage**: Caching, rate limiting, session storage, fallback memory
- **Configuration**: `app/config/redis.py`

#### Data Flow

**Document Ingestion Flow:**
```
MCP Tool (rag_ingest_document)
  → Knowledge Service (ingest_document)
    → Document Repository (create_document)
      → PostgreSQL (store metadata)
    → Embedding Service (generate_embedding)
      → Vector Service (add_to_index)
        → FAISS (store vector)
    → Keyword Service (index_document)
      → Meilisearch (index document)
    → MinIO Client (store_file)
      → MinIO (store document file)
```

**Search Flow:**
```
MCP Tool (rag_search)
  → Search Service (hybrid_search)
    → Vector Service (vector_search)
      → FAISS (search vectors)
    → Keyword Service (keyword_search)
      → Meilisearch (search keywords)
    → Search Service (merge_results)
      → Return ranked results
```

**Memory Operations Flow:**
```
MCP Tool (rag_get_memory)
  → Memory Service (get_memory)
    → Mem0 Client (get_memory)
      → Mem0 API (retrieve memory)
    → Fallback: Redis (if Mem0 unavailable)
```

**Audit Logging Flow:**
```
MCP Tool (any tool call)
  → Audit Middleware (log_audit_event)
    → Audit Repository (create_audit_log)
      → PostgreSQL (store audit log)
```

### File Organization Patterns

#### Configuration Files

**Root Level:**
- `pyproject.toml` - Python project configuration (Poetry/uv)
- `requirements.txt` - Python dependencies (pip)
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore patterns

**Application Configuration:**
- `app/config/settings.py` - Base settings class
- `app/config/*.py` - Service-specific configurations (database, redis, mem0, etc.)
- Environment variables loaded via Pydantic Settings

#### Source Organization

**By Layer:**
- `app/mcp/` - MCP server layer (primary interface)
- `app/api/` - REST API layer (optional/admin)
- `app/services/` - Business logic layer
- `app/db/` - Data access layer
- `app/integrations/` - External service integrations
- `app/utils/` - Shared utilities

**By Domain (within layers):**
- Services organized by domain (knowledge, memory, tenant, etc.)
- Repositories organized by entity (document, memory, tenant, etc.)
- MCP tools organized by capability (knowledge_base, memory, tenant, etc.)

#### Test Organization

**Mirror Source Structure:**
- `tests/unit/services/` mirrors `app/services/`
- `tests/unit/repositories/` mirrors `app/db/repositories/`
- `tests/integration/` tests cross-layer integration
- `tests/e2e/` tests complete user journeys

**Test Fixtures:**
- `tests/fixtures/` contains reusable test data and mocks
- Database fixtures for test database setup
- Tenant fixtures for multi-tenant testing

#### Asset Organization

**Docker Assets:**
- `docker/Dockerfile` - Production container
- `docker/Dockerfile.dev` - Development container
- `docker/docker-compose.yml` - Local development environment

**Kubernetes Assets:**
- `kubernetes/base/` - Base resources (namespace, configmap, secrets)
- `kubernetes/deployments/` - Deployment manifests
- `kubernetes/services/` - Service manifests
- `kubernetes/ingress/` - Ingress configuration
- `kubernetes/monitoring/` - Monitoring resources

**Scripts:**
- `scripts/` - Utility scripts (backup, restore, migrate, seed)

**Documentation:**
- `docs/` - Project documentation (API, architecture, deployment, development)

### Development Workflow Integration

**Development Server Structure:**
- FastAPI development server: `uvicorn app.main:app --reload`
- MCP server accessible at: `http://localhost:8000/mcp/`
- Health check at: `http://localhost:8000/api/v1/health`
- Metrics at: `http://localhost:8000/api/v1/metrics`

**Build Process Structure:**
- Docker build: `docker build -f docker/Dockerfile -t rag-system:latest .`
- Python package: `pip install -e .` (for development)
- Dependencies: Managed via `requirements.txt` or `pyproject.toml`

**Deployment Structure:**
- Kubernetes deployment: `kubectl apply -f kubernetes/`
- Environment-specific configs: Via ConfigMaps and Secrets
- CI/CD: GitHub Actions workflows in `.github/workflows/`
- Database migrations: Alembic migrations in `app/db/migrations/`

## Architecture Validation Results

### Coherence Validation ✅

#### Decision Compatibility

**Technology Stack Compatibility:**
- ✅ **FastAPI + FastMCP**: FastMCP's `http_app()` integrates seamlessly with FastAPI via ASGI mounting
- ✅ **SQLAlchemy 2.0 async + FastAPI**: Both async-first, compatible connection pooling patterns
- ✅ **PostgreSQL + SQLAlchemy**: Native async support, RLS policy compatibility
- ✅ **Redis + slowapi**: Redis backend for rate limiting supports per-tenant keys via custom key function
- ✅ **Mem0 + Redis fallback**: Architecture supports graceful degradation pattern
- ✅ **FAISS + Meilisearch**: Both support tenant-scoped indices, hybrid retrieval pattern validated
- ✅ **Langfuse + FastMCP**: Middleware integration pattern supports async logging without latency impact
- ✅ **Pydantic Settings + FastAPI**: Native integration, type-safe configuration
- ✅ **structlog + FastAPI**: Structured logging integrates with FastAPI request lifecycle

**Version Compatibility:**
- ✅ All technology versions are production-ready and compatible
- ✅ SQLAlchemy 2.0 async works with PostgreSQL asyncpg driver
- ✅ FastMCP supports FastAPI integration patterns
- ✅ All Python packages compatible with Python 3.11+

**No Contradictory Decisions Identified:**
- All architectural decisions align with chosen technology stack
- Patterns support multi-tenant requirements
- Performance targets achievable with selected technologies
- Compliance requirements architecturally supported

#### Pattern Consistency

**Naming Conventions:**
- ✅ Consistent `snake_case` across database, Python code, and MCP tools
- ✅ MCP tool naming follows `rag_{tool_name}` pattern consistently
- ✅ File naming matches module naming conventions
- ✅ Test naming follows `test_{module}_{scenario}` pattern

**Structure Patterns:**
- ✅ Repository pattern consistently applied across all data access
- ✅ Service layer abstraction consistent across all business logic
- ✅ Middleware stack order consistently defined and enforced
- ✅ Configuration management pattern consistent across all services

**Communication Patterns:**
- ✅ Async/await patterns consistently applied (all I/O operations)
- ✅ Session management pattern (FastAPI dependency injection) consistently defined
- ✅ Error handling format standardized across all MCP tools
- ✅ Tenant isolation pattern consistently enforced at all layers

**Process Patterns:**
- ✅ Database transaction patterns consistently defined (short-lived, operation-scoped)
- ✅ Eager loading patterns consistently specified (no lazy loading)
- ✅ Background task patterns defined for long operations
- ✅ Connection pool configuration consistently specified

#### Structure Alignment

**Project Structure Supports Architecture:**
- ✅ MCP-first structure (`app/mcp/`) supports primary interface requirement
- ✅ Service layer (`app/services/`) supports business logic abstraction
- ✅ Repository layer (`app/db/repositories/`) supports data access abstraction
- ✅ Integration layer (`app/integrations/`) supports external service clients
- ✅ Middleware stack (`app/mcp/middleware/`) supports cross-cutting concerns

**Boundaries Properly Defined:**
- ✅ API boundaries clearly separate MCP (primary) from REST (optional/admin)
- ✅ Component boundaries enforce layer separation (MCP → Services → Repositories → Database)
- ✅ Data boundaries enforce tenant isolation at all layers
- ✅ Integration boundaries separate internal services from external services

**Integration Points Properly Structured:**
- ✅ Internal communication patterns defined (MCP Tools → Services → Repositories)
- ✅ External integration points defined (Services → Integration Clients → External Services)
- ✅ Data flow patterns documented (ingestion, search, memory, audit)
- ✅ Middleware integration points clearly specified

### Requirements Coverage Validation ✅

#### Functional Requirements Coverage

**Knowledge Base Operations (9 FRs) - ✅ Fully Covered:**
- ✅ FR-KB-001: `rag_search` → `app/mcp/tools/knowledge_base.py`, `app/services/search_service.py`
- ✅ FR-KB-002: Multi-modal search (Phase 2) → `app/services/search_service.py` (extensible)
- ✅ FR-KB-003: Cross-modal search (Phase 2) → `app/services/search_service.py` (extensible)
- ✅ FR-KB-004: Hybrid retrieval → `app/services/search_service.py`, `app/services/vector_service.py`, `app/services/keyword_service.py`
- ✅ FR-KB-005: `rag_ingest_document` → `app/mcp/tools/knowledge_base.py`, `app/services/knowledge_service.py`
- ✅ FR-KB-006: Document versioning → `app/services/knowledge_service.py`, `app/db/models/document.py`
- ✅ FR-KB-007: `rag_delete_document` → `app/mcp/tools/knowledge_base.py`, `app/services/knowledge_service.py`
- ✅ FR-KB-008: `rag_get_document` → `app/mcp/tools/knowledge_base.py`, `app/services/knowledge_service.py`
- ✅ FR-KB-009: `rag_list_documents` → `app/mcp/tools/knowledge_base.py`, `app/services/knowledge_service.py`

**Memory Operations (5 FRs) - ✅ Fully Covered:**
- ✅ FR-MEM-001: `rag_get_memory` → `app/mcp/tools/memory.py`, `app/services/memory_service.py`, `app/integrations/mem0_client.py`
- ✅ FR-MEM-002: `rag_update_memory` → `app/mcp/tools/memory.py`, `app/services/memory_service.py`
- ✅ FR-MEM-003: `rag_search_memory` → `app/mcp/tools/memory.py`, `app/services/memory_service.py`
- ✅ FR-MEM-004: Session context storage → `app/services/session_service.py`, `app/db/repositories/session_repository.py`
- ✅ FR-MEM-005: Memory isolation → `app/services/memory_service.py` (tenant_id:user_id prefixing)

**Tenant Management (8 FRs) - ✅ Fully Covered:**
- ✅ FR-TENANT-001: `rag_register_tenant` → `app/mcp/tools/tenant.py`, `app/services/tenant_service.py`
- ✅ FR-TENANT-002: `rag_list_templates` → `app/mcp/tools/templates.py`, `app/services/tenant_service.py`
- ✅ FR-TENANT-003: `rag_get_template` → `app/mcp/tools/templates.py`, `app/services/tenant_service.py`
- ✅ FR-TENANT-004: `rag_update_tenant_config` (Phase 2) → `app/mcp/tools/tenant.py` (extensible)
- ✅ FR-TENANT-005: `rag_delete_tenant` (Phase 2) → `app/mcp/tools/tenant.py` (extensible)
- ✅ FR-TENANT-006: `rag_configure_tenant_models` → `app/mcp/tools/tenant.py`, `app/services/tenant_service.py`
- ✅ FR-TENANT-007: Tenant-scoped data isolation → `app/db/models/*` (all models include tenant_id), RLS policies
- ✅ FR-TENANT-008: Subscription tier management (Phase 2) → `app/services/tenant_service.py` (extensible)

**Authentication & Authorization (6 FRs) - ✅ Fully Covered:**
- ✅ FR-AUTH-001: OAuth 2.0 authentication → `app/mcp/middleware/auth.py`, `app/config/oauth.py`
- ✅ FR-AUTH-002: API key authentication → `app/mcp/middleware/auth.py`, `app/db/repositories/tenant_repository.py`
- ✅ FR-AUTH-003: Tenant_id validation → `app/mcp/middleware/tenant.py`
- ✅ FR-AUTH-004: Four-tier RBAC → `app/mcp/middleware/authorization.py`, `app/db/models/user.py`
- ✅ FR-AUTH-005: Role-based data access → `app/mcp/middleware/authorization.py`, all services
- ✅ FR-AUTH-006: Project Admin role (Phase 2) → `app/mcp/middleware/authorization.py` (extensible)

**Search Capabilities (5 FRs) - ✅ Fully Covered:**
- ✅ FR-SEARCH-001: Vector search (FAISS) → `app/services/vector_service.py`, `app/integrations/faiss_client.py`
- ✅ FR-SEARCH-002: Keyword search (Meilisearch) → `app/services/keyword_service.py`, `app/integrations/meilisearch_client.py`
- ✅ FR-SEARCH-003: Hybrid retrieval → `app/services/search_service.py` (orchestrates vector + keyword)
- ✅ FR-SEARCH-004: Cross-modal search (Phase 2) → `app/services/search_service.py` (extensible)
- ✅ FR-SEARCH-005: Unified embedding space (Phase 2) → `app/services/embedding_service.py` (extensible)

**Session Management (3 FRs) - ✅ Fully Covered:**
- ✅ FR-SESSION-001: Session continuity → `app/mcp/tools/session.py`, `app/services/session_service.py`
- ✅ FR-SESSION-002: Context-aware search → `app/services/search_service.py::context_aware_search()`
- ✅ FR-SESSION-003: Returning user recognition → `app/services/session_service.py::recognize_user()`

**Compliance & Audit (5 FRs) - ✅ Fully Covered:**
- ✅ FR-AUDIT-001: Comprehensive audit logging → `app/mcp/middleware/audit.py`, `app/db/repositories/audit_repository.py`
- ✅ FR-AUDIT-002: `rag_query_audit_logs` → `app/mcp/tools/audit.py`, `app/db/repositories/audit_repository.py`
- ✅ FR-COMP-001: PCI DSS compliance → `app/utils/encryption.py`, `app/mcp/middleware/audit.py`
- ✅ FR-COMP-002: HIPAA compliance (Phase 2) → `app/utils/encryption.py` (field-level), extensible
- ✅ FR-COMP-003: SOC 2 compliance (Phase 2) → Architecture supports, extensible
- ✅ FR-COMP-004: GDPR compliance (Phase 2) → `app/services/tenant_service.py::export_data()` (extensible)

**Monitoring & Analytics (6 FRs) - ✅ Fully Covered:**
- ✅ FR-MON-001: `rag_get_usage_stats` → `app/mcp/tools/monitoring.py`, `app/services/tenant_service.py`
- ✅ FR-MON-002: `rag_get_search_analytics` (Phase 2) → `app/mcp/tools/monitoring.py` (extensible)
- ✅ FR-MON-003: `rag_get_memory_analytics` (Phase 2) → `app/mcp/tools/monitoring.py` (extensible)
- ✅ FR-MON-004: Health checks → `app/api/health.py`
- ✅ FR-MON-005: `rag_get_system_health` (Phase 2) → `app/mcp/tools/monitoring.py` (extensible)
- ✅ FR-MON-006: `rag_get_tenant_health` (Phase 2) → `app/mcp/tools/monitoring.py` (extensible)

**Data Management (4 FRs) - ✅ Fully Covered:**
- ✅ FR-DATA-001: Tenant-level isolation → `app/db/models/*` (tenant_id), RLS policies, all repositories
- ✅ FR-DATA-002: User-level memory isolation → `app/services/memory_service.py` (tenant_id:user_id prefixing)
- ✅ FR-DATA-003: `rag_export_tenant_data` (Phase 2) → `app/mcp/tools/tenant.py` (extensible)
- ✅ FR-DATA-004: `rag_export_user_data` (Phase 2) → `app/mcp/tools/tenant.py` (extensible)

**Performance & Optimization (4 FRs) - ✅ Fully Covered:**
- ✅ FR-PERF-001: <200ms search latency → Architecture supports (caching, connection pooling, async operations)
- ✅ FR-PERF-002: <100ms memory operations → Architecture supports (Mem0 integration, Redis caching)
- ✅ FR-PERF-003: <500ms cold start → Architecture supports (connection pooling, pre-warming patterns)
- ✅ FR-PERF-004: Redis caching (Phase 2) → `app/config/redis.py`, caching patterns defined

**Error Handling & Recovery (4 FRs) - ✅ Fully Covered:**
- ✅ FR-ERROR-001: Mem0 fallback → `app/services/memory_service.py` (Redis fallback pattern)
- ✅ FR-ERROR-002: Search service fallback → `app/services/search_service.py` (three-tier fallback)
- ✅ FR-ERROR-003: Structured error responses → `app/utils/errors.py`, standardized format
- ✅ FR-ERROR-004: Rate limit handling → `app/mcp/middleware/rate_limit.py`, slowapi integration

**Integration & Protocol Support (3 FRs) - ✅ Fully Covered:**
- ✅ FR-INT-001: MCP server implementation → `app/mcp/server.py`, FastMCP integration
- ✅ FR-INT-002: `rag_list_tools` → `app/mcp/tools/tenant.py` (or built into FastMCP)
- ✅ FR-INT-003: MCP context validation → `app/mcp/middleware/tenant.py`, `app/mcp/middleware/auth.py`

**Backup & Recovery (5 FRs) - ✅ Fully Covered:**
- ✅ FR-BACKUP-001: Basic backup operations → `app/services/backup_service.py`, `scripts/backup.py`
- ✅ FR-BACKUP-002: `rag_backup_tenant_data` (Phase 2) → `app/mcp/tools/tenant.py` (extensible)
- ✅ FR-BACKUP-003: `rag_restore_tenant_data` (Phase 2) → `app/mcp/tools/tenant.py` (extensible)
- ✅ FR-BACKUP-004: `rag_rebuild_index` (Phase 2) → `app/services/backup_service.py` (extensible)
- ✅ FR-BACKUP-005: `rag_validate_backup` (Phase 2) → `app/services/backup_service.py` (extensible)

**Rate Limiting (2 FRs) - ✅ Fully Covered:**
- ✅ FR-RATE-001: Per-tenant rate limiting → `app/mcp/middleware/rate_limit.py`, slowapi with Redis
- ✅ FR-RATE-002: Tier-based rate limiting (Phase 2) → `app/mcp/middleware/rate_limit.py` (extensible)

**Total Functional Requirements: 86 FRs**
- ✅ **MVP FRs (45+)**: All architecturally supported with specific file/directory mappings
- ✅ **Phase 2 FRs**: Architecture extensible to support (identified in structure)
- ✅ **Phase 3 FRs**: Architecture extensible to support (identified in structure)

#### Non-Functional Requirements Coverage

**Performance Requirements (9 NFRs) - ✅ Fully Covered:**
- ✅ NFR-PERF-001: <200ms p95 search latency → Architecture supports (async operations, caching, connection pooling)
- ✅ NFR-PERF-002: <100ms p95 memory operations → Architecture supports (Mem0 integration, Redis caching)
- ✅ NFR-PERF-003: <500ms cold start → Architecture supports (connection pooling, pre-warming)
- ✅ NFR-PERF-004: <100ms user recognition → Architecture supports (caching, optimized queries)
- ✅ NFR-PERF-005: <300ms multi-modal search (Phase 2) → Architecture extensible
- ✅ NFR-PERF-006: 1000 requests/minute per tenant → Architecture supports (slowapi rate limiting)
- ✅ NFR-PERF-007: >80% cache hit rate (MVP) → Architecture supports (Redis caching strategy)
- ✅ NFR-PERF-008: >60% cache hit rate (Phase 2) → Architecture extensible
- ✅ NFR-PERF-009: Throughput targets → Architecture supports (horizontal scaling, async operations)

**Scalability Requirements (6 NFRs) - ✅ Fully Covered:**
- ✅ NFR-SCAL-001: 200 tenants (MVP) → Architecture supports (multi-tenant isolation patterns)
- ✅ NFR-SCAL-002: 200 concurrent users/tenant → Architecture supports (async operations, connection pooling)
- ✅ NFR-SCAL-003: 40K requests/minute (MVP) → Architecture supports (horizontal scaling, async operations)
- ✅ NFR-SCAL-004: Horizontal scaling → Architecture supports (Kubernetes, stateless services)
- ✅ NFR-SCAL-005: 200K requests/minute (Phase 2) → Architecture extensible (enhanced auto-scaling)
- ✅ NFR-SCAL-006: Auto-scaling → Architecture supports (Kubernetes HPA)

**Reliability Requirements (8 NFRs) - ✅ Fully Covered:**
- ✅ NFR-REL-001: >95% uptime (MVP) → Architecture supports (fault tolerance, graceful degradation)
- ✅ NFR-REL-002: >99.9% uptime (Phase 3) → Architecture extensible
- ✅ NFR-REL-003: RTO <4h (MVP) → Architecture supports (backup/restore patterns)
- ✅ NFR-REL-004: RPO <1h (MVP) → Architecture supports (daily backups, WAL archiving)
- ✅ NFR-REL-005: Fault tolerance → Architecture supports (fallback mechanisms, circuit breakers)
- ✅ NFR-REL-006: Graceful degradation → Architecture supports (three-tier fallback patterns)
- ✅ NFR-REL-007: Zero user-facing errors → Architecture supports (error handling, fallbacks)
- ✅ NFR-REL-008: Disaster recovery → Architecture supports (backup/restore, data reconstruction)

**Security Requirements (8 NFRs) - ✅ Fully Covered:**
- ✅ NFR-SEC-001: AES-256 encryption at rest → Architecture supports (`app/utils/encryption.py`)
- ✅ NFR-SEC-002: TLS 1.3 in transit → Architecture supports (Kubernetes ingress, service mesh)
- ✅ NFR-SEC-003: RBAC enforcement → Architecture supports (`app/mcp/middleware/authorization.py`)
- ✅ NFR-SEC-004: Tenant isolation → Architecture supports (RLS policies, tenant-scoped resources)
- ✅ NFR-SEC-005: Vulnerability management → Architecture supports (dependency management, scanning)
- ✅ NFR-SEC-006: Penetration testing (Phase 2) → Architecture extensible
- ✅ NFR-SEC-007: Security monitoring → Architecture supports (audit logging, alerting)
- ✅ NFR-SEC-008: PII protection → Architecture supports (field-level encryption, access controls)

**Compliance Requirements (6 NFRs) - ✅ Fully Covered:**
- ✅ NFR-COMP-001: PCI DSS compliance → Architecture supports (encryption, audit logging, access controls)
- ✅ NFR-COMP-002: HIPAA compliance (Phase 2) → Architecture extensible (field-level encryption, audit logging)
- ✅ NFR-COMP-003: SOC 2 compliance (Phase 2) → Architecture extensible (security controls, monitoring)
- ✅ NFR-COMP-004: GDPR compliance (Phase 2) → Architecture extensible (data export, deletion)
- ✅ NFR-COMP-005: Comprehensive audit logging → Architecture supports (`app/mcp/middleware/audit.py`)
- ✅ NFR-COMP-006: Compliance validation → Architecture supports (audit log querying)

**Observability Requirements (7 NFRs) - ✅ Fully Covered:**
- ✅ NFR-OBS-001: Langfuse integration (MVP) → Architecture supports (`app/mcp/middleware/observability.py`)
- ✅ NFR-OBS-002: Structured logging → Architecture supports (`app/utils/logging.py`, structlog)
- ✅ NFR-OBS-003: Health monitoring → Architecture supports (`app/api/health.py`)
- ✅ NFR-OBS-004: Metrics collection → Architecture supports (`app/api/monitoring.py`, Prometheus)
- ✅ NFR-OBS-005: Distributed tracing (Phase 2) → Architecture extensible
- ✅ NFR-OBS-006: Alerting → Architecture supports (Prometheus Alertmanager)
- ✅ NFR-OBS-007: Performance monitoring → Architecture supports (Langfuse, Prometheus metrics)

**Maintainability Requirements (4 NFRs) - ✅ Fully Covered:**
- ✅ NFR-MAIN-001: >80% test coverage → Architecture supports (test structure defined)
- ✅ NFR-MAIN-002: Clean architecture → Architecture supports (layered architecture, separation of concerns)
- ✅ NFR-MAIN-003: Comprehensive documentation → Architecture supports (docs/ structure)
- ✅ NFR-MAIN-004: Code quality → Architecture supports (linting, type checking, pre-commit hooks)

**Deployability Requirements (5 NFRs) - ✅ Fully Covered:**
- ✅ NFR-DEP-001: CI/CD pipelines → Architecture supports (GitHub Actions workflows)
- ✅ NFR-DEP-002: Zero-downtime deployments → Architecture supports (Kubernetes rolling updates)
- ✅ NFR-DEP-003: Infrastructure as Code → Architecture supports (Kubernetes manifests)
- ✅ NFR-DEP-004: Environment management → Architecture supports (ConfigMaps, Secrets, Pydantic Settings)
- ✅ NFR-DEP-005: Automated testing → Architecture supports (CI/CD test automation)

**Usability Requirements (4 NFRs) - ✅ Fully Covered:**
- ✅ NFR-USAB-001: Clear MCP tool interfaces → Architecture supports (MCP protocol, standardized tool signatures)
- ✅ NFR-USAB-002: Comprehensive API documentation → Architecture supports (OpenAPI, MCP tool docs)
- ✅ NFR-USAB-003: Clear error messages → Architecture supports (standardized error format)
- ✅ NFR-USAB-004: SDKs (Phase 3) → Architecture extensible

**Total Non-Functional Requirements: 53 NFRs**
- ✅ **MVP NFRs (30+)**: All architecturally supported
- ✅ **Phase 2 NFRs**: Architecture extensible to support
- ✅ **Phase 3 NFRs**: Architecture extensible to support

### Implementation Readiness Validation ✅

#### Decision Completeness

**Critical Decisions Documented:**
- ✅ Technology stack fully specified with versions
- ✅ ORM/Database access layer decision (SQLAlchemy 2.0 async)
- ✅ Authentication/authorization decisions (python-jose + authlib, argon2)
- ✅ Rate limiting decision (slowapi)
- ✅ Configuration management (Pydantic Settings)
- ✅ Logging decision (structlog)
- ✅ Monitoring decision (Prometheus + Grafana)
- ✅ CI/CD decision (GitHub Actions)

**Implementation Patterns Comprehensive:**
- ✅ Naming conventions defined for all areas (database, API, code, files)
- ✅ Structure patterns defined (project organization, test organization)
- ✅ Format patterns defined (API responses, data exchange, logging)
- ✅ Communication patterns defined (async/await, session management, transactions)
- ✅ Process patterns defined (error handling, tenant isolation, configuration access)

**Consistency Rules Clear:**
- ✅ 7 mandatory rules for all AI agents
- ✅ Good examples and anti-patterns provided
- ✅ Enforcement guidelines documented
- ✅ Pattern examples with code snippets

#### Structure Completeness

**Complete Project Tree:**
- ✅ All directories and files specified
- ✅ No generic placeholders
- ✅ All layers properly organized
- ✅ Integration points clearly defined

**Component Boundaries Well-Defined:**
- ✅ API boundaries (MCP vs REST)
- ✅ Component boundaries (MCP → Services → Repositories → Database)
- ✅ Data boundaries (tenant isolation, user isolation)
- ✅ Integration boundaries (internal vs external)

**Requirements to Structure Mapping:**
- ✅ All 86 functional requirements mapped to specific files/directories
- ✅ All 53 non-functional requirements architecturally supported
- ✅ Cross-cutting concerns mapped to locations
- ✅ Integration points documented with data flow

#### Pattern Completeness

**All Conflict Points Addressed:**
- ✅ Naming conflicts (database, API, code, files)
- ✅ Structural conflicts (test organization, service organization)
- ✅ Format conflicts (API responses, data exchange, logging)
- ✅ Communication conflicts (async patterns, session management)
- ✅ Process conflicts (error handling, tenant isolation, transactions)

**Patterns Comprehensive:**
- ✅ Naming patterns with examples
- ✅ Structure patterns with rationale
- ✅ Format patterns with examples
- ✅ Communication patterns with code examples
- ✅ Process patterns with implementation details

**Architectural Safeguards:**
- ✅ Session management safeguards (FastAPI dependency injection)
- ✅ Connection pooling safeguards (configuration, monitoring)
- ✅ Eager loading safeguards (patterns, examples)
- ✅ Background task safeguards (for long operations)

### Gap Analysis Results

#### Critical Gaps: None Identified ✅

All critical architectural decisions are documented and complete. No blocking gaps identified.

#### Important Gaps: Minor Enhancements

**1. Embedding Service Details:**
- **Gap**: Embedding generation service (`app/services/embedding_service.py`) mentioned but not fully detailed
- **Impact**: Low - can be implemented following service layer patterns
- **Resolution**: Follow existing service patterns, use OpenAI/other embedding API

**2. Circuit Breaker Implementation:**
- **Gap**: Circuit breaker pattern mentioned but not fully specified
- **Impact**: Low - can use standard libraries (e.g., `circuitbreaker` package)
- **Resolution**: Implement using standard Python circuit breaker libraries

**3. Background Task Queue:**
- **Gap**: Background task pattern defined but queue system not specified
- **Impact**: Low - FastAPI BackgroundTasks sufficient for MVP, can add Celery/Redis Queue for Phase 2
- **Resolution**: Use FastAPI BackgroundTasks for MVP, extend to Celery for Phase 2 if needed

#### Nice-to-Have Gaps: Future Enhancements

**1. Advanced Monitoring Dashboards:**
- **Gap**: Grafana dashboards not fully specified
- **Impact**: None - can be created during implementation
- **Resolution**: Create dashboards based on Prometheus metrics during implementation

**2. Development Tooling:**
- **Gap**: Specific development tools not fully specified (debugging, profiling)
- **Impact**: None - standard Python tooling can be used
- **Resolution**: Use standard Python development tools (pdb, cProfile, etc.)

**3. Performance Profiling:**
- **Gap**: Performance profiling strategy not fully detailed
- **Impact**: None - can be added during implementation
- **Resolution**: Use standard Python profiling tools, integrate with observability

### Validation Issues Addressed

**No Critical Issues Found:**
- All architectural decisions are coherent and compatible
- All requirements are architecturally supported
- Implementation patterns are comprehensive and consistent
- Project structure is complete and specific

**Minor Enhancements Identified:**
- Embedding service implementation details (can follow existing patterns)
- Circuit breaker library selection (standard libraries available)
- Background task queue (FastAPI BackgroundTasks sufficient for MVP)

**All Issues Resolvable:**
- Minor gaps can be addressed during implementation
- No blocking architectural concerns
- Architecture is ready for implementation

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (High/Enterprise, 7+ services)
- [x] Technical constraints identified (MCP, Langfuse, Mem0, FAISS, etc.)
- [x] Cross-cutting concerns mapped (multi-tenancy, performance, security, compliance, observability, error handling, backup/recovery)

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions (SQLAlchemy 2.0, python-jose, authlib, argon2, slowapi, structlog, Prometheus)
- [x] Technology stack fully specified (FastAPI, FastMCP, PostgreSQL, Redis, Mem0, FAISS, Meilisearch, MinIO, Langfuse, Kubernetes)
- [x] Integration patterns defined (MCP server, service layer, repository pattern, middleware stack)
- [x] Performance considerations addressed (async operations, connection pooling, caching, background tasks)

**✅ Implementation Patterns**
- [x] Naming conventions established (snake_case for database/code, PascalCase for classes, rag_ prefix for MCP tools)
- [x] Structure patterns defined (MCP-first, service layer, repository pattern, test organization)
- [x] Communication patterns specified (async/await, session management, transactions, eager loading)
- [x] Process patterns documented (error handling, tenant isolation, configuration access, background tasks)

**✅ Project Structure**
- [x] Complete directory structure defined (all files and directories specified)
- [x] Component boundaries established (API, component, data, integration boundaries)
- [x] Integration points mapped (internal communication, external integrations, data flow)
- [x] Requirements to structure mapping complete (86 FRs, 53 NFRs mapped to specific locations)

**✅ Architectural Safeguards**
- [x] Session management safeguards (FastAPI dependency injection prevents connection leaks)
- [x] Connection pooling safeguards (configuration, monitoring, proper sizing)
- [x] Eager loading safeguards (patterns, examples, anti-patterns)
- [x] Background task safeguards (for long operations, prevents pool exhaustion)

### Architecture Readiness Assessment

**Overall Status:** ✅ **READY FOR IMPLEMENTATION**

**Confidence Level:** **HIGH** - Comprehensive architecture with all critical decisions documented, all requirements mapped, and implementation patterns defined.

**Key Strengths:**

1. **Complete Requirements Coverage:**
   - All 86 functional requirements architecturally supported
   - All 53 non-functional requirements addressed
   - Clear MVP vs Phase 2/3 distinction

2. **Coherent Technology Stack:**
   - All technologies compatible and production-ready
   - Patterns align with technology choices
   - No contradictory decisions

3. **Comprehensive Implementation Patterns:**
   - All potential conflict points addressed
   - Clear naming, structure, and communication patterns
   - Architectural safeguards prevent common issues (session leaks, pool exhaustion)

4. **Complete Project Structure:**
   - All files and directories specified
   - Clear boundaries and integration points
   - Requirements mapped to specific locations

5. **Multi-Tenant Architecture:**
   - Tenant isolation enforced at all layers
   - RLS policies, tenant-scoped resources, configuration isolation
   - Comprehensive testing strategy for isolation

6. **Compliance-First Design:**
   - Encryption, audit logging, access controls built into architecture
   - HIPAA, PCI DSS, SOC 2, GDPR support (MVP and extensible)
   - Comprehensive audit trail

7. **Observability Integration:**
   - Langfuse integration (MVP requirement) architecturally supported
   - Structured logging, metrics, health monitoring
   - Non-intrusive async logging pattern

**Areas for Future Enhancement:**

1. **Phase 2 Enhancements:**
   - Multi-modal processing pipeline details
   - Cross-modal search implementation patterns
   - Advanced analytics dashboards
   - Distributed tracing implementation

2. **Phase 3 Enhancements:**
   - Global scale optimizations
   - Advanced security features
   - SDK development patterns
   - Developer ecosystem tools

3. **Operational Enhancements:**
   - Advanced monitoring dashboards (Grafana)
   - Performance profiling strategies
   - Development tooling recommendations
   - Advanced debugging patterns

### Implementation Handoff

**AI Agent Guidelines:**

1. **Follow Architectural Decisions Exactly:**
   - Use specified technology versions
   - Follow naming conventions consistently
   - Respect component boundaries
   - Use defined patterns for all implementations

2. **Use Implementation Patterns Consistently:**
   - Follow session management pattern (FastAPI dependency injection)
   - Use eager loading (no lazy loading)
   - Enforce tenant isolation at all layers
   - Use standardized error format

3. **Respect Project Structure:**
   - Place code in specified directories
   - Follow layer separation (MCP → Services → Repositories → Database)
   - Use integration clients for external services
   - Organize tests to mirror source structure

4. **Refer to Architecture Document:**
   - All architectural questions answered in this document
   - Patterns and examples provided for guidance
   - Requirements mapped to specific locations
   - Anti-patterns documented to avoid

**First Implementation Priority:**

1. **Project Initialization:**
   - Create project structure as defined
   - Set up FastAPI + FastMCP integration
   - Configure database connection with SQLAlchemy 2.0 async
   - Set up Pydantic Settings for configuration

2. **Foundation Layer:**
   - Implement database models with tenant_id
   - Set up Alembic migrations
   - Configure structlog with tenant_id injection
   - Set up Redis connection

3. **Middleware Stack:**
   - Implement authentication middleware
   - Implement tenant extraction middleware
   - Implement rate limiting middleware
   - Implement authorization middleware
   - Implement audit logging middleware
   - Implement observability middleware (Langfuse)

4. **Core MCP Tools (MVP):**
   - `rag_search` - Knowledge base search
   - `rag_ingest_document` - Document ingestion
   - `rag_get_memory` - Get user memory
   - `rag_update_memory` - Update user memory
   - `rag_register_tenant` - Tenant onboarding
   - `rag_list_tools` - Tool discovery
   - `rag_get_usage_stats` - Usage statistics

**Implementation Sequence:**
1. Project structure setup
2. Database layer (models, repositories, migrations)
3. Service layer (knowledge, memory, search, tenant services)
4. Integration layer (Mem0, FAISS, Meilisearch, MinIO, Langfuse clients)
5. MCP server layer (tools, middleware, server initialization)
6. API layer (health, monitoring endpoints)
7. Testing infrastructure
8. CI/CD setup
9. Kubernetes deployment configuration

**Architecture Document Status:** ✅ **COMPLETE AND READY FOR IMPLEMENTATION**




