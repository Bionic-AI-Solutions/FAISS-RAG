# Epic 8: Monitoring, Analytics & Operations - Test Plan

**Epic ID:** 154  
**Status:** In Progress  
**Test Plan Date:** 2026-01-08

## Overview

This test plan validates the complete Epic 8 functionality including all monitoring, analytics, and operational capabilities. All tests use real services (no mocks) and follow the integration test pattern established in previous epics.

## Test Scope

### Stories Covered
- **Story 8.1:** Usage Statistics MCP Tool
- **Story 8.2:** Search Analytics MCP Tool
- **Story 8.3:** Memory Analytics MCP Tool
- **Story 8.4:** System Health Monitoring MCP Tool
- **Story 8.5:** Tenant Health Monitoring MCP Tool

### Test Categories
1. **Integration Tests:** End-to-end workflows using real services
2. **Performance Tests:** Response time validation (<200ms p95)
3. **Security Tests:** RBAC enforcement
4. **Reliability Tests:** Caching and aggregation accuracy
5. **Audit Tests:** Audit logging validation

## Test Environment

### Prerequisites
- All services running (PostgreSQL, Redis, MinIO, Meilisearch, FAISS, Mem0)
- Test tenant registered and configured
- Test documents ingested for analytics scenarios
- Test memory operations performed for memory analytics
- Test search operations performed for search analytics

### Test Data Setup
- **Tenant:** Registered test tenant with UUID
- **Documents:** Multiple documents ingested (text, PDF, etc.)
- **Memory Operations:** User memories created, updated, searched
- **Search Operations:** Multiple search queries executed
- **Audit Logs:** Sufficient audit log data for analytics aggregation

## Test Scenarios

### Scenario 1: Usage Statistics Retrieval

**Objective:** Validate usage statistics aggregation and accuracy

**Test Steps:**
1. Register test tenant
2. Perform multiple search operations
3. Perform multiple memory operations
4. Perform multiple document operations
5. Execute `rag_get_usage_stats` with tenant_id
6. Verify statistics accuracy (total_searches, total_memory_operations, total_document_operations, active_users, storage_usage)
7. Verify date range filtering
8. Verify metrics filtering
9. Verify caching (5-minute TTL)

**Expected Results:**
- Statistics retrieved successfully
- Statistics are accurate and match actual operations
- Date range filtering works correctly
- Metrics filtering works correctly
- Caching improves performance (<200ms p95)
- Statistics updated in near real-time (within 5 minutes)

**Performance Targets:**
- Response time: <200ms (p95)
- Cache hit: <50ms
- Cache miss: <200ms

---

### Scenario 2: Search Analytics Aggregation

**Objective:** Validate search analytics aggregation and filtering

**Test Steps:**
1. Perform multiple search operations with different queries
2. Perform searches with different document types
3. Perform searches by different users
4. Execute `rag_get_search_analytics` with tenant_id
5. Verify analytics accuracy (total_searches, average_response_time, top_queries, zero_result_queries, search_trends)
6. Verify date range filtering
7. Verify user_id filtering
8. Verify document_type filtering
9. Verify caching

**Expected Results:**
- Analytics retrieved successfully
- Analytics are accurate and match actual searches
- Filtering works correctly (date_range, user_id, document_type)
- Top queries identified correctly
- Zero-result queries identified correctly
- Search trends calculated correctly
- Caching improves performance (<200ms p95)

**Performance Targets:**
- Response time: <200ms (p95)
- Cache hit: <50ms
- Cache miss: <200ms

---

### Scenario 3: Memory Analytics Aggregation

**Objective:** Validate memory analytics aggregation and filtering

**Test Steps:**
1. Perform multiple memory operations (create, update, search)
2. Perform memory operations by different users
3. Execute `rag_get_memory_analytics` with tenant_id
4. Verify analytics accuracy (total_memories, active_users, memory_usage_trends, top_memory_keys, memory_access_patterns)
5. Verify date range filtering
6. Verify user_id filtering
7. Verify caching

**Expected Results:**
- Analytics retrieved successfully
- Analytics are accurate and match actual memory operations
- Filtering works correctly (date_range, user_id)
- Memory usage trends calculated correctly
- Top memory keys identified correctly
- Memory access patterns identified correctly
- Caching improves performance (<200ms p95)

**Performance Targets:**
- Response time: <200ms (p95)
- Cache hit: <50ms
- Cache miss: <200ms

---

### Scenario 4: System Health Monitoring

**Objective:** Validate system health monitoring for all components

**Test Steps:**
1. Execute `rag_get_system_health`
2. Verify component health checks (PostgreSQL, Redis, MinIO, Meilisearch, Mem0, Langfuse, FAISS)
3. Verify health aggregation (overall_status)
4. Verify performance metrics collection (average_response_time, p95_response_time, p99_response_time, total_requests, requests_per_second)
5. Verify error rates calculation (total_requests, successful_requests, failed_requests, error_rate_percent, errors_by_type)
6. Verify health summary and recommendations
7. Verify degraded/unhealthy component identification
8. Verify caching (30-second TTL for near real-time)

**Expected Results:**
- System health retrieved successfully
- All component health checks performed
- Overall status calculated correctly (healthy, degraded, unhealthy)
- Performance metrics accurate
- Error rates calculated correctly
- Health summary provides actionable insights
- Degraded/unhealthy components identified correctly
- Caching improves performance (<200ms p95)

**Performance Targets:**
- Response time: <200ms (p95)
- Cache hit: <50ms
- Cache miss: <200ms
- Cache TTL: 30 seconds (near real-time)

---

### Scenario 5: Tenant Health Monitoring

**Objective:** Validate tenant-specific health monitoring

**Test Steps:**
1. Register test tenant
2. Ingest documents
3. Perform search operations
4. Perform memory operations
5. Execute `rag_get_tenant_health` with tenant_id
6. Verify tenant-specific component health checks (FAISS, MinIO, Meilisearch)
7. Verify tenant usage metrics (total_documents, total_searches, total_memory_operations, storage_usage_bytes)
8. Verify tenant performance metrics (average_response_time, p95_response_time, p99_response_time, total_requests, requests_per_second)
9. Verify tenant error rates (total_requests, successful_requests, failed_requests, error_rate_percent, errors_by_type)
10. Verify tenant health summary and recommendations
11. Verify degraded/unhealthy component identification for tenant
12. Verify caching (30-second TTL)

**Expected Results:**
- Tenant health retrieved successfully
- Tenant-specific component health checks performed
- Tenant status calculated correctly (healthy, degraded, unhealthy)
- Tenant usage metrics accurate
- Tenant performance metrics accurate
- Tenant error rates calculated correctly
- Tenant health summary provides actionable insights
- Degraded/unhealthy tenant components identified correctly
- Caching improves performance (<200ms p95)

**Performance Targets:**
- Response time: <200ms (p95)
- Cache hit: <50ms
- Cache miss: <200ms
- Cache TTL: 30 seconds (near real-time)

---

### Scenario 6: Date Range Filtering

**Objective:** Validate date range filtering for all analytics tools

**Test Steps:**
1. Perform operations over multiple days
2. Execute analytics tools with different date ranges
3. Verify results filtered correctly by date range
4. Verify default date range (last 30 days) works correctly
5. Verify custom date ranges work correctly

**Expected Results:**
- Date range filtering works correctly for all analytics tools
- Default date range (last 30 days) applied correctly
- Custom date ranges applied correctly
- Results match expected date range

---

### Scenario 7: Performance Validation

**Objective:** Validate performance targets (<200ms p95) for all analytics tools

**Test Steps:**
1. Execute each analytics tool multiple times
2. Measure response times
3. Calculate p95 response time
4. Verify p95 < 200ms for all tools
5. Verify caching improves performance

**Expected Results:**
- All analytics tools meet performance target (<200ms p95)
- Caching significantly improves performance
- Cache hit response time <50ms
- Cache miss response time <200ms

**Performance Targets:**
- Usage Statistics: <200ms (p95)
- Search Analytics: <200ms (p95)
- Memory Analytics: <200ms (p95)
- System Health: <200ms (p95)
- Tenant Health: <200ms (p95)

---

### Scenario 8: Caching Validation

**Objective:** Validate Redis caching for all analytics tools

**Test Steps:**
1. Execute analytics tool (cache miss)
2. Verify result cached in Redis
3. Execute same analytics tool immediately (cache hit)
4. Verify cached result returned
5. Wait for cache TTL expiration
6. Execute analytics tool again (cache miss)
7. Verify new result cached

**Expected Results:**
- Caching works correctly for all analytics tools
- Cache keys unique per tool and parameters
- Cache TTL correct (5 minutes for analytics, 30 seconds for health)
- Cache hit returns immediately (<50ms)
- Cache miss triggers recalculation

**Cache TTLs:**
- Usage Statistics: 5 minutes
- Search Analytics: 5 minutes
- Memory Analytics: 5 minutes
- System Health: 30 seconds
- Tenant Health: 30 seconds

---

### Scenario 9: RBAC Enforcement

**Objective:** Validate RBAC enforcement for all analytics and monitoring tools

**Test Steps:**
1. Test `rag_get_usage_stats` with different roles (Uber Admin, Tenant Admin, User)
2. Test `rag_get_search_analytics` with different roles (Uber Admin, Tenant Admin, User)
3. Test `rag_get_memory_analytics` with different roles (Uber Admin, Tenant Admin, User)
4. Test `rag_get_system_health` with different roles (Uber Admin, Tenant Admin, User)
5. Test `rag_get_tenant_health` with different roles (Uber Admin, Tenant Admin, User)
6. Verify Tenant Admin can only query their own tenant
7. Verify unauthorized access denied

**Expected Results:**
- `rag_get_usage_stats`: Uber Admin and Tenant Admin allowed, User denied
- `rag_get_search_analytics`: Uber Admin and Tenant Admin allowed, User denied
- `rag_get_memory_analytics`: Uber Admin and Tenant Admin allowed, User denied
- `rag_get_system_health`: Uber Admin allowed, Tenant Admin and User denied
- `rag_get_tenant_health`: Uber Admin and Tenant Admin (own tenant) allowed, User denied
- Tenant Admin cannot query other tenants
- Unauthorized access raises `AuthorizationError`

---

### Scenario 10: Analytics Aggregation Accuracy

**Objective:** Validate analytics aggregation accuracy from audit logs

**Test Steps:**
1. Perform known number of operations (searches, memory operations, document operations)
2. Execute analytics tools
3. Verify statistics match actual operations
4. Verify aggregation from multiple sources (audit logs, system metrics)
5. Verify near real-time updates (within 5 minutes)

**Expected Results:**
- Analytics accurately reflect actual operations
- Aggregation from multiple sources works correctly
- Statistics updated in near real-time (within 5 minutes)
- No data loss or duplication

---

### Scenario 11: Health Summary and Recommendations

**Objective:** Validate health summary and recommendations generation

**Test Steps:**
1. Execute system health monitoring
2. Execute tenant health monitoring
3. Verify health summary generated
4. Verify recommendations provided
5. Verify degraded/unhealthy components identified
6. Verify actionable insights provided

**Expected Results:**
- Health summary generated correctly
- Recommendations provided based on health status
- Degraded/unhealthy components identified correctly
- Summary provides actionable insights for platform operators

---

### Scenario 12: Concurrent Analytics Queries

**Objective:** Validate concurrent analytics queries for multiple tenants

**Test Steps:**
1. Register multiple test tenants
2. Execute analytics queries concurrently for all tenants
3. Verify all queries complete successfully
4. Verify no resource conflicts
5. Verify performance acceptable under load

**Expected Results:**
- All concurrent queries complete successfully
- No resource conflicts or deadlocks
- Performance acceptable under concurrent load
- System remains available during concurrent queries

**Performance Targets:**
- Concurrent queries: All complete within performance targets
- System availability: No degradation during concurrent operations

---

### Scenario 13: Audit Logging Validation

**Objective:** Validate audit logging for all analytics and monitoring operations

**Test Steps:**
1. Execute each analytics tool
2. Execute each monitoring tool
3. Verify audit logs created for each operation
4. Verify audit logs contain required information (tenant_id, user_id, operation, timestamp, status)

**Expected Results:**
- Audit logs created for all operations
- Audit logs contain required information
- Audit logs accessible for compliance

---

### Scenario 14: Error Handling and Fault Tolerance

**Objective:** Validate error handling and fault tolerance

**Test Scenarios:**
1. **Analytics with missing tenant:** Verify appropriate error raised
2. **Analytics with invalid date range:** Verify appropriate error raised
3. **Health monitoring with service unavailable:** Verify graceful error handling
4. **Analytics with corrupted audit logs:** Verify graceful error handling
5. **Health monitoring with partial service failure:** Verify degraded status identified

**Expected Results:**
- Appropriate errors raised for invalid inputs
- Graceful error handling for service unavailability
- Degraded status identified correctly
- Error messages clear and actionable

---

### Scenario 15: End-to-End Analytics Workflow

**Objective:** Validate complete analytics workflow

**Test Steps:**
1. Register test tenant
2. Ingest documents
3. Perform search operations
4. Perform memory operations
5. Retrieve usage statistics
6. Retrieve search analytics
7. Retrieve memory analytics
8. Monitor system health
9. Monitor tenant health
10. Verify all analytics accurate and consistent

**Expected Results:**
- Complete workflow executes successfully
- All steps complete without errors
- Analytics accurate and consistent across all tools
- Performance targets met

---

## Performance Targets

### Response Time (p95)
- **Usage Statistics:** <200ms
- **Search Analytics:** <200ms
- **Memory Analytics:** <200ms
- **System Health:** <200ms
- **Tenant Health:** <200ms

### Caching
- **Analytics Tools (Usage, Search, Memory):** 5-minute TTL
- **Health Tools (System, Tenant):** 30-second TTL
- **Cache Hit:** <50ms
- **Cache Miss:** <200ms

### Near Real-Time Updates
- **Analytics Updates:** Within 5 minutes
- **Health Updates:** Within 30 seconds (cached)

---

## Test Implementation

### Test File Structure
```
tests/integration/
  test_epic8_monitoring_analytics_workflows.py
    - TestEpic8UsageStatistics
    - TestEpic8SearchAnalytics
    - TestEpic8MemoryAnalytics
    - TestEpic8SystemHealth
    - TestEpic8TenantHealth
    - TestEpic8Performance
    - TestEpic8Caching
    - TestEpic8Security
    - TestEpic8Reliability
```

### Test Fixtures
- `registered_test_tenants`: Session-scoped fixture for test tenants
- `test_tenant_id`: Function-scoped fixture for tenant UUID
- `test_user_id`: Function-scoped fixture for user UUID
- `test_documents`: Fixture for pre-ingested test documents
- `test_memory_operations`: Fixture for pre-created memory operations
- `test_search_operations`: Fixture for pre-executed search operations

### Test Utilities
- `get_tool_func(tool_name)`: Get underlying function from MCP tool
- `create_test_operations()`: Helper to create test operations for analytics
- `verify_analytics_accuracy()`: Helper to verify analytics accuracy
- `measure_response_time()`: Helper to measure response times

---

## Test Execution

### Prerequisites
1. All services running (PostgreSQL, Redis, MinIO, Meilisearch, FAISS, Mem0)
2. Test environment configured
3. Test data setup (documents, memory operations, search operations)

### Execution Command
```bash
# Run all Epic 8 integration tests
pytest tests/integration/test_epic8_monitoring_analytics_workflows.py -v -m integration

# Run specific test scenario
pytest tests/integration/test_epic8_monitoring_analytics_workflows.py::TestEpic8UsageStatistics::test_usage_statistics_retrieval -v

# Run performance tests
pytest tests/integration/test_epic8_monitoring_analytics_workflows.py -v -m performance

# Run security tests
pytest tests/integration/test_epic8_monitoring_analytics_workflows.py -v -m security
```

### Expected Test Results
- All integration tests pass
- All performance targets met
- All security validations pass
- All reliability tests pass

---

## Success Criteria

### Functional
- ✅ All analytics tools retrieve accurate data
- ✅ All monitoring tools provide accurate health status
- ✅ All filtering options work correctly
- ✅ All caching mechanisms work correctly
- ✅ All end-to-end workflows pass

### Performance
- ✅ All analytics tools meet performance target (<200ms p95)
- ✅ Caching improves performance significantly
- ✅ Near real-time updates work correctly (within 5 minutes for analytics, 30 seconds for health)

### Security
- ✅ RBAC enforcement verified for all tools
- ✅ Unauthorized access denied appropriately
- ✅ Tenant Admin can only query their own tenant
- ✅ Audit logging verified for all operations

### Reliability
- ✅ Error handling verified
- ✅ Fault tolerance verified
- ✅ Concurrent operations verified
- ✅ Analytics aggregation accuracy verified

---

## Test Deliverables

1. **Integration Test Suite:** `tests/integration/test_epic8_monitoring_analytics_workflows.py`
2. **Test Plan Document:** `_bmad-output/planning-artifacts/epic-8-test-plan.md` (this document)
3. **Test Results Report:** Generated after test execution
4. **Verification Document:** Epic 8 verification document with test results

---

## Next Steps

1. ⏳ Create test plan document (Task 8.T.1) - **IN PROGRESS**
2. ⏳ Write integration tests for usage statistics (Task 8.T.2)
3. ⏳ Write integration tests for search analytics (Task 8.T.3)
4. ⏳ Write integration tests for memory analytics (Task 8.T.4)
5. ⏳ Write integration tests for system health monitoring (Task 8.T.5)
6. ⏳ Write integration tests for tenant health monitoring (Task 8.T.6)
7. ⏳ Write integration tests for performance and caching (Task 8.T.7)
8. ⏳ Create verification documentation and attach to Epic 8 (Task 8.T.8)

---

**Test Plan Created By:** BMAD Master  
**Date:** 2026-01-08  
**Status:** Ready for Implementation


