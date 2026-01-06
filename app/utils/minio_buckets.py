"""
MinIO bucket utilities with tenant-scoped bucket isolation.

All MinIO buckets are tenant-scoped to ensure complete tenant isolation.
Each tenant has a separate bucket: tenant-{tenant_id}
"""

from typing import Optional
from uuid import UUID

from app.mcp.middleware.tenant import get_tenant_id_from_context
from app.utils.errors import TenantIsolationError


def get_tenant_bucket_name(tenant_id: Optional[UUID] = None) -> str:
    """
    Get the bucket name for a tenant.
    
    Args:
        tenant_id: Tenant ID (optional, will be extracted from context if not provided)
        
    Returns:
        str: Bucket name: tenant-{tenant_id}
        
    Raises:
        TenantIsolationError: If tenant_id is not available
    """
    if tenant_id is None:
        tenant_id = get_tenant_id_from_context()
    
    if tenant_id is None:
        raise TenantIsolationError(
            "Tenant ID not found in context. Cannot create tenant-scoped bucket name.",
            error_code="FR-ERROR-003"
        )
    
    return f"tenant-{tenant_id}"


def extract_tenant_from_bucket(bucket_name: str) -> Optional[UUID]:
    """
    Extract tenant_id from a tenant-scoped bucket name.
    
    Args:
        bucket_name: Bucket name (tenant-{tenant_id})
        
    Returns:
        UUID: Tenant ID or None if not found
    """
    if not bucket_name.startswith("tenant-"):
        return None
    
    try:
        # Extract tenant_id from bucket name: tenant-{tenant_id}
        tenant_id_str = bucket_name.replace("tenant-", "", 1)
        return UUID(tenant_id_str)
    except (ValueError, AttributeError):
        return None


def validate_tenant_bucket(bucket_name: str, expected_tenant_id: Optional[UUID] = None) -> None:
    """
    Validate that a bucket name belongs to the expected tenant.
    
    Args:
        bucket_name: Bucket name to validate
        expected_tenant_id: Expected tenant ID (optional, will be extracted from context if not provided)
        
    Raises:
        TenantIsolationError: If bucket doesn't belong to expected tenant
    """
    if expected_tenant_id is None:
        expected_tenant_id = get_tenant_id_from_context()
    
    if expected_tenant_id is None:
        raise TenantIsolationError(
            "Tenant ID not found in context. Cannot validate bucket name.",
            error_code="FR-ERROR-003"
        )
    
    # Extract tenant_id from bucket name
    bucket_tenant_id = extract_tenant_from_bucket(bucket_name)
    
    if bucket_tenant_id is None:
        raise TenantIsolationError(
            f"Bucket '{bucket_name}' does not have tenant prefix. All buckets must be tenant-scoped (tenant-{{tenant_id}}).",
            error_code="FR-ERROR-003"
        )
    
    if bucket_tenant_id != expected_tenant_id:
        raise TenantIsolationError(
            f"Tenant isolation violation: Bucket '{bucket_name}' belongs to tenant {bucket_tenant_id} "
            f"but context tenant is {expected_tenant_id}",
            error_code="FR-ERROR-003"
        )



