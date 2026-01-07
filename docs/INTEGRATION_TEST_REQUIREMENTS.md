# Integration Test Requirements for Epic Completion

## CRITICAL RULE

**Epics can ONLY be closed after integration tests pass.**

## Epic Closure Prerequisites

Before an Epic can be marked as "Closed" (status 82) in OpenProject, ALL of the following must be satisfied:

1. ✅ **All stories are "Closed" (82)**
2. ✅ **All tasks in all stories are "Closed" (82)**
3. ✅ **All bugs in all stories are "Closed" (82)**
4. ✅ **Integration tests pass** (`pytest tests/integration/test_epic{epic_number}_*.py -v`)
5. ✅ **Test documentation created and attached**

## Integration Test Requirements

### Test Location

Integration tests for an epic should be located in:
```
tests/integration/test_epic{epic_number}_{feature}.py
```

Example:
- Epic 4: `tests/integration/test_epic4_search_workflows.py`
- Epic 2: `tests/integration/test_epic2_tenant_registration.py`

### Test Execution

Before closing an epic, run:

```bash
# Run all integration tests for the epic
pytest tests/integration/test_epic{epic_number}_*.py -v

# Example for Epic 4:
pytest tests/integration/test_epic4_*.py -v
```

### Test Requirements

Integration tests MUST:

1. **Use real services** - No mocks for external services (database, Redis, MinIO, Meilisearch, FAISS)
2. **Use MCP tools** - Register tenants using `rag_register_tenant` MCP tool (Epic 2)
3. **Test end-to-end workflows** - Verify complete functionality, not just individual components
4. **Verify acceptance criteria** - All story acceptance criteria must be validated
5. **Test performance** - Verify performance requirements are met (where applicable)
6. **Test tenant isolation** - Verify multi-tenant isolation (where applicable)

### Test Environment Setup

Integration tests require:

- ✅ Database connection (PostgreSQL)
- ✅ Redis connection
- ✅ MinIO connection (for file storage)
- ✅ Meilisearch connection (for keyword search)
- ✅ FAISS setup (for vector search)
- ✅ OpenAI API key OR GPU-AI MCP server (for embedding generation)

### Async Event Loop Configuration

**CRITICAL:** Integration tests MUST use session-scoped event loops to avoid `RuntimeError: Task got Future attached to a different loop`.

**Required Setup:**

1. **Create `tests/integration/conftest.py`:**
   ```python
   @pytest.fixture(scope="session")
   def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
       """Create a session-scoped event loop for integration tests."""
       policy = asyncio.get_event_loop_policy()
       loop = policy.new_event_loop()
       asyncio.set_event_loop(loop)
       yield loop
       loop.close()
   
   @pytest_asyncio.fixture(scope="session")
   async def test_db_engine(event_loop) -> AsyncEngine:
       """Create a session-scoped database engine with NullPool."""
       engine = create_async_engine(
           database_url,
           poolclass=NullPool,  # Avoids event loop conflicts
           echo=False,
       )
       yield engine
       await engine.dispose()
   ```

2. **Update `pyproject.toml`:**
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   asyncio_default_fixture_loop_scope = "session"
   markers = [
       "integration: marks tests as integration tests",
   ]
   ```

3. **Use NullPool for database connections:**
   - Avoids connection pool sharing across event loops
   - Each database operation gets a fresh connection
   - Connection closed immediately after use

**Reference:** See `docs/EPIC_4_INTEGRATION_TEST_FIXES.md` for complete implementation details.

### Test Execution Workflow

1. **Before closing epic:**
   ```bash
   # 1. Ensure all services are running
   docker compose -f docker/docker-compose.yml up -d
   
   # 2. Run migrations
   alembic upgrade head
   
   # 3. Run integration tests
   pytest tests/integration/test_epic{epic_number}_*.py -v
   
   # 4. Verify all tests pass
   # If any test fails, fix issues and iterate
   ```

2. **After all tests pass:**
   - Create/update test documentation
   - Attach test documentation to epic in OpenProject
   - Close epic (status 82)

### Test Documentation

For each epic, create:

- **Test Plan:** `docs/epic{epic_number}_test_plan.md`
- **Test Results:** `docs/epic{epic_number}_test_results.md`
- **Verification Report:** `docs/epic{epic_number}_verification.md`

Attach these documents to the epic in OpenProject using:
```python
mcp_openproject_add_work_package_attachment(
    work_package_id=epic_id,
    file_data=base64_encoded_doc,
    filename="epic{epic_number}_verification.md",
    content_type="text/markdown"
)
```

## Integration with BMAD Workflow

This requirement is integrated into:

- **`.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`** - Epic closure rules
- **`.cursor/rules/bmad/bmm/workflows/test-validation.mdc`** - Test validation workflow

## References

- **Epic Story Lifecycle:** `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`
- **Test Validation Workflow:** `.cursor/rules/bmad/bmm/workflows/test-validation.mdc`
- **Database Connection Setup:** `docs/EPIC_4_TESTING_PRIORITY.md`

