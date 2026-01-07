---
document_type: ux-design-specification
title: Admin UI Design Specification - FAISS-RAG System
author: Sally (UX Designer) with John (PM) and Winston (Architect)
date: 2026-01-04
status: approved
version: 1.0
workflow_source: party-mode-discussion
---

# Admin UI Design Specification - FAISS-RAG System

## Executive Summary

This document defines the design specification for the Admin UI of the FAISS-RAG System with Mem0. The UI provides role-based administration capabilities for Uber Admins (platform-level) and Tenant Admins (tenant-level), with a unified interface architecture that allows Uber Admins to seamlessly switch between platform and tenant contexts.

**Key Design Decision**: Single unified admin UI with role-based views, where Uber Admin interface is a superset of Tenant Admin interface, enabling Uber Admins to help tenants directly without switching tools.

---

## Design Principles

1. **Role-Based Access**: UI adapts based on user role (Uber Admin, Tenant Admin, Project Admin)
2. **Unified Architecture**: Single codebase with role-based feature flags
3. **Context Switching**: Uber Admins can switch between platform view and tenant-specific views
4. **Visual Clarity**: Clear indicators of current role and context
5. **Consistent UX**: Shared components and patterns across all roles
6. **Scalable Design**: Architecture supports adding Project Admin and End User views in future phases

---

## User Personas & Use Cases

### Persona 1: Alex Chen - Uber Admin (Platform Level)

**Role**: Platform administrator managing entire RAG infrastructure across all tenants

**Key Use Cases**:
- Onboard new tenants (<5 minutes target)
- Monitor platform health across all tenants
- View cross-tenant analytics and metrics
- Manage platform-wide configurations
- Access audit logs across all tenants
- Help individual tenants when issues arise
- Manage subscription tiers and billing (post-MVP)

**Journey Reference**: Journey 13 from PRD

### Persona 2: Lisa Thompson - Tenant Admin

**Role**: Healthcare organization administrator managing her tenant's knowledge base and configurations

**Key Use Cases**:
- Upload and manage documents (multi-modal: text, images, tables)
- Configure tenant-specific models and settings
- Ensure HIPAA compliance
- Monitor tenant usage and analytics
- Manage Project Admins and End Users within tenant
- View tenant-specific audit logs
- Manage tenant backups and restore operations

**Journey Reference**: Journey 14 from PRD

### Persona 3: Pat Williams - Support Troubleshooter

**Role**: Support engineer troubleshooting tenant issues

**Key Use Cases**:
- Investigate tenant configuration issues
- Review system logs and observability data
- Identify root causes of search accuracy problems
- Update tenant configurations to resolve issues
- Document solutions for future reference

**Journey Reference**: Journey 16 from PRD

---

## UI Architecture

### Single Unified Admin UI

**Architecture Pattern**:
```
UI Layer (Role-Based Views)
  ↓
REST Proxy Backend (Role Context + Tenant Context)
  ↓
MCP Tools (tenant_id parameter)
  ↓
RBAC Middleware (validates role + tenant access)
```

**Technology Stack** (Recommended):
- **Frontend**: React/Next.js with TypeScript
- **Backend**: FastAPI REST proxy (calls MCP tools)
- **State Management**: React Context/Redux for role and tenant context
- **UI Framework**: Material-UI or Tailwind CSS + Headless UI
- **Authentication**: OAuth 2.0 with role-based token claims

---

## Navigation Structure

### Uber Admin Navigation (Superset View)

```
Uber Admin Navigation:
├── Platform Dashboard (Uber Admin only)
│   └── Overview of all tenants, platform health, cross-tenant metrics
├── Tenant Management (Uber Admin only)
│   ├── Tenant List (all tenants)
│   ├── Create New Tenant
│   └── [Select Tenant] → Switches to Tenant Admin view for that tenant
├── Platform Analytics (Uber Admin only)
│   └── Cross-tenant analytics, system-wide metrics
├── Platform Settings (Uber Admin only)
│   └── System-wide configurations, subscription tiers, billing
├── All Audit Logs (Uber Admin only)
│   └── Query across all tenants with tenant filter
└── [When in Tenant Context - Shows Tenant Admin Navigation]:
    ├── Tenant Dashboard (shared with Tenant Admin)
    ├── Document Management (shared)
    ├── Configuration (shared)
    ├── Analytics (shared)
    ├── User Management (shared)
    ├── Audit Logs (shared)
    └── [Exit Tenant Context] button → Returns to Platform view
```

### Tenant Admin Navigation (Base View)

```
Tenant Admin Navigation:
├── Tenant Dashboard
│   └── Overview of tenant health, usage stats, recent activity
├── Document Management
│   ├── Upload Documents (drag-and-drop, multi-modal support)
│   ├── Document List (with search, filters, pagination)
│   ├── Document Viewer
│   └── Document Actions (update, delete, version history)
├── Configuration
│   ├── Model Settings (embedding models, domain-specific configs)
│   ├── Compliance Profiles (HIPAA, PCI DSS, GDPR)
│   ├── Rate Limits & Quotas
│   └── Template Management
├── Analytics & Reporting
│   ├── Usage Statistics
│   ├── Search Analytics
│   ├── Memory Analytics
│   └── Performance Metrics
├── User Management
│   ├── Project Admins
│   ├── End Users
│   └── Role Assignments
└── Audit Logs
    └── Tenant-specific audit logs with filtering
```

---

## Key UI Components & Features

### 1. Base Layout (All Roles)

**Components**:
- **Navigation Sidebar**: Role-appropriate sections, collapsible
- **Header Bar**: 
  - Current role indicator
  - Tenant context (if applicable)
  - User profile menu
  - Notifications (if any)
- **Breadcrumbs**: Navigation context
- **Main Content Area**: Role-based views

**Visual Design**:
- Clean, professional interface
- Consistent color scheme and typography
- Responsive design (desktop-first, mobile-responsive)
- Accessible (WCAG 2.1 AA compliance)

### 2. Tenant Context Switcher (Uber Admin Only)

**Location**: Header bar, prominent placement

**Functionality**:
- Dropdown showing all tenants
- Search/filter capability for large tenant lists
- "Switch to Tenant View" action
- Visual indicator when in tenant context

**Visual Indicator**:
- Banner/Alert: "🔧 Uber Admin Mode - Viewing: [Tenant Name]"
- "Exit to Platform View" button
- Different background color or border to indicate context switch

### 3. Platform Dashboard (Uber Admin)

**Key Metrics Display**:
- Total tenants count
- Active tenants (last 24 hours)
- Platform health status (overall)
- Total searches (last 24 hours, 7 days, 30 days)
- System resource utilization
- Recent tenant onboarding activity
- Critical alerts/issues

**Visualizations**:
- Tenant health status grid/cards
- Platform usage trends (line charts)
- Tenant distribution by domain (pie chart)
- System component health indicators

### 4. Tenant Dashboard (Tenant Admin & Uber Admin in Tenant Context)

**Key Metrics Display**:
- Tenant health status
- Usage statistics (searches, memory operations, document count)
- Recent activity feed
- Compliance status indicators
- Storage usage
- Rate limit status

**Quick Actions**:
- Upload Document
- View Analytics
- Manage Configuration
- View Audit Logs

### 5. Document Management

**Upload Interface**:
- Drag-and-drop zone
- File browser
- Multi-file upload support
- Progress indicators
- File type validation
- Preview before upload

**Document List**:
- Table/grid view with columns:
  - Document name
  - Type (text, image, table, audio, video)
  - Upload date
  - Status (processing, indexed, error)
  - Size
  - Actions (view, update, delete)
- Search and filter capabilities
- Pagination
- Bulk actions (delete multiple)

**Document Viewer**:
- Full document preview
- Metadata display
- Version history
- Related documents
- Search within document

### 6. Configuration Management

**Form-Based Interface**:
- Model Settings:
  - Embedding model selection
  - Domain-specific model configuration
  - Model parameters (temperature, top_p, etc.)
- Compliance Profiles:
  - Template selection (fintech, healthcare, retail)
  - Compliance requirement checkboxes
  - Custom compliance settings
- Rate Limits & Quotas:
  - Requests per minute
  - Storage limits
  - Search quotas
  - Burst allowances
- Template Management:
  - Available templates
  - Template customization
  - Template preview

**Validation**:
- Real-time validation
- Error messages
- Save confirmation
- Change history

### 7. Analytics & Reporting

**Dashboard Views**:
- Usage Statistics:
  - Searches over time
  - Memory operations
  - Document operations
  - User activity
- Search Analytics:
  - Query performance
  - Response times
  - Result relevance scores
  - Popular queries
- Memory Analytics:
  - Memory usage by user
  - Memory effectiveness metrics
  - Memory growth trends
- Performance Metrics:
  - API response times
  - System latency
  - Error rates

**Visualizations**:
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distributions
- Heatmaps for activity patterns
- Export capabilities (CSV, PDF)

### 8. Tenant Management (Uber Admin Only)

**Tenant List**:
- Table view with columns:
  - Tenant name/ID
  - Domain (fintech, healthcare, retail)
  - Status (active, inactive, suspended)
  - Created date
  - Last activity
  - Subscription tier
  - Actions (view, edit, delete, switch context)
- Search and filter
- Sort capabilities
- Bulk actions

**Create Tenant**:
- Multi-step wizard:
  1. Basic Information (name, domain, contact)
  2. Template Selection
  3. Initial Configuration
  4. Review & Create
- Template preview
- Validation at each step

**Tenant Details**:
- Full tenant information
- Configuration overview
- Usage statistics
- Health status
- "Switch to Tenant View" button

### 9. Audit Logs

**Query Interface**:
- Filter options:
  - Date range (timestamp)
  - Actor (user_id, tenant_id, role)
  - Action type
  - Resource
  - Result status (success, error)
  - Metadata fields
- Search capability
- Pagination (cursor-based or limit/offset)

**Results Display**:
- Table view with columns:
  - Timestamp
  - Actor
  - Action
  - Resource
  - Result
  - Metadata (expandable)
- Export capabilities
- Detail view for individual log entries

**Access Control**:
- Tenant Admin: Only their tenant's logs
- Uber Admin: All tenants' logs with tenant filter

### 10. User Management (Tenant Admin)

**User List**:
- Table view showing:
  - User name/ID
  - Role (Project Admin, End User)
  - Email
  - Last activity
  - Assigned projects
  - Actions (edit, delete, assign projects)
- Search and filter
- Role-based filtering

**User Actions**:
- Create new user
- Assign roles
- Assign to projects
- Deactivate user
- View user activity

---

## Role-Based Access Control (UI Level)

### Uber Admin Permissions

**Platform-Level Access**:
- ✅ View Platform Dashboard
- ✅ Manage all tenants (create, update, delete)
- ✅ View cross-tenant analytics
- ✅ Access all audit logs
- ✅ Manage platform settings
- ✅ View system health (all components)

**Tenant-Level Access** (via context switch):
- ✅ All Tenant Admin permissions for any tenant
- ✅ Can switch tenant context
- ✅ Can help tenants directly

### Tenant Admin Permissions

**Tenant-Level Access**:
- ✅ View Tenant Dashboard (their tenant only)
- ✅ Manage documents (their tenant)
- ✅ Configure tenant settings
- ✅ View tenant analytics
- ✅ Manage users (Project Admins, End Users)
- ✅ View tenant audit logs
- ✅ Manage tenant backups

**Restrictions**:
- ❌ Cannot access other tenants
- ❌ Cannot view platform-wide metrics
- ❌ Cannot create/delete tenants
- ❌ Cannot access other tenants' audit logs

---

## MVP Scope (Phase 1)

### Must-Have Features

1. **Authentication & Authorization**
   - OAuth 2.0 login
   - Role-based access control
   - Session management

2. **Tenant Admin Core Features**
   - Tenant Dashboard
   - Document Management (upload, list, view, delete)
   - Basic Configuration (model settings, compliance)
   - Basic Analytics (usage stats, search analytics)
   - User Management (list, create, assign roles)

3. **Uber Admin Core Features**
   - Platform Dashboard
   - Tenant Management (list, create, view details)
   - Tenant Context Switcher
   - Basic Platform Analytics
   - Access to Tenant Admin features via context switch

4. **Base Infrastructure**
   - REST Proxy Backend (FastAPI)
   - MCP Tool Integration
   - Role-based UI routing
   - Responsive layout

### Nice-to-Have (Phase 2)

- Advanced Analytics (cross-tenant, detailed metrics)
- Audit Logs UI (query interface)
- Advanced Configuration (templates, custom settings)
- Backup Management UI
- Troubleshooting Tools (observability dashboard)
- Project Admin View
- End User View (read-only)

---

## Technical Implementation Details

### Backend Architecture

**REST Proxy Service**:
- FastAPI application
- Endpoints mirror MCP tool capabilities
- Session management (role, tenant_context)
- Authentication middleware
- RBAC validation before MCP calls
- Error handling and logging

**MCP Integration**:
- MCP client library
- Tool calls with tenant_id parameter
- Response transformation for UI consumption
- Error handling and retry logic

**Session Management**:
```python
session = {
    "user_id": "...",
    "role": "uber_admin" | "tenant_admin",
    "tenant_id": "...",  # For tenant admin
    "tenant_context": "...",  # For uber admin when in tenant mode
    "permissions": [...]
}
```

### Frontend Architecture

**Component Structure**:
```
src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── Breadcrumbs.tsx
│   ├── dashboard/
│   │   ├── PlatformDashboard.tsx
│   │   └── TenantDashboard.tsx
│   ├── documents/
│   │   ├── DocumentList.tsx
│   │   ├── DocumentUpload.tsx
│   │   └── DocumentViewer.tsx
│   ├── configuration/
│   │   ├── ModelSettings.tsx
│   │   ├── ComplianceSettings.tsx
│   │   └── RateLimits.tsx
│   ├── analytics/
│   │   ├── UsageStats.tsx
│   │   ├── SearchAnalytics.tsx
│   │   └── MemoryAnalytics.tsx
│   ├── tenants/
│   │   ├── TenantList.tsx
│   │   ├── TenantCreate.tsx
│   │   └── TenantDetails.tsx
│   └── shared/
│       ├── TenantContextSwitcher.tsx
│       ├── RoleIndicator.tsx
│       └── DataTable.tsx
├── contexts/
│   ├── AuthContext.tsx
│   ├── TenantContext.tsx
│   └── RoleContext.tsx
├── services/
│   ├── api.ts (REST client)
│   ├── mcp-proxy.ts
│   └── auth.ts
└── routes/
    ├── PlatformRoutes.tsx (Uber Admin)
    ├── TenantRoutes.tsx (Tenant Admin)
    └── SharedRoutes.tsx
```

**State Management**:
- React Context for auth, role, tenant context
- Local state for component-specific data
- React Query for server state and caching

**Routing**:
- Role-based route protection
- Dynamic routes based on permissions
- Context-aware navigation

---

## User Experience Flows

### Flow 1: Uber Admin Onboarding New Tenant

1. Login as Uber Admin
2. Navigate to "Tenant Management"
3. Click "Create New Tenant"
4. Multi-step wizard:
   - Enter tenant information
   - Select domain template
   - Configure initial settings
   - Review and confirm
5. Tenant created successfully
6. Option to "Switch to Tenant View" to verify setup

### Flow 2: Tenant Admin Uploading Documents

1. Login as Tenant Admin
2. Navigate to "Document Management"
3. Click "Upload Documents"
4. Drag-and-drop or browse files
5. Select multiple files (text, images, tables)
6. Review file list
7. Click "Upload"
8. View upload progress
9. Documents appear in list when indexed
10. Can view, update, or delete documents

### Flow 3: Uber Admin Helping Tenant

1. Login as Uber Admin
2. Navigate to "Tenant Management"
3. Select tenant from list
4. Click "Switch to Tenant View"
5. Banner appears: "🔧 Uber Admin Mode - Viewing: Healthcare Tenant"
6. Can now access all Tenant Admin features for that tenant
7. Make necessary changes
8. Click "Exit to Platform View" when done

### Flow 4: Tenant Admin Viewing Analytics

1. Login as Tenant Admin
2. Navigate to "Analytics & Reporting"
3. View dashboard with key metrics
4. Select time range (24h, 7d, 30d)
5. View detailed charts and graphs
6. Export data if needed

---

## Visual Design Guidelines

### Color Scheme

**Primary Colors**:
- Primary: Blue (#1976D2) - Trust, professionalism
- Secondary: Green (#4CAF50) - Success, health
- Accent: Orange (#FF9800) - Alerts, attention

**Status Colors**:
- Success: Green (#4CAF50)
- Warning: Orange (#FF9800)
- Error: Red (#F44336)
- Info: Blue (#2196F3)

**Role Indicators**:
- Uber Admin: Purple accent (#9C27B0)
- Tenant Admin: Blue accent (#2196F3)
- Context Switch: Yellow accent (#FFC107)

### Typography

- **Headings**: Sans-serif, bold (e.g., Inter, Roboto)
- **Body**: Sans-serif, regular (e.g., Inter, Roboto)
- **Code/Monospace**: For technical data (e.g., Fira Code, Consolas)

### Spacing & Layout

- Consistent spacing scale (4px, 8px, 16px, 24px, 32px)
- Grid-based layout
- Responsive breakpoints:
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px

### Icons

- Consistent icon library (Material Icons or Heroicons)
- Clear visual hierarchy
- Accessible (proper ARIA labels)

---

## Accessibility Requirements

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios (4.5:1 for text)
- Focus indicators
- ARIA labels and roles
- Alternative text for images

---

## Performance Requirements

- Initial page load: < 2 seconds
- Dashboard data load: < 1 second
- Document upload: Real-time progress feedback
- Search/filter operations: < 500ms
- Chart rendering: < 1 second for 1000 data points

---

## Security Considerations

- All API calls authenticated
- Role-based UI rendering (don't show what user can't access)
- CSRF protection
- XSS prevention
- Secure session management
- HTTPS only
- Input validation and sanitization

---

## Testing Strategy

### Unit Tests
- Component rendering
- State management
- Utility functions
- API client methods

### Integration Tests
- Authentication flows
- Role-based access
- Tenant context switching
- Document upload/download
- Configuration updates

### E2E Tests
- Complete user journeys
- Cross-browser testing
- Role switching scenarios
- Error handling

---

## Success Metrics

### User Experience Metrics
- Time to onboard new tenant: < 5 minutes (target)
- Time to upload documents: < 2 minutes for 10 documents
- Time to find information: < 30 seconds
- User satisfaction score: > 4.5/5

### Technical Metrics
- Page load time: < 2 seconds
- API response time: < 500ms (p95)
- Error rate: < 0.1%
- Uptime: > 99.9%

---

## Next Steps & Implementation Plan

### Phase 1: MVP (Weeks 1-8)

**Week 1-2: Foundation**
- Set up frontend project (React/Next.js)
- Set up backend REST proxy (FastAPI)
- Implement authentication and RBAC
- Create base layout components

**Week 3-4: Tenant Admin Core**
- Tenant Dashboard
- Document Management (upload, list, view)
- Basic Configuration UI

**Week 5-6: Uber Admin Core**
- Platform Dashboard
- Tenant Management (list, create)
- Tenant Context Switcher

**Week 7-8: Polish & Testing**
- Analytics UI (basic)
- User Management
- Testing and bug fixes
- Documentation

### Phase 2: Enhanced Features (Post-MVP)

- Advanced Analytics
- Audit Logs UI
- Backup Management
- Troubleshooting Tools
- Project Admin View
- Mobile optimization

---

## Approval & Sign-off

**Approved by**:
- RAGLeader (Product Owner)
- Sally (UX Designer)
- John (Product Manager)
- Winston (Architect)

**Date**: 2026-01-04

**Status**: Ready for Implementation

---

## Appendix

### Related Documents
- PRD: `_bmad-output/planning-artifacts/prd.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- Party Mode Discussion: `_bmad-output/party-mode-session.md`

### MCP Tools Reference
All admin UI features map to existing MCP tools:
- `rag_list_tenants` - Tenant list
- `rag_get_tenant_info` - Tenant details
- `rag_create_tenant` - Create tenant
- `rag_update_tenant_config` - Update configuration
- `rag_get_usage_analytics` - Analytics
- `rag_list_documents` - Document list
- `rag_ingest` - Document upload
- `rag_query_audit_logs` - Audit logs
- And more...

See PRD Section "Core Capabilities (MCP Tools)" for complete list.




