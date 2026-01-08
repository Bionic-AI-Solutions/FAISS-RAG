#!/usr/bin/env python3
"""
Create all Admin UI stories in OpenProject.
"""

import json
import sys
from pathlib import Path

# Read epics.md to extract story details
epics_file = Path("_bmad-output/planning-artifacts/epics.md")
if not epics_file.exists():
    print(f"Error: {epics_file} not found")
    sys.exit(1)

# Epic IDs from OpenProject
EPIC_10_ID = 755
EPIC_11_ID = 756
EPIC_12_ID = 757

# Story type and priority
STORY_TYPE_ID = 41
PRIORITY_HIGH = 74

# Stories to create
stories = [
    # Epic 10 stories
    {
        "epic_id": EPIC_10_ID,
        "subject": "Story 10.2: REST Proxy Backend Setup & MCP Integration",
        "description": """As a **Developer**,
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
**And** Error responses from MCP tools are properly handled and returned""",
    },
    {
        "epic_id": EPIC_10_ID,
        "subject": "Story 10.3: OAuth 2.0 Authentication Integration",
        "description": """As a **User**,
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
**And** Token expiration is handled gracefully""",
    },
    {
        "epic_id": EPIC_10_ID,
        "subject": "Story 10.4: RBAC Middleware & Role-Based UI Rendering",
        "description": """As a **User**,
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
**And** Unauthorized actions show appropriate error messages""",
    },
    {
        "epic_id": EPIC_10_ID,
        "subject": "Story 10.5: Base Layout Components (Sidebar, Header, Breadcrumbs)",
        "description": """As a **User**,
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
**And** Layout follows design system spacing and typography""",
    },
    {
        "epic_id": EPIC_10_ID,
        "subject": "Story 10.6: Session Management & Tenant Context Handling",
        "description": """As a **Uber Admin**,
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
**And** Context switch is persisted in session""",
    },
    {
        "epic_id": EPIC_10_ID,
        "subject": "Story 10.T: Admin UI Foundation Test Story",
        "description": """As a **QA Engineer**,
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
**And** All components follow design system guidelines""",
    },
]

print(json.dumps(stories, indent=2))
