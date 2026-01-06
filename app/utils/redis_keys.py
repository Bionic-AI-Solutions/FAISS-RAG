"""
Redis key utilities with tenant prefixing for isolation.

All Redis keys are prefixed with tenant:{tenant_id}: to ensure complete tenant isolation.
"""

from typing import Optional
from uuid import UUID

from app.mcp.middleware.tenant import get_tenant_id_from_context
from app.utils.errors import TenantIsolationError


def prefix_key(key: str, tenant_id: Optional[UUID] = None) -> str:
    """
    Prefix a Redis key with tenant:{tenant_id}: for tenant isolation.
    
    Args:
        key: Base Redis key (without tenant prefix)
        tenant_id: Tenant ID (optional, will be extracted from context if not provided)
        
    Returns:
        str: Prefixed key: tenant:{tenant_id}:{key}
        
    Raises:
        TenantIsolationError: If tenant_id is not available
    """
    if tenant_id is None:
        tenant_id = get_tenant_id_from_context()
    
    if tenant_id is None:
        raise TenantIsolationError(
            "Tenant ID not found in context. Cannot create tenant-scoped Redis key.",
            error_code="FR-ERROR-003"
        )
    
    # Ensure key doesn't already have tenant prefix
    if key.startswith(f"tenant:{tenant_id}:"):
        return key
    
    # Prefix with tenant:{tenant_id}:
    return f"tenant:{tenant_id}:{key}"


def prefix_memory_key(key: str, tenant_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> str:
    """
    Prefix a memory Redis key with tenant:{tenant_id}:user:{user_id}: for user-level isolation.
    
    Args:
        key: Base Redis key (without tenant/user prefix)
        tenant_id: Tenant ID (optional, will be extracted from context if not provided)
        user_id: User ID (optional, for user-scoped keys)
        
    Returns:
        str: Prefixed key: tenant:{tenant_id}:user:{user_id}:{key} or tenant:{tenant_id}:{key} if no user_id
    """
    if tenant_id is None:
        tenant_id = get_tenant_id_from_context()
    
    if tenant_id is None:
        raise TenantIsolationError(
            "Tenant ID not found in context. Cannot create tenant-scoped Redis key.",
            error_code="FR-ERROR-003"
        )
    
    # If user_id is provided, use user-scoped prefix
    if user_id:
        # Ensure key doesn't already have prefix
        if key.startswith(f"tenant:{tenant_id}:user:{user_id}:"):
            return key
        return f"tenant:{tenant_id}:user:{user_id}:{key}"
    
    # Otherwise, just use tenant prefix
    return prefix_key(key, tenant_id)


def extract_tenant_from_key(key: str) -> Optional[UUID]:
    """
    Extract tenant_id from a prefixed Redis key.
    
    Args:
        key: Prefixed Redis key (tenant:{tenant_id}:...)
        
    Returns:
        UUID: Tenant ID or None if not found
    """
    if not key.startswith("tenant:"):
        return None
    
    try:
        # Extract tenant_id from key: tenant:{tenant_id}:...
        parts = key.split(":", 2)
        if len(parts) >= 2:
            return UUID(parts[1])
    except (ValueError, IndexError):
        return None
    
    return None


def validate_tenant_key(key: str, expected_tenant_id: Optional[UUID] = None) -> None:
    """
    Validate that a Redis key belongs to the expected tenant.
    
    Args:
        key: Redis key to validate
        expected_tenant_id: Expected tenant ID (optional, will be extracted from context if not provided)
        
    Raises:
        TenantIsolationError: If key doesn't belong to expected tenant
    """
    if expected_tenant_id is None:
        expected_tenant_id = get_tenant_id_from_context()
    
    if expected_tenant_id is None:
        raise TenantIsolationError(
            "Tenant ID not found in context. Cannot validate Redis key.",
            error_code="FR-ERROR-003"
        )
    
    # Extract tenant_id from key
    key_tenant_id = extract_tenant_from_key(key)
    
    if key_tenant_id is None:
        raise TenantIsolationError(
            f"Redis key '{key}' does not have tenant prefix. All keys must be tenant-scoped.",
            error_code="FR-ERROR-003"
        )
    
    if key_tenant_id != expected_tenant_id:
        raise TenantIsolationError(
            f"Tenant isolation violation: Key '{key}' belongs to tenant {key_tenant_id} "
            f"but context tenant is {expected_tenant_id}",
            error_code="FR-ERROR-003"
        )


# Common Redis key patterns (will be prefixed with tenant:{tenant_id}:)
class RedisKeyPatterns:
    """Common Redis key patterns for tenant-scoped operations."""
    
    @staticmethod
    def cache_key(resource_type: str, resource_id: str, tenant_id: Optional[UUID] = None) -> str:
        """
        Generate a cache key for a resource.
        
        Args:
            resource_type: Type of resource (e.g., 'document', 'embedding', 'search')
            resource_id: Resource identifier
            tenant_id: Tenant ID (optional)
            
        Returns:
            str: Prefixed cache key: tenant:{tenant_id}:cache:{resource_type}:{resource_id}
        """
        base_key = f"cache:{resource_type}:{resource_id}"
        return prefix_key(base_key, tenant_id)
    
    @staticmethod
    def session_key(session_id: str, tenant_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> str:
        """
        Generate a session key.
        
        Args:
            session_id: Session identifier
            tenant_id: Tenant ID (optional)
            user_id: User ID (optional)
            
        Returns:
            str: Prefixed session key: tenant:{tenant_id}:user:{user_id}:session:{session_id} or tenant:{tenant_id}:session:{session_id}
        """
        base_key = f"session:{session_id}"
        return prefix_memory_key(base_key, tenant_id, user_id)
    
    @staticmethod
    def rate_limit_key(identifier: str, tenant_id: Optional[UUID] = None) -> str:
        """
        Generate a rate limit key.
        
        Args:
            identifier: Rate limit identifier (e.g., user_id, api_key)
            tenant_id: Tenant ID (optional)
            
        Returns:
            str: Prefixed rate limit key: tenant:{tenant_id}:rate_limit:{identifier}
        """
        base_key = f"rate_limit:{identifier}"
        return prefix_key(base_key, tenant_id)
    
    @staticmethod
    def memory_key(user_id: str, memory_id: Optional[str] = None, tenant_id: Optional[UUID] = None) -> str:
        """
        Generate a memory key with tenant:user prefix.
        
        Args:
            user_id: User identifier (string, as used by Mem0)
            memory_id: Optional memory identifier
            tenant_id: Tenant ID (optional)
            
        Returns:
            str: Prefixed memory key: tenant:{tenant_id}:user:{user_id}:memory:{memory_id} or tenant:{tenant_id}:user:{user_id}:memory
        """
        if memory_id:
            base_key = f"memory:{user_id}:{memory_id}"
        else:
            base_key = f"memory:{user_id}"
        
        # Convert user_id string to UUID if possible for prefix_memory_key
        try:
            user_uuid = UUID(user_id)
            return prefix_memory_key(base_key, tenant_id, user_uuid)
        except ValueError:
            # If user_id is not a UUID, just use tenant prefix
            return prefix_key(base_key, tenant_id)



