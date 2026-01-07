# RBAC Roles and Permissions

**Last Updated:** 2026-01-06  
**Purpose:** Define the four-tier RBAC structure and role capabilities for the RAG system.

## Role Hierarchy

The system supports four roles in a hierarchical structure:

1. **Uber Admin** - Platform-level access across all tenants
2. **Tenant Admin** - Tenant-level access within their tenant
3. **Project Admin** - Project-scoped access within a tenant (Phase 2)
4. **End User** - User-level read-only access with user-scoped memory

## Role Definitions

### Uber Admin (`uber_admin`)

**Description:** Platform-level access across all tenants

**Capabilities:**
- Full platform access across all tenants
- Create, update, delete tenants
- View cross-tenant analytics and platform-wide metrics
- Manage platform-wide configurations and system settings
- Access all audit logs across tenants
- Manage subscription tiers and billing
- System-level disaster recovery and backup operations
- Access all MCP tools

**Restrictions:** None

**Use Cases:**
- Platform operators managing the entire system
- System administrators performing cross-tenant operations
- Support staff troubleshooting platform-wide issues

### Tenant Admin (`tenant_admin`)

**Description:** Tenant-level access within their tenant

**Capabilities:**
- Full tenant access within their tenant
- Configure tenant settings (models, compliance, templates, rate limits, quotas)
- Manage Project Admins and End Users within their tenant
- View tenant-wide usage stats, analytics, and audit logs
- Configure tenant-specific compliance profiles
- Manage tenant backups and restore operations
- Access tenant health monitoring and diagnostics
- Access tenant-scoped MCP tools

**Restrictions:**
- Cannot access other tenants' data
- Cannot perform platform-wide operations

**Use Cases:**
- Tenant administrators managing their organization's data
- IT administrators configuring tenant-specific settings
- Compliance officers reviewing tenant audit logs

### Project Admin (`project_admin`) - Phase 2

**Description:** Project-scoped access within a tenant

**Capabilities:**
- Project-scoped access within a tenant
- Manage knowledge bases for specific projects
- Configure project-specific models and settings
- View project-level usage stats and analytics
- Manage End Users assigned to their projects
- Access project-specific audit logs
- Configure project-level compliance settings

**Restrictions:**
- Cannot access other projects' data
- Cannot modify tenant-level configurations

**Use Cases:**
- Project managers managing project-specific knowledge bases
- Team leads configuring project settings
- Department heads overseeing project operations

### End User (`end_user`)

**Description:** User-level read-only access with user-scoped memory

**Capabilities:**
- Read-only access with role-based data filtering
- Search knowledge bases (filtered by their role/permissions)
- Access their own memory (user_id-scoped)
- Read access to documents (filtered by permissions)

**Restrictions:**
- Cannot modify tenant or project configurations
- Cannot access audit logs or usage stats
- Cannot access other users' memory or data
- Limited to their assigned projects within tenant

**Use Cases:**
- End users searching knowledge bases
- Chatbot users accessing their conversation history
- Voice bot users retrieving personalized responses

## Tool Permissions

Each MCP tool has specific role requirements. The following table shows which roles can access each tool:

| Tool Name | Uber Admin | Tenant Admin | Project Admin | End User |
|-----------|------------|--------------|---------------|----------|
| `rag_list_tools` | ✅ | ✅ | ✅ | ✅ |
| `rag_register_tenant` | ✅ | ❌ | ❌ | ❌ |
| `rag_list_templates` | ✅ | ✅ | ✅ | ✅ |
| `rag_get_template` | ✅ | ✅ | ✅ | ✅ |
| `rag_configure_tenant_models` | ✅ | ✅ | ❌ | ❌ |
| `rag_update_tenant_config` | ✅ | ✅ | ❌ | ❌ |
| `rag_delete_tenant` | ✅ | ❌ | ❌ | ❌ |
| `rag_ingest` | ✅ | ✅ | ✅ | ❌ |
| `rag_delete_document` | ✅ | ✅ | ✅ | ❌ |
| `rag_get_document` | ✅ | ✅ | ✅ | ✅ |
| `rag_list_documents` | ✅ | ✅ | ✅ | ✅ |
| `rag_search` | ✅ | ✅ | ✅ | ✅ |
| `mem0_get_user_memory` | ✅ | ✅ | ✅ | ✅ |
| `mem0_update_memory` | ✅ | ✅ | ✅ | ✅ |
| `mem0_search_memory` | ✅ | ✅ | ✅ | ✅ |
| `rag_query_audit_logs` | ✅ | ✅ | ❌ | ❌ |
| `rag_get_usage_stats` | ✅ | ✅ | ❌ | ❌ |
| `rag_get_search_analytics` | ✅ | ✅ | ❌ | ❌ |
| `rag_get_memory_analytics` | ✅ | ✅ | ❌ | ❌ |
| `rag_get_system_health` | ✅ | ✅ | ❌ | ❌ |
| `rag_get_tenant_health` | ✅ | ✅ | ❌ | ❌ |
| `rag_backup_tenant_data` | ✅ | ✅ | ❌ | ❌ |
| `rag_restore_tenant_data` | ✅ | ✅ | ❌ | ❌ |
| `rag_rebuild_index` | ✅ | ✅ | ❌ | ❌ |
| `rag_validate_backup` | ✅ | ✅ | ❌ | ❌ |
| `rag_export_tenant_data` | ✅ | ✅ | ❌ | ❌ |
| `rag_export_user_data` | ✅ | ✅ | ❌ | ❌ |

## Role Mapping

### Legacy Role Support

For backward compatibility, the following legacy role names are mapped to `end_user`:
- `user` → `end_user`
- `viewer` → `end_user`

### Role Extraction

Roles are extracted from:
1. **OAuth 2.0 Token Claims** (preferred): `role` claim in JWT token
2. **User Profile Lookup** (fallback): User profile endpoint if claims missing
3. **API Key Association**: Default role for API key users (typically `end_user` or `tenant_admin`)

## Implementation

### Role Enum

Roles are defined in `app/mcp/middleware/rbac.py`:

```python
from app.mcp.middleware.rbac import UserRole

# Role enum values
UserRole.UBER_ADMIN      # "uber_admin"
UserRole.TENANT_ADMIN    # "tenant_admin"
UserRole.PROJECT_ADMIN   # "project_admin"
UserRole.END_USER        # "end_user"
```

### Permission Checking

```python
from app.mcp.middleware.rbac import can_access_tool, UserRole

# Check if role can access tool
if can_access_tool(UserRole.END_USER, "rag_ingest"):
    # Allow access
    pass
else:
    # Deny access (403 Forbidden)
    raise AuthorizationError("Access denied")
```

### Tool Permission Mapping

Tool permissions are defined in `TOOL_PERMISSIONS` dictionary in `app/mcp/middleware/rbac.py`:

```python
TOOL_PERMISSIONS: dict[str, Set[UserRole]] = {
    "rag_list_tools": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    "rag_register_tenant": {UserRole.UBER_ADMIN},
    # ... more tools
}
```

## Data Access Patterns

### Uber Admin
- **Tenant Data**: Can access all tenants' data
- **User Data**: Can access all users' data across all tenants
- **Audit Logs**: Can access all audit logs
- **Cross-Tenant Operations**: Allowed

### Tenant Admin
- **Tenant Data**: Can access only their tenant's data
- **User Data**: Can access all users' data within their tenant
- **Audit Logs**: Can access only their tenant's audit logs
- **Cross-Tenant Operations**: Not allowed

### Project Admin (Phase 2)
- **Project Data**: Can access only their project's data within tenant
- **User Data**: Can access users assigned to their projects
- **Audit Logs**: Can access only their project's audit logs
- **Cross-Project Operations**: Not allowed

### End User
- **User Data**: Can access only their own data (user_id-scoped)
- **Memory**: Can access only their own memories
- **Documents**: Can read documents filtered by permissions
- **Audit Logs**: Cannot access
- **Cross-User Operations**: Not allowed

## Related Documentation

- `app/mcp/middleware/rbac.py` - RBAC role and permission definitions
- `app/mcp/middleware/authorization.py` - Authorization middleware implementation
- `app/db/models/user.py` - User model with role field
- `docs/AUTHORIZATION_CONFIGURATION.md` - Authorization configuration settings












