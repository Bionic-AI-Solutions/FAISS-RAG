# Testing Strategy: Unit Tests + Integration Tests

**Status:** MANDATORY REQUIREMENT  
**Applies To:** All agents (Dev, Test Team, TEA)

## CRITICAL RULE

**Every story MUST have both unit tests AND integration tests** to ensure components work correctly in isolation AND in real-life scenarios.

## Why Both?

### Unit Tests (with Mocks)
- ✅ **Fast execution** - No external dependencies, runs in milliseconds
- ✅ **Isolated testing** - Test code logic without external services
- ✅ **Easy debugging** - Failures point directly to code issues
- ✅ **Test edge cases** - Easy to simulate error conditions
- ✅ **Consistent with codebase** - All unit tests use mocks (Meilisearch, Mem0, Redis)

### Integration Tests (with Real Services)
- ✅ **Real-world validation** - Components work with actual services
- ✅ **Catch integration issues** - Service compatibility, configuration problems
- ✅ **Performance validation** - Real performance metrics (<150ms p95, etc.)
- ✅ **End-to-end workflows** - Complete user journeys work correctly
- ✅ **Production readiness** - Confidence that code works in production

## Test Structure

### Unit Tests
**Location:** `tests/unit/test_<component>.py`

**Pattern:**
```python
# Mock external services
with patch("app.services.faiss_manager.faiss", create=True):
    # Test our logic
    results = service.search(...)
    assert results == expected
```

**What to Test:**
- Business logic and data transformations
- Tenant isolation and security
- Error handling and edge cases
- Input validation
- Result processing and ranking

### Integration Tests
**Location:** `tests/integration/test_<component>_integration.py`

**Pattern:**
```python
# Use real services
async def test_search_with_real_faiss():
    # Create real FAISS index
    index = faiss.IndexFlatL2(384)
    # Add real documents
    # Perform real search
    # Verify results
```

**What to Test:**
- End-to-end workflows
- Service integration points
- Performance requirements
- Real-world scenarios
- Service compatibility

## Agent Responsibilities

### Dev Agent
**During Task Implementation:**
1. **Write unit tests first** (TDD approach)
   - Mock external services
   - Test all code paths
   - Verify logic correctness
2. **Write integration tests**
   - Use real services
   - Test end-to-end workflows
   - Verify performance requirements
3. **Run both test suites** before marking task "In testing" (79)
   ```bash
   # Unit tests (fast, no services needed)
   python3 -m pytest tests/unit/test_<component>.py -v
   
   # Integration tests (requires services)
   python3 -m pytest tests/integration/test_<component>_integration.py -v
   ```

**Before Task Completion:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage meets requirements (>80%)
- [ ] Performance requirements validated (integration tests)
- [ ] Update task status to "In testing" (79)

### Test Team / TEA Agent
**During Validation:**
1. **Run unit test suite** (with mocks) - Verify logic and edge cases
2. **Run integration test suite** (with real services) - Verify real-world functionality
3. Verify acceptance criteria covered
4. Verify performance requirements met
5. Update status: "Closed" (82) if passes, "Test failed" (81) if fails

## Best Practices

### Unit Tests
- **Mock at the service boundary** - Mock FAISS, Meilisearch, Redis, not internal functions
- **Test one thing at a time** - Each test should verify one behavior
- **Use descriptive test names** - `test_search_tenant_isolation_cross_tenant_access_prevented`
- **Test edge cases** - Empty inputs, missing data, error conditions

### Integration Tests
- **Use real services** - FAISS indices, Meilisearch, Redis, databases
- **Test complete workflows** - End-to-end user journeys
- **Validate performance** - Measure actual response times
- **Test with real data** - Use realistic test data
- **Clean up after tests** - Remove test indices, clear test data

## Test Organization

```
tests/
├── unit/                          # Unit tests (with mocks)
│   ├── test_faiss_search.py
│   ├── test_vector_search_service.py
│   ├── test_keyword_search_service.py
│   └── test_hybrid_search_service.py
│
├── integration/                   # Integration tests (with real services)
│   ├── test_faiss_vector_search_integration.py
│   ├── test_meilisearch_keyword_search_integration.py
│   ├── test_hybrid_search_integration.py
│   └── test_rag_search_tool_integration.py
│
└── fixtures/                      # Test fixtures
    ├── faiss_indices.py          # FAISS index fixtures
    └── test_data.py              # Test data generators
```

## Integration Test Patterns

**Location:** Configured in `project-config.yaml` → `testing.integration_test_patterns.location`

**Default:** Epic-level patterns (one file per Epic)

**File Pattern:** `_bmad-output/implementation-artifacts/integration-test-patterns-epic-{n}.md`

**Creation:**
- Created during Epic grooming by Test Team/TEA
- Can be enhanced during story grooming as more clarity is gained
- Attached to Epic work package in OpenProject via MCP

**Content:**
- Integration test setup patterns
- Real service configuration
- Test fixture usage
- Performance testing patterns
- Examples from existing integration tests

**Usage:**
- Dev references pattern doc during implementation
- Dev writes integration tests following patterns
- Test fixtures located in `tests/fixtures/` (standard pytest location)

**Configuration Options:**
- `"epic-level"`: One pattern file per Epic (RECOMMENDED for projects without Features)
- `"single-file"`: Single pattern file for all epics
- `"test-directory"`: Patterns in `tests/integration/patterns/`

## References

- **QA Workflow:** `_bmad/bmm/testarch/procedures/qa-workflow.md`
- **System Readiness:** `_bmad/bmm/testarch/procedures/system-readiness.md`
- **Test Data Responsibility:** `_bmad/bmm/testarch/procedures/test-data-responsibility.md`
- **Story Verification:** `_bmad/workflows/STORY_VERIFICATION_STANDARD.md`
- **Integration Test Patterns Config:** `_bmad/_config/project-config.yaml` → `testing.integration_test_patterns`

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-08  
**Owner:** Test Team / TEA Agent  
**Review Frequency:** Quarterly
