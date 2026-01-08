"""
RBAC (Role-Based Access Control) roles and permissions definitions.
"""

from enum import Enum
from typing import Set, Optional

from app.utils.errors import AuthorizationError


class UserRole(str, Enum):
    """
    User roles in the system.
    
    Roles are hierarchical:
    - uber_admin: Platform-level access across all tenants
    - tenant_admin: Tenant-level access within their tenant
    - project_admin: Project-level access within a tenant (Phase 2)
    - end_user: User-level read-only access with user-scoped memory
    """
    
    UBER_ADMIN = "uber_admin"
    TENANT_ADMIN = "tenant_admin"
    PROJECT_ADMIN = "project_admin"  # Phase 2
    END_USER = "end_user"
    
    # Legacy role names for backward compatibility
    USER = "user"  # Maps to END_USER
    VIEWER = "viewer"  # Maps to END_USER
    
    @classmethod
    def from_string(cls, role_str: str) -> "UserRole":
        """
        Convert string role to UserRole enum.
        
        Handles legacy role names and case-insensitive matching.
        
        Args:
            role_str: Role string (e.g., "uber_admin", "user", "Uber_Admin")
        
        Returns:
            UserRole: Corresponding enum value
        
        Raises:
            ValueError: If role string is invalid
        """
        role_lower = role_str.lower().strip()
        
        # Map legacy role names
        if role_lower in ("user", "viewer"):
            return cls.END_USER
        
        # Try to match enum value
        for role in cls:
            if role.value.lower() == role_lower:
                return role
        
        raise ValueError(f"Invalid role: {role_str}")


# Tool permission definitions
# Each tool requires specific roles to execute
TOOL_PERMISSIONS: dict[str, Set[UserRole]] = {
    # Discovery tools - available to all authenticated users
    "rag_list_tools": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    
    # Tenant management tools - Uber Admin and Tenant Admin only
    "rag_register_tenant": {UserRole.UBER_ADMIN},
    "rag_list_templates": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    "rag_get_template": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    "rag_configure_tenant_models": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    "rag_update_tenant_config": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},  # Phase 2
    "rag_delete_tenant": {UserRole.UBER_ADMIN},  # Phase 2
    
    # Document management tools
    "rag_ingest": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN},
    "rag_delete_document": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN},
    "rag_get_document": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    "rag_list_documents": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    
    # Search tools - all authenticated users
    "rag_search": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    
    # Memory tools - all authenticated users (user-scoped)
    "mem0_get_user_memory": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    "mem0_update_memory": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    "mem0_search_memory": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN, UserRole.PROJECT_ADMIN, UserRole.END_USER},
    
    # Audit log tools - Uber Admin and Tenant Admin only
    "rag_query_audit_logs": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    
    # Monitoring tools
    "rag_get_usage_stats": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    "rag_get_search_analytics": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    "rag_get_memory_analytics": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    "rag_get_system_health": {UserRole.UBER_ADMIN},  # Uber Admin only - system-wide health monitoring
    "rag_get_tenant_health": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    
    # Backup tools - Uber Admin and Tenant Admin only
    "rag_backup_tenant_data": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    "rag_restore_tenant_data": {UserRole.UBER_ADMIN},  # Uber Admin only - destructive operation
    "rag_rebuild_index": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},
    "rag_validate_backup": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},  # Phase 2
    
    # Data export tools - Uber Admin and Tenant Admin only
    "rag_export_tenant_data": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},  # Phase 2
    "rag_export_user_data": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},  # Phase 2
    
    # Tenant management tools - Epic 9
    "rag_delete_tenant": {UserRole.UBER_ADMIN},  # Uber Admin only - destructive operation
    "rag_update_subscription_tier": {UserRole.UBER_ADMIN},  # Uber Admin only
    "rag_get_subscription_tier": {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN},  # Uber Admin and Tenant Admin
}


def get_role_permissions(role: UserRole) -> dict[str, bool]:
    """
    Get permissions for a specific role.
    
    Args:
        role: User role
    
    Returns:
        dict: Mapping of tool names to permission (True if allowed)
    """
    permissions = {}
    for tool_name, allowed_roles in TOOL_PERMISSIONS.items():
        permissions[tool_name] = role in allowed_roles
    return permissions


def can_access_tool(role: UserRole, tool_name: str) -> bool:
    """
    Check if a role can access a specific tool.
    
    Args:
        role: User role
        tool_name: Name of the MCP tool
    
    Returns:
        bool: True if role can access tool, False otherwise
    """
    allowed_roles = TOOL_PERMISSIONS.get(tool_name, set())
    return role in allowed_roles


def check_tool_permission(role: UserRole, tool_name: str) -> None:
    """
    Check if a role can access a specific tool, raising AuthorizationError if not.
    
    Args:
        role: User role
        tool_name: Name of the MCP tool
    
    Raises:
        AuthorizationError: If role cannot access tool (403 Forbidden)
    """
    if not can_access_tool(role, tool_name):
        raise AuthorizationError(
            f"Role '{role.value}' does not have permission to access tool '{tool_name}'",
            error_code="FR-ERROR-003"
        )


def get_required_role_for_tool(tool_name: str) -> Optional[UserRole]:
    """
    Get the minimum required role for a tool (for informational purposes).
    
    Args:
        tool_name: Name of the MCP tool
    
    Returns:
        UserRole: Minimum required role, or None if tool not found
    """
    allowed_roles = TOOL_PERMISSIONS.get(tool_name, set())
    if not allowed_roles:
        return None
    
    # Return the most restrictive role (hierarchy: END_USER < PROJECT_ADMIN < TENANT_ADMIN < UBER_ADMIN)
    role_hierarchy = [UserRole.END_USER, UserRole.PROJECT_ADMIN, UserRole.TENANT_ADMIN, UserRole.UBER_ADMIN]
    for role in role_hierarchy:
        if role in allowed_roles:
            return role
    
    return None


def get_role_capabilities(role: UserRole) -> dict:
    """
    Get detailed capabilities for a role.
    
    Args:
        role: User role
    
    Returns:
        dict: Role capabilities description
    """
    capabilities = {
        UserRole.UBER_ADMIN: {
            "description": "Platform-level access across all tenants",
            "capabilities": [
                "Full platform access across all tenants",
                "Create, update, delete tenants",
                "View cross-tenant analytics and platform-wide metrics",
                "Manage platform-wide configurations and system settings",
                "Access all audit logs across tenants",
                "Manage subscription tiers and billing",
                "System-level disaster recovery and backup operations",
                "Access all MCP tools",
            ],
            "restrictions": [],
        },
        UserRole.TENANT_ADMIN: {
            "description": "Tenant-level access within their tenant",
            "capabilities": [
                "Full tenant access within their tenant",
                "Configure tenant settings (models, compliance, templates, rate limits, quotas)",
                "Manage Project Admins and End Users within their tenant",
                "View tenant-wide usage stats, analytics, and audit logs",
                "Configure tenant-specific compliance profiles",
                "Manage tenant backups and restore operations",
                "Access tenant health monitoring and diagnostics",
                "Access tenant-scoped MCP tools",
            ],
            "restrictions": [
                "Cannot access other tenants' data",
                "Cannot perform platform-wide operations",
            ],
        },
        UserRole.PROJECT_ADMIN: {
            "description": "Project-scoped access within a tenant (Phase 2)",
            "capabilities": [
                "Project-scoped access within a tenant",
                "Manage knowledge bases for specific projects",
                "Configure project-specific models and settings",
                "View project-level usage stats and analytics",
                "Manage End Users assigned to their projects",
                "Access project-specific audit logs",
                "Configure project-level compliance settings",
            ],
            "restrictions": [
                "Cannot access other projects' data",
                "Cannot modify tenant-level configurations",
            ],
        },
        UserRole.END_USER: {
            "description": "User-level read-only access with user-scoped memory",
            "capabilities": [
                "Read-only access with role-based data filtering",
                "Search knowledge bases (filtered by their role/permissions)",
                "Access their own memory (user_id-scoped)",
                "Read access to documents (filtered by permissions)",
            ],
            "restrictions": [
                "Cannot modify tenant or project configurations",
                "Cannot access audit logs or usage stats",
                "Cannot access other users' memory or data",
                "Limited to their assigned projects within tenant",
            ],
        },
    }
    
    return capabilities.get(role, {})

