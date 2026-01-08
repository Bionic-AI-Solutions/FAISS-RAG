# Epic 10: Integration Test Story

## Story 10.IT: Admin UI Foundation Integration Tests (Live Systems)

**As a** QA Engineer,  
**I want** to validate the Admin UI foundation with live systems and real services,  
**So that** I can ensure the REST proxy correctly integrates with MCP tools, authentication works with real OAuth providers, and the system works end-to-end.

---

## Acceptance Criteria

**Given** Admin UI foundation is implemented  
**When** I run integration tests with live systems  
**Then** REST proxy successfully calls live MCP tools (tenant management, document management)  
**And** OAuth 2.0 authentication flow works with real OAuth provider  
**And** JWT tokens are validated against real JWKS endpoint  
**And** Role-based access control works with real database/backend  
**And** Session management persists correctly across page reloads  
**And** Tenant context switching works with real tenant data  
**And** Error handling works for real service failures (MCP errors, network errors)  
**And** Performance requirements are met (<150ms p95 for API calls)  
**And** End-to-end user journeys work correctly (login → dashboard → navigation)  
**And** All integration tests pass with real services running

---

## Test Scope

### Integration Test Areas

1. **REST Proxy → MCP Integration**
   - Test real MCP tool calls (list_tenants, get_tenant, create_tenant)
   - Test real MCP tool calls (list_documents, ingest_document)
   - Test error handling for MCP failures
   - Test performance with real MCP responses

2. **OAuth 2.0 Integration**
   - Test real OAuth authorization flow
   - Test token exchange with real OAuth provider
   - Test JWT validation with real JWKS endpoint
   - Test token refresh flow

3. **RBAC Integration**
   - Test role-based access with real database
   - Test tenant isolation with real tenant data
   - Test permission enforcement with real backend

4. **Session Management Integration**
   - Test session persistence with real browser storage
   - Test session expiration handling
   - Test tenant context persistence

5. **End-to-End User Journeys**
   - Test complete login flow (OAuth → token → dashboard)
   - Test tenant admin journey (login → tenant dashboard → document upload)
   - Test uber admin journey (login → platform dashboard → tenant switching)

---

## Test Infrastructure Requirements

### Required Services
- ✅ Live MCP server running
- ✅ Live OAuth provider (or test OAuth server)
- ✅ Live backend API (FastAPI)
- ✅ Live database (PostgreSQL)
- ✅ Live frontend (Next.js dev server)

### Test Environment
- **Location**: `frontend/__tests__/integration/`
- **Framework**: Vitest with Playwright (for E2E) or Vitest with real HTTP client
- **Test Data**: Real test tenants, test users, test documents
- **Cleanup**: Remove test data after each test run

---

## Test Files Structure

```
frontend/
├── __tests__/
│   ├── unit/                    # ✅ Already created (unit tests with mocks)
│   │   ├── auth.test.tsx
│   │   ├── rbac.test.tsx
│   │   ├── tenant-context.test.tsx
│   │   └── components/
│   │       └── AppShell.test.tsx
│   │
│   └── integration/             # ❌ MISSING - Need to create
│       ├── auth.integration.test.tsx      # OAuth flow with real provider
│       ├── mcp-proxy.integration.test.tsx # REST proxy → MCP calls
│       ├── rbac.integration.test.tsx      # RBAC with real backend
│       ├── session.integration.test.tsx   # Session with real storage
│       └── e2e/
│           ├── tenant-admin-journey.test.tsx
│           └── uber-admin-journey.test.tsx
```

---

## Implementation Notes

### Integration Test Patterns

**From BMAD Testing Strategy:**
- Use real services (MCP server, OAuth provider, database)
- Test complete workflows (end-to-end user journeys)
- Validate performance (measure actual response times)
- Test with real data (realistic test data)
- Clean up after tests (remove test indices, clear test data)

### Example Integration Test

```typescript
// frontend/__tests__/integration/mcp-proxy.integration.test.tsx
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { mcpClient } from '@/app/lib/mcp-client';

describe('REST Proxy → MCP Integration', () => {
  beforeAll(async () => {
    // Ensure MCP server is running
    // Ensure test tenant exists
  });

  afterAll(async () => {
    // Clean up test tenant
  });

  it('should successfully call list_tenants MCP tool', async () => {
    const response = await fetch('/api/v1/tenants', {
      headers: { 'Authorization': `Bearer ${testToken}` }
    });
    const tenants = await response.json();
    expect(tenants).toBeDefined();
    expect(Array.isArray(tenants)).toBe(true);
  });

  it('should handle MCP errors correctly', async () => {
    // Test error handling for MCP failures
  });

  it('should meet performance requirements (<150ms p95)', async () => {
    const start = Date.now();
    await fetch('/api/v1/tenants', {
      headers: { 'Authorization': `Bearer ${testToken}` }
    });
    const duration = Date.now() - start;
    expect(duration).toBeLessThan(150);
  });
});
```

---

## Dependencies

- **Epic 10 Stories**: All stories must be implemented before integration tests
- **Live Services**: MCP server, OAuth provider, database must be running
- **Test Data**: Test tenants, test users must be created

---

## Status

**Current**: ❌ **NOT CREATED** - Integration test story missing  
**Required**: ✅ **MANDATORY** per BMAD testing strategy  
**Action**: Create Story 10.IT in OpenProject and implement integration tests
