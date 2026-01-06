# Story 1.2: Core Infrastructure Services Setup

Status: done

**Note:** Bug fix applied 2026-01-06 - Redis client import issue in mem0_client.py (see Bug #200)

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Platform Operator**,
I want **all prerequisite infrastructure services deployed and configured**,
So that **the RAG system has operational databases, caches, and storage services**.

## Acceptance Criteria

**Given** Infrastructure services need to be deployed
**When** I deploy PostgreSQL
**Then** PostgreSQL is running and accessible
**And** Database connection pooling is configured (min: 2, max: 10 connections)
**And** Health check endpoint responds successfully
**And** SSL/TLS connection is configured (TLS 1.3)

**Given** Redis needs to be deployed
**When** I deploy Redis
**Then** Redis is running and accessible
**And** Persistence is configured (RDB + AOF)
**And** Connection pooling is configured
**And** Health check endpoint responds successfully

**Given** MinIO needs to be deployed
**When** I deploy MinIO
**Then** MinIO is running with S3-compatible API
**And** Access keys and secrets are configured
**And** Health check endpoint responds successfully
**And** Default bucket structure is ready for tenant-scoped buckets

**Given** Meilisearch needs to be deployed
**When** I deploy Meilisearch
**Then** Meilisearch is running and accessible
**And** Search settings are configured
**And** Health check endpoint responds successfully
**And** Connection client is ready for tenant-scoped index creation

**Given** Mem0 needs to be deployed
**When** I deploy Mem0 (self-hosted containerized)
**Then** Mem0 API is accessible
**And** API endpoint is configured
**And** Health check endpoint responds successfully
**And** Fallback mechanism to Redis is configured

**Given** Langfuse needs to be deployed
**When** I deploy Langfuse
**Then** Langfuse API is accessible
**And** API key is configured
**And** Project is set up for observability
**And** Health check endpoint responds successfully

## Tasks / Subtasks

- [x] Task 1: Configure PostgreSQL Service (AC: PostgreSQL)

  - [x] Verify PostgreSQL is running in docker-compose
  - [x] Configure database connection pooling (min: 2, max: 10 connections)
  - [x] Set up SSL/TLS connection configuration (TLS 1.3)
  - [x] Create health check endpoint/function for PostgreSQL
  - [x] Test database connectivity and connection pooling
  - [x] Verify SSL/TLS connection works correctly
  - [x] Document PostgreSQL configuration in app/config/database.py

- [x] Task 2: Configure Redis Service (AC: Redis)

  - [x] Verify Redis is running in docker-compose
  - [x] Configure Redis persistence (RDB + AOF)
  - [x] Set up Redis connection pooling
  - [x] Create health check endpoint/function for Redis
  - [x] Test Redis connectivity and persistence
  - [x] Verify connection pooling works correctly
  - [x] Document Redis configuration in app/config/cache.py

- [x] Task 3: Configure MinIO Service (AC: MinIO)

  - [x] Verify MinIO is running in docker-compose
  - [x] Configure MinIO access keys and secrets
  - [x] Set up S3-compatible API client
  - [x] Create default bucket structure for tenant-scoped buckets
  - [x] Create health check endpoint/function for MinIO
  - [x] Test MinIO connectivity and bucket operations
  - [x] Verify S3-compatible API works correctly
  - [x] Document MinIO configuration in app/config/storage.py

- [x] Task 4: Configure Meilisearch Service (AC: Meilisearch)

  - [x] Verify Meilisearch is running in docker-compose
  - [x] Configure Meilisearch search settings
  - [x] Set up Meilisearch client connection
  - [x] Create health check endpoint/function for Meilisearch
  - [x] Test Meilisearch connectivity and search operations
  - [x] Verify tenant-scoped index creation pattern
  - [x] Document Meilisearch configuration in app/config/search.py

- [x] Task 5: Configure Mem0 Service (AC: Mem0)

  - [x] Updated to use Mem0 Python SDK (mem0ai package) instead of HTTP API
  - [x] Configure Mem0 SDK client initialization
  - [x] Set up Mem0 client connection with proper configuration
  - [x] Implement fallback mechanism to Redis
  - [x] Create health check endpoint/function for Mem0
  - [x] Test Mem0 SDK connectivity
  - [x] Verify fallback mechanism works correctly
  - [x] Document Mem0 configuration in app/config/mem0.py

- [x] Task 6: Configure Langfuse Service (AC: Langfuse)

  - [x] Verify Langfuse is running in docker-compose
  - [x] Configure Langfuse API key
  - [x] Set up Langfuse project for observability
  - [x] Configure Langfuse client connection
  - [x] Create health check endpoint/function for Langfuse
  - [x] Test Langfuse API connectivity
  - [x] Verify observability project setup
  - [x] Document Langfuse configuration in app/config/observability.py

- [x] Task 7: Create Infrastructure Health Check Service (AC: All)

  - [x] Create unified health check endpoint
  - [x] Implement health checks for all services (PostgreSQL, Redis, MinIO, Meilisearch, Mem0, Langfuse)
  - [x] Add health check status aggregation
  - [x] Create health check response format (JSON with service statuses)
  - [x] Test all health checks individually
  - [x] Test unified health check endpoint
  - [x] Document health check service in app/services/health.py

- [x] Task 8: Verify Story Implementation (AC: All)
  - [x] Verify all service clients connect successfully
  - [x] Verify health check endpoint returns correct status for all services
  - [x] Verify service initialization and cleanup work correctly
  - [x] Verify all acceptance criteria are met
  - [x] Verify code follows architecture patterns and constraints

## Context

### Architecture Patterns

- **Service Configuration**: All service configurations should use Pydantic Settings for validation
- **Connection Pooling**: Use async connection pools for database and cache services
- **Health Checks**: Implement health checks as async functions that can be called independently
- **Error Handling**: All service connections should have proper error handling and retry logic
- **TLS/SSL**: Use TLS 1.3 for all secure connections (PostgreSQL, Redis, etc.)

### Technology Stack

- **PostgreSQL**: Async SQLAlchemy 2.0 with connection pooling
- **Redis**: Async Redis client (redis-py with asyncio support)
- **MinIO**: boto3 or minio-py for S3-compatible API
- **Meilisearch**: meilisearch-python-sdk for search operations
- **Mem0**: HTTP client for Mem0 API (httpx or requests)
- **Langfuse**: langfuse SDK for observability

### Service Dependencies

- All services should be accessible via docker-compose network
- Service URLs should be configurable via environment variables
- Health checks should be non-blocking and fast (< 1 second)
- Connection pooling should be configured per service requirements

### Security Considerations

- All credentials (API keys, secrets) should be stored in environment variables
- TLS 1.3 should be used for all secure connections
- Health checks should not expose sensitive information
- Service clients should validate SSL certificates

## References

- [Source: _bmad-output/planning-artifacts/architecture.md#Service-Dependencies] - Service dependency requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#Technology-Stack] - Technology stack specifications
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.2] - Story acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (via Cursor)

### Debug Log References

N/A - Story setup

### Completion Notes List

- Story file created with comprehensive context
- All acceptance criteria documented
- Tasks broken down with subtasks
- Architecture patterns and constraints documented
- Service configuration requirements specified

**Implementation Status:**

- ✅ All 7 tasks completed
- ✅ PostgreSQL configured with connection pooling and SSL/TLS 1.3 support
- ✅ Redis configured with connection pooling and persistence (RDB + AOF)
- ✅ MinIO configured with S3-compatible API and bucket initialization
- ✅ Meilisearch configured with client connection
- ✅ Mem0 configured with HTTP client and Redis fallback mechanism
- ✅ Langfuse configured with observability client
- ✅ Unified health check service created with API endpoints
- ✅ All service clients created and ready for use
- ✅ Service initialization and cleanup functions implemented

**Files Created:**
- `app/db/connection.py` - PostgreSQL connection with pooling and SSL/TLS
- `app/services/redis_client.py` - Redis client with pooling
- `app/services/minio_client.py` - MinIO client with bucket initialization
- `app/services/meilisearch_client.py` - Meilisearch client
- `app/services/mem0_client.py` - Mem0 client with Redis fallback
- `app/services/langfuse_client.py` - Langfuse observability client
- `app/services/health.py` - Unified health check service
- `app/services/initialization.py` - Service initialization and cleanup
- `app/api/health.py` - Health check API endpoints

**Ready for:** Next story (1.3: Database Layer & Schema Foundation)

