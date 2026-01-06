"""
MinIO (S3-compatible) client setup with tenant-scoped bucket configuration.
"""

from typing import Optional
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.config.minio import minio_settings
from app.utils.minio_buckets import (
    get_tenant_bucket_name,
    validate_tenant_bucket,
    TenantIsolationError,
)
from app.mcp.middleware.tenant import get_tenant_id_from_context


# Global MinIO client instance
_minio_client: Optional[Minio] = None


def create_minio_client() -> Minio:
    """
    Create MinIO client instance.
    
    Returns:
        Minio: Configured MinIO client
    """
    global _minio_client
    
    if _minio_client is None:
        _minio_client = Minio(
            f"{minio_settings.endpoint}:{minio_settings.port}",
            access_key=minio_settings.access_key,
            secret_key=minio_settings.secret_key,
            secure=minio_settings.use_ssl,
            region=minio_settings.region,
        )
    
    return _minio_client


async def get_tenant_bucket(tenant_id: Optional[UUID] = None, create_if_missing: bool = True) -> str:
    """
    Get or create a tenant-scoped bucket.
    
    Args:
        tenant_id: Tenant ID (optional, will be extracted from context if not provided)
        create_if_missing: If True, create bucket if it doesn't exist
        
    Returns:
        str: Bucket name (tenant-{tenant_id})
        
    Raises:
        TenantIsolationError: If tenant_id is not available
    """
    bucket_name = get_tenant_bucket_name(tenant_id)
    client = create_minio_client()
    
    try:
        # Check if bucket exists
        if not client.bucket_exists(bucket_name):
            if create_if_missing:
                # Create tenant-scoped bucket
                client.make_bucket(
                    bucket_name,
                    location=minio_settings.bucket_region,
                )
            else:
                raise TenantIsolationError(
                    f"Bucket '{bucket_name}' does not exist for tenant {tenant_id}",
                    error_code="FR-ERROR-003"
                )
    except S3Error as e:
        # Bucket might already exist or other error
        if e.code != "BucketAlreadyOwnedByYou":
            raise
    
    return bucket_name


async def validate_bucket_access(bucket_name: str, tenant_id: Optional[UUID] = None) -> None:
    """
    Validate that bucket access is allowed for the tenant.
    
    Args:
        bucket_name: Bucket name to validate
        tenant_id: Tenant ID (optional, will be extracted from context if not provided)
        
    Raises:
        TenantIsolationError: If bucket doesn't belong to tenant
    """
    validate_tenant_bucket(bucket_name, tenant_id)


async def initialize_minio_buckets():
    """
    Initialize default bucket structure.
    
    Note: Tenant buckets are created on-demand via get_tenant_bucket().
    This function is kept for backward compatibility but doesn't create tenant buckets.
    """
    client = create_minio_client()
    
    # Check if default bucket exists (for backward compatibility)
    # Tenant buckets will be created on-demand
    try:
        if not client.bucket_exists(minio_settings.bucket_name):
            # Create default bucket (for backward compatibility)
            client.make_bucket(
                minio_settings.bucket_name,
                location=minio_settings.bucket_region,
            )
    except S3Error as e:
        # Bucket might already exist or other error
        if e.code != "BucketAlreadyOwnedByYou":
            raise


async def upload_document_content(
    tenant_id: UUID,
    document_id: UUID,
    content: bytes,
    content_type: str = "text/plain",
) -> str:
    """
    Upload document content to tenant-scoped MinIO bucket.
    
    Args:
        tenant_id: Tenant ID
        document_id: Document ID
        content: Document content as bytes
        content_type: MIME type of the content (default: text/plain)
        
    Returns:
        str: Object name/path in bucket
        
    Raises:
        TenantIsolationError: If tenant_id is not available
        S3Error: If upload fails
    """
    from io import BytesIO
    
    bucket_name = await get_tenant_bucket(tenant_id, create_if_missing=True)
    client = create_minio_client()
    
    # Validate bucket access
    await validate_bucket_access(bucket_name, tenant_id)
    
    # Object name: documents/{document_id}
    object_name = f"documents/{document_id}"
    
    # Upload content
    content_stream = BytesIO(content)
    client.put_object(
        bucket_name,
        object_name,
        content_stream,
        length=len(content),
        content_type=content_type,
    )
    
    logger.info(
        "Document content uploaded to MinIO",
        tenant_id=str(tenant_id),
        document_id=str(document_id),
        bucket_name=bucket_name,
        object_name=object_name,
        content_length=len(content),
    )
    
    return object_name


async def get_document_content(
    tenant_id: UUID,
    document_id: UUID,
) -> bytes:
    """
    Retrieve document content from tenant-scoped MinIO bucket.
    
    Args:
        tenant_id: Tenant ID
        document_id: Document ID
        
    Returns:
        bytes: Document content
        
    Raises:
        TenantIsolationError: If tenant_id is not available
        S3Error: If retrieval fails
    """
    from io import BytesIO
    
    bucket_name = await get_tenant_bucket(tenant_id, create_if_missing=False)
    client = create_minio_client()
    
    # Validate bucket access
    await validate_bucket_access(bucket_name, tenant_id)
    
    # Object name: documents/{document_id}
    object_name = f"documents/{document_id}"
    
    # Retrieve content
    response = client.get_object(bucket_name, object_name)
    content = response.read()
    response.close()
    response.release_conn()
    
    logger.debug(
        "Document content retrieved from MinIO",
        tenant_id=str(tenant_id),
        document_id=str(document_id),
        bucket_name=bucket_name,
        object_name=object_name,
        content_length=len(content),
    )
    
    return content


async def check_minio_health() -> dict[str, bool | str]:
    """
    Check MinIO connectivity and health.
    
    Returns:
        dict: Health check result with status and message
    """
    try:
        client = create_minio_client()
        
        # List buckets to check connectivity
        buckets = client.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        # Check if default bucket exists
        default_bucket_exists = minio_settings.bucket_name in bucket_names
        
        return {
            "status": True,
            "message": f"MinIO is healthy (Buckets: {len(bucket_names)}, Default bucket: {'exists' if default_bucket_exists else 'missing'})",
        }
    except Exception as e:
        return {"status": False, "message": f"MinIO health check failed: {str(e)}"}

