
# System Readiness & Dependency Management for Integration Tests

## Purpose

This procedure establishes clear responsibility for ensuring all dependency systems are running and ready before conducting integration tests. This prevents test failures due to missing services and ensures reliable test execution.

## Scope

This procedure applies to:
- Integration test execution (Dev and Test Team)
- Pre-testing system verification
- Dependency service management
- Test environment readiness

## Critical Rule

**Integration tests require real services to be running. The agent/team member running integration tests is responsible for ensuring all required dependency systems are operational before test execution.**

---

## Responsibility Assignment

### Primary Responsibility: Test Team / TEA Agent

**The Test Team / TEA Agent is the PRIMARY responsible party for ensuring system readiness before integration test validation.**

**Rationale:**
- Test Team validates work after Dev completes it
- Test Team needs reliable test environment for validation
- Test Team has final say on test pass/fail
- Test Team should verify environment before running tests

**Test Team Responsibilities:**
1. **Before Task Validation:**
   - Verify all required backend services are running
   - Verify database/test data is available
   - Verify external dependencies (MCP servers, APIs) are accessible
   - Verify environment variables are configured correctly
   - Run system health checks
   - Document any service issues in test results

2. **Before Story Validation:**
   - Verify all required services for the story are running
   - Verify integration test patterns are available
   - Verify test fixtures are ready
   - Run comprehensive system readiness check

3. **If Services Are Not Running:**
   - **Option 1:** Start services using project scripts/tools
   - **Option 2:** Document service unavailability and create blocker
   - **Option 3:** Request Dev to start services (if Dev has access)
   - **Never:** Run integration tests with services down and claim tests pass

### Secondary Responsibility: Dev Agent

**The Dev Agent is responsible for ensuring system readiness when running integration tests during development.**

**Dev Responsibilities:**
1. **Before Running Integration Tests:**
   - Verify required services are running
   - Start services if needed (using project scripts)
   - Verify test data is available
   - Run quick health check

2. **Before Marking Task "In Testing" (79):**
   - Ensure integration tests pass with real services
   - Document any service dependencies in task comments
   - Note any special service requirements

3. **Service Management:**
   - Use project scripts to start/stop services
   - Document service startup procedures
   - Report service issues to team

---

## System Readiness Checklist

### Pre-Integration Test Checklist

**Before running ANY integration tests, verify:**

- [ ] **Backend Services:**
  - [ ] REST API server running (if required)
  - [ ] Main RAG backend running (if required)
  - [ ] MCP servers running (if required)
  - [ ] Database server running (if required)
  - [ ] Redis server running (if required)
  - [ ] Meilisearch running (if required)
  - [ ] Other required services running

- [ ] **Service Health:**
  - [ ] All services respond to health checks
  - [ ] Services are accessible from test environment
  - [ ] Network connectivity verified
  - [ ] Ports are not blocked

- [ ] **Test Data:**
  - [ ] Test database is available
  - [ ] Test data fixtures are loaded
  - [ ] Test indices are created (if required)
  - [ ] Test tenants are configured (if required)

- [ ] **Configuration:**
  - [ ] Environment variables set correctly
  - [ ] Test configuration files present
  - [ ] Service URLs/endpoints configured
  - [ ] Authentication credentials available (if required)

- [ ] **Integration Test Patterns:**
  - [ ] Integration test pattern file available (if epic-level patterns used)
  - [ ] Test fixtures available in `tests/fixtures/`
  - [ ] Test helpers/utilities available

---

## Service Startup Procedures

### Standard Service Startup

**Use project scripts for service management:**

```bash
# Check service status
./scripts/check_services.py

# Start all required services
./scripts/start_services.sh

# Start specific service
docker compose up -d <service-name>

# Verify service health
curl http://localhost:<port>/health
```

### Service Verification Commands

**Before running integration tests, verify services:**

```bash
# Check if services are running
docker compose ps

# Check service health endpoints
curl http://localhost:8000/health  # REST proxy
curl http://localhost:8001/health  # Main RAG backend
curl http://localhost:6379         # Redis (if applicable)

# Check MCP server availability
# (Use MCP client tools to verify connection)
```

---

## Workflow Integration

### Dev Agent Workflow

**When Dev runs integration tests:**

```
1. Check if services are running
   ↓
2. If services down → Start services using scripts
   ↓
3. Verify service health
   ↓
4. Run integration tests
   ↓
5. Document service status in task comments
```

**Example Task Comment:**
```
Integration tests completed:
- Services verified: REST API (8000), RAG Backend (8001), Redis (6379)
- All integration tests passing
- Service health: All services operational
```

### Test Team / TEA Agent Workflow

**When Test Team validates:**

```
1. Review task/story requirements
   ↓
2. Identify required services
   ↓
3. Verify all services are running
   ↓
4. If services down → Start services OR create blocker
   ↓
5. Run integration test suite
   ↓
6. Document service status in validation results
```

**Example Validation Comment:**
```
Task validation completed:
- Services verified: All required services running
- Integration tests: 12/12 passing
- Service health: All services operational
- Validation: PASSED
```

---

## Failure Scenarios

### Scenario 1: Services Not Running

**When:** Test Team finds services are down

**Actions:**
1. **Attempt to start services:**
   ```bash
   ./scripts/start_services.sh
   ```

2. **If startup fails:**
   - Document service issue
   - Create blocker work package in OpenProject
   - Assign to appropriate team member (Dev/Infrastructure)
   - Mark validation as "Blocked" (status 83)

3. **If startup succeeds:**
   - Verify service health
   - Proceed with integration tests
   - Document service restart in validation results

### Scenario 2: Service Unavailable

**When:** Required service is not available (e.g., external API down)

**Actions:**
1. Document service unavailability
2. Check if service is critical for validation
3. **If critical:**
   - Create blocker work package
   - Mark validation as "Blocked" (status 83)
   - Wait for service availability
4. **If not critical:**
   - Document limitation in validation results
   - Proceed with available tests
   - Note missing test coverage

### Scenario 3: Service Configuration Issues

**When:** Services are running but misconfigured

**Actions:**
1. Document configuration issue
2. Check configuration files
3. **If fixable:**
   - Fix configuration
   - Restart services
   - Verify health
   - Proceed with tests
4. **If not fixable:**
   - Create bug work package
   - Document configuration issue
   - Assign to Dev/Infrastructure

---

## Integration with Existing Procedures

### Testing Strategy Integration

**Reference:** `_bmad/bmm/testarch/procedures/testing-strategy.md`

**Updated Dev Agent Responsibilities:**
- ✅ Write integration tests (with real services)
- ✅ **Verify services are running before running integration tests**
- ✅ **Start services if needed**
- ✅ Run integration tests
- ✅ Document service status

**Updated Test Team Responsibilities:**
- ✅ **Verify all required services are running before validation**
- ✅ **Start services if needed OR create blocker**
- ✅ Run integration test suite (with real services)
- ✅ Document service status in validation results

### QA Workflow Integration

**Reference:** `_bmad/bmm/testarch/procedures/qa-workflow.md`

**Updated Task Validation Checklist:**
- [ ] **All required services verified and running**
- [ ] Task implementation reviewed
- [ ] Unit tests pass (with mocks)
- [ ] Integration tests pass (with real services)
- [ ] Acceptance criteria met

**Updated Story Validation Checklist:**
- [ ] **All required services verified and running**
- [ ] All tasks closed
- [ ] All acceptance criteria met
- [ ] Unit tests pass (with mocks)
- [ ] Integration tests pass (with real services)

### Browser Testing Integration

**Reference:** `_bmad/bmm/testarch/procedures/browser-testing.md`

**Pre-Testing Checklist (already includes):**
- [ ] All backend services are running (if required)
- [ ] Frontend development server is running
- [ ] Database/test data is available (if required)

**Responsibility:** QA/UX team member conducting browser testing

---

## Service Health Check Scripts

### Recommended Project Scripts

**Create these scripts in your project:**

1. **`scripts/check_services.py`**
   - Check all required services
   - Verify health endpoints
   - Report service status

2. **`scripts/start_services.sh`**
   - Start all required services
   - Wait for health checks
   - Report startup status

3. **`scripts/stop_services.sh`**
   - Stop all services gracefully
   - Clean up test data (optional)

**Example `check_services.py`:**
```python
#!/usr/bin/env python3
"""Check if all required services are running."""

import requests
import sys

SERVICES = {
    "REST Proxy": "http://localhost:8000/health",
    "RAG Backend": "http://localhost:8001/health",
    "Redis": "redis://localhost:6379",
}

def check_service(name, url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: Running")
            return True
        else:
            print(f"❌ {name}: Not healthy (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: Not accessible ({e})")
        return False

def main():
    all_healthy = True
    for name, url in SERVICES.items():
        if not check_service(name, url):
            all_healthy = False
    
    if not all_healthy:
        print("\n⚠️  Some services are not running. Start services before running integration tests.")
        sys.exit(1)
    else:
        print("\n✅ All services are running and healthy.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## Best Practices

### 1. Always Verify Before Testing

**✅ Good:**
```bash
# Verify services before running tests
./scripts/check_services.py
pytest tests/integration/
```

**❌ Bad:**
```bash
# Run tests without checking
pytest tests/integration/  # May fail due to missing services
```

### 2. Document Service Status

**✅ Good:**
```
Integration tests: 12/12 passing
Services verified: REST API (8000), RAG Backend (8001), Redis (6379)
All services operational
```

**❌ Bad:**
```
Integration tests: 12/12 passing
```

### 3. Create Blockers for Service Issues

**✅ Good:**
- Service unavailable → Create blocker → Wait for fix
- Document blocker in validation results

**❌ Bad:**
- Service unavailable → Run tests anyway → Claim tests pass

### 4. Use Project Scripts

**✅ Good:**
- Use standardized scripts for service management
- Consistent service startup across team

**❌ Bad:**
- Manual service startup (error-prone)
- Different procedures for each team member

---

## Escalation

### If Services Cannot Be Started

1. **Document the issue** in validation results
2. **Create blocker work package** in OpenProject
3. **Assign to appropriate team member:**
   - Dev: If service code issue
   - Infrastructure: If deployment/environment issue
   - PM: If external dependency issue
4. **Mark validation as "Blocked" (status 83)**
5. **Wait for resolution** before proceeding

---

## Summary

**Primary Responsibility:** Test Team / TEA Agent
- Verify services before validation
- Start services if needed
- Create blockers if services unavailable

**Secondary Responsibility:** Dev Agent
- Verify services before running integration tests
- Start services if needed
- Document service status

**Key Principle:** The agent running integration tests is responsible for ensuring system readiness. Never run integration tests with services down and claim tests pass.

---

## References

- **Testing Strategy:** `_bmad/bmm/testarch/procedures/testing-strategy.md`
- **QA Workflow:** `_bmad/bmm/testarch/procedures/qa-workflow.md`
- **Browser Testing:** `_bmad/bmm/testarch/procedures/browser-testing.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-08  
**Owner:** Test Team / TEA Agent  
**Review Frequency:** Quarterly
