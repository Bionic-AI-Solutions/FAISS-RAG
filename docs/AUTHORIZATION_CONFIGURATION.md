# Authorization Configuration

**Last Updated:** 2026-01-06  
**Purpose:** Document authorization and RBAC configuration settings.

## Overview

The authorization system uses Role-Based Access Control (RBAC) to enforce permissions for MCP tools. Configuration is managed through environment variables and the `AuthorizationSettings` class.

## Configuration File

Authorization settings are defined in `app/config/authorization.py` and loaded from environment variables.

## Environment Variables

### RBAC Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `RBAC_ENABLED` | `true` | Enable/disable RBAC enforcement |
| `DEFAULT_ROLE` | `end_user` | Default role for users without explicit role assignment |
| `STRICT_MODE` | `true` | Deny access if tool not found in permissions (strict) or allow (permissive) |
| `AUTHORIZATION_TIMEOUT_MS` | `50` | Maximum authorization time in milliseconds |
| `LOG_ALL_AUTHORIZATION_ATTEMPTS` | `true` | Log all authorization attempts to audit log |
| `ENABLE_ROLE_INHERITANCE` | `false` | Enable role inheritance (higher roles inherit lower role permissions) |

## Configuration Examples

### Basic Configuration

```bash
# .env file
RBAC_ENABLED=true
DEFAULT_ROLE=end_user
STRICT_MODE=true
AUTHORIZATION_TIMEOUT_MS=50
LOG_ALL_AUTHORIZATION_ATTEMPTS=true
ENABLE_ROLE_INHERITANCE=false
```

### Development Configuration

```bash
# Development: More permissive for testing
RBAC_ENABLED=true
DEFAULT_ROLE=end_user
STRICT_MODE=false  # Allow unknown tools
AUTHORIZATION_TIMEOUT_MS=100  # More lenient timeout
LOG_ALL_AUTHORIZATION_ATTEMPTS=true
```

### Production Configuration

```bash
# Production: Strict security
RBAC_ENABLED=true
DEFAULT_ROLE=end_user
STRICT_MODE=true  # Deny unknown tools
AUTHORIZATION_TIMEOUT_MS=50  # Strict performance requirement
LOG_ALL_AUTHORIZATION_ATTEMPTS=true
ENABLE_ROLE_INHERITANCE=false
```

## Role Definitions

Roles are defined in `app/mcp/middleware/rbac.py`:

- **uber_admin**: Platform-level access across all tenants
- **tenant_admin**: Tenant-level access within their tenant
- **project_admin**: Project-scoped access within a tenant (Phase 2)
- **end_user**: User-level read-only access with user-scoped memory

## Tool Permissions

Tool permissions are defined in `TOOL_PERMISSIONS` dictionary in `app/mcp/middleware/rbac.py`. Each tool maps to a set of allowed roles.

## Configuration Usage

### In Code

```python
from app.config.authorization import authorization_settings

# Check if RBAC is enabled
if authorization_settings.rbac_enabled:
    # Perform authorization check
    pass

# Get default role
default_role = authorization_settings.default_role

# Check strict mode
if authorization_settings.strict_mode:
    # Deny access if tool not in permissions
    pass
```

### Middleware Integration

The authorization middleware automatically uses these settings:

- `rbac_enabled`: Controls whether authorization checks are performed
- `strict_mode`: Controls behavior for unknown tools
- `authorization_timeout_ms`: Used for performance monitoring
- `log_all_authorization_attempts`: Controls audit logging

## Performance Considerations

- **Authorization Timeout**: Set to 50ms by default to meet performance requirements (FR-AUTH-004, FR-AUTH-005)
- **Strict Mode**: Enabled by default for security; disable only in development
- **Audit Logging**: Can be disabled if performance is critical, but not recommended for production

## Security Considerations

- **Default Role**: Should always be `end_user` in production (most restrictive)
- **Strict Mode**: Should be `true` in production to deny unknown tools
- **Role Inheritance**: Currently disabled; explicit permissions only for clarity and security

## Related Documentation

- `app/config/authorization.py` - Authorization configuration class
- `app/mcp/middleware/rbac.py` - RBAC role and permission definitions
- `app/mcp/middleware/authorization.py` - Authorization middleware implementation
- `docs/RBAC_ROLES_AND_PERMISSIONS.md` - Complete RBAC documentation












