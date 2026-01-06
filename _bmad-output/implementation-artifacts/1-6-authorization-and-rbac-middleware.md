# Story 1.6: Authorization & RBAC Middleware

Status: done

## Story

As a **Platform Operator**,
I want **four-tier RBAC with role-based access control implemented**,
So that **users can only access resources permitted by their role**.

## Acceptance Criteria

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

## Tasks / Subtasks

- [x] Task 1: Define RBAC Roles and Permissions (AC: RBAC structure)
  - [x] Create role enum/constants (Uber Admin, Tenant Admin, Project Admin, End User)
  - [x] Define permission structure for each role
  - [x] Create tool permission mapping (which tools each role can access)
  - [x] Document role capabilities and restrictions
  - [x] Add role to User model if not already present

- [x] Task 2: Implement Role Permission Checking (AC: Role-based access logic)
  - [x] Create permission checking functions
  - [x] Implement Uber Admin permission checks (full platform access)
  - [x] Implement Tenant Admin permission checks (tenant-scoped access)
  - [x] Implement End User permission checks (read-only, user-scoped)
  - [x] Implement Project Admin permission checks (Phase 2 - placeholder)
  - [x] Create authorization error exception (403 Forbidden, FR-ERROR-003)

- [x] Task 3: Create Authorization Middleware (AC: Middleware integration)
  - [x] Create authorization middleware in app/mcp/middleware/authorization.py
  - [x] Extract role from authenticated context
  - [x] Check tool permissions before execution
  - [x] Prevent tool execution on authorization failure
  - [x] Integrate with authentication middleware (execute after auth)
  - [x] Store authorization context for downstream use

- [x] Task 4: Integrate Audit Logging for Authorization (AC: Audit logs)
  - [x] Log role and permission checks
  - [x] Log authorization successes
  - [x] Log authorization failures with reason
  - [x] Include tool name and role in audit log
  - [x] Test audit log creation for authorization events

- [x] Task 5: Add Authorization Configuration (AC: All)
  - [x] Create app/config/authorization.py with RBAC settings
  - [x] Configure role permissions mapping
  - [x] Add environment variables for authorization settings
  - [x] Document configuration in docs/AUTHORIZATION_CONFIGURATION.md

- [x] Task 6: Add Authorization Tests (AC: All)
  - [x] Create unit tests for role permission checking
  - [x] Create unit tests for authorization middleware
  - [x] Create integration tests for RBAC enforcement
  - [x] Test unauthorized access returns 403 Forbidden
  - [x] Test role-based tool access restrictions
  - [x] Test audit logging for authorization
  - [x] Verify all tests pass (40 tests, all passing)

- [x] Task 7: Verify Story Implementation (AC: All)
  - [x] Verify RBAC roles are properly defined
  - [x] Verify permission checking works correctly
  - [x] Verify middleware executes after authentication
  - [x] Verify authorization failures prevent tool execution
  - [x] Verify audit logs capture authorization events
  - [x] Verify all acceptance criteria are met
  - [x] Verify code follows architecture patterns

