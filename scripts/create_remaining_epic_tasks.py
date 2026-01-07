#!/usr/bin/env python3
"""
Create tasks for remaining epics (7, 8, 9) in OpenProject.

Epic 7: Data Protection & Disaster Recovery
Epic 8: Monitoring, Analytics & Operations
Epic 9: Advanced Compliance & Data Governance
"""

import json
from typing import List, Dict, Any

# Project ID
PROJECT_ID = 8

# Work Package Type IDs
TASK_TYPE_ID = 36

# Status IDs
STATUS_NEW = 71
STATUS_CLOSED = 82

# Priority IDs
PRIORITY_NORMAL = 73
PRIORITY_HIGH = 74

# Story IDs from OpenProject
STORY_7_1_ID = 150  # Story 7.1: Tenant Backup MCP Tool
STORY_7_2_ID = 151  # Story 7.2: Tenant Restore MCP Tool
STORY_7_3_ID = 152  # Story 7.3: FAISS Index Rebuild MCP Tool
STORY_7_4_ID = 153  # Story 7.4: Backup Validation MCP Tool

STORY_8_1_ID = 155  # Story 8.1: Usage Statistics MCP Tool
STORY_8_2_ID = 156  # Story 8.2: Search Analytics MCP Tool
STORY_8_3_ID = 157  # Story 8.3: Memory Analytics MCP Tool
STORY_8_4_ID = 158  # Story 8.4: System Health Monitoring MCP Tool
STORY_8_5_ID = 159  # Story 8.5: Tenant Health Monitoring MCP Tool

STORY_9_1_ID = 161  # Story 9.1: HIPAA Compliance Support
STORY_9_2_ID = 162  # Story 9.2: SOC 2 Compliance Support
STORY_9_3_ID = 163  # Story 9.3: GDPR Compliance Support
STORY_9_4_ID = 164  # Story 9.4: Tenant Data Export MCP Tool
STORY_9_5_ID = 165  # Story 9.5: User Data Export MCP Tool
STORY_9_6_ID = 166  # Story 9.6: Tenant Configuration Update MCP Tool
STORY_9_7_ID = 167  # Story 9.7: Tenant Deletion MCP Tool
STORY_9_8_ID = 168  # Story 9.8: Subscription Tier Management
STORY_9_9_ID = 169  # Story 9.9: Project Admin Role Support


def create_epic7_tasks() -> List[Dict[str, Any]]:
    """Create tasks for Epic 7 stories."""
    # Story 7.1: Tenant Backup MCP Tool (150)
    story_7_1_tasks = [
        {
            "subject": "Task 7.1.1: Create rag_backup_tenant_data MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Implement rag_backup_tenant_data MCP tool that accepts tenant_id, backup_type (full, incremental), and optional backup_location.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.2: Implement PostgreSQL data backup",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Back up PostgreSQL data (tenant-scoped tables) to backup infrastructure.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.3: Implement FAISS index backup",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Back up FAISS index (tenant-scoped) to backup infrastructure.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.4: Implement MinIO objects backup",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Back up MinIO objects (tenant-scoped bucket) to backup infrastructure.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.5: Implement Meilisearch index backup",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Back up Meilisearch index (tenant-scoped) to backup infrastructure.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.6: Create backup manifest with metadata",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Create backup manifest with metadata (timestamp, tenant_id, backup_type, file_list).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.7: Implement backup progress tracking",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Implement backup progress tracking (percentage complete, estimated time remaining).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.8: Implement backup validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Validate backup integrity, verify manifest, log status, and trigger alerts on failures.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.9: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.10: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Write comprehensive unit tests for rag_backup_tenant_data including authorization, backup operations, validation, and progress tracking.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.1.11: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_1_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 7.2: Tenant Restore MCP Tool (151)
    story_7_2_tasks = [
        {
            "subject": "Task 7.2.1: Create rag_restore_tenant_data MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Implement rag_restore_tenant_data MCP tool that accepts tenant_id, backup_id, restore_type (full, partial), and confirmation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.2: Implement backup validation before restore",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Validate backup exists and is valid before starting restore operation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.3: Implement safety backup before restore",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Create safety backup of current data before restore operation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.4: Implement PostgreSQL data restore",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Restore PostgreSQL data (tenant-scoped tables) from backup.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.5: Implement FAISS index restore",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Restore FAISS index (tenant-scoped) from backup.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.6: Implement MinIO objects restore",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Restore MinIO objects (tenant-scoped bucket) from backup.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.7: Implement Meilisearch index restore",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Restore Meilisearch index (tenant-scoped) from backup.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.8: Implement restore integrity validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Validate restore integrity after restore operation completes.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.9: Implement restore progress tracking",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Implement restore progress tracking (percentage complete, estimated time remaining).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.10: Add RBAC (Uber Admin only)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Restrict access to Uber Admin role only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.11: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Write comprehensive unit tests for rag_restore_tenant_data including authorization, restore operations, validation, and progress tracking.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.2.12: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_2_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 7.3: FAISS Index Rebuild MCP Tool (152)
    story_7_3_tasks = [
        {
            "subject": "Task 7.3.1: Create rag_rebuild_index MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Implement rag_rebuild_index MCP tool that accepts tenant_id, index_type (FAISS), and rebuild_type (full, incremental).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.2: Implement document retrieval for rebuild",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Retrieve all documents for tenant from PostgreSQL for index rebuild.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.3: Implement embedding regeneration",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Regenerate embeddings for all documents using tenant-configured embedding model.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.4: Implement FAISS index rebuild",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Rebuild FAISS index with new embeddings for tenant.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.5: Implement index integrity validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Validate index integrity after rebuild operation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.6: Implement incremental rebuild support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Support incremental rebuild (only new/changed documents) in addition to full rebuild.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.7: Implement background rebuild support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Support background (async) rebuild operations for large indices.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.8: Implement rebuild progress tracking",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Implement rebuild progress tracking and alerting on failures.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.9: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.10: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Write comprehensive unit tests for rag_rebuild_index including authorization, rebuild operations, validation, and progress tracking.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.3.11: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_3_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 7.4: Backup Validation MCP Tool (153)
    story_7_4_tasks = [
        {
            "subject": "Task 7.4.1: Create rag_validate_backup MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Implement rag_validate_backup MCP tool that accepts backup_id, tenant_id, and validation_type (integrity, completeness).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.2: Implement backup manifest validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Validate backup manifest exists and is valid.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.3: Implement backup file existence validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Validate all backup files exist and are accessible.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.4: Implement backup file integrity validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Validate backup file integrity using checksums.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.5: Implement backup completeness validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Validate backup completeness (all required components present).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.6: Generate validation report",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Return validation report with status and details.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.7: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Write comprehensive unit tests for rag_validate_backup including authorization, validation operations, and report generation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 7.4.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_7_4_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    return story_7_1_tasks + story_7_2_tasks + story_7_3_tasks + story_7_4_tasks


def create_epic8_tasks() -> List[Dict[str, Any]]:
    """Create tasks for Epic 8 stories."""
    # Story 8.1: Usage Statistics MCP Tool (155)
    story_8_1_tasks = [
        {
            "subject": "Task 8.1.1: Create rag_get_usage_stats MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Implement rag_get_usage_stats MCP tool that accepts tenant_id, date_range, and optional metrics_filter.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.2: Implement statistics aggregation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Aggregate usage statistics from audit logs and system metrics: total_searches, total_memory_operations, total_document_operations, active_users, storage_usage.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.3: Implement date range filtering",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Support filtering by date_range and specific metrics.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.4: Implement statistics caching",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Cache statistics for performance and update in near real-time (within 5 minutes).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.5: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.6: Ensure response time <200ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Optimize statistics retrieval to complete within <200ms (p95).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Write comprehensive unit tests for rag_get_usage_stats including authorization, aggregation, filtering, caching, and performance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.1.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_1_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 8.2: Search Analytics MCP Tool (156)
    story_8_2_tasks = [
        {
            "subject": "Task 8.2.1: Create rag_get_search_analytics MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Implement rag_get_search_analytics MCP tool that accepts tenant_id, date_range, and optional filters.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.2: Implement search analytics aggregation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Aggregate search analytics from audit logs and search metrics: total_searches, average_response_time, top_queries, zero_result_queries, search_trends.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.3: Implement filtering support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Support filtering by date_range, user_id, document_type, or other criteria.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.4: Implement trends and patterns analysis",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Include trends over time, top queries and patterns, and performance metrics (latency, accuracy).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.5: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.6: Ensure response time <200ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Optimize analytics retrieval to complete within <200ms (p95).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Write comprehensive unit tests for rag_get_search_analytics including authorization, aggregation, filtering, and performance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.2.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_2_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 8.3: Memory Analytics MCP Tool (157)
    story_8_3_tasks = [
        {
            "subject": "Task 8.3.1: Create rag_get_memory_analytics MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Implement rag_get_memory_analytics MCP tool that accepts tenant_id, date_range, and optional filters.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.3.2: Implement memory analytics aggregation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Aggregate memory analytics from audit logs and memory metrics: total_memories, active_users, memory_usage_trends, top_memory_keys, memory_access_patterns.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.3.3: Implement filtering support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Support filtering by date_range, user_id, or other criteria.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.3.4: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.3.5: Ensure response time <200ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Optimize analytics retrieval to complete within <200ms (p95).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.3.6: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Write comprehensive unit tests for rag_get_memory_analytics including authorization, aggregation, filtering, and performance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.3.7: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_3_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 8.4: System Health Monitoring MCP Tool (158)
    story_8_4_tasks = [
        {
            "subject": "Task 8.4.1: Create rag_get_system_health MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Implement rag_get_system_health MCP tool that returns system health status.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.2: Implement component health checks",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Check health of all components: PostgreSQL, FAISS, Mem0, Redis, Meilisearch, MinIO.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.3: Implement health aggregation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Aggregate health from all components and identify degraded or unhealthy components.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.4: Implement performance metrics collection",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Collect performance_metrics and error_rates for system health assessment.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.5: Generate health summary and recommendations",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Provide health summary and recommendations based on component status.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.6: Add RBAC (Uber Admin only)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Restrict access to Uber Admin role only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.7: Ensure response time <200ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Optimize health check to complete within <200ms (p95).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Write comprehensive unit tests for rag_get_system_health including authorization, health checks, aggregation, and performance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.4.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_4_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 8.5: Tenant Health Monitoring MCP Tool (159)
    story_8_5_tasks = [
        {
            "subject": "Task 8.5.1: Create rag_get_tenant_health MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Implement rag_get_tenant_health MCP tool that accepts tenant_id and returns tenant health status.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.2: Implement tenant-specific component health checks",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Check health of tenant-specific components (tenant-scoped FAISS index, MinIO bucket, Meilisearch index, etc.).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.3: Implement tenant health aggregation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Aggregate health from tenant-specific components and identify tenant-specific issues.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.4: Implement tenant usage and performance metrics",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Collect usage_metrics, error_rates, and performance_metrics for tenant health assessment.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.5: Generate tenant health summary and recommendations",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Provide tenant health summary and recommendations based on tenant-specific component status.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.6: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.7: Ensure response time <200ms (p95)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Optimize tenant health check to complete within <200ms (p95).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Write comprehensive unit tests for rag_get_tenant_health including authorization, health checks, aggregation, and performance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 8.5.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_8_5_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    return story_8_1_tasks + story_8_2_tasks + story_8_3_tasks + story_8_4_tasks + story_8_5_tasks


def create_epic9_tasks() -> List[Dict[str, Any]]:
    """Create tasks for Epic 9 stories."""
    # Story 9.1: HIPAA Compliance Support (161)
    story_9_1_tasks = [
        {
            "subject": "Task 9.1.1: Implement patient data protection",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Enforce encryption at rest and in transit for patient data (FR-COMP-002).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.2: Implement minimum necessary access principle",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Enforce minimum necessary access principle using role-based access controls.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.3: Implement comprehensive audit trails",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Maintain comprehensive audit trails for all patient data access with HIPAA compliance flags.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.4: Implement configurable data retention policies",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Support configurable data retention policies per tenant.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.5: Implement compliance validation during onboarding",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Perform compliance validation during tenant onboarding for healthcare tenants.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.6: Implement automated compliance validation checks",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Run daily automated compliance validation checks: encryption status, access control enforcement, audit log completeness, data retention policy compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.7: Implement compliance alerting",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Trigger alerts to Uber Admin and Tenant Admin on compliance validation failures.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Write comprehensive unit tests for HIPAA compliance features including data protection, access controls, audit trails, and validation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.1.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_1_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.2: SOC 2 Compliance Support (162)
    story_9_2_tasks = [
        {
            "subject": "Task 9.2.1: Implement security controls",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Implement and validate security controls for SOC 2 compliance (FR-COMP-003).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.2: Implement availability monitoring",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Implement availability monitoring and reporting.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.3: Implement processing integrity validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Validate processing integrity for SOC 2 compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.4: Implement confidentiality controls",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Enforce confidentiality controls for SOC 2 compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.5: Implement privacy controls",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Implement privacy controls for SOC 2 compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.6: Implement compliance reporting",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Provide compliance reporting capabilities for SOC 2.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.7: Implement automated compliance validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Run daily automated compliance validation checks: security control effectiveness, availability metrics, processing integrity verification, confidentiality enforcement, privacy policy compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.8: Implement compliance alerting",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Trigger alerts to Uber Admin on compliance validation failures.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.9: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Write comprehensive unit tests for SOC 2 compliance features including security controls, availability monitoring, and validation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.2.10: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_2_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.3: GDPR Compliance Support (163)
    story_9_3_tasks = [
        {
            "subject": "Task 9.3.1: Implement data subject rights support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Support data subject rights: right to access, right to erasure, right to data portability (FR-COMP-004).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.2: Implement data processing consent tracking",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Track data processing consent for GDPR compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.3: Implement data breach notification procedures",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Implement data breach notification procedures for GDPR compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.4: Implement DPIA support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Support Data Protection Impact Assessments (DPIAs) for GDPR compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.5: Implement GDPR compliance flags",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Set GDPR-specific compliance flags in audit logs.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.6: Implement automated compliance validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Run daily automated compliance validation checks: data subject rights fulfillment, consent tracking completeness, breach notification readiness, DPIA requirements compliance.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.7: Implement compliance alerting",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Trigger alerts to Uber Admin and Tenant Admin on compliance validation failures.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Write comprehensive unit tests for GDPR compliance features including data subject rights, consent tracking, and validation.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.3.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_3_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.4: Tenant Data Export MCP Tool (164)
    story_9_4_tasks = [
        {
            "subject": "Task 9.4.1: Create rag_export_tenant_data MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Implement rag_export_tenant_data MCP tool that accepts tenant_id, export_format (JSON, CSV), and optional filters (FR-DATA-003).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.2: Implement tenant data export",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Export all tenant data: documents, memories, configurations, audit logs.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.3: Implement export format support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Support export in specified format (JSON, CSV).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.4: Implement filtering support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Support filtering by date_range, data_type, or other criteria.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.5: Create export package with manifest",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Create export package with manifest for data portability.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.6: Implement secure export storage",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Store export in secure location with expiration for automatic cleanup.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.7: Add RBAC (Uber Admin and Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Restrict access to Uber Admin and Tenant Admin roles only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.8: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Write comprehensive unit tests for rag_export_tenant_data including authorization, export operations, filtering, and security.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.4.9: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_4_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.5: User Data Export MCP Tool (165)
    story_9_5_tasks = [
        {
            "subject": "Task 9.5.1: Create rag_export_user_data MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Implement rag_export_user_data MCP tool that accepts user_id, tenant_id, and export_format (JSON, CSV) (FR-DATA-004).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.2: Implement user data export",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Export all user data: memories, session_context, audit_logs (user-specific).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.3: Implement export format support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Support export in specified format (JSON, CSV) in machine-readable format.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.4: Create export package with manifest",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Create export package with manifest for GDPR right to data portability.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.5: Implement secure export storage",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Store export in secure location with expiration for automatic cleanup.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.6: Add RBAC (user's own data or Tenant Admin)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Restrict access to user's own data (or Tenant Admin for user management).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Write comprehensive unit tests for rag_export_user_data including authorization, export operations, and security.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.5.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_5_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.6: Tenant Configuration Update MCP Tool (166)
    story_9_6_tasks = [
        {
            "subject": "Task 9.6.1: Create rag_update_tenant_config MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Implement rag_update_tenant_config MCP tool that accepts tenant_id and configuration_updates (models, compliance, rate_limits, quotas) (FR-TENANT-004).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.2: Implement configuration validation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Validate configuration updates before applying changes.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.3: Implement configuration update",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Update tenant configuration in tenant_config table and apply changes to tenant operations.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.4: Implement configuration change logging",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Log configuration changes for audit purposes.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.5: Add RBAC (Tenant Admin only)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Restrict access to Tenant Admin role only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.6: Ensure response time <200ms",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Optimize configuration update to complete within <200ms.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Write comprehensive unit tests for rag_update_tenant_config including authorization, validation, and update operations.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.6.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_6_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.7: Tenant Deletion MCP Tool (167)
    story_9_7_tasks = [
        {
            "subject": "Task 9.7.1: Create rag_delete_tenant MCP tool",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Implement rag_delete_tenant MCP tool that accepts tenant_id, confirmation, and delete_type (soft, hard) (FR-TENANT-005).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.2: Implement soft delete (default)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Perform soft delete by default (mark as deleted, retain data for recovery period).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.3: Implement hard delete option",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Support hard delete option (Uber Admin only, permanent deletion).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.4: Implement safety backup before deletion",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Create safety backup of current data before deletion.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.5: Implement tenant resource deletion",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Delete tenant-scoped resources (FAISS index, MinIO bucket, Meilisearch index, Redis keys).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.6: Implement audit log retention",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Retain audit logs per compliance requirements even after tenant deletion.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.7: Implement soft delete recovery",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Allow recovery within recovery period (30 days default) for soft-deleted tenants.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.8: Add RBAC (Uber Admin only)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Restrict access to Uber Admin role only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.9: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Write comprehensive unit tests for rag_delete_tenant including authorization, soft/hard delete, resource deletion, and recovery.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.7.10: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_7_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.8: Subscription Tier Management (168)
    story_9_8_tasks = [
        {
            "subject": "Task 9.8.1: Define subscription tier structure",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Define subscription tier structure: Free, Basic, Enterprise with different quotas (FR-TENANT-008).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.2: Implement tier storage in tenant_config",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Store tier assignment in tenant_config table.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.3: Implement tier quota enforcement",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Enforce tier quotas by rate limiting and quota checking.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.4: Implement tier upgrade/downgrade support",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Support tier upgrades and downgrades with quota adjustments.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.5: Implement tier-based rate limiting",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Implement tier-based rate limiting: Free (100 hits/minute), Basic (500 hits/minute), Enterprise (1000 hits/minute) (FR-RATE-002).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.6: Add RBAC (Uber Admin only)",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Restrict access to Uber Admin role only.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Write comprehensive unit tests for subscription tier management including tier assignment, quota enforcement, and rate limiting.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.8.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_8_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    # Story 9.9: Project Admin Role Support (169)
    story_9_9_tasks = [
        {
            "subject": "Task 9.9.1: Add Project Admin role to RBAC structure",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Add Project Admin role to RBAC structure (FR-AUTH-006).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.2: Implement project-scoped access",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Implement project-scoped access for Project Admin role (manage knowledge bases for specific projects).",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.3: Implement project-level analytics access",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Enable Project Admin to view project-level analytics.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.4: Implement project assignment storage",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Store and validate project assignments for Project Admin role.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.5: Implement project-scoped permission enforcement",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Enforce Project Admin permissions in authorization middleware with project_id scope.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.6: Prevent cross-project access",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Ensure Project Admin access is limited to resources within assigned projects and prevent cross-project access.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.7: Write unit tests",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Write comprehensive unit tests for Project Admin role including project-scoped access, permission enforcement, and cross-project access prevention.",
            "status_id": STATUS_NEW,
        },
        {
            "subject": "Task 9.9.8: Create verification documentation",
            "type_id": TASK_TYPE_ID,
            "parent_id": STORY_9_9_ID,
            "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
            "status_id": STATUS_NEW,
        },
    ]
    
    return story_9_1_tasks + story_9_2_tasks + story_9_3_tasks + story_9_4_tasks + story_9_5_tasks + story_9_6_tasks + story_9_7_tasks + story_9_8_tasks + story_9_9_tasks


def main():
    """Main execution function."""
    print("=" * 80)
    print("Creating Tasks for Epic 7, 8, and 9")
    print("=" * 80)
    
    all_tasks = []
    
    # Epic 7 tasks
    epic7_tasks = create_epic7_tasks()
    all_tasks.extend(epic7_tasks)
    print(f"\nEpic 7 tasks: {len(epic7_tasks)}")
    
    # Epic 8 tasks
    epic8_tasks = create_epic8_tasks()
    all_tasks.extend(epic8_tasks)
    print(f"Epic 8 tasks: {len(epic8_tasks)}")
    
    # Epic 9 tasks
    epic9_tasks = create_epic9_tasks()
    all_tasks.extend(epic9_tasks)
    print(f"Epic 9 tasks: {len(epic9_tasks)}")
    
    print(f"\nTotal tasks to create: {len(all_tasks)}")
    
    # Remove status_id from all tasks (not accepted during creation)
    for task in all_tasks:
        task.pop("status_id", None)
    
    # Split into batches of 20
    batches = []
    for i in range(0, len(all_tasks), 20):
        batches.append(all_tasks[i:i+20])
    
    print(f"Number of batches: {len(batches)}")
    
    # Save batches to files
    for i, batch in enumerate(batches, 1):
        with open(f"/tmp/epic789_batch_{i}.json", "w") as f:
            json.dump(batch, f, indent=2)
        print(f"Batch {i} saved to /tmp/epic789_batch_{i}.json ({len(batch)} tasks)")
    
    print("\n" + "=" * 80)
    print("Task definitions ready. Use MCP tools to create them in OpenProject.")
    print("=" * 80)
    
    return all_tasks


if __name__ == "__main__":
    main()




