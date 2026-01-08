# Epic 7: Data Protection & Disaster Recovery - Test Plan

**Epic ID:** 149  
**Status:** In Progress  
**Test Plan Date:** 2026-01-07

## Overview

This test plan validates the complete Epic 7 functionality including all backup, restore, rebuild, and validation operations. All tests use real services (no mocks) and follow the integration test pattern established in Epic 3, 4, 5, and 6.

## Test Scope

### Stories Covered
- **Story 7.1:** Tenant Backup MCP Tool
- **Story 7.2:** Tenant Restore MCP Tool
- **Story 7.3:** FAISS Index Rebuild MCP Tool
- **Story 7.4:** Backup Validation MCP Tool

### Test Categories
1. **Integration Tests:** End-to-end workflows using real services
2. **Performance Tests:** RTO/RPO target validation
3. **Security Tests:** RBAC enforcement
4. **Reliability Tests:** Fault tolerance and error handling
5. **Audit Tests:** Audit logging validation

## Test Environment

### Prerequisites
- All services running (PostgreSQL, Redis, MinIO, Meilisearch, FAISS, Mem0)
- Test tenant registered and configured
- Test documents ingested for backup/restore scenarios
- Backup directory configured (`BACKUP_BASE_DIR`)

### Test Data Setup
- **Tenant:** Registered test tenant with UUID
- **Documents:** Multiple documents ingested (text, PDF, etc.)
- **FAISS Index:** Populated with document embeddings
- **MinIO:** Documents stored in tenant bucket
- **Meilisearch:** Documents indexed in tenant index

## Test Scenarios

### Scenario 1: Full Backup Operation

**Objective:** Validate complete tenant data backup (PostgreSQL, FAISS, MinIO, Meilisearch)

**Test Steps:**
1. Register test tenant
2. Ingest multiple documents
3. Execute `rag_backup_tenant_data` with `backup_type="full"`
4. Verify backup manifest created
5. Verify all components backed up (PostgreSQL, FAISS, MinIO, Meilisearch)
6. Verify backup files exist and are accessible
7. Verify backup checksums match
8. Verify backup progress tracking

**Expected Results:**
- Backup completes successfully
- Backup manifest contains all required components
- All backup files exist and are valid
- Backup ID returned for tracking
- Backup timestamp recorded
- Backup completes within RTO target (<2 hours for full backup)

**Performance Targets:**
- Full backup: <2 hours
- Backup progress tracking: Updates available during backup

---

### Scenario 2: Incremental Backup Operation

**Objective:** Validate incremental backup (only changed data)

**Test Steps:**
1. Create initial full backup
2. Modify/add documents
3. Execute `rag_backup_tenant_data` with `backup_type="incremental"`
4. Verify only changed components backed up
5. Verify backup manifest reflects incremental backup
6. Verify backup size is smaller than full backup

**Expected Results:**
- Incremental backup completes successfully
- Only changed components backed up
- Backup manifest indicates incremental backup
- Backup completes within RTO target (<30 minutes for incremental)

**Performance Targets:**
- Incremental backup: <30 minutes

---

### Scenario 3: Tenant Restore Operation

**Objective:** Validate complete tenant data restore from backup

**Test Steps:**
1. Create backup of test tenant
2. Modify tenant data (delete documents, modify data)
3. Execute `rag_restore_tenant_data` with backup_id
4. Verify safety backup created before restore
5. Verify all components restored (PostgreSQL, FAISS, MinIO, Meilisearch)
6. Verify restored data matches original backup
7. Verify restore progress tracking

**Expected Results:**
- Safety backup created before restore
- All components restored successfully
- Restored data matches original backup
- Restore completes within reasonable time
- Restore progress tracking available

**Performance Targets:**
- Restore operation: <1 hour for full restore
- Safety backup: <30 minutes

---

### Scenario 4: FAISS Index Rebuild (Full)

**Objective:** Validate FAISS index rebuild from source documents

**Test Steps:**
1. Create test tenant with documents
2. Corrupt or delete FAISS index
3. Execute `rag_rebuild_index` with `rebuild_type="full"` and `confirmation_code="FR-BACKUP-004"`
4. Verify all documents retrieved from PostgreSQL
5. Verify embeddings regenerated for all documents
6. Verify FAISS index rebuilt with new embeddings
7. Verify index integrity validated
8. Verify index metadata updated

**Expected Results:**
- Index rebuild completes successfully
- All documents processed
- All embeddings regenerated
- Index integrity validated
- Index size matches document count
- Rebuild completes within reasonable time

**Performance Targets:**
- Full rebuild: Depends on document count (target: <4 hours for 10,000 documents)

---

### Scenario 5: FAISS Index Rebuild (Incremental)

**Objective:** Validate incremental FAISS index rebuild

**Test Steps:**
1. Create test tenant with existing index
2. Add new documents
3. Execute `rag_rebuild_index` with `rebuild_type="incremental"` and `confirmation_code="FR-BACKUP-004"`
4. Verify only new/changed documents processed
5. Verify index updated with new embeddings
6. Verify index integrity validated

**Expected Results:**
- Incremental rebuild completes successfully
- Only new/changed documents processed
- Index updated correctly
- Index integrity validated
- Rebuild completes faster than full rebuild

---

### Scenario 6: Backup Validation (Full)

**Objective:** Validate backup integrity and completeness

**Test Steps:**
1. Create backup of test tenant
2. Execute `rag_validate_backup` with `validation_type="full"`
3. Verify manifest validation
4. Verify file existence validation
5. Verify file integrity validation (checksums)
6. Verify backup completeness validation

**Expected Results:**
- Validation completes successfully
- All validations pass (manifest, file existence, integrity, completeness)
- Validation report generated with detailed status
- Validation completes within reasonable time

**Performance Targets:**
- Full validation: <5 minutes

---

### Scenario 7: Backup Validation (Integrity Only)

**Objective:** Validate backup file integrity (checksums only)

**Test Steps:**
1. Create backup of test tenant
2. Execute `rag_validate_backup` with `validation_type="integrity"`
3. Verify only checksum validation performed
4. Verify checksums match for all components

**Expected Results:**
- Integrity validation completes successfully
- All checksums match
- Validation report includes integrity status only

---

### Scenario 8: Backup Validation (Completeness Only)

**Objective:** Validate backup completeness (required components only)

**Test Steps:**
1. Create backup of test tenant
2. Execute `rag_validate_backup` with `validation_type="completeness"`
3. Verify all required components present (PostgreSQL, FAISS, MinIO, Meilisearch)
4. Verify completeness validation passes

**Expected Results:**
- Completeness validation completes successfully
- All required components present
- Validation report includes completeness status only

---

### Scenario 9: Safety Backup Before Restore

**Objective:** Validate safety backup created before restore operation

**Test Steps:**
1. Create initial backup
2. Modify tenant data
3. Execute `rag_restore_tenant_data` with `confirmation=True`
4. Verify safety backup created before restore
5. Verify safety backup ID returned
6. Verify safety backup can be used for recovery

**Expected Results:**
- Safety backup created automatically
- Safety backup ID returned in restore response
- Safety backup contains current state before restore
- Safety backup can be used to recover if restore fails

---

### Scenario 10: Backup Progress Tracking

**Objective:** Validate backup progress tracking during operation

**Test Steps:**
1. Create large backup (many documents)
2. Monitor backup progress
3. Verify progress updates available
4. Verify estimated time remaining calculated
5. Verify progress percentage accurate

**Expected Results:**
- Progress tracking available during backup
- Progress updates reflect current status
- Estimated time remaining provided
- Progress percentage accurate

---

### Scenario 11: Restore Progress Tracking

**Objective:** Validate restore progress tracking during operation

**Test Steps:**
1. Create backup
2. Execute restore operation
3. Monitor restore progress
4. Verify progress updates available
5. Verify component-level progress tracked

**Expected Results:**
- Progress tracking available during restore
- Progress updates reflect current status
- Component-level progress tracked
- Progress percentage accurate

---

### Scenario 12: Concurrent Backup Operations

**Objective:** Validate concurrent backup operations for multiple tenants

**Test Steps:**
1. Register multiple test tenants
2. Execute backup operations concurrently for all tenants
3. Verify all backups complete successfully
4. Verify no resource conflicts
5. Verify performance acceptable under load

**Expected Results:**
- All concurrent backups complete successfully
- No resource conflicts or deadlocks
- Performance acceptable under concurrent load
- System remains available during concurrent backups

**Performance Targets:**
- Concurrent backups: All complete within RTO targets
- System availability: No degradation during concurrent operations

---

### Scenario 13: RBAC Enforcement

**Objective:** Validate RBAC enforcement for all backup/restore/rebuild/validation tools

**Test Steps:**
1. Test `rag_backup_tenant_data` with different roles (Uber Admin, Tenant Admin, User)
2. Test `rag_restore_tenant_data` with different roles (Uber Admin only)
3. Test `rag_rebuild_index` with different roles (Uber Admin, Tenant Admin, User)
4. Test `rag_validate_backup` with different roles (Uber Admin, Tenant Admin, User)
5. Verify unauthorized access denied

**Expected Results:**
- `rag_backup_tenant_data`: Uber Admin and Tenant Admin allowed, User denied
- `rag_restore_tenant_data`: Uber Admin allowed, Tenant Admin and User denied
- `rag_rebuild_index`: Uber Admin and Tenant Admin allowed, User denied
- `rag_validate_backup`: Uber Admin and Tenant Admin allowed, User denied
- Unauthorized access raises `AuthorizationError`

---

### Scenario 14: Audit Logging Validation

**Objective:** Validate audit logging for all backup/restore/rebuild/validation operations

**Test Steps:**
1. Execute backup operation
2. Execute restore operation
3. Execute rebuild operation
4. Execute validation operation
5. Verify audit logs created for each operation
6. Verify audit logs contain required information (tenant_id, user_id, operation, timestamp, status)

**Expected Results:**
- Audit logs created for all operations
- Audit logs contain required information
- Audit logs accessible for compliance

---

### Scenario 15: Error Handling and Fault Tolerance

**Objective:** Validate error handling and fault tolerance

**Test Scenarios:**
1. **Backup with missing tenant:** Verify appropriate error raised
2. **Restore with invalid backup_id:** Verify appropriate error raised
3. **Rebuild with missing documents:** Verify appropriate error raised
4. **Validation with corrupted backup:** Verify validation detects corruption
5. **Backup with service unavailable:** Verify graceful error handling
6. **Restore with partial backup:** Verify appropriate error handling

**Expected Results:**
- Appropriate errors raised for invalid inputs
- Validation detects corrupted backups
- Graceful error handling for service unavailability
- Error messages clear and actionable

---

### Scenario 16: End-to-End Backup/Restore Workflow

**Objective:** Validate complete backup/restore workflow

**Test Steps:**
1. Register test tenant
2. Ingest multiple documents
3. Create full backup
4. Validate backup
5. Modify tenant data
6. Restore from backup
7. Verify restored data matches original
8. Verify all components restored correctly

**Expected Results:**
- Complete workflow executes successfully
- All steps complete without errors
- Restored data matches original backup
- All components restored correctly

---

## Performance Targets

### RTO (Recovery Time Objective)
- **Full Backup:** <2 hours
- **Incremental Backup:** <30 minutes
- **Full Restore:** <1 hour
- **Safety Backup:** <30 minutes

### RPO (Recovery Point Objective)
- **Backup Frequency:** <1 hour (target for automated backups)

### Performance Metrics
- **Backup Progress Tracking:** Updates every 10% or 5 minutes
- **Restore Progress Tracking:** Updates every 10% or 5 minutes
- **Validation Time:** <5 minutes for full validation
- **Rebuild Time:** Depends on document count (target: <4 hours for 10,000 documents)

---

## Test Implementation

### Test File Structure
```
tests/integration/
  test_epic7_backup_restore_workflows.py
    - TestEpic7BackupWorkflows
    - TestEpic7RestoreWorkflows
    - TestEpic7RebuildWorkflows
    - TestEpic7ValidationWorkflows
    - TestEpic7EndToEndWorkflows
    - TestEpic7Performance
    - TestEpic7Security
    - TestEpic7Reliability
```

### Test Fixtures
- `registered_test_tenants`: Session-scoped fixture for test tenants
- `test_tenant_id`: Function-scoped fixture for tenant UUID
- `test_user_id`: Function-scoped fixture for user UUID
- `test_documents`: Fixture for pre-ingested test documents
- `backup_directory`: Fixture for backup directory setup

### Test Utilities
- `get_tool_func(tool_name)`: Get underlying function from MCP tool
- `create_test_backup()`: Helper to create test backup
- `validate_backup_structure()`: Helper to validate backup structure
- `compare_tenant_data()`: Helper to compare tenant data before/after restore

---

## Test Execution

### Prerequisites
1. All services running (PostgreSQL, Redis, MinIO, Meilisearch, FAISS, Mem0)
2. Test environment configured
3. Backup directory accessible

### Execution Command
```bash
# Run all Epic 7 integration tests
pytest tests/integration/test_epic7_backup_restore_workflows.py -v -m integration

# Run specific test scenario
pytest tests/integration/test_epic7_backup_restore_workflows.py::TestEpic7BackupWorkflows::test_full_backup_operation -v

# Run performance tests
pytest tests/integration/test_epic7_backup_restore_workflows.py -v -m performance

# Run security tests
pytest tests/integration/test_epic7_backup_restore_workflows.py -v -m security
```

### Expected Test Results
- All integration tests pass
- All performance targets met
- All security validations pass
- All reliability tests pass

---

## Success Criteria

### Functional
- ✅ All backup operations complete successfully
- ✅ All restore operations complete successfully
- ✅ All rebuild operations complete successfully
- ✅ All validation operations complete successfully
- ✅ All end-to-end workflows pass

### Performance
- ✅ Full backup completes within RTO target (<2 hours)
- ✅ Incremental backup completes within RTO target (<30 minutes)
- ✅ Full restore completes within RTO target (<1 hour)
- ✅ Validation completes within reasonable time (<5 minutes)

### Security
- ✅ RBAC enforcement verified for all tools
- ✅ Unauthorized access denied appropriately
- ✅ Audit logging verified for all operations

### Reliability
- ✅ Error handling verified
- ✅ Fault tolerance verified
- ✅ Concurrent operations verified

---

## Test Deliverables

1. **Integration Test Suite:** `tests/integration/test_epic7_backup_restore_workflows.py`
2. **Test Plan Document:** `_bmad-output/planning-artifacts/epic-7-test-plan.md` (this document)
3. **Test Results Report:** Generated after test execution
4. **Verification Document:** Epic 7 verification document with test results

---

## Next Steps

1. ✅ Create test plan document (Task 7.T.1) - **COMPLETE**
2. ⏳ Write integration tests for backup operations (Task 7.T.2)
3. ⏳ Write integration tests for restore operations (Task 7.T.3)
4. ⏳ Write integration tests for FAISS index rebuild (Task 7.T.4)
5. ⏳ Write integration tests for backup validation (Task 7.T.5)
6. ⏳ Write integration tests for safety backups and progress tracking (Task 7.T.6)
7. ⏳ Create verification documentation and attach to Epic 7 (Task 7.T.7)

---

**Test Plan Created By:** BMAD Master  
**Date:** 2026-01-07  
**Status:** Ready for Implementation


