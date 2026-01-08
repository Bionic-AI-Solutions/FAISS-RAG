---
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/product-brief-new-rag-2026-01-03.md
  - _bmad-output/planning-artifacts/admin-ui-design-specification.md
  - _bmad-output/planning-artifacts/admin-ui-complete-ux-design.md
  - _bmad-output/planning-artifacts/admin-ui-user-journey-maps.md
requirementsExtracted:
  functionalRequirements: 70
  nonFunctionalRequirements: 64
  additionalRequirements: 16
epicsDesigned: true
totalEpics: 12
epicsApproved: true
adminUIEpicsAdded: true
adminUIEpics: [10, 11, 12]
adminUIStories: 18
---

# mem0-rag - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for mem0-rag, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-KB-001 (MVP): System must support text-based knowledge base search via `rag_search` MCP tool.
FR-KB-002 (Phase 2): System must support multi-modal knowledge base search (text, images, audio, video).
FR-KB-003 (Phase 2): System must support cross-modal search via `rag_cross_modal_search` MCP tool.
FR-KB-004 (MVP): System must support hybrid retrieval (vector search + keyword search).
FR-KB-005 (MVP): System must support document ingestion via `rag_ingest` MCP tool.
FR-KB-006 (MVP): System must support document versioning on update.
FR-KB-007 (MVP): System must support document deletion via `rag_delete_document` MCP tool.
FR-KB-008 (MVP): System must support document retrieval via `rag_get_document` MCP tool.
FR-KB-009 (MVP): System must support document listing via `rag_list_documents` MCP tool.
FR-MEM-001 (MVP): System must support user memory retrieval via `mem0_get_user_memory` MCP tool.
FR-MEM-002 (MVP): System must support user memory update via `mem0_update_memory` MCP tool.
FR-MEM-003 (MVP): System must support user memory search via `mem0_search_memory` MCP tool.
FR-MEM-004 (MVP): System must support session context storage and retrieval.
FR-MEM-005 (MVP): System must support memory isolation per tenant and user.
FR-TENANT-001 (MVP): System must support tenant registration via `rag_register_tenant` MCP tool.
FR-TENANT-002 (MVP): System must support template listing via `rag_list_templates` MCP tool.
FR-TENANT-003 (MVP): System must support template details retrieval via `rag_get_template` MCP tool.
FR-TENANT-004 (Phase 2): System must support tenant configuration update via `rag_update_tenant_config` MCP tool.
FR-TENANT-005 (Phase 2): System must support tenant deletion via `rag_delete_tenant` MCP tool.
FR-TENANT-006 (MVP): System must support tenant model configuration via `rag_configure_tenant_models` MCP tool.
FR-TENANT-007 (MVP): System must support tenant-scoped data isolation.
FR-TENANT-008 (Phase 2): System must support subscription tier management.
FR-AUTH-001 (MVP): System must support OAuth 2.0 authentication for MCP clients.
FR-AUTH-002 (MVP): System must support tenant-based API key authentication.
FR-AUTH-003 (MVP): System must validate tenant_id in MCP request context.
FR-AUTH-004 (MVP): System must support four-tier RBAC structure.
FR-AUTH-005 (MVP): System must enforce role-based data access.
FR-AUTH-006 (Phase 2): System must support Project Admin role for project-scoped access.
FR-SEARCH-001 (MVP): System must support semantic vector search using FAISS.
FR-SEARCH-002 (MVP): System must support keyword search using Meilisearch.
FR-SEARCH-003 (MVP): System must support hybrid retrieval (vector + keyword).
FR-SEARCH-004 (Phase 2): System must support cross-modal search (text→image, image→text).
FR-SEARCH-005 (Phase 2): System must support unified embedding space for all modalities.
FR-SESSION-001 (MVP): System must support session continuity across interruptions.
FR-SESSION-002 (MVP): System must support context-aware search results.
FR-SESSION-003 (MVP): System must support returning user recognition.
FR-AUDIT-001 (MVP): System must log all RAG transactions to audit logs.
FR-AUDIT-002 (MVP): System must support audit log querying via `rag_query_audit_logs` MCP tool.
FR-COMP-001 (MVP): System must support PCI DSS compliance for fintech domain.
FR-COMP-002 (Phase 2): System must support HIPAA compliance for healthcare domain.
FR-COMP-003 (Phase 2): System must support SOC 2 compliance.
FR-COMP-004 (Phase 2): System must support GDPR compliance.
FR-MON-001 (MVP): System must support usage statistics retrieval via `rag_get_usage_stats` MCP tool.
FR-MON-002 (Phase 2): System must support search analytics via `rag_get_search_analytics` MCP tool.
FR-MON-003 (Phase 2): System must support memory analytics via `rag_get_memory_analytics` MCP tool.
FR-MON-004 (MVP): System must support basic health checks.
FR-MON-005 (Phase 2): System must support system health monitoring via `rag_get_system_health` MCP tool.
FR-MON-006 (Phase 2): System must support tenant health monitoring via `rag_get_tenant_health` MCP tool.
FR-DATA-001 (MVP): System must enforce tenant-level data isolation.
FR-DATA-002 (MVP): System must enforce user-level memory isolation.
FR-DATA-003 (Phase 2): System must support tenant data export via `rag_export_tenant_data` MCP tool.
FR-DATA-004 (Phase 2): System must support user data export via `rag_export_user_data` MCP tool.
FR-PERF-001 (MVP): System must respond to search queries within 200ms (p95) for voice interactions.
FR-PERF-002 (MVP): System must respond to memory operations within 100ms (p95).
FR-PERF-003 (MVP): System must support cold start performance of <500ms.
FR-PERF-004 (Phase 2): System must support Redis caching layer for performance.
FR-ERROR-001 (MVP): System must handle Mem0 API failures gracefully.
FR-ERROR-002 (MVP): System must handle search service failures gracefully.
FR-ERROR-003 (MVP): System must provide structured error responses.
FR-ERROR-004 (MVP): System must handle rate limit exceeded errors.
FR-INT-001 (MVP): System must implement MCP (Model Context Protocol) server.
FR-INT-002 (MVP): System must support MCP tool discovery via `rag_list_tools` MCP tool.
FR-INT-003 (MVP): System must validate MCP request context.
FR-BACKUP-001 (MVP): System must support basic backup operations.
FR-BACKUP-002 (Phase 2): System must support tenant backup via `rag_backup_tenant_data` MCP tool.
FR-BACKUP-003 (Phase 2): System must support tenant restore via `rag_restore_tenant_data` MCP tool.
FR-BACKUP-004 (Phase 2): System must support FAISS index rebuild via `rag_rebuild_index` MCP tool.
FR-BACKUP-005 (Phase 2): System must support backup validation via `rag_validate_backup` MCP tool.
FR-RATE-001 (MVP): System must enforce per-tenant rate limiting.
FR-RATE-002 (Phase 2): System must support tier-based rate limiting.

### NonFunctional Requirements

NFR-PERF-001 (MVP): System must respond to search queries within 200ms (p95) for voice interactions.
NFR-PERF-002 (MVP): System must respond to memory operations within 100ms (p95).
NFR-PERF-003 (MVP): System must support cold start performance of <500ms.
NFR-PERF-004 (MVP): System must respond to user recognition within 100ms (p95).
NFR-PERF-005 (Phase 2): System must respond to multi-modal search queries within 300ms (p95).
NFR-PERF-006 (MVP): System must support 1000 requests per minute per tenant (rate limit).
NFR-PERF-007 (MVP): System must support 200 concurrent users per tenant.
NFR-PERF-008 (Phase 2): System must support tier-based throughput limits.
NFR-PERF-009 (MVP): System must optimize CPU and memory usage.
NFR-PERF-010 (MVP): System must achieve >80% cache hit rate for user memories.
NFR-PERF-011 (Phase 2): System must achieve >60% cache hit rate for search results.
NFR-SCALE-001 (MVP): System must support horizontal scaling via Kubernetes.
NFR-SCALE-002 (MVP): System must support elastic scaling (auto-scaling).
NFR-SCALE-003 (MVP): System must support 200 tenants with complete data isolation.
NFR-SCALE-004 (MVP): System must support 200 concurrent users per tenant.
NFR-SCALE-005 (Phase 3): System must support thousands of tenants with global data residency.
NFR-SCALE-006 (MVP): System must handle 40,000 requests per minute across all tenants (200 tenants × 200 requests/minute).
NFR-SCALE-007 (Phase 2): System must handle 200,000 requests per minute across all tenants.
NFR-REL-001 (MVP): System must achieve >95% uptime.
NFR-REL-002 (Phase 2): System must achieve >99% uptime.
NFR-REL-003 (Phase 3): System must achieve >99.9% uptime (three nines).
NFR-REL-004 (MVP): System must handle Mem0 API failures gracefully.
NFR-REL-005 (MVP): System must handle search service failures gracefully.
NFR-REL-006 (MVP): System must prevent cascade failures.
NFR-REL-007 (MVP): System must achieve RTO (Recovery Time Objective) of <4 hours.
NFR-REL-008 (MVP): System must achieve RPO (Recovery Point Objective) of <1 hour.
NFR-REL-009 (Phase 2): System must achieve RTO of <2 hours and RPO of <30 minutes.
NFR-SEC-001 (MVP): System must encrypt all data at rest using AES-256.
NFR-SEC-002 (MVP): System must encrypt all data in transit using TLS 1.3.
NFR-SEC-003 (MVP): System must enforce RBAC (Role-Based Access Control).
NFR-SEC-004 (MVP): System must enforce tenant-level data isolation.
NFR-SEC-005 (MVP): System must support OAuth 2.0 and tenant-based API key authentication.
NFR-SEC-006 (MVP): System must protect PII (Personally Identifiable Information).
NFR-SEC-007 (MVP): System must prevent data leakage.
NFR-SEC-008 (MVP): System must perform regular security scans.
NFR-SEC-009 (Phase 2): System must perform penetration testing.
NFR-COMP-001 (Phase 2): System must comply with HIPAA requirements for healthcare tenants.
NFR-COMP-002 (MVP): System must comply with PCI DSS requirements for fintech tenants.
NFR-COMP-003 (Phase 2): System must comply with SOC 2 requirements.
NFR-COMP-004 (Phase 2): System must comply with GDPR requirements.
NFR-COMP-005 (MVP): System must maintain comprehensive audit logs for all transactions.
NFR-OBS-001 (MVP): System must provide comprehensive system health monitoring.
NFR-OBS-002 (MVP): System must track performance metrics.
NFR-OBS-003 (Phase 2): System must integrate with Langfuse for observability.
NFR-OBS-004 (MVP): System must provide structured logging.
NFR-OBS-005 (MVP): System must support tenant-scoped logging.
NFR-OBS-006 (MVP): System must maintain audit logs for compliance.
NFR-OBS-007 (Phase 2): System must support distributed tracing.
NFR-OBS-008 (MVP): System must provide proactive alerting.
NFR-OBS-009 (MVP): System must alert on error rate increases.
NFR-MAIN-001 (MVP): System must follow clean architecture principles.
NFR-MAIN-002 (MVP): System must maintain comprehensive documentation.
NFR-MAIN-003 (MVP): System must achieve >80% test coverage.
NFR-MAIN-004 (MVP): System must support automated testing.
NFR-MAIN-005 (MVP): System must provide clear error messages.
NFR-MAIN-006 (Phase 2): System must support distributed tracing.
NFR-DEPLOY-001 (MVP): System must support automated CI/CD pipelines.
NFR-DEPLOY-002 (MVP): System must support zero-downtime deployments.
NFR-DEPLOY-003 (MVP): System must use Infrastructure as Code (IaC).
NFR-DEPLOY-004 (MVP): System must support environment-specific configurations.
NFR-USAB-001 (MVP): System must provide clear MCP tool interfaces.
NFR-USAB-002 (MVP): System must provide comprehensive API documentation.
NFR-USAB-003 (MVP): System must provide clear error messages for developers.
NFR-USAB-004 (Phase 3): System must provide SDKs for multiple languages.

### Additional Requirements

- **Starter Template**: Start from scratch with custom FastMCP + FastAPI structure (no cookiecutter template)
- **Infrastructure Setup (MVP)**: Complete infrastructure setup and configuration for all prerequisite components:
  - **PostgreSQL**: Installation, database schema creation, RLS (Row Level Security) policies setup, connection pooling configuration, health checks
  - **Redis**: Installation, cluster configuration (if needed), persistence setup (RDB + AOF), health checks, connection pooling
  - **MinIO**: Installation, bucket creation (tenant-scoped buckets), access key/secret configuration, health checks, S3-compatible API setup
  - **Meilisearch**: Installation, index creation, tenant-scoped index configuration, search settings, health checks, connection setup
  - **Mem0**: Self-hosted deployment (containerized), API endpoint configuration, health checks, fallback mechanism setup
  - **FAISS**: Library installation, index initialization patterns, tenant-partitioned index structure, persistence configuration (mmap)
  - **Langfuse**: Installation, API key configuration, project setup, async logging integration, health checks
  - **Kubernetes**: Cluster setup (local and production), pod definitions, service definitions, ConfigMaps, Secrets, HPA (Horizontal Pod Autoscaler)
  - **Docker/Docker Compose**: Local development environment with all services, networking, volume mounts, environment variables
  - **Environment Configuration**: .env.example template, environment-specific configs (dev/staging/prod), secrets management
  - **Health Checks**: Health check endpoints for all services, startup probes, readiness probes, liveness probes
  - **Connection Pooling**: Database connection pools, Redis connection pools, service client connection management
  - **Initial Data Setup**: Database migrations (Alembic), initial schema creation, default tenant templates, seed data if needed
- **Infrastructure**: Kubernetes deployment with pod autoscaling, horizontal scaling support
- **Data Isolation**: PostgreSQL RLS with tenant_id policies, tenant-scoped FAISS indices, tenant-prefixed Redis keys
- **Observability**: Langfuse integration as middleware in MCP server layer (MVP requirement, async logging)
- **MCP Server**: FastMCP implementation with HTTP transport, mounted into FastAPI app
- **Database**: SQLAlchemy 2.0 async with Alembic migrations, connection pooling
- **Caching**: Multi-level Redis caching for memory, search results, document metadata
- **Security**: AES-256 encryption at rest, TLS 1.3 in transit, built into all components

### FR Coverage Map

FR-AUDIT-001: Epic 1 (Secure Platform Foundation) - System must log all RAG transactions to audit logs.
FR-AUDIT-002: Epic 1 (Secure Platform Foundation) - System must support audit log querying via `rag_query_audit_logs` MCP tool.
FR-AUTH-001: Epic 1 (Secure Platform Foundation) - System must support OAuth 2.0 authentication for MCP clients.
FR-AUTH-002: Epic 1 (Secure Platform Foundation) - System must support tenant-based API key authentication.
FR-AUTH-003: Epic 1 (Secure Platform Foundation) - System must validate tenant_id in MCP request context.
FR-AUTH-004: Epic 1 (Secure Platform Foundation) - System must support four-tier RBAC structure.
FR-AUTH-005: Epic 1 (Secure Platform Foundation) - System must enforce role-based data access.
FR-AUTH-006: Epic 9 (Advanced Compliance & Data Governance) - System must support Project Admin role for project-scoped access.
FR-BACKUP-001: Epic 1 (Secure Platform Foundation) - System must support basic backup operations.
FR-BACKUP-002: Epic 7 (Data Protection & Disaster Recovery) - System must support tenant backup via `rag_backup_tenant_data` MCP tool.
FR-BACKUP-003: Epic 7 (Data Protection & Disaster Recovery) - System must support tenant restore via `rag_restore_tenant_data` MCP tool.
FR-BACKUP-004: Epic 7 (Data Protection & Disaster Recovery) - System must support FAISS index rebuild via `rag_rebuild_index` MCP tool.
FR-BACKUP-005: Epic 7 (Data Protection & Disaster Recovery) - System must support backup validation via `rag_validate_backup` MCP tool.
FR-COMP-001: Epic 9 (Advanced Compliance & Data Governance) - System must support PCI DSS compliance for fintech domain.
FR-COMP-002: Epic 9 (Advanced Compliance & Data Governance) - System must support HIPAA compliance for healthcare domain.
FR-COMP-003: Epic 9 (Advanced Compliance & Data Governance) - System must support SOC 2 compliance.
FR-COMP-004: Epic 9 (Advanced Compliance & Data Governance) - System must support GDPR compliance.
FR-DATA-001: Epic 1 (Secure Platform Foundation) - System must enforce tenant-level data isolation.
FR-DATA-002: Epic 1 (Secure Platform Foundation) - System must enforce user-level memory isolation.
FR-DATA-003: Epic 9 (Advanced Compliance & Data Governance) - System must support tenant data export via `rag_export_tenant_data` MCP tool.
FR-DATA-004: Epic 9 (Advanced Compliance & Data Governance) - System must support user data export via `rag_export_user_data` MCP tool.
FR-ERROR-001: Epic 5 (Memory & Personalization) - System must handle Mem0 API failures gracefully.
FR-ERROR-002: Epic 4 (Search & Discovery) - System must handle search service failures gracefully.
FR-ERROR-003: Epic 1 (Secure Platform Foundation) - System must provide structured error responses.
FR-ERROR-004: Epic 1 (Secure Platform Foundation) - System must handle rate limit exceeded errors.
FR-INT-001: Epic 1 (Secure Platform Foundation) - System must implement MCP (Model Context Protocol) server.
FR-INT-002: Epic 1 (Secure Platform Foundation) - System must support MCP tool discovery via `rag_list_tools` MCP tool.
FR-INT-003: Epic 1 (Secure Platform Foundation) - System must validate MCP request context.
FR-KB-001: Epic 4 (Search & Discovery) - System must support text-based knowledge base search via `rag_search` MCP tool.
FR-KB-002: Epic 4 (Search & Discovery) - Phase 2 extension: Multi-modal knowledge base search (text, images, audio, video).
FR-KB-003: Epic 4 (Search & Discovery) - Phase 2 extension: Cross-modal search via `rag_cross_modal_search` MCP tool.
FR-KB-004: Epic 4 (Search & Discovery) - System must support hybrid retrieval (vector search + keyword search).
FR-KB-005: Epic 3 (Knowledge Base Management) - System must support document ingestion via `rag_ingest` MCP tool.
FR-KB-006: Epic 3 (Knowledge Base Management) - System must support document versioning on update.
FR-KB-007: Epic 3 (Knowledge Base Management) - System must support document deletion via `rag_delete_document` MCP tool.
FR-KB-008: Epic 3 (Knowledge Base Management) - System must support document retrieval via `rag_get_document` MCP tool.
FR-KB-009: Epic 3 (Knowledge Base Management) - System must support document listing via `rag_list_documents` MCP tool.
FR-MEM-001: Epic 5 (Memory & Personalization) - System must support user memory retrieval via `mem0_get_user_memory` MCP tool.
FR-MEM-002: Epic 5 (Memory & Personalization) - System must support user memory update via `mem0_update_memory` MCP tool.
FR-MEM-003: Epic 5 (Memory & Personalization) - System must support user memory search via `mem0_search_memory` MCP tool.
FR-MEM-004: Epic 6 (Session Continuity & User Recognition) - System must support session context storage and retrieval.
FR-MEM-005: Epic 5 (Memory & Personalization) - System must support memory isolation per tenant and user.
FR-MON-001: Epic 8 (Monitoring, Analytics & Operations) - System must support usage statistics retrieval via `rag_get_usage_stats` MCP tool.
FR-MON-002: Epic 8 (Monitoring, Analytics & Operations) - System must support search analytics via `rag_get_search_analytics` MCP tool.
FR-MON-003: Epic 8 (Monitoring, Analytics & Operations) - System must support memory analytics via `rag_get_memory_analytics` MCP tool.
FR-MON-004: Epic 1 (Secure Platform Foundation) - System must support basic health checks.
FR-MON-005: Epic 8 (Monitoring, Analytics & Operations) - System must support system health monitoring via `rag_get_system_health` MCP tool.
FR-MON-006: Epic 8 (Monitoring, Analytics & Operations) - System must support tenant health monitoring via `rag_get_tenant_health` MCP tool.
FR-PERF-001: Epic 4 (Search & Discovery) - System must respond to search queries within 200ms (p95) for voice interactions.
FR-PERF-002: Epic 5 (Memory & Personalization) - System must respond to memory operations within 100ms (p95).
FR-PERF-003: Epic 6 (Session Continuity & User Recognition) - System must support cold start performance of <500ms.
FR-PERF-004: Epic 6 (Session Continuity & User Recognition) - System must support Redis caching layer for performance.
FR-RATE-001: Epic 1 (Secure Platform Foundation) - System must enforce per-tenant rate limiting.
FR-RATE-002: Epic 9 (Advanced Compliance & Data Governance) - System must support tier-based rate limiting.
FR-SEARCH-001: Epic 4 (Search & Discovery) - System must support semantic vector search using FAISS.
FR-SEARCH-002: Epic 4 (Search & Discovery) - System must support keyword search using Meilisearch.
FR-SEARCH-003: Epic 4 (Search & Discovery) - System must support hybrid retrieval (vector + keyword).
FR-SEARCH-004: Epic 4 (Search & Discovery) - Phase 2 extension: Cross-modal search (text→image, image→text).
FR-SEARCH-005: Epic 4 (Search & Discovery) - Phase 2 extension: Unified embedding space for all modalities.
FR-SESSION-001: Epic 6 (Session Continuity & User Recognition) - System must support session continuity across interruptions.
FR-SESSION-002: Epic 6 (Session Continuity & User Recognition) - System must support context-aware search results.
FR-SESSION-003: Epic 6 (Session Continuity & User Recognition) - System must support returning user recognition.
FR-TENANT-001: Epic 2 (Tenant Onboarding & Configuration) - System must support tenant registration via `rag_register_tenant` MCP tool.
FR-TENANT-002: Epic 2 (Tenant Onboarding & Configuration) - System must support template listing via `rag_list_templates` MCP tool.
FR-TENANT-003: Epic 2 (Tenant Onboarding & Configuration) - System must support template details retrieval via `rag_get_template` MCP tool.
FR-TENANT-004: Epic 9 (Advanced Compliance & Data Governance) - System must support tenant configuration update via `rag_update_tenant_config` MCP tool.
FR-TENANT-005: Epic 9 (Advanced Compliance & Data Governance) - System must support tenant deletion via `rag_delete_tenant` MCP tool.
FR-TENANT-006: Epic 2 (Tenant Onboarding & Configuration) - System must support tenant model configuration via `rag_configure_tenant_models` MCP tool.
FR-TENANT-007: Epic 2 (Tenant Onboarding & Configuration) - System must support tenant-scoped data isolation.
FR-TENANT-008: Epic 9 (Advanced Compliance & Data Governance) - System must support subscription tier management.

**Note:** Phase 2 FRs (FR-KB-002, FR-KB-003, FR-SEARCH-004, FR-SEARCH-005) are extensions to Epic 4 for multi-modal and cross-modal search capabilities.

## Epic List

### Epic 1: Secure Platform Foundation

Platform operators can deploy a secure, auditable RAG system with all prerequisite infrastructure, authentication, authorization, basic backups, and health monitoring operational.

**FRs covered:** FR-INT-001, FR-INT-002, FR-INT-003, FR-AUTH-001, FR-AUTH-002, FR-AUTH-003, FR-AUTH-004, FR-AUTH-005, FR-AUDIT-001, FR-AUDIT-002, FR-MON-004, FR-BACKUP-001, FR-DATA-001, FR-DATA-002, FR-RATE-001, FR-ERROR-003, FR-ERROR-004

**Note:** Includes infrastructure setup, authentication, authorization, audit logging, basic backups, and health monitoring

#### Story 1.1: Project Structure & Development Environment Setup

As a **Developer**,
I want **to set up the project structure and local development environment**,
So that **I can begin implementing the RAG system with all necessary scaffolding in place**.

**Acceptance Criteria:**

**Given** I am starting a new project from scratch
**When** I initialize the project structure following the architecture document
**Then** The directory structure matches the architecture specification (app/, tests/, docker/, kubernetes/, scripts/)
**And** All **init**.py files are created for Python package structure
**And** pyproject.toml and requirements.txt are configured with base dependencies
**And** .env.example template is created with all required environment variables
**And** .gitignore is configured to exclude sensitive files
**And** README.md contains project overview and setup instructions

**Given** I want to run the system locally
**When** I execute docker-compose up
**Then** All prerequisite services start (PostgreSQL, Redis, MinIO, Meilisearch, Mem0, Langfuse)
**And** Services are accessible on their configured ports
**And** Health checks pass for all services
**And** Network connectivity is established between services

**Given** I need to configure the development environment
**When** I copy .env.example to .env and configure values
**Then** All environment variables are properly loaded by the application
**And** Configuration validation passes with Pydantic Settings

#### Story 1.2: Core Infrastructure Services Setup

As a **Platform Operator**,
I want **all prerequisite infrastructure services deployed and configured**,
So that **the RAG system has operational databases, caches, and storage services**.

**Acceptance Criteria:**

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

**Given** FAISS library needs to be available
**When** I install FAISS
**Then** FAISS Python library is installed
**And** Index initialization patterns are ready
**And** Tenant-partitioned index structure is defined
**And** Persistence configuration (mmap) is ready

#### Story 1.3: Database Layer & Schema Foundation

As a **Platform Operator**,
I want **database schema created with tenant isolation**,
So that **data can be stored securely with proper multi-tenant isolation**.

**Acceptance Criteria:**

**Given** Database schema needs to be created
**When** I run Alembic migrations
**Then** Core tables are created (tenants, users, documents, audit_logs, tenant_api_keys)
**And** All tables include tenant_id column for multi-tenant isolation
**And** Foreign key relationships are properly established
**And** Indexes are created for performance (tenant_id, user_id, timestamp)

**Given** Row Level Security (RLS) needs to be configured
**When** I set up PostgreSQL RLS policies
**Then** RLS is enabled on all tenant-scoped tables
**And** Policies enforce tenant_id isolation (users can only access their tenant's data)
**And** Policies are tested to prevent cross-tenant data access
**And** Uber Admin role can bypass RLS for platform operations

**Given** Database connection management is needed
**When** I configure SQLAlchemy 2.0 async
**Then** AsyncSession is configured with connection pooling
**And** Database connection string is loaded from environment
**And** Connection health checks are implemented
**And** Connection retry logic handles transient failures

**Given** Database models need to be defined
**When** I create SQLAlchemy ORM models
**Then** All core entities are modeled (Tenant, User, Document, AuditLog, TenantApiKey)
**And** Models include proper relationships and constraints
**And** Models support async operations
**And** Models include tenant_id for isolation

#### Story 1.4: MCP Server Framework Implementation

As a **Platform Operator**,
I want **FastMCP server implemented with HTTP transport**,
So that **MCP tools can be exposed and consumed by chatbot systems**.

**Acceptance Criteria:**

**Given** MCP server needs to be implemented
**When** I initialize FastMCP server
**Then** FastMCP server instance is created
**And** HTTP transport is configured
**And** Server is mounted into FastAPI app at /mcp endpoint
**And** Server startup and shutdown lifecycle is managed

**Given** MCP tool discovery is required
**When** I implement rag_list_tools MCP tool
**Then** Tool returns list of all available MCP tools
**And** Each tool includes description, parameters, and return types
**And** Tool discovery follows MCP protocol standard
**And** Tool list is dynamically generated from registered tools

**Given** MCP request context validation is needed
**When** I implement context validation middleware
**Then** All MCP requests are validated for required context (tenant_id, user_id, role)
**And** Invalid context returns appropriate error (FR-ERROR-003)
**And** Context is extracted and made available to tools
**And** Context validation happens before tool execution

**Given** FastAPI integration is needed
**When** I integrate FastMCP with FastAPI
**Then** FastMCP http_app() is mounted into FastAPI
**And** Combined lifespan manages both FastAPI and FastMCP startup/shutdown
**And** Health check endpoints are accessible via FastAPI
**And** MCP endpoints are accessible at /mcp path

#### Story 1.5: Authentication Middleware

As a **Platform Operator**,
I want **OAuth 2.0 and API key authentication implemented**,
So that **MCP clients can securely authenticate to access the system**.

**Acceptance Criteria:**

**Given** OAuth 2.0 authentication is required
**When** I implement OAuth 2.0 token validation
**Then** Bearer tokens are extracted from Authorization header
**And** Tokens are validated against OAuth provider
**And** User_id and tenant_id are extracted from token claims (preferred) or user profile lookup (fallback)
**And** Authentication completes within <50ms (FR-AUTH-001)
**And** Invalid tokens return 401 Unauthorized with structured error (FR-ERROR-003)

**Given** API key authentication is required
**When** I implement tenant-based API key validation
**Then** API keys are extracted from request headers or context
**And** API keys are validated against tenant_api_keys table
**And** Tenant_id is extracted from API key association
**And** Associated user_id is retrieved
**And** Authentication completes within <50ms (FR-AUTH-002)
**And** Invalid API keys return 401 Unauthorized with structured error

**Given** Authentication middleware needs to be integrated
**When** I implement auth middleware in app/mcp/middleware/auth.py
**Then** Middleware executes as first step in middleware stack
**And** Authenticated user_id is stored in context for downstream middleware
**And** Authentication failures prevent tool execution
**And** Audit logs capture authentication attempts (success/failure)

#### Story 1.6: Authorization & RBAC Middleware

As a **Platform Operator**,
I want **four-tier RBAC with role-based access control implemented**,
So that **users can only access resources permitted by their role**.

**Acceptance Criteria:**

**Given** RBAC structure needs to be implemented
**When** I implement authorization middleware
**Then** Four roles are supported: Uber Admin, Tenant Admin, Project Admin (Phase 2), End User
**And** Role is extracted from authenticated user context
**And** Role permissions are defined for each MCP tool
**And** Permission checking happens before tool execution (FR-AUTH-004)

**Given** Role-based data access needs to be enforced
**When** I implement role-based access logic
**Then** Uber Admin has full platform access and cross-tenant operations
**And** Tenant Admin has full tenant access within their tenant
**And** End User has read-only access with user-scoped memory and role-based knowledge base filtering
**And** Each MCP tool checks role permissions before execution (FR-AUTH-005)
**And** Unauthorized access returns 403 Forbidden with structured error

**Given** Authorization middleware needs to be integrated
**When** I implement authorization middleware in app/mcp/middleware/authorization.py
**Then** Middleware executes after authentication and tenant extraction
**And** Role permissions are checked against tool requirements
**And** Authorization failures prevent tool execution
**And** Audit logs capture role and permission checks

#### Story 1.7: Tenant Isolation & Data Security

As a **Platform Operator**,
I want **tenant-level and user-level data isolation enforced**,
So that **data from different tenants and users is completely isolated**.

**Acceptance Criteria:**

**Given** Tenant-level isolation needs to be enforced
**When** I implement tenant isolation patterns
**Then** PostgreSQL RLS policies enforce tenant_id isolation at database level (FR-DATA-001)
**And** FAISS indices are tenant-scoped (separate index per tenant)
**And** Redis keys are prefixed with tenant_id
**And** MinIO buckets are tenant-scoped
**And** Zero cross-tenant data access is possible (validated through testing)

**Given** User-level memory isolation needs to be enforced
**When** I implement user memory isolation
**Then** Memory keys are prefixed with tenant_id:user_id format (FR-DATA-002)
**And** Users can only access their own memory (except Tenant Admin for management)
**And** Memory isolation is enforced at Mem0 and Redis layers
**And** Zero cross-user memory access is possible (validated through testing)

**Given** Tenant extraction middleware is needed
**When** I implement tenant extraction middleware
**Then** Tenant_id is extracted from authenticated context or request
**Then** Tenant_id is validated against authenticated user's tenant membership (FR-AUTH-003)
**And** Invalid tenant_id returns 403 Forbidden error
**And** Tenant context is stored for downstream middleware and tools

#### Story 1.8: Audit Logging Infrastructure

As a **Platform Operator**,
I want **comprehensive audit logging for all operations**,
So that **all system activities are tracked for compliance and security**.

**Acceptance Criteria:**

**Given** Audit logging is required for all transactions
**When** I implement audit logging middleware
**Then** All MCP tool calls are logged to audit_logs table (FR-AUDIT-001)
**And** Mandatory fields are captured: timestamp (ISO 8601), actor (user_id, tenant_id, role, auth_method), action (operation type), resource (document_id, memory_key, search_query), result (success/failure, details), metadata (IP, session_id, compliance_flags)
**And** Audit logs are stored in PostgreSQL with indexed fields (timestamp, tenant_id, user_id, action_type)
**And** Logging happens asynchronously to avoid latency impact

**Given** Audit log querying is required
**When** I implement rag_query_audit_logs MCP tool
**Then** Tool supports filtering by timestamp, actor (user_id, tenant_id, role), action_type, resource, result_status, metadata (FR-AUDIT-002)
**And** Tool supports pagination (cursor-based or limit/offset)
**And** Access is restricted to Tenant Admin and Uber Admin roles only
**And** Query performance is optimized with proper indexing

**Given** Audit middleware needs to be integrated
**When** I implement audit middleware in app/mcp/middleware/audit.py
**Then** Middleware executes before and after tool execution
**And** Pre-execution logs capture request details
**And** Post-execution logs capture result and response details
**And** Audit logging is non-blocking (async)

#### Story 1.9: Rate Limiting Middleware

As a **Platform Operator**,
I want **per-tenant rate limiting implemented**,
So that **system resources are protected from abuse and overuse**.

**Acceptance Criteria:**

**Given** Rate limiting is required
**When** I implement rate limiting middleware
**Then** Per-tenant rate limiting is enforced (1000 hits/minute default, configurable) (FR-RATE-001)
**And** Redis-based sliding window algorithm is used
**And** Rate limit tracking uses tenant_id as key prefix
**And** Rate limit exceeded returns 429 Too Many Requests with Retry-After header (FR-ERROR-004)
**And** Rate limit headers are included (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)

**Given** Rate limiting middleware needs to be integrated
**When** I implement rate limit middleware in app/mcp/middleware/rate_limit.py
**Then** Middleware executes after authentication and tenant extraction
**And** Rate limit checking happens before tool execution
**And** Rate limit violations are logged to audit logs
**And** Rate limit state is managed in Redis with proper TTL

#### Story 1.10: Error Handling Framework

As a **Platform Operator**,
I want **structured error responses and comprehensive error handling**,
So that **developers and users receive clear, actionable error information**.

**Acceptance Criteria:**

**Given** Structured error responses are required
**When** I implement error handling utilities
**Then** All errors return structured format: error code, error message, error details, recovery suggestions, request_id (FR-ERROR-003)
**And** Appropriate HTTP status codes are used (400, 401, 403, 404, 429, 500, 503)
**And** MCP protocol error format is followed
**And** Error codes are consistent across all tools

**Given** Rate limit errors need special handling
**When** I implement rate limit error handling
**Then** 429 Too Many Requests is returned with Retry-After header (FR-ERROR-004)
**And** Rate limit information is included (limit, remaining, reset time)
**And** Error message explains rate limit exceeded and suggests retry time

**Given** Error handling utilities are needed
**When** I implement error utilities in app/utils/errors.py
**Then** Error classes are defined for different error types
**And** Error serialization follows structured format
**And** Error logging captures full error context
**And** Error handling is consistent across all MCP tools

#### Story 1.11: Health Check Endpoints

As a **Platform Operator**,
I want **health check endpoints for system monitoring**,
So that **I can verify system and component health**.

**Acceptance Criteria:**

**Given** Health checks are required
**When** I implement basic health check endpoint
**Then** Health check endpoint returns system health status (healthy, degraded, unhealthy) (FR-MON-004)
**And** Component status is included (PostgreSQL, FAISS, Mem0, Redis, MCP server)
**And** Response time is <50ms for health check
**And** Health check is accessible without authentication

**Given** Component health validation is needed
**When** I implement component health checks
**Then** PostgreSQL connection is validated
**And** Redis connection is validated
**And** Mem0 API health is checked
**And** FAISS index accessibility is validated
**And** Component failures are reported in health status

**Given** Health check endpoints need to be implemented
**When** I implement health endpoints in app/api/health.py
**Then** /health endpoint returns overall system health
**Then** /ready endpoint returns readiness status (for Kubernetes)
**And** Health checks are integrated into FastAPI app
**And** Health status is suitable for Kubernetes liveness and readiness probes

#### Story 1.12: Basic Backup Operations

As a **Platform Operator**,
I want **basic backup operations for critical data**,
So that **data can be recovered in case of system failures**.

**Acceptance Criteria:**

**Given** Backup operations are required
**When** I implement basic backup scripts
**Then** PostgreSQL daily backups are configured (FR-BACKUP-001)
**And** FAISS indices daily snapshots are configured
**And** Mem0 memory daily snapshots are configured
**And** Backup retention is 30 days for critical data, 7 days for indices
**And** Backups are stored in separate backup infrastructure

**Given** Backup automation is needed
**When** I implement backup scheduling
**Then** Backups run automatically on daily schedule
**And** Backup status is logged
**And** Backup failures trigger alerts
**And** Backup validation checks are performed

**Given** Backup scripts are needed
**When** I implement backup script in scripts/backup.py
**Then** Script can backup PostgreSQL (WAL archiving, daily backups)
**And** Script can backup FAISS indices (daily snapshots)
**And** Script can backup Mem0 memory (daily snapshots)
**And** Script supports backup validation

#### Story 1.13: Observability Integration (Langfuse)

As a **Platform Operator**,
I want **Langfuse integrated for tool call tracking and observability**,
So that **I can monitor MCP tool performance and usage**.

**Acceptance Criteria:**

**Given** Langfuse integration is required (MVP requirement)
**When** I implement Langfuse middleware
**Then** All MCP tool calls are logged to Langfuse (NFR-OBS-003)
**And** Tool execution time is tracked
**And** Cache hit rates are tracked per tenant
**And** Error rates are tracked per tenant
**And** Logging is asynchronous to avoid latency impact

**Given** Langfuse middleware needs to be integrated
**When** I implement observability middleware in app/mcp/middleware/observability.py
**Then** Middleware executes before and after tool execution
**And** Pre-execution logs capture tool name, parameters, user, tenant
**And** Post-execution logs capture execution time, result, cache status
**And** Langfuse client is configured with API key and project settings
**And** Integration is non-intrusive (async logging)

**Given** Langfuse configuration is needed
**When** I configure Langfuse in app/config/langfuse.py
**Then** Langfuse API key is loaded from environment
**And** Project configuration is set up
**And** Client connection is validated
**And** Health check validates Langfuse availability

### Epic 2: Tenant Onboarding & Configuration

Platform operators can onboard new tenants with domain templates, and tenants can discover available templates and configure their domain-specific settings.

**FRs covered:** FR-TENANT-001, FR-TENANT-002, FR-TENANT-003, FR-TENANT-006, FR-TENANT-007

**Note:** Complete tenant onboarding capability with template-based setup

#### Story 2.1: Domain Template Management

As a **Platform Operator**,
I want **domain templates to be defined and stored in the system**,
So that **tenants can select appropriate templates during onboarding**.

**Acceptance Criteria:**

**Given** Domain templates need to be created
**When** I create template data models
**Then** Template schema includes: template_id, template_name, domain_type (fintech, healthcare, retail, customer_service, custom), description, compliance_checklist, default_configuration, customization_options
**And** Templates are stored in PostgreSQL templates table
**And** Initial templates are seeded via Alembic migration script (Fintech template for MVP)
**And** Migration script includes template data insertion with proper error handling
**And** Template seeding is idempotent (can be run multiple times safely)

**Given** Template data needs to be accessible
**When** I query templates
**Then** Templates can be retrieved by template_id
**And** Templates can be listed with domain filter
**And** Template details include all configuration options and compliance requirements
**And** Template queries complete within <50ms (p95)

#### Story 2.2: Template Discovery MCP Tool

As a **Tenant Admin**,
I want **to discover available domain templates**,
So that **I can select the most appropriate template for my tenant**.

**Acceptance Criteria:**

**Given** Template listing is required
**When** I implement rag_list_templates MCP tool
**Then** Tool returns list of available templates with descriptions (FR-TENANT-002)
**And** Tool supports optional domain filter parameter
**And** Each template includes: template_id, template_name, domain_type, description, compliance_checklist, configuration_options
**And** Tool is accessible to all authenticated users (for discovery)
**And** Response time is <100ms (p95)

**Given** Template details retrieval is required
**When** I implement rag_get_template MCP tool
**Then** Tool returns complete template details for given template_id (FR-TENANT-003)
**And** Details include: configuration options, compliance requirements, customization guide, example configurations
**And** Tool is accessible to all authenticated users
**And** Response time is <100ms (p95)

#### Story 2.3: Tenant Registration MCP Tool

As a **Platform Operator (Uber Admin)**,
I want **to register new tenants with domain templates**,
So that **tenants can be onboarded with appropriate domain configurations**.

**Acceptance Criteria:**

**Given** Tenant registration is required
**When** I implement rag_register_tenant MCP tool
**Then** Tool accepts: tenant_id, tenant_name, domain_template (mandatory), optional configuration (FR-TENANT-001)
**And** Tool validates template_id exists and is valid
**And** Tool creates tenant record in tenants table
**And** Tool applies template default configuration
**And** Tool creates tenant-scoped resources (FAISS index, MinIO bucket, Meilisearch index, Redis key prefix)
**And** Access is restricted to Uber Admin role only
**And** Registration completes within <500ms

**Given** Template-based configuration needs to be applied
**When** I register a tenant with a template
**Then** Default compliance settings from template are applied
**And** Default data models from template are configured
**And** Tenant can customize settings after registration
**And** Template configuration is stored in tenant_config table

**Given** Tenant-scoped resources need to be initialized
**When** I register a tenant
**Then** Tenant-scoped FAISS index is created (using tenant-prefixed index name pattern: `tenant_{tenant_id}_index` for scalability)
**And** Tenant-scoped MinIO bucket is created
**And** Tenant-scoped Meilisearch index is created
**And** Tenant Redis key prefix is configured
**And** All resources are properly isolated by tenant_id
**And** Index creation pattern supports horizontal scaling (single FAISS index with tenant filtering for MVP, separate indices per tenant for Phase 2 if needed)

#### Story 2.4: Tenant Model Configuration MCP Tool

As a **Tenant Admin**,
I want **to configure tenant-specific AI models**,
So that **my tenant can use domain-appropriate models for embeddings and LLM operations**.

**Acceptance Criteria:**

**Given** Model configuration is required
**When** I implement rag_configure_tenant_models MCP tool
**Then** Tool accepts: tenant_id, model_configuration (embedding_model, llm_model, domain-specific models) (FR-TENANT-006)
**And** Tool validates model configuration (model availability, compatibility)
**And** Tool stores configuration in tenant_config table
**And** Tool updates tenant model settings for all operations
**And** Access is restricted to Tenant Admin role only
**And** Configuration update completes within <200ms

**Given** Model validation is required
**When** I configure tenant models
**Then** System validates embedding model is available and compatible
**And** System validates LLM model is available and compatible
**And** System validates domain-specific models (if specified)
**And** Invalid model configurations return structured error with suggestions

#### Story 2.5: Tenant Data Isolation Validation

As a **Platform Operator**,
I want **tenant-scoped data isolation to be validated and enforced**,
So that **data from different tenants is completely isolated**.

**Acceptance Criteria:**

**Given** Tenant isolation needs to be validated
**When** I implement tenant isolation validation
**Then** PostgreSQL RLS policies enforce tenant_id isolation (FR-TENANT-007)
**And** FAISS indices are tenant-scoped (separate index per tenant)
**And** Redis keys are prefixed with tenant_id
**And** MinIO buckets are tenant-scoped
**And** Meilisearch indices are tenant-scoped
**And** Zero cross-tenant data access is possible (validated through comprehensive testing)

**Given** Isolation testing is required
**When** I run isolation tests
**Then** Tests verify no cross-tenant data access in PostgreSQL (100% test coverage with negative test cases)
**And** Tests verify no cross-tenant index access in FAISS (attempts to access other tenant's index return empty results or errors)
**And** Tests verify no cross-tenant key access in Redis (tenant A cannot access tenant B's keys)
**And** Tests verify no cross-tenant bucket access in MinIO (tenant A cannot list or access tenant B's bucket)
**And** Tests verify no cross-tenant index access in Meilisearch (tenant A cannot query tenant B's index)
**And** All isolation tests pass with 100% pass rate
**And** Isolation tests include edge cases: concurrent access, tenant deletion, tenant re-creation with same ID

### Epic 3: Knowledge Base Management

Tenants can ingest, manage, version, and organize their knowledge base documents, building their searchable content repository.

**FRs covered:** FR-KB-005, FR-KB-006, FR-KB-007, FR-KB-008, FR-KB-009

**Note:** Complete document management capability for building knowledge base

#### Story 3.1: Document Ingestion MCP Tool

As a **Tenant Admin**,
I want **to ingest documents into the knowledge base**,
So that **documents become searchable and available for RAG operations**.

**Acceptance Criteria:**

**Given** Document ingestion is required
**When** I implement rag_ingest MCP tool
**Then** Tool accepts: document_content (text, images, tables), document_metadata (title, source, type), tenant_id, optional document_id (FR-KB-005)
**And** Tool extracts text content from documents
**And** Tool generates embeddings using tenant-configured embedding model
**And** Tool stores document in PostgreSQL documents table
**And** Tool stores document content in MinIO (tenant-scoped bucket)
**And** Tool indexes document in FAISS (tenant-scoped index)
**And** Tool indexes document in Meilisearch (tenant-scoped index)
**And** Tool returns document_id and ingestion status
**And** Access is restricted to Tenant Admin and End User roles
**And** Ingestion completes within <2s for typical documents

**Given** Multi-modal document support is required
**When** I ingest documents with different modalities
**Then** Text documents are processed and indexed
**And** Image documents are processed (OCR if needed) and indexed
**And** Table documents are processed and indexed
**And** All modalities are stored with proper metadata
**And** Audio and video document support is deferred to Phase 2 (separate story for audio/video ingestion pipeline)

#### Story 3.2: Document Versioning

As a **Tenant Admin**,
I want **documents to be versioned when updated**,
So that **I can track document changes and maintain history**.

**Acceptance Criteria:**

**Given** Document versioning is required
**When** I update an existing document
**Then** New version is created with incremented version number (FR-KB-006)
**And** Previous version is retained in document_versions table
**And** Document metadata includes current version number
**And** Version history is queryable
**And** FAISS and Meilisearch indices are updated with new version
**And** Old version embeddings are marked as deprecated (not deleted for history)

**Given** Version retrieval is required
**When** I query document versions
**Then** All versions of a document can be retrieved
**And** Version metadata includes: version_number, created_at, created_by, change_summary
**And** Specific version can be retrieved by version_number

#### Story 3.3: Document Deletion MCP Tool

As a **Tenant Admin**,
I want **to delete documents from the knowledge base**,
So that **I can remove outdated or incorrect documents**.

**Acceptance Criteria:**

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

#### Story 3.4: Document Retrieval MCP Tool

As a **User**,
I want **to retrieve specific documents from the knowledge base**,
So that **I can access document content and metadata**.

**Acceptance Criteria:**

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

#### Story 3.5: Document Listing MCP Tool

As a **User**,
I want **to list documents in the knowledge base**,
So that **I can browse and discover available documents**.

**Acceptance Criteria:**

**Given** Document listing is required
**When** I implement rag_list_documents MCP tool
**Then** Tool accepts: tenant_id, optional filters (document_type, source, date_range), pagination parameters (FR-KB-009)
**And** Tool returns list of documents with metadata (document_id, title, type, source, created_at, version)
**And** Tool supports pagination (cursor-based or limit/offset)
**And** Tool filters results by tenant_id (tenant isolation)
**And** Tool supports filtering by document_type, source, date_range
**And** Access is available to Tenant Admin and End User roles
**And** Listing completes within <200ms (p95)

**Given** Document search within listing is required
**When** I list documents with search query
**Then** Tool supports optional search query parameter
**And** Tool filters documents by search query (title, content preview)
**And** Results are ranked by relevance

### Epic 4: Search & Discovery

Users can search the knowledge base using hybrid retrieval (vector + keyword) to find relevant information quickly and accurately.

**FRs covered:** FR-KB-001, FR-KB-004, FR-SEARCH-001, FR-SEARCH-002, FR-SEARCH-003, FR-ERROR-002, FR-PERF-001

**Phase 2 Extensions:** FR-KB-002 (multi-modal search), FR-KB-003 (cross-modal search), FR-SEARCH-004 (cross-modal search), FR-SEARCH-005 (unified embedding space)

**Note:** Complete search capability with hybrid retrieval and fallback mechanisms. Phase 2 adds multi-modal and cross-modal search capabilities.

#### Story 4.1: FAISS Vector Search Implementation

As a **User**,
I want **semantic vector search using FAISS**,
So that **I can find documents based on semantic similarity**.

**Acceptance Criteria:**

**Given** Vector search is required
**When** I implement FAISS vector search
**Then** Search query is converted to embedding using tenant-configured embedding model (FR-SEARCH-001)
**And** Embedding is searched in tenant-scoped FAISS index
**And** Results are ranked by cosine similarity (or configured distance metric)
**And** Top K results are returned (default K=10, configurable)
**And** Response time is <150ms (p95) for vector search
**And** Search accuracy is >90% (relevant results in top 5)

**Given** Tenant isolation is required
**When** I perform vector search
**Then** Search is performed only in tenant's FAISS index
**And** Cross-tenant index access is prevented
**And** Results are filtered by tenant_id

#### Story 4.2: Meilisearch Keyword Search Implementation

As a **User**,
I want **keyword search using Meilisearch**,
So that **I can find documents using exact keyword matching**.

**Acceptance Criteria:**

**Given** Keyword search is required
**When** I implement Meilisearch keyword search
**Then** Search query is sent to tenant-scoped Meilisearch index (FR-SEARCH-002)
**And** Meilisearch performs full-text search with ranking
**And** Results are ranked by relevance score
**And** Top K results are returned (default K=10, configurable)
**And** Response time is <100ms (p95) for keyword search

**Given** Tenant isolation is required
**When** I perform keyword search
**Then** Search is performed only in tenant's Meilisearch index
**And** Cross-tenant index access is prevented
**And** Results are filtered by tenant_id

#### Story 4.3: Hybrid Retrieval Engine

As a **User**,
I want **hybrid retrieval combining vector and keyword search**,
So that **I get the best results from both semantic and keyword matching**.

**Acceptance Criteria:**

**Given** Hybrid retrieval is required
**When** I implement hybrid search
**Then** Vector search results are retrieved from FAISS (FR-SEARCH-003)
**And** Keyword search results are retrieved from Meilisearch
**And** Results are merged and deduplicated by document_id
**And** Results are re-ranked using combined relevance score (weighted combination)
**And** Final ranked results are returned
**And** Response time is <200ms (p95) for hybrid search (FR-PERF-001)

**Given** Fallback mechanism is required
**When** FAISS or Meilisearch service fails
**Then** Three-tier fallback is implemented: FAISS + Meilisearch → FAISS only → Meilisearch only (FR-ERROR-002)
**And** Fallback is triggered when FAISS or Meilisearch returns 5xx errors or connection timeouts (>500ms)
**And** Fallback is transparent to user (no error, degraded results)
**And** Fallback is logged for monitoring with service degradation alerts
**And** Fallback behavior is tested: simulate FAISS failure, verify Meilisearch-only results; simulate Meilisearch failure, verify FAISS-only results; simulate both failures, verify graceful error handling

#### Story 4.4: RAG Search MCP Tool

As a **User**,
I want **to search the knowledge base via MCP tool**,
So that **I can retrieve relevant documents for RAG operations**.

**Acceptance Criteria:**

**Given** RAG search is required
**When** I implement rag_search MCP tool
**Then** Tool accepts: search_query (text), tenant_id, user_id, optional filters (document_type, date_range, tags) (FR-KB-001)
**And** Tool performs hybrid retrieval (vector + keyword)
**And** Tool returns ranked list of relevant documents with metadata (document_id, title, snippet, relevance_score, source, timestamp)
**And** Tool supports optional filters for document_type, date_range, tags
**And** Access is available to Tenant Admin and End User roles
**And** Response time is <200ms (p95) for voice interactions (FR-PERF-001)
**And** Search accuracy is >90% (relevant results in top 5)

**Given** Context-aware search is required
**When** I perform search with user context
**Then** Search results can be personalized based on user memory (if available)
**And** Session context can influence result ranking
**And** Personalization is optional and configurable

### Epic 5: Memory & Personalization

System remembers user context and history, enabling personalized experiences and context-aware responses across sessions.

**FRs covered:** FR-MEM-001, FR-MEM-002, FR-MEM-003, FR-MEM-005, FR-ERROR-001, FR-PERF-002

**Note:** Complete memory management with user personalization

#### Story 5.1: Mem0 Integration Layer

As a **Platform Operator**,
I want **Mem0 integrated for user memory management**,
So that **the system can store and retrieve user memories**.

**Acceptance Criteria:**

**Given** Mem0 integration is required
**When** I implement Mem0 integration layer
**Then** Mem0 client is configured with API endpoint and credentials
**And** Mem0 connection is validated on startup
**And** Mem0 health check is implemented
**And** Fallback mechanism to Redis is configured if Mem0 is unavailable (FR-ERROR-001)
**And** Memory keys use tenant_id:user_id format for isolation (FR-MEM-005)

**Given** Mem0 API failures need handling
**When** Mem0 API fails
**Then** System falls back to Redis for memory operations (read-only mode: retrieves existing memories, queues writes for later sync)
**And** Fallback is triggered when Mem0 returns 5xx errors or connection timeouts (>500ms)
**And** Fallback is transparent to users (no errors, operations complete successfully)
**And** Fallback is logged for monitoring with service degradation alerts
**And** System retries Mem0 connection periodically (exponential backoff, max 5 retries)
**And** Queued writes are synced to Mem0 when connection is restored
**And** Fallback behavior is tested: simulate Mem0 failure, verify Redis fallback; verify write queuing; verify sync on recovery

#### Story 5.2: User Memory Retrieval MCP Tool

As a **User**,
I want **to retrieve my user memories**,
So that **I can access stored context and preferences**.

**Acceptance Criteria:**

**Given** Memory retrieval is required
**When** I implement mem0_get_user_memory MCP tool
**Then** Tool accepts: user_id, tenant_id, optional memory_key, optional filters (FR-MEM-001)
**And** Tool retrieves memories from Mem0 (or Redis fallback) using tenant_id:user_id key format
**And** Tool returns user memory data (key-value pairs) with metadata (timestamp, source)
**And** Tool supports filtering by memory_key or other criteria
**And** Access is restricted to user's own memories (or Tenant Admin for management)
**And** Response time is <100ms (p95) for memory retrieval (FR-PERF-002)

**Given** Memory isolation is required
**When** I retrieve memories
**Then** Only memories for the specified user_id and tenant_id are returned
**And** Cross-user memory access is prevented
**And** Cross-tenant memory access is prevented

#### Story 5.3: User Memory Update MCP Tool

As a **User**,
I want **to update my user memories**,
So that **I can store and modify my context and preferences**.

**Acceptance Criteria:**

**Given** Memory update is required
**When** I implement mem0_update_memory MCP tool
**Then** Tool accepts: user_id, tenant_id, memory_key, memory_value, optional metadata (FR-MEM-002)
**And** Tool creates memory if it doesn't exist
**And** Tool updates memory if it exists
**And** Tool maintains version history (optional)
**And** Tool stores memory in Mem0 (or Redis fallback) with tenant_id:user_id key format
**And** Access is restricted to user's own memories (or Tenant Admin for management)
**And** Response time is <100ms (p95) for memory update (FR-PERF-002)

**Given** Memory validation is required
**When** I update a memory
**Then** Memory key and value are validated
**And** Memory size limits are enforced
**And** Invalid memory data returns structured error

#### Story 5.4: User Memory Search MCP Tool

As a **User**,
I want **to search my user memories**,
So that **I can find relevant stored context**.

**Acceptance Criteria:**

**Given** Memory search is required
**When** I implement mem0_search_memory MCP tool
**Then** Tool accepts: user_id, tenant_id, search_query, optional filters (FR-MEM-003)
**And** Tool searches memories using semantic search (Mem0) or keyword search (Redis fallback)
**And** Tool returns relevant memory entries matching query, ranked by relevance
**And** Tool supports filtering by memory_key, timestamp, or other criteria
**And** Access is restricted to user's own memories (or Tenant Admin for management)
**And** Response time is <100ms (p95) for memory search (FR-PERF-002)

### Epic 6: Session Continuity & User Recognition

Users can resume conversations seamlessly, and returning users are recognized instantly with personalized greetings and context.

**FRs covered:** FR-SESSION-001, FR-SESSION-002, FR-SESSION-003, FR-MEM-004, FR-PERF-003, FR-PERF-004

**Note:** Complete session management for seamless user experience

#### Story 6.1: Session Context Storage

As a **User**,
I want **my session context to be stored**,
So that **I can resume conversations after interruptions**.

**Acceptance Criteria:**

**Given** Session context storage is required
**When** I implement session context storage
**Then** Session context is stored in Redis with key format: tenant_id:user_id:session_id (FR-MEM-004)
**And** Session context includes: conversation_state, interrupted_queries, recent_interactions, user_preferences
**And** Session context has TTL (time-to-live) for automatic cleanup (default 24 hours)
**And** Session context can be updated incrementally
**And** Storage completes within <100ms (p95) (FR-PERF-003)
**And** Background cleanup job runs daily to remove orphaned sessions (sessions with no recent activity for 48+ hours)
**And** Cleanup job is configurable per tenant (TTL and cleanup frequency)

**Given** Session context retrieval is required
**When** I retrieve session context
**Then** Session context is retrieved by session_id, user_id, tenant_id
**And** Context includes all stored conversation state
**And** Retrieval completes within <100ms (p95) (FR-PERF-003)

#### Story 6.2: Session Continuity Support

As a **User**,
I want **to resume conversations seamlessly**,
So that **I can continue where I left off after interruptions**.

**Acceptance Criteria:**

**Given** Session continuity is required
**When** I implement session continuity
**Then** System stores session context on conversation interruptions (FR-SESSION-001)
**And** System retrieves session context on session resumption
**And** System enables seamless conversation continuation
**And** Previous conversation state is restored
**And** Interrupted queries are preserved and can be resumed

**Given** Session resumption is required
**When** I resume a session
**Then** Session context is loaded automatically
**And** Conversation continues from where it left off
**And** User doesn't need to repeat previous context
**And** Resumption completes within <500ms (cold start acceptable) (FR-PERF-003)

#### Story 6.3: Context-Aware Search Results

As a **User**,
I want **search results to be personalized based on my context**,
So that **I get more relevant and personalized information**.

**Acceptance Criteria:**

**Given** Context-aware search is required
**When** I implement context-aware search
**Then** Search results are personalized based on user memory (FR-SESSION-002)
**And** Search results are personalized based on session context
**And** User preferences influence result ranking
**And** Personalization is optional and configurable per tenant
**And** Personalization doesn't degrade search performance (<200ms p95)

**Given** Context integration is required
**When** I perform a search
**Then** User memory is retrieved and used for personalization
**And** Session context is retrieved and used for personalization
**And** Knowledge base search is combined with user context
**And** Results are ranked considering both relevance and personalization

#### Story 6.4: Returning User Recognition

As a **User**,
I want **to be recognized when I return**,
So that **I get personalized greetings and context**.

**Acceptance Criteria:**

**Given** User recognition is required
**When** I implement user recognition
**Then** System recognizes returning users by user_id and tenant_id (FR-SESSION-003)
**Then** System retrieves user memory on recognition
**And** System provides personalized greeting based on user memory
**And** System provides context summary (recent interactions, preferences)
**And** Recognition completes within <100ms (p95) (FR-PERF-003)

**Given** Redis caching is required for performance
**When** I recognize a user
**Then** User memory is cached in Redis for fast access (FR-PERF-004)
**And** Cache hit rate is >80% for user memories
**And** Cache TTL is configured appropriately
**And** Cache invalidation happens on memory updates

### Epic 7: Data Protection & Disaster Recovery

Platform operators can backup tenant data, restore from backups, rebuild indices, and meet RTO/RPO objectives for business continuity.

**FRs covered:** FR-BACKUP-002, FR-BACKUP-003, FR-BACKUP-004, FR-BACKUP-005

**Note:** Advanced backup and disaster recovery capabilities (Phase 2 features)

#### Story 7.1: Tenant Backup MCP Tool

As a **Platform Operator**,
I want **to backup tenant data**,
So that **I can recover tenant data in case of failures**.

**Acceptance Criteria:**

**Given** Tenant backup is required
**When** I implement rag_backup_tenant_data MCP tool
**Then** Tool accepts: tenant_id, backup_type (full, incremental), optional backup_location (FR-BACKUP-002)
**And** Tool backs up PostgreSQL data (tenant-scoped tables)
**And** Tool backs up FAISS index (tenant-scoped)
**And** Tool backs up MinIO objects (tenant-scoped bucket)
**And** Tool backs up Meilisearch index (tenant-scoped)
**And** Tool creates backup manifest with metadata (timestamp, tenant_id, backup_type, file_list)
**And** Tool stores backup in separate backup infrastructure
**And** Access is restricted to Uber Admin and Tenant Admin roles
**And** Backup completes within RTO target: <2 hours for full backup, <30 minutes for incremental backup (for typical tenant with <10GB data)
**And** Backup progress is trackable (percentage complete, estimated time remaining)

**Given** Backup validation is required
**When** I create a backup
**Then** Backup integrity is validated
**And** Backup manifest is verified
**And** Backup status is logged
**And** Backup failures trigger alerts

#### Story 7.2: Tenant Restore MCP Tool

As a **Platform Operator**,
I want **to restore tenant data from backups**,
So that **I can recover from data loss or corruption**.

**Acceptance Criteria:**

**Given** Tenant restore is required
**When** I implement rag_restore_tenant_data MCP tool
**Then** Tool accepts: tenant_id, backup_id, restore_type (full, partial), confirmation (FR-BACKUP-003)
**And** Tool validates backup exists and is valid
**And** Tool restores PostgreSQL data (tenant-scoped tables)
**And** Tool restores FAISS index (tenant-scoped)
**And** Tool restores MinIO objects (tenant-scoped bucket)
**And** Tool restores Meilisearch index (tenant-scoped)
**And** Tool validates restore integrity
**And** Access is restricted to Uber Admin role only
**And** Restore completes within RTO target: <4 hours for full restore, <1 hour for partial restore (for typical tenant with <10GB data)
**And** Restore progress is trackable (percentage complete, estimated time remaining)

**Given** Restore safety is required
**When** I restore tenant data
**Then** Current data is backed up before restore (safety backup)
**And** Restore requires explicit confirmation
**And** Restore is logged for audit
**And** Restore failures trigger alerts

#### Story 7.3: FAISS Index Rebuild MCP Tool

As a **Platform Operator**,
I want **to rebuild FAISS indices**,
So that **I can recover from index corruption or optimize indices**.

**Acceptance Criteria:**

**Given** Index rebuild is required
**When** I implement rag_rebuild_index MCP tool
**Then** Tool accepts: tenant_id, index_type (FAISS), rebuild_type (full, incremental) (FR-BACKUP-004)
**And** Tool retrieves all documents for tenant from PostgreSQL
**And** Tool regenerates embeddings for all documents
**And** Tool rebuilds FAISS index with new embeddings
**And** Tool validates index integrity
**And** Tool updates index metadata
**And** Access is restricted to Uber Admin and Tenant Admin roles
**And** Rebuild completes within reasonable time (depends on document count)

**Given** Rebuild optimization is required
**When** I rebuild an index
**Then** Rebuild can be performed incrementally (only new/changed documents)
**And** Rebuild can be performed in background (async)
**And** Rebuild progress is trackable
**And** Rebuild failures trigger alerts

#### Story 7.4: Backup Validation MCP Tool

As a **Platform Operator**,
I want **to validate backup integrity**,
So that **I can ensure backups are recoverable**.

**Acceptance Criteria:**

**Given** Backup validation is required
**When** I implement rag_validate_backup MCP tool
**Then** Tool accepts: backup_id, tenant_id, validation_type (integrity, completeness) (FR-BACKUP-005)
**And** Tool validates backup manifest exists and is valid
**And** Tool validates all backup files exist and are accessible
**And** Tool validates backup file integrity (checksums)
**And** Tool validates backup completeness (all required components present)
**And** Tool returns validation report with status and details
**And** Access is restricted to Uber Admin and Tenant Admin roles
**And** Validation completes within reasonable time

### Epic 8: Monitoring, Analytics & Operations

Platform operators and tenants can monitor system health, track usage, analyze performance, and manage operations effectively.

**FRs covered:** FR-MON-001, FR-MON-002, FR-MON-003, FR-MON-005, FR-MON-006

**Note:** Complete monitoring and analytics capability for operations

#### Story 8.1: Usage Statistics MCP Tool

As a **Platform Operator or Tenant Admin**,
I want **to retrieve usage statistics**,
So that **I can monitor system usage and plan capacity**.

**Acceptance Criteria:**

**Given** Usage statistics are required
**When** I implement rag_get_usage_stats MCP tool
**Then** Tool accepts: tenant_id, date_range, optional metrics_filter (FR-MON-001)
**And** Tool returns usage statistics: total_searches, total_memory_operations, total_document_operations, active_users, storage_usage
**And** Tool supports filtering by date_range
**And** Tool supports filtering by specific metrics
**And** Tool aggregates statistics from audit logs and system metrics
**And** Access is available to Uber Admin and Tenant Admin roles
**And** Response time is <200ms (p95)

**Given** Statistics aggregation is required
**When** I retrieve usage statistics
**Then** Statistics are aggregated from multiple sources (audit logs, system metrics)
**And** Statistics are cached for performance
**And** Statistics are updated in near real-time (within 5 minutes)

#### Story 8.2: Search Analytics MCP Tool

As a **Tenant Admin**,
I want **to analyze search performance and patterns**,
So that **I can optimize search quality and user experience**.

**Acceptance Criteria:**

**Given** Search analytics are required
**When** I implement rag_get_search_analytics MCP tool
**Then** Tool accepts: tenant_id, date_range, optional filters (FR-MON-002)
**And** Tool returns search analytics: total_searches, average_response_time, top_queries, zero_result_queries, search_trends
**And** Tool supports filtering by date_range
**And** Tool supports filtering by user_id, document_type, or other criteria
**And** Tool aggregates analytics from audit logs and search metrics
**And** Access is available to Uber Admin and Tenant Admin roles
**And** Response time is <200ms (p95)

**Given** Analytics visualization is required
**When** I retrieve search analytics
**Then** Analytics include trends over time
**And** Analytics include top queries and patterns
**And** Analytics include performance metrics (latency, accuracy)

#### Story 8.3: Memory Analytics MCP Tool

As a **Tenant Admin**,
I want **to analyze memory usage and patterns**,
So that **I can understand user engagement and memory effectiveness**.

**Acceptance Criteria:**

**Given** Memory analytics are required
**When** I implement rag_get_memory_analytics MCP tool
**Then** Tool accepts: tenant_id, date_range, optional filters (FR-MON-003)
**And** Tool returns memory analytics: total_memories, active_users, memory_usage_trends, top_memory_keys, memory_access_patterns
**And** Tool supports filtering by date_range
**And** Tool supports filtering by user_id or other criteria
**And** Tool aggregates analytics from audit logs and memory metrics
**And** Access is available to Uber Admin and Tenant Admin roles
**And** Response time is <200ms (p95)

#### Story 8.4: System Health Monitoring MCP Tool

As a **Platform Operator**,
I want **to monitor overall system health**,
So that **I can ensure system availability and performance**.

**Acceptance Criteria:**

**Given** System health monitoring is required
**When** I implement rag_get_system_health MCP tool
**Then** Tool returns system health status: overall_status, component_status (PostgreSQL, FAISS, Mem0, Redis, Meilisearch, MinIO), performance_metrics, error_rates (FR-MON-005)
**And** Tool aggregates health from all components
**And** Tool identifies degraded or unhealthy components
**And** Tool provides health summary and recommendations
**And** Access is restricted to Uber Admin role only
**And** Response time is <200ms (p95)

#### Story 8.5: Tenant Health Monitoring MCP Tool

As a **Tenant Admin**,
I want **to monitor my tenant's health**,
So that **I can ensure my tenant's operations are healthy**.

**Acceptance Criteria:**

**Given** Tenant health monitoring is required
**When** I implement rag_get_tenant_health MCP tool
**Then** Tool accepts: tenant_id (FR-MON-006)
**And** Tool returns tenant health status: tenant_status, component_status (tenant-specific), usage_metrics, error_rates, performance_metrics
**And** Tool aggregates health from tenant-specific components
**And** Tool identifies tenant-specific issues
**And** Tool provides health summary and recommendations
**And** Access is available to Uber Admin and Tenant Admin roles
**And** Response time is <200ms (p95)

### Epic 9: Advanced Compliance & Data Governance

System supports advanced compliance frameworks (HIPAA, SOC 2, GDPR) and enables comprehensive data governance operations including data export.

**FRs covered:** FR-COMP-001, FR-COMP-002, FR-COMP-003, FR-COMP-004, FR-DATA-003, FR-DATA-004, FR-TENANT-004, FR-TENANT-005, FR-TENANT-008, FR-AUTH-006, FR-RATE-002

**Note:** Advanced compliance and data governance features (mostly Phase 2)

#### Story 9.1: HIPAA Compliance Support

As a **Platform Operator**,
I want **HIPAA compliance support for healthcare tenants**,
So that **healthcare tenants can meet regulatory requirements**.

**Acceptance Criteria:**

**Given** HIPAA compliance is required
**When** I implement HIPAA compliance features
**Then** Patient data protection is enforced (encryption at rest and in transit) (FR-COMP-002)
**And** Minimum necessary access principle is enforced (role-based access controls)
**And** Comprehensive audit trails are maintained for all patient data access
**And** Data retention policies are configurable per tenant
**And** HIPAA-specific compliance flags are set in audit logs
**And** Compliance validation is performed during tenant onboarding
**And** Automated compliance validation checks run daily: encryption status, access control enforcement, audit log completeness, data retention policy compliance
**And** Compliance validation failures trigger alerts to Uber Admin and Tenant Admin
**And** Compliance validation reports are available via `rag_get_compliance_status` MCP tool (Phase 2)

**Given** HIPAA audit requirements are required
**When** I access patient data
**Then** All access is logged with HIPAA compliance flags
**And** Audit logs include: who, what, when, why for all patient data access
**And** Audit logs are tamper-proof and retained per HIPAA requirements

#### Story 9.2: SOC 2 Compliance Support

As a **Platform Operator**,
I want **SOC 2 compliance support**,
So that **the platform meets security and availability standards**.

**Acceptance Criteria:**

**Given** SOC 2 compliance is required
**When** I implement SOC 2 compliance features
**Then** Security controls are implemented and validated (FR-COMP-003)
**And** Availability monitoring is implemented
**And** Processing integrity is validated
**And** Confidentiality controls are enforced
**And** Privacy controls are implemented
**And** Compliance reporting is available
**And** Automated compliance validation checks run daily: security control effectiveness, availability metrics, processing integrity verification, confidentiality enforcement, privacy policy compliance
**And** Compliance validation failures trigger alerts to Uber Admin
**And** Compliance validation reports are available via `rag_get_compliance_status` MCP tool (Phase 2)

**Given** SOC 2 controls validation is required
**When** I validate SOC 2 controls
**Then** Security controls are tested and validated
**And** Availability metrics are tracked and reported
**And** Processing integrity is verified
**And** Compliance reports are generated

#### Story 9.3: GDPR Compliance Support

As a **Platform Operator**,
I want **GDPR compliance support**,
So that **EU tenants can meet data protection requirements**.

**Acceptance Criteria:**

**Given** GDPR compliance is required
**When** I implement GDPR compliance features
**Then** Data subject rights are supported (right to access, right to erasure, right to data portability) (FR-COMP-004)
**And** Data processing consent is tracked
**And** Data breach notification procedures are implemented
**And** Data protection impact assessments (DPIAs) are supported
**And** GDPR-specific compliance flags are set in audit logs
**And** Automated compliance validation checks run daily: data subject rights fulfillment, consent tracking completeness, breach notification readiness, DPIA requirements compliance
**And** Compliance validation failures trigger alerts to Uber Admin and Tenant Admin
**And** Compliance validation reports are available via `rag_get_compliance_status` MCP tool (Phase 2)

**Given** GDPR data export is required
**When** I export user data
**Then** All user data is exported in machine-readable format
**And** Export includes: documents, memories, audit logs, configuration
**And** Export is secure and authenticated

#### Story 9.4: Tenant Data Export MCP Tool

As a **Tenant Admin**,
I want **to export my tenant's data**,
So that **I can meet data portability requirements or migrate data**.

**Acceptance Criteria:**

**Given** Tenant data export is required
**When** I implement rag_export_tenant_data MCP tool
**Then** Tool accepts: tenant_id, export_format (JSON, CSV), optional filters (FR-DATA-003)
**And** Tool exports all tenant data: documents, memories, configurations, audit logs
**And** Tool exports data in specified format
**And** Tool supports filtering by date_range, data_type, or other criteria
**And** Tool creates export package with manifest
**And** Tool stores export in secure location with expiration
**And** Access is restricted to Uber Admin and Tenant Admin roles
**And** Export completes within reasonable time (depends on data size)

**Given** Export security is required
**When** I export tenant data
**Then** Export is authenticated and authorized
**And** Export is encrypted in transit
**And** Export access is logged for audit
**And** Export has expiration date for automatic cleanup

#### Story 9.5: User Data Export MCP Tool

As a **User**,
I want **to export my personal data**,
So that **I can exercise my data portability rights (GDPR)**.

**Acceptance Criteria:**

**Given** User data export is required
**When** I implement rag_export_user_data MCP tool
**Then** Tool accepts: user_id, tenant_id, export_format (JSON, CSV) (FR-DATA-004)
**And** Tool exports all user data: memories, session_context, audit_logs (user-specific)
**And** Tool exports data in specified format
**And** Tool creates export package with manifest
**And** Tool stores export in secure location with expiration
**And** Access is restricted to user's own data (or Tenant Admin for user management)
**And** Export completes within reasonable time

**Given** GDPR right to data portability is required
**When** I export user data
**Then** Export includes all user personal data
**And** Export is in machine-readable format
**And** Export is secure and authenticated

#### Story 9.6: Tenant Configuration Update MCP Tool

As a **Tenant Admin**,
I want **to update my tenant configuration**,
So that **I can adjust settings as my needs change**.

**Acceptance Criteria:**

**Given** Tenant configuration update is required
**When** I implement rag_update_tenant_config MCP tool
**Then** Tool accepts: tenant_id, configuration_updates (models, compliance, rate_limits, quotas) (FR-TENANT-004)
**And** Tool validates configuration updates
**And** Tool updates tenant configuration in tenant_config table
**And** Tool applies configuration changes to tenant operations
**And** Tool returns updated configuration
**And** Access is restricted to Tenant Admin role only
**And** Update completes within <200ms

**Given** Configuration validation is required
**When** I update tenant configuration
**Then** Configuration changes are validated
**And** Invalid configurations return structured error
**And** Configuration changes are logged for audit

#### Story 9.7: Tenant Deletion MCP Tool

As a **Platform Operator (Uber Admin)**,
I want **to delete tenants**,
So that **I can remove tenants that are no longer needed**.

**Acceptance Criteria:**

**Given** Tenant deletion is required
**When** I implement rag_delete_tenant MCP tool
**Then** Tool accepts: tenant_id, confirmation, delete_type (soft, hard) (FR-TENANT-005)
**And** Tool performs soft delete by default (mark as deleted, retain data for recovery period)
**And** Tool supports hard delete option (Uber Admin only, permanent deletion)
**And** Tool deletes tenant-scoped resources (FAISS index, MinIO bucket, Meilisearch index, Redis keys)
**And** Tool retains audit logs per compliance requirements
**And** Access is restricted to Uber Admin role only
**And** Deletion requires explicit confirmation

**Given** Deletion safety is required
**When** I delete a tenant
**Then** Current data is backed up before deletion (safety backup)
**Then** Soft delete allows recovery within recovery period (30 days default)
**And** Hard delete is irreversible and requires additional confirmation
**And** Deletion is logged for audit

#### Story 9.8: Subscription Tier Management

As a **Platform Operator (Uber Admin)**,
I want **to manage subscription tiers for tenants**,
So that **I can offer different service levels**.

**Acceptance Criteria:**

**Given** Subscription tier management is required
**When** I implement subscription tier management
**Then** System supports multiple tiers: Free, Basic, Enterprise (FR-TENANT-008)
**And** Each tier has different quotas: searches/month, storage, rate_limits
**And** Tier assignment is stored in tenant_config table
**And** Tier quotas are enforced by rate limiting and quota checking
**And** Tier upgrades/downgrades are supported
**And** Access is restricted to Uber Admin role only

**Given** Tier-based rate limiting is required
**When** I implement tier-based rate limiting
**Then** Rate limits vary by subscription tier (FR-RATE-002)
**And** Free tier has lower rate limits (e.g., 100 hits/minute)
**And** Basic tier has moderate rate limits (e.g., 500 hits/minute)
**And** Enterprise tier has higher rate limits (e.g., 1000 hits/minute)
**And** Rate limit enforcement uses tier configuration

#### Story 9.9: Project Admin Role Support

As a **Platform Operator**,
I want **Project Admin role for project-scoped access**,
So that **tenants can delegate project-level management**.

**Acceptance Criteria:**

**Given** Project Admin role is required
**When** I implement Project Admin role
**Then** Project Admin role is added to RBAC structure (FR-AUTH-006)
**And** Project Admin can manage knowledge bases for specific projects
**And** Project Admin can view project-level analytics
**And** Project Admin access is scoped to specific project_id
**And** Project Admin permissions are enforced in authorization middleware
**And** Project Admin role is available in Phase 2

**Given** Project-scoped access is required
**When** I access resources as Project Admin
**Then** Access is limited to resources within assigned projects
**And** Cross-project access is prevented
**And** Project assignments are stored and validated

---

## Admin UI Epics

### Epic 10: Admin UI Foundation & Authentication

**Goal**: Establish the foundational infrastructure for the Admin UI, including authentication, RBAC integration, base layout components, and REST proxy backend that connects the frontend to existing MCP tools.

**Business Value**: Enables secure, role-based access to the RAG platform administration interface, providing the foundation for all admin features.

**Scope**: 
- Frontend project setup (React/Next.js with TypeScript)
- REST proxy backend (FastAPI) for MCP tool integration
- OAuth 2.0 authentication integration
- RBAC middleware for role-based UI rendering
- Base layout components (sidebar, header, breadcrumbs)
- Session management and tenant context handling
- Error handling and loading states

**Success Criteria**:
- Users can authenticate via OAuth 2.0
- UI adapts based on user role (Uber Admin, Tenant Admin)
- REST proxy successfully calls existing MCP tools
- Base layout components are reusable and responsive
- Session and tenant context are properly managed

**Dependencies**: 
- Epic 1 (Secure Platform Foundation) - Authentication and RBAC backend
- Epic 2 (Tenant Onboarding) - Tenant management MCP tools

**Design Documents**:
- Admin UI Design Specification: `admin-ui-design-specification.md`
- Admin UI Complete UX Design: `admin-ui-complete-ux-design.md`
- User Journey Maps: `admin-ui-user-journey-maps.md`
- Wireframes: `admin-ui-wireframes.md`

**Technical Considerations**:
- Frontend: React 18+ with Next.js 14+, TypeScript, Material-UI or Tailwind CSS
- Backend: FastAPI REST proxy that translates HTTP requests to MCP tool calls
- State Management: React Context for role and tenant context
- Authentication: OAuth 2.0 with JWT tokens containing role claims
- Integration: REST proxy must call existing MCP tools (rag_*, mem0_*) with proper tenant_id

**Timeline**: Weeks 1-2 of MVP (8-week timeline)

#### Story 10.1: Frontend Project Setup & Base Structure

As a **Developer**,
I want **to set up the frontend project structure with React/Next.js and TypeScript**,
So that **I have a solid foundation for building the Admin UI**.

**Acceptance Criteria:**

**Given** I am starting Admin UI development
**When** I set up the frontend project
**Then** Project uses Next.js 14+ with App Router
**And** TypeScript is configured with strict mode
**And** Project structure includes: `app/`, `components/`, `lib/`, `types/`, `styles/`
**And** Material-UI or Tailwind CSS is installed and configured
**And** ESLint and Prettier are configured
**And** Project follows the design system from `admin-ui-complete-ux-design.md`
**And** Base layout structure is created (AppShell component)
**And** Project is ready for component development

**Given** Design system integration is required
**When** I set up the frontend project
**Then** Color palette from design system is configured (Primary Blue: #1976D2, etc.)
**And** Typography system is configured (Inter/Roboto fonts, size scale)
**And** Spacing scale is configured (4px grid system)
**And** Component library foundation is ready

**Design References**:
- Design System: `admin-ui-complete-ux-design.md` (Design System section)
- Base Layout Wireframe: `admin-ui-wireframes.md` (Base Layout section)

#### Story 10.2: REST Proxy Backend Setup & MCP Integration

As a **Developer**,
I want **to create a FastAPI REST proxy backend that integrates with existing MCP tools**,
So that **the frontend can interact with the RAG platform through HTTP APIs**.

**Acceptance Criteria:**

**Given** I am setting up the REST proxy backend
**When** I create the FastAPI application
**Then** FastAPI project structure includes: `app/`, `api/`, `services/`, `models/`, `middleware/`
**And** MCP client integration is implemented to call existing MCP tools
**And** REST API endpoints are created for: authentication, tenant operations, document operations, search operations
**And** Request/response models are defined using Pydantic
**And** Error handling middleware is implemented
**And** CORS is configured for frontend origin
**And** API documentation is generated (OpenAPI/Swagger)

**Given** MCP tool integration is required
**When** I implement REST endpoints
**Then** Endpoints translate HTTP requests to MCP tool calls
**And** tenant_id is extracted from session/context and passed to MCP tools
**And** Role validation is performed before MCP tool calls
**And** MCP tool responses are transformed to REST API responses
**And** Error responses from MCP tools are properly handled and returned

**Given** Existing MCP tools must be integrated
**When** I implement REST endpoints
**Then** Tenant management endpoints call: `rag_register_tenant`, `rag_list_templates`, `rag_get_template`, `rag_configure_tenant_models`
**And** Document management endpoints call: `rag_ingest`, `rag_list_documents`, `rag_get_document`, `rag_delete_document`
**And** Search endpoints call: `rag_search` (when implemented)
**And** Analytics endpoints call: `rag_get_usage_stats` (when implemented)
**And** All endpoints properly handle tenant_id and role validation

**Technical References**:
- Architecture Document: `architecture.md` (MCP Server Layer section)
- Existing MCP Tools: Epic 2, 3, 4 stories for tool specifications

#### Story 10.3: OAuth 2.0 Authentication Integration

As a **User**,
I want **to authenticate using OAuth 2.0**,
So that **I can securely access the Admin UI with my platform credentials**.

**Acceptance Criteria:**

**Given** I am implementing authentication
**When** I integrate OAuth 2.0
**Then** Frontend redirects to OAuth provider for authentication
**Then** OAuth callback handles authentication response
**And** JWT tokens are stored securely (httpOnly cookies or secure storage)
**And** Token refresh mechanism is implemented
**And** User role is extracted from token claims (uber_admin, tenant_admin, project_admin, end_user)
**And** User session is established with role context
**And** Unauthenticated users are redirected to login
**And** Token expiration is handled gracefully

**Given** Role-based access is required
**When** I authenticate
**Then** User role from token is stored in session context
**And** UI adapts based on role (Uber Admin vs Tenant Admin navigation)
**And** API requests include role information for backend validation
**And** Unauthorized access attempts are blocked

**Given** Backend integration is required
**When** I implement authentication
**Then** REST proxy validates JWT tokens
**And** Token claims (role, tenant_id) are extracted and used for authorization
**And** Invalid or expired tokens return 401 Unauthorized
**And** Authentication middleware is integrated with MCP tool calls

**Design References**:
- Login Page: Journey maps show login as first touchpoint
- Authentication Flow: `admin-ui-design-specification.md` (Authentication section)

#### Story 10.4: RBAC Middleware & Role-Based UI Rendering

As a **User**,
I want **the UI to adapt based on my role**,
So that **I only see features and data appropriate for my access level**.

**Acceptance Criteria:**

**Given** I am implementing RBAC
**When** I create RBAC middleware
**Then** Frontend has role context provider (React Context)
**And** Navigation components check role before rendering menu items
**And** Page components check role before rendering content
**And** API calls include role information in headers
**And** Backend validates role before processing requests
**And** Unauthorized actions show appropriate error messages

**Given** Role-based navigation is required
**When** I implement navigation
**Then** Uber Admin sees: Platform Dashboard, Tenant Management, Platform Analytics, Platform Settings, All Audit Logs
**And** Tenant Admin sees: Tenant Dashboard, Document Management, Configuration, Analytics, User Management, Audit Logs
**And** Navigation items are hidden/shown based on role
**And** Role indicator is displayed in header (e.g., "Uber Admin" badge)

**Given** Backend RBAC integration is required
**When** I implement RBAC
**Then** REST proxy validates role from JWT token
**And** MCP tool calls include role validation
**And** Role-based data filtering is applied (Uber Admin sees all tenants, Tenant Admin sees only their tenant)
**And** Unauthorized API calls return 403 Forbidden

**Design References**:
- Navigation Structure: `admin-ui-complete-ux-design.md` (Information Architecture section)
- Role Indicators: `admin-ui-complete-ux-design.md` (Design System - Role Indicators)

#### Story 10.5: Base Layout Components (Sidebar, Header, Breadcrumbs)

As a **User**,
I want **consistent navigation and layout across all Admin UI pages**,
So that **I can easily navigate and understand my current location**.

**Acceptance Criteria:**

**Given** I am implementing base layout
**When** I create layout components
**Then** AppShell component provides consistent page structure
**And** Sidebar navigation component is created with role-based menu items
**And** Header component shows: logo, user info, role indicator, tenant context switcher (Uber Admin), logout button
**And** Breadcrumbs component shows current page hierarchy
**And** Layout is responsive (mobile, tablet, desktop)
**And** Layout follows design system spacing and typography

**Given** Sidebar navigation is required
**When** I implement sidebar
**Then** Sidebar shows navigation items based on user role
**And** Active navigation item is highlighted
**And** Sidebar is collapsible on mobile
**And** Navigation items have icons and labels
**And** Navigation follows the structure from `admin-ui-complete-ux-design.md`

**Given** Header component is required
**When** I implement header
**Then** Header shows platform logo and name
**And** Header shows current user name and role
**And** Header shows tenant context switcher for Uber Admin (when in platform view)
**And** Header shows current tenant name when in tenant context
**And** Header shows logout button
**And** Header is sticky at top of page

**Given** Breadcrumbs are required
**When** I implement breadcrumbs
**Then** Breadcrumbs show: Home > Section > Page
**And** Breadcrumbs are clickable for navigation
**And** Breadcrumbs adapt based on current route
**And** Breadcrumbs follow design system styling

**Design References**:
- Base Layout Wireframe: `admin-ui-wireframes.md` (Base Layout section)
- Navigation Structure: `admin-ui-complete-ux-design.md` (Information Architecture section)
- Visual Mockups: `journey-mockups/alex-journey/01-platform-dashboard.png` (shows layout structure)

#### Story 10.6: Session Management & Tenant Context Handling

As a **Uber Admin**,
I want **to switch between platform view and tenant-specific views**,
So that **I can manage the platform and help individual tenants**.

**Acceptance Criteria:**

**Given** I am implementing session management
**When** I create session context
**Then** User session stores: user_id, role, tenant_id (for Tenant Admin), current_context (platform or tenant)
**And** Session persists across page refreshes
**And** Session is cleared on logout
**And** Session timeout is handled gracefully

**Given** Tenant context switching is required (Uber Admin)
**When** I implement context switching
**Then** Uber Admin can select a tenant from dropdown in header
**And** UI switches to Tenant Admin view for selected tenant
**And** Banner shows: "🔧 Uber Admin Mode - Viewing: [Tenant Name]"
**And** Navigation changes to Tenant Admin navigation
**And** All API calls use selected tenant_id
**And** "Exit to Platform View" button returns to platform view
**And** Context switch is persisted in session

**Given** Tenant context is required
**When** I implement tenant context
**Then** Tenant Admin always has tenant_id from authentication
**And** All API calls automatically include tenant_id
**And** Tenant context is displayed in header
**And** Cross-tenant access is prevented

**Design References**:
- Context Switcher: `journey-mockups/pat-journey/01-context-switcher.png`
- Tenant Context Banner: `admin-ui-user-journey-maps.md` (Pat's Journey - Stage 2)

#### Story 10.T: Admin UI Foundation Test Story

As a **QA Engineer**,
I want **to validate the Admin UI foundation**,
So that **I can ensure authentication, RBAC, and base layout work correctly**.

**Acceptance Criteria:**

**Given** Admin UI foundation is implemented
**When** I test the foundation
**Then** OAuth 2.0 authentication works for all user roles
**And** JWT tokens are properly validated
**And** Role-based navigation renders correctly for each role
**And** Base layout components are responsive and accessible
**And** Session management works correctly
**And** Tenant context switching works for Uber Admin
**And** REST proxy successfully calls MCP tools
**And** Error handling works for authentication failures
**And** Error handling works for authorization failures
**And** All components follow design system guidelines

---

### Epic 11: Tenant Admin Core Features

**Goal**: Implement core features for Tenant Admin users, including tenant dashboard, document management, configuration, analytics, and user management, enabling tenants to fully manage their RAG knowledge base.

**Business Value**: Empowers tenant administrators to independently manage their knowledge base, upload documents, configure settings, monitor usage, and manage users without requiring platform operator assistance.

**Scope**:
- Tenant Dashboard with overview metrics and quick actions
- Document Management (upload, list, view, delete, version history)
- Configuration (model settings, compliance profiles, rate limits)
- Analytics & Reporting (usage stats, search analytics, memory analytics)
- User Management (Project Admins, End Users, role assignments)

**Success Criteria**:
- Tenant Admin can view tenant dashboard with key metrics
- Tenant Admin can upload and manage documents
- Tenant Admin can configure tenant settings
- Tenant Admin can view analytics and reports
- Tenant Admin can manage users within tenant
- All features integrate with existing MCP tools

**Dependencies**: 
- Epic 10 (Admin UI Foundation) - Base infrastructure
- Epic 2 (Tenant Onboarding) - Tenant management MCP tools
- Epic 3 (Knowledge Base Management) - Document MCP tools
- Epic 4 (Search & Discovery) - Search MCP tools (for analytics)
- Epic 5 (Memory & Personalization) - Memory MCP tools (for analytics)

**Design Documents**:
- User Journey: Lisa Thompson (Tenant Admin) - `admin-ui-user-journey-maps.md`
- Visual Mockups: `journey-mockups/lisa-journey/` (5 mockups)
- Wireframes: `admin-ui-wireframes.md` (Tenant Admin sections)

**Technical Considerations**:
- All features must call existing MCP tools via REST proxy
- Document upload must support multi-modal (text, images, tables)
- Configuration changes must update tenant_config via MCP tools
- Analytics must aggregate data from multiple MCP tool responses
- User management must integrate with RBAC system

**Timeline**: Weeks 3-4 of MVP (8-week timeline)

#### Story 11.1: Tenant Dashboard Implementation

As a **Tenant Admin**,
I want **to view my tenant dashboard with overview metrics and quick actions**,
So that **I can quickly understand my tenant's health and take common actions**.

**Acceptance Criteria:**

**Given** I am implementing tenant dashboard
**When** I create the dashboard page
**Then** Dashboard shows: Health Status indicator (Healthy/Warning/Error)
**And** Dashboard shows: Total Documents count
**And** Dashboard shows: Recent Uploads count and list
**And** Dashboard shows: Quick Actions (Upload Document, View Analytics)
**And** Dashboard shows: Usage Statistics (searches, memory operations, storage)
**And** Dashboard shows: Recent Activity feed
**And** Dashboard data is fetched from MCP tools: `rag_get_usage_stats`, `rag_list_documents` (recent)
**And** Dashboard is responsive and follows design system

**Given** Health status is required
**When** I implement health status
**Then** Health status is determined from tenant health check (via MCP tool or REST endpoint)
**And** Health status shows appropriate color indicator (green/yellow/red)
**And** Health status includes brief status message
**And** Health status links to detailed health page (if available)

**Given** Quick actions are required
**When** I implement quick actions
**Then** "Upload Document" button navigates to document upload page
**And** "View Analytics" button navigates to analytics page
**And** Quick actions are prominently displayed
**And** Quick actions are contextual based on tenant state

**Design References**:
- Tenant Dashboard Mockup: `journey-mockups/lisa-journey/01-tenant-dashboard.png`
- Dashboard Wireframe: `admin-ui-wireframes.md` (Tenant Dashboard section)
- User Journey: `admin-ui-user-journey-maps.md` (Lisa's Journey - Stage 1)

#### Story 11.2: Document Management - Upload & List

As a **Tenant Admin**,
I want **to upload documents and view my document list**,
So that **I can manage my knowledge base content**.

**Acceptance Criteria:**

**Given** I am implementing document upload
**When** I create upload functionality
**Then** Upload page has drag-and-drop zone
**And** Upload page has "Browse Files" button
**And** Upload supports multiple file selection
**And** Upload shows file list with: name, size, type, validation status
**And** Upload validates file types (PDF, DOCX, TXT, images, etc.)
**And** Upload shows progress for each file (Uploading → Processing → Indexing → Complete)
**And** Upload calls MCP tool: `rag_ingest` with document_content, document_metadata, tenant_id
**And** Upload handles errors gracefully (file too large, invalid type, processing failure)
**And** Upload can be minimized to continue working while files process

**Given** I am implementing document list
**When** I create document list page
**Then** List shows table with columns: Name, Type, Date, Status, Actions
**And** List has search bar at top
**And** List has filter options (Type, Status, Date Range)
**And** List has pagination (50 per page)
**And** List calls MCP tool: `rag_list_documents` with tenant_id, filters, pagination
**And** List shows document status (Indexed, Processing, Error)
**And** List has actions: View, Update, Delete for each document
**And** List is responsive and follows design system

**Given** Document status is required
**When** I implement status display
**Then** Status shows: ✅ Indexed (green), ⏳ Processing (yellow), ❌ Error (red)
**And** Status includes tooltip with details
**And** Error status shows error message on hover/click

**Design References**:
- Document List Mockup: `journey-mockups/lisa-journey/02-document-list.png`
- Upload Dialog Mockup: `journey-mockups/lisa-journey/03-upload-dialog.png`
- Upload Progress Mockup: `journey-mockups/lisa-journey/05-upload-progress.png`
- User Journey: `admin-ui-user-journey-maps.md` (Lisa's Journey - Stages 2, 3)

#### Story 11.3: Document Management - Viewer & Actions

As a **Tenant Admin**,
I want **to view document details and perform actions (update, delete)**,
So that **I can manage individual documents in my knowledge base**.

**Acceptance Criteria:**

**Given** I am implementing document viewer
**When** I create document viewer page
**Then** Viewer shows document preview (PDF viewer, image viewer, text viewer)
**And** Viewer shows metadata panel: Name, Type, Size, Upload Date, Status
**And** Viewer shows version history (v1.0, v0.9, v0.8, etc.)
**And** Viewer has action buttons: Update, Delete, Download
**And** Viewer calls MCP tool: `rag_get_document` with document_id, tenant_id
**And** Viewer handles different document types appropriately
**And** Viewer is responsive and follows design system

**Given** I am implementing document update
**When** I create update functionality
**Then** Update button opens update dialog
**And** Update dialog allows selecting new file
**And** Update dialog has optional version notes field
**And** Update calls MCP tool: `rag_ingest` with document_id (for versioning)
**And** Update shows confirmation with new version number
**And** Update preserves previous versions (version history)
**And** Update shows progress (Processing → Indexing → Complete)

**Given** I am implementing document deletion
**When** I create delete functionality
**Then** Delete button shows confirmation dialog
**And** Delete confirmation shows document name and warning
**And** Delete calls MCP tool: `rag_delete_document` with document_id, tenant_id
**And** Delete shows success message
**And** Delete removes document from list
**And** Delete handles errors gracefully

**Design References**:
- Document Viewer Mockup: `journey-mockups/lisa-journey/04-document-viewer.png`
- User Journey: `admin-ui-user-journey-maps.md` (Lisa's Journey - Stage 4)

#### Story 11.4: Configuration Management

As a **Tenant Admin**,
I want **to configure my tenant settings (models, compliance, rate limits)**,
So that **I can customize my RAG system for my domain and requirements**.

**Acceptance Criteria:**

**Given** I am implementing configuration page
**When** I create configuration interface
**Then** Configuration page has tabs/sections: Model Settings, Compliance Profile, Rate Limits & Quotas
**And** Model Settings shows: Embedding Model dropdown, Domain selector, Model Parameters
**And** Compliance Profile shows: Compliance framework selector (HIPAA, PCI DSS, GDPR), compliance settings
**And** Rate Limits & Quotas shows: Rate limit settings, Storage quota, Usage quotas
**And** Configuration calls MCP tool: `rag_configure_tenant_models` for model settings
**And** Configuration calls MCP tool: `rag_update_tenant_config` for other settings (when available)
**And** Configuration shows current settings
**And** Configuration validates changes before saving
**And** Configuration shows save confirmation
**And** Configuration handles errors gracefully

**Given** Model settings are required
**When** I implement model configuration
**Then** Embedding Model dropdown shows available models (text-embedding-ada-002, text-embedding-3-large, etc.)
**And** Domain selector shows available domains (Healthcare, Fintech, Legal, etc.)
**And** Model Parameters section shows configurable parameters
**And** Model settings are saved via MCP tool
**And** Model changes trigger re-indexing notification (if applicable)

**Given** Compliance profile is required
**When** I implement compliance configuration
**Then** Compliance framework selector shows available frameworks
**And** Compliance settings are displayed based on selected framework
**And** Compliance settings are saved and applied
**And** Compliance status is displayed

**Design References**:
- Configuration Page Mockup: `journey-mockups/pat-journey/02-configuration.png`
- Configuration Wireframe: `admin-ui-wireframes.md` (Configuration section)
- User Journey: `admin-ui-user-journey-maps.md` (Lisa's Journey - Configuration use case)

#### Story 11.5: Analytics & Reporting

As a **Tenant Admin**,
I want **to view analytics and reports for my tenant**,
So that **I can understand usage patterns and optimize my knowledge base**.

**Acceptance Criteria:**

**Given** I am implementing analytics page
**When** I create analytics interface
**Then** Analytics page has tabs/sections: Usage Statistics, Search Analytics, Memory Analytics
**And** Usage Statistics shows: Total searches, Memory operations, Storage usage, Active users
**And** Search Analytics shows: Query performance chart, Top queries, Relevance scores, Error rate
**And** Memory Analytics shows: Memory operations over time, Memory usage by user
**And** Analytics calls MCP tool: `rag_get_usage_stats` for usage statistics
**And** Analytics calls MCP tool: `rag_get_search_analytics` for search analytics (when available)
**And** Analytics calls MCP tool: `rag_get_memory_analytics` for memory analytics (when available)
**And** Analytics shows charts and graphs (using charting library)
**And** Analytics has time range selector (Last 7 days, Last 30 days, Custom range)
**And** Analytics is responsive and follows design system

**Given** Charts and visualizations are required
**When** I implement analytics
**Then** Charts use appropriate chart types (line, bar, pie, etc.)
**And** Charts are interactive (hover for details, zoom, etc.)
**And** Charts follow design system colors
**And** Charts are accessible (ARIA labels, keyboard navigation)

**Design References**:
- Analytics Dashboard Mockup: `journey-mockups/pat-journey/03-analytics.png`
- Analytics Wireframe: `admin-ui-wireframes.md` (Analytics section)
- User Journey: `admin-ui-user-journey-maps.md` (Lisa's Journey - Analytics use case)

#### Story 11.6: User Management

As a **Tenant Admin**,
I want **to manage Project Admins and End Users within my tenant**,
So that **I can control access and delegate responsibilities**.

**Acceptance Criteria:**

**Given** I am implementing user management
**When** I create user management page
**Then** User management shows: List of users (Project Admins, End Users)
**And** User list shows: Name, Email, Role, Status, Actions
**And** User management has "Create User" button
**And** User management has search and filter options
**And** User management calls backend API (which may use MCP tools or direct database access)
**And** User management allows: Create user, Assign role, Deactivate user
**And** User management shows role assignments
**And** User management is responsive and follows design system

**Given** User creation is required
**When** I implement user creation
**Then** Create User dialog/form has: Name, Email, Role selector, Initial permissions
**And** User creation validates email format
**And** User creation assigns user to current tenant
**And** User creation sends invitation email (if applicable)
**And** User creation shows success confirmation

**Given** Role assignment is required
**When** I implement role management
**Then** Role selector shows available roles (Project Admin, End User)
**And** Role changes are saved
**And** Role changes are logged for audit
**And** Role changes take effect immediately

**Design References**:
- User Management Wireframe: `admin-ui-wireframes.md` (User Management section)
- User Journey: `admin-ui-user-journey-maps.md` (Lisa's Journey - User Management use case)

#### Story 11.T: Tenant Admin Core Features Test Story

As a **QA Engineer**,
I want **to validate Tenant Admin core features**,
So that **I can ensure all features work correctly and integrate with backend**.

**Acceptance Criteria:**

**Given** Tenant Admin features are implemented
**When** I test the features
**Then** Tenant dashboard displays correct metrics
**And** Document upload works for all supported file types
**And** Document list displays and filters correctly
**And** Document viewer displays documents correctly
**And** Document update creates new versions correctly
**And** Document deletion works correctly
**And** Configuration changes are saved and applied
**And** Analytics display correct data
**And** User management works correctly
**And** All features integrate with MCP tools correctly
**And** All features follow design system guidelines
**And** All features are responsive and accessible

---

### Epic 12: Uber Admin Core Features

**Goal**: Implement core features for Uber Admin users, including platform dashboard, tenant management, tenant context switcher, and platform analytics, enabling platform operators to manage the entire RAG infrastructure.

**Business Value**: Enables platform operators to efficiently onboard tenants, monitor platform health, manage all tenants, and provide support through tenant context switching, reducing operational overhead and improving tenant satisfaction.

**Scope**:
- Platform Dashboard with cross-tenant metrics and system health
- Tenant Management (list, create, view details, tenant creation wizard)
- Tenant Context Switcher (switch to tenant view, exit to platform view)
- Platform Analytics (cross-tenant metrics, system performance, usage trends)

**Success Criteria**:
- Uber Admin can view platform dashboard with cross-tenant metrics
- Uber Admin can create new tenants via wizard (<5 minutes)
- Uber Admin can view and manage all tenants
- Uber Admin can switch to tenant context to help tenants
- Uber Admin can view platform-wide analytics
- All features integrate with existing MCP tools

**Dependencies**: 
- Epic 10 (Admin UI Foundation) - Base infrastructure
- Epic 11 (Tenant Admin Core Features) - Tenant features (for context switching)
- Epic 2 (Tenant Onboarding) - Tenant management MCP tools

**Design Documents**:
- User Journey: Alex Chen (Uber Admin) - `admin-ui-user-journey-maps.md`
- Visual Mockups: `journey-mockups/alex-journey/` (5 mockups)
- Wireframes: `admin-ui-wireframes.md` (Uber Admin sections)

**Technical Considerations**:
- Platform dashboard must aggregate data from all tenants
- Tenant creation wizard must call multiple MCP tools in sequence
- Context switching must preserve Uber Admin permissions
- Platform analytics must aggregate cross-tenant data
- All features must respect Uber Admin role permissions

**Timeline**: Weeks 5-6 of MVP (8-week timeline)

#### Story 12.1: Platform Dashboard Implementation

As a **Uber Admin**,
I want **to view the platform dashboard with cross-tenant metrics and system health**,
So that **I can monitor the overall platform status and identify issues**.

**Acceptance Criteria:**

**Given** I am implementing platform dashboard
**When** I create the dashboard page
**Then** Dashboard shows: Total Tenants count
**And** Dashboard shows: Active Tenants count
**And** Dashboard shows: System Health status (Healthy/Warning/Error)
**And** Dashboard shows: Platform Metrics (total searches, total documents, total users)
**And** Dashboard shows: Tenant Health Grid (table/list of tenants with health status)
**And** Dashboard shows: Usage Trends chart (over time)
**And** Dashboard shows: Recent Activity feed (cross-tenant)
**And** Dashboard data is aggregated from all tenants (via MCP tools or direct queries)
**And** Dashboard is responsive and follows design system

**Given** Tenant health grid is required
**When** I implement health grid
**Then** Grid shows: Tenant Name, Domain, Health Status, Document Count, Last Activity
**And** Grid is sortable and filterable
**And** Grid links to tenant details page
**And** Grid shows health status indicators (green/yellow/red)
**And** Grid calls backend API to aggregate tenant data

**Given** System health is required
**When** I implement system health
**Then** System health aggregates health from all services (FAISS, Meilisearch, PostgreSQL, Redis, MinIO)
**And** System health shows overall status
**And** System health shows service-level status
**And** System health links to detailed health page

**Design References**:
- Platform Dashboard Mockup: `journey-mockups/alex-journey/01-platform-dashboard.png`
- Dashboard Wireframe: `admin-ui-wireframes.md` (Platform Dashboard section)
- User Journey: `admin-ui-user-journey-maps.md` (Alex's Journey - Stage 1)

#### Story 12.2: Tenant Management - List & Details

As a **Uber Admin**,
I want **to view and manage all tenants**,
So that **I can monitor tenant status and access tenant details**.

**Acceptance Criteria:**

**Given** I am implementing tenant list
**When** I create tenant list page
**Then** List shows table with columns: Tenant Name, Domain, Status, Health, Documents, Users, Actions
**And** List has search bar at top
**And** List has filter options (Domain, Status, Health)
**And** List has pagination
**And** List calls MCP tool or backend API to get all tenants
**And** List shows tenant status (Active, Inactive, Suspended)
**And** List has actions: View Details, Switch to Tenant View, Edit (if available)
**And** List is responsive and follows design system

**Given** I am implementing tenant details
**When** I create tenant details page
**Then** Details page shows: Tenant information (name, domain, contact info)
**And** Details page shows: Health status
**And** Details page shows: Configuration summary (models, compliance, rate limits)
**And** Details page shows: Quick stats (documents, users, usage)
**And** Details page shows: "Switch to Tenant View" button
**And** Details page calls MCP tools: `rag_get_template` (if template-based), tenant config queries
**And** Details page is responsive and follows design system

**Design References**:
- Tenant List Mockup: `journey-mockups/alex-journey/02-tenant-list.png`
- Tenant Details: Referenced in journey maps
- User Journey: `admin-ui-user-journey-maps.md` (Alex's Journey - Stage 2, 5)

#### Story 12.3: Tenant Creation Wizard

As a **Uber Admin**,
I want **to create new tenants via a multi-step wizard**,
So that **I can onboard tenants quickly (<5 minutes)**.

**Acceptance Criteria:**

**Given** I am implementing tenant creation wizard
**When** I create the wizard
**Then** Wizard has 4 steps: Basic Information, Template Selection, Initial Configuration, Review & Create
**And** Wizard shows progress indicator (Step X of 4)
**And** Wizard has Next/Back navigation
**And** Wizard validates each step before proceeding
**And** Wizard calls MCP tools: `rag_list_templates`, `rag_get_template`, `rag_register_tenant`, `rag_configure_tenant_models`
**And** Wizard shows success confirmation with tenant ID
**And** Wizard allows "View Tenant" or "Switch to Tenant View" after creation

**Given** Step 1: Basic Information is required
**When** I implement step 1
**Then** Step 1 form has: Tenant Name, Domain (dropdown), Contact Email, Contact Phone
**And** Step 1 validates required fields
**And** Step 1 validates email format
**And** Step 1 shows validation errors

**Given** Step 2: Template Selection is required
**When** I implement step 2
**Then** Step 2 shows template cards with preview
**And** Step 2 shows template details (compliance, models, settings)
**And** Step 2 has "Preview Template" button
**And** Step 2 calls MCP tool: `rag_list_templates` to get available templates
**And** Step 2 calls MCP tool: `rag_get_template` to get template details
**And** Step 2 allows selecting a template

**Given** Step 3: Initial Configuration is required
**When** I implement step 3
**Then** Step 3 shows pre-filled settings from selected template
**And** Step 3 allows adjusting settings (compliance, embedding model, rate limits, storage quota)
**And** Step 3 shows current selections
**And** Step 3 validates configuration

**Given** Step 4: Review & Create is required
**When** I implement step 4
**Then** Step 4 shows summary: Tenant name, domain, template, key settings, estimated setup time
**And** Step 4 has "Create Tenant" button
**And** Step 4 calls MCP tools in sequence: `rag_register_tenant`, `rag_configure_tenant_models`
**And** Step 4 shows creation progress (Creating tenant record → Provisioning FAISS index → Setting up Redis namespace → Configuring PostgreSQL schema → Applying compliance settings → Initializing models)
**And** Step 4 shows success message with tenant ID, status, setup time
**And** Step 4 provides actions: "View Tenant", "Switch to Tenant View"

**Design References**:
- Tenant Wizard Step 1 Mockup: `journey-mockups/alex-journey/03-tenant-wizard-step1.png`
- Tenant Progress Mockup: `journey-mockups/alex-journey/04-tenant-progress.png`
- Tenant Success Mockup: `journey-mockups/alex-journey/05-tenant-success.png`
- User Journey: `admin-ui-user-journey-maps.md` (Alex's Journey - Stage 3, 4)

#### Story 12.4: Tenant Context Switcher

As a **Uber Admin**,
I want **to switch to a tenant's view to help them**,
So that **I can see exactly what they see and assist with issues**.

**Acceptance Criteria:**

**Given** I am implementing context switcher
**When** I create context switcher component
**Then** Context switcher appears in header for Uber Admin
**Then** Context switcher is a dropdown/select component
**And** Context switcher shows list of all tenants (searchable)
**And** Context switcher allows selecting a tenant
**And** Context switcher triggers context switch when tenant is selected
**And** Context switch updates UI to Tenant Admin view
**And** Context switch shows banner: "🔧 Uber Admin Mode - Viewing: [Tenant Name]"
**And** Context switch updates navigation to Tenant Admin navigation
**And** Context switch updates all API calls to use selected tenant_id
**And** Context switch provides "Exit to Platform View" button
**And** Context switch is persisted in session

**Given** Context switch banner is required
**When** I implement banner
**Then** Banner is prominently displayed at top of page
**And** Banner shows Uber Admin mode indicator
**And** Banner shows current tenant name
**And** Banner has "Exit to Platform View" button
**And** Banner follows design system (yellow accent for context switch)

**Given** Context switch navigation is required
**When** I implement navigation update
**Then** Navigation changes from Platform navigation to Tenant Admin navigation
**And** Navigation shows all Tenant Admin menu items
**And** Navigation maintains Uber Admin permissions (can access all features)
**And** Navigation returns to Platform navigation when exiting context

**Design References**:
- Context Switcher Mockup: `journey-mockups/pat-journey/01-context-switcher.png`
- User Journey: `admin-ui-user-journey-maps.md` (Alex's Journey - Stage 5, Pat's Journey - Stage 2)

#### Story 12.5: Platform Analytics

As a **Uber Admin**,
I want **to view platform-wide analytics and metrics**,
So that **I can understand platform usage and performance trends**.

**Acceptance Criteria:**

**Given** I am implementing platform analytics
**When** I create analytics page
**Then** Analytics page has tabs/sections: Cross-Tenant Metrics, System Performance, Usage Trends
**And** Cross-Tenant Metrics shows: Total searches across all tenants, Total documents, Total users, Average tenant health
**And** System Performance shows: Service health metrics, Response times, Error rates, Throughput
**And** Usage Trends shows: Usage over time charts, Tenant growth, Feature adoption
**And** Analytics aggregates data from all tenants (via MCP tools or direct queries)
**And** Analytics has time range selector
**And** Analytics shows charts and graphs
**And** Analytics is responsive and follows design system

**Given** Cross-tenant aggregation is required
**When** I implement analytics
**Then** Analytics calls backend API to aggregate data from all tenants
**And** Analytics handles large datasets efficiently
**And** Analytics shows loading states during data fetch
**And** Analytics handles errors gracefully

**Design References**:
- Platform Analytics Wireframe: `admin-ui-wireframes.md` (Platform Analytics section)
- User Journey: `admin-ui-user-journey-maps.md` (Alex's Journey - Platform Analytics use case)

#### Story 12.T: Uber Admin Core Features Test Story

As a **QA Engineer**,
I want **to validate Uber Admin core features**,
So that **I can ensure all features work correctly and integrate with backend**.

**Acceptance Criteria:**

**Given** Uber Admin features are implemented
**When** I test the features
**Then** Platform dashboard displays correct cross-tenant metrics
**And** Tenant list displays and filters correctly
**And** Tenant creation wizard completes in <5 minutes
**And** Tenant creation wizard calls all MCP tools correctly
**And** Tenant context switcher works correctly
**And** Context switch shows correct tenant view
**And** Context switch allows exiting to platform view
**And** Platform analytics display correct aggregated data
**And** All features integrate with MCP tools correctly
**And** All features follow design system guidelines
**And** All features are responsive and accessible
