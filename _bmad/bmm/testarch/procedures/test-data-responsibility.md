
# Test Data & Fixture Creation Responsibility

## Purpose

This procedure establishes clear responsibility for creating test data and fixtures for both unit tests (mock fixtures) and integration tests (real system test data). This ensures test data is created consistently and maintained properly.

## Scope

This procedure applies to:
- Mock fixtures for unit tests
- Test data in real systems for integration tests
- Shared/reusable test fixtures
- Test data factories
- Integration test patterns

---

## Responsibility Assignment

### 1. Mock Fixtures for Unit Tests

**PRIMARY RESPONSIBILITY: Dev Agent**

**Dev Agent creates mock fixtures as part of TDD (Test-Driven Development) cycle:**

**When:**
- During task implementation
- As part of writing unit tests first (red-green-refactor)
- When mocking external services

**What to Create:**
- Mock objects for external services (FAISS, Meilisearch, Redis, databases)
- Mock data structures matching service interfaces
- Mock response objects
- Test doubles (stubs, mocks, fakes)

**Location:**
- Inline in test files (for test-specific mocks)
- `tests/unit/fixtures/` (for shared unit test fixtures)
- Using `unittest.mock` or `pytest.fixture` decorators

**Example:**
```python
# tests/unit/test_search_service.py
from unittest.mock import patch, MagicMock

def test_search_with_mocked_faiss():
    # Dev creates mock fixture inline
    mock_index = MagicMock()
    mock_index.search.return_value = ([0, 1, 2], [0.9, 0.8, 0.7])
    
    with patch("app.services.faiss_manager.faiss", mock_index):
        results = search_service.search("query")
        assert len(results) == 3
```

**Best Practices:**
- Mock at service boundary (not internal functions)
- Use descriptive mock names
- Document mock behavior
- Reuse common mocks via pytest fixtures

---

### 2. Test Data in Real Systems for Integration Tests

**PRIMARY RESPONSIBILITY: Dev Agent (Creates), Test Team/TEA (Validates)**

**Dev Agent creates test data during integration test implementation:**

**When:**
- During task implementation
- When writing integration tests
- Before running integration tests

**What to Create:**
- Real test data in databases
- Real test indices (FAISS, Meilisearch)
- Real test tenants/users
- Real test documents/records
- Test data using factories or generators

**Location:**
- `tests/fixtures/` - Test fixtures for real data
- `tests/integration/fixtures/` - Integration-specific fixtures
- Using pytest fixtures with real service connections

**Example:**
```python
# tests/fixtures/test_data.py
import pytest
from app.services.faiss_manager import FaissManager

@pytest.fixture
def test_faiss_index():
    # Dev creates real FAISS index fixture
    index = faiss.IndexFlatL2(384)
    # Add test vectors
    vectors = np.random.rand(10, 384).astype('float32')
    index.add(vectors)
    yield index
    # Cleanup
    del index

# tests/integration/test_search_integration.py
def test_search_with_real_faiss(test_faiss_index):
    # Dev uses real fixture in integration test
    results = search_service.search("query", index=test_faiss_index)
    assert len(results) > 0
```

**Test Team/TEA Validation:**
- Verify test data is realistic
- Verify test data covers edge cases
- Verify test data cleanup works
- Verify test data doesn't cause collisions

---

### 3. Shared/Reusable Test Fixtures

**PRIMARY RESPONSIBILITY: TEA Agent / Test Team**

**TEA Agent creates shared fixtures during test framework setup:**

**When:**
- During test framework initialization (TEA workflow: `testarch-framework`)
- During ATDD workflow (before implementation)
- When establishing test infrastructure
- When creating reusable test patterns

**What to Create:**
- Common fixtures used across multiple tests
- Fixture architecture (Playwright `test.extend()` pattern)
- Data factories (using `@faker-js/faker`)
- Test utilities and helpers
- Fixture composition patterns

**Location:**
- `tests/support/fixtures/` - Shared fixtures (Playwright/Cypress)
- `tests/fixtures/` - Shared fixtures (pytest)
- `tests/support/factories/` - Data factories

**Example:**
```typescript
// tests/support/fixtures/auth.fixture.ts (TEA creates)
import { test as base } from '@playwright/test';
import { createUser, deleteUser } from '../factories/user-factory';

export const test = base.extend({
  authenticatedUser: async ({ page }, use) => {
    // Setup: Create and authenticate user
    const user = await createUser();
    await page.goto('/login');
    await page.fill('[data-testid="email"]', user.email);
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    await use(user);
    
    // Cleanup: Delete user
    await deleteUser(user.id);
  },
});
```

**TEA Responsibilities:**
- Create fixture architecture following best practices
- Use data factories (not hardcoded data)
- Implement auto-cleanup in fixtures
- Document fixture usage patterns
- Ensure fixtures are composable and isolated

---

### 4. Integration Test Patterns

**PRIMARY RESPONSIBILITY: Test Team / TEA Agent**

**Test Team/TEA creates integration test patterns during Epic grooming:**

**When:**
- During Epic grooming (before story implementation)
- Can be enhanced during story grooming
- Before Dev starts implementation

**What to Create:**
- Integration test setup patterns
- Real service configuration examples
- Test fixture usage examples
- Performance testing patterns
- Examples from existing integration tests

**Location:**
- `_bmad-output/implementation-artifacts/integration-test-patterns-epic-{n}.md`
- Attached to Epic work package in OpenProject

**Content:**
- Integration test setup patterns
- Real service configuration
- Test fixture usage
- Performance testing patterns
- Examples from existing integration tests

**Example Pattern Document:**
```markdown
# Integration Test Patterns - Epic 11

## Service Configuration
- REST API: http://localhost:8000
- RAG Backend: http://localhost:8001
- Redis: localhost:6379

## Test Fixture Usage
```python
@pytest.fixture
def test_tenant():
    # Create test tenant
    tenant = create_tenant(name="test-tenant")
    yield tenant
    # Cleanup
    delete_tenant(tenant.id)
```

## Performance Patterns
- Search operations: <150ms p95
- Document upload: <2s p95
```

**Test Team/TEA Responsibilities:**
- Create pattern document during Epic grooming
- Include real service configuration
- Document fixture usage patterns
- Provide examples from existing tests
- Update patterns during story grooming (if needed)

---

### 5. Test Data Factories

**PRIMARY RESPONSIBILITY: TEA Agent (Framework), Dev Agent (Story-Specific)**

**TEA Agent creates factory architecture during framework setup:**

**When:**
- During test framework initialization
- During ATDD workflow
- When establishing data generation patterns

**What to Create:**
- Factory functions using `@faker-js/faker`
- Factory architecture (overrides support)
- Bulk creation helpers
- Type-safe factory exports

**Location:**
- `tests/support/factories/` - Shared factories
- `tests/fixtures/factories/` - pytest factories

**Example:**
```typescript
// tests/support/factories/user-factory.ts (TEA creates)
import { faker } from '@faker-js/faker';

export const createUser = (overrides = {}) => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  name: faker.person.fullName(),
  role: 'user',
  ...overrides,
});

export const createUsers = (count: number) => 
  Array.from({ length: count }, () => createUser());
```

**Dev Agent creates story-specific factories:**

**When:**
- When story requires specific data patterns
- When existing factories don't cover story needs
- During integration test implementation

**What to Create:**
- Story-specific factory functions
- Domain-specific test data generators
- Custom data builders

**Location:**
- `tests/fixtures/` - Story-specific factories
- Inline in test files (if very specific)

---

## Complete Responsibility Matrix

| Test Data Type | Primary Responsibility | Secondary Responsibility | When Created |
|---------------|----------------------|------------------------|--------------|
| **Mock Fixtures (Unit Tests)** | Dev Agent | - | During task implementation (TDD) |
| **Real Test Data (Integration Tests)** | Dev Agent | Test Team validates | During task implementation |
| **Shared Fixtures** | TEA Agent | Test Team | During framework setup / ATDD |
| **Integration Test Patterns** | Test Team / TEA | - | During Epic grooming |
| **Data Factories (Framework)** | TEA Agent | - | During framework setup |
| **Data Factories (Story-Specific)** | Dev Agent | - | During story implementation |

---

## Workflow Integration

### Dev Agent Workflow

**During Task Implementation:**

```
1. Write failing unit test
   ↓
2. Create mock fixtures (inline or in tests/unit/fixtures/)
   ↓
3. Implement code to make test pass
   ↓
4. Write integration test
   ↓
5. Create real test data fixtures (in tests/fixtures/)
   ↓
6. Run integration tests with real services
   ↓
7. Verify test data cleanup
```

**Example Dev Task Comment:**
```
Task completed:
- Unit tests: 5/5 passing (mocks created inline)
- Integration tests: 3/3 passing (test fixtures in tests/fixtures/test_data.py)
- Test data: Created test tenants, documents, indices
- Cleanup: All test data cleaned up after tests
```

### TEA Agent Workflow

**During Framework Setup:**

```
1. Initialize test framework (testarch-framework workflow)
   ↓
2. Create fixture architecture (tests/support/fixtures/)
   ↓
3. Create data factories (tests/support/factories/)
   ↓
4. Document fixture usage patterns
   ↓
5. Create integration test patterns (during Epic grooming)
```

**During ATDD Workflow:**

```
1. Generate failing acceptance tests
   ↓
2. Create required fixtures for E2E tests
   ↓
3. Create data factories for test data
   ↓
4. Document mock requirements
   ↓
5. Provide implementation checklist to Dev
```

### Test Team Workflow

**During Epic Grooming:**

```
1. Review Epic requirements
   ↓
2. Create integration test pattern document
   ↓
3. Document real service configuration
   ↓
4. Document fixture usage examples
   ↓
5. Attach pattern doc to Epic work package
```

**During Story Validation:**

```
1. Review Dev's test data creation
   ↓
2. Verify test data is realistic
   ↓
3. Verify test data covers edge cases
   ↓
4. Verify test data cleanup works
   ↓
5. Provide feedback if improvements needed
```

---

## Best Practices

### Mock Fixtures (Unit Tests)

**✅ Good:**
```python
# Mock at service boundary
with patch("app.services.faiss_manager.faiss", create=True):
    # Test logic
```

**❌ Bad:**
```python
# Mock internal functions
with patch("app.services.search_service._internal_helper"):
    # Test logic
```

### Real Test Data (Integration Tests)

**✅ Good:**
```python
@pytest.fixture
def test_tenant():
    tenant = create_tenant(name=f"test-tenant-{uuid.uuid4()}")
    yield tenant
    delete_tenant(tenant.id)  # Cleanup
```

**❌ Bad:**
```python
# Hardcoded test data
tenant = Tenant(id=1, name="test-tenant")  # May collide
```

### Data Factories

**✅ Good:**
```typescript
// Use faker for random data
export const createUser = (overrides = {}) => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  ...overrides,
});
```

**❌ Bad:**
```typescript
// Hardcoded data
export const createUser = () => ({
  id: "user-1",
  email: "test@example.com",  // May collide
});
```

---

## Test Data Cleanup

### Responsibility: Same as Creation

**Who creates test data → Who ensures cleanup**

- **Dev Agent:** Ensures test data cleanup in fixtures (teardown)
- **TEA Agent:** Ensures shared fixtures have auto-cleanup
- **Test Team:** Validates cleanup works during validation

**Cleanup Patterns:**

1. **Pytest Fixtures:**
```python
@pytest.fixture
def test_data():
    # Setup
    data = create_test_data()
    yield data
    # Teardown (always runs)
    cleanup_test_data(data)
```

2. **Playwright Fixtures:**
```typescript
export const test = base.extend({
  testData: async ({}, use) => {
    const data = await createTestData();
    await use(data);
    await cleanupTestData(data);  // Auto-cleanup
  },
});
```

---

## Integration with Existing Procedures

### Testing Strategy Integration

**Reference:** `_bmad/bmm/testarch/procedures/testing-strategy.md`

**Updated Responsibilities:**

**Dev Agent:**
- ✅ Write unit tests with mocks
- ✅ **Create mock fixtures for unit tests**
- ✅ Write integration tests with real services
- ✅ **Create real test data fixtures for integration tests**
- ✅ Ensure test data cleanup

**Test Team / TEA:**
- ✅ **Create shared fixtures during framework setup**
- ✅ **Create integration test patterns during Epic grooming**
- ✅ Validate test data quality during validation

### System Readiness Integration

**Reference:** `_bmad/bmm/testarch/procedures/system-readiness.md`

**Test Data Verification:**
- Test Team verifies test data is available before running integration tests
- Test Team verifies test fixtures are ready
- Test Team verifies test data cleanup works

---

## Summary

**Mock Fixtures (Unit Tests):**
- **Responsible:** Dev Agent
- **When:** During task implementation (TDD)
- **Location:** Inline or `tests/unit/fixtures/`

**Real Test Data (Integration Tests):**
- **Responsible:** Dev Agent (creates), Test Team (validates)
- **When:** During task implementation
- **Location:** `tests/fixtures/` or `tests/integration/fixtures/`

**Shared Fixtures:**
- **Responsible:** TEA Agent / Test Team
- **When:** During framework setup / ATDD
- **Location:** `tests/support/fixtures/`

**Integration Test Patterns:**
- **Responsible:** Test Team / TEA Agent
- **When:** During Epic grooming
- **Location:** `_bmad-output/implementation-artifacts/integration-test-patterns-epic-{n}.md`

**Data Factories:**
- **Framework:** TEA Agent (during framework setup)
- **Story-Specific:** Dev Agent (during story implementation)
- **Location:** `tests/support/factories/` or `tests/fixtures/factories/`

---

## References

- **Testing Strategy:** `_bmad/bmm/testarch/procedures/testing-strategy.md`
- **System Readiness:** `_bmad/bmm/testarch/procedures/system-readiness.md`
- **QA Workflow:** `_bmad/bmm/testarch/procedures/qa-workflow.md`
- **Data Factories Knowledge:** `_bmad/bmm/testarch/knowledge/data-factories.md`
- **Fixture Architecture Knowledge:** `_bmad/bmm/testarch/knowledge/fixture-architecture.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-08  
**Owner:** Test Team / TEA Agent  
**Review Frequency:** Quarterly
