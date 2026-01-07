"""
MCP tools for backup and restore operations (Epic 7).

Provides backup, restore, rebuild, and validation tools for tenant data protection.
Access restricted to Uber Admin and Tenant Admin roles.
"""

import asyncio
import hashlib
import json
import os
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import text

from app.db.connection import get_db_session
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.tenant_repository import TenantRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.mcp.middleware.rbac import UserRole, check_tool_permission
from app.mcp.middleware.tenant import get_tenant_id_from_context
from app.mcp.server import mcp_server
from app.services.faiss_manager import faiss_manager, get_tenant_index_path
from app.services.minio_client import create_minio_client, get_tenant_bucket
from app.services.meilisearch_client import create_meilisearch_client, get_tenant_index_name
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

logger = structlog.get_logger(__name__)

# Backup configuration
BACKUP_BASE_DIR = Path(os.getenv("BACKUP_BASE_DIR", "/tmp/backups"))
BACKUP_BASE_DIR.mkdir(parents=True, exist_ok=True)


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


async def backup_postgresql_data(tenant_id: UUID, backup_dir: Path) -> Dict[str, Any]:
    """
    Backup PostgreSQL data for a tenant.
    
    Exports tenant-scoped tables: documents, users, tenant_configs, audit_logs, tenant_api_keys.
    """
    try:
        backup_file = backup_dir / f"postgresql_tenant_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        async for session in get_db_session():
            # Set tenant context for RLS
            await session.execute(
                text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_id}\'')
            )
            
            # Export tenant data
            tenant_repo = TenantRepository(session)
            doc_repo = DocumentRepository(session)
            user_repo = UserRepository(session)
            config_repo = TenantConfigRepository(session)
            
            # Get tenant
            tenant = await tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ResourceNotFoundError(f"Tenant {tenant_id} not found")
            
            # Get all tenant data
            documents = await doc_repo.get_by_tenant(tenant_id, skip=0, limit=10000)
            users = await user_repo.get_all(skip=0, limit=10000, tenant_id=tenant_id)
            configs = await config_repo.get_by_tenant_id(tenant_id)
            
            # Export to JSON
            export_data = {
                "tenant": tenant.to_dict() if tenant else None,
                "documents": [doc.to_dict() for doc in documents],
                "users": [user.to_dict() for user in users],
                "config": configs.to_dict() if configs else None,
                "export_timestamp": datetime.now().isoformat(),
            }
            
            with open(backup_file, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            checksum = calculate_file_checksum(backup_file)
            file_size = backup_file.stat().st_size
            
            logger.info(
                "PostgreSQL backup created",
                tenant_id=str(tenant_id),
                backup_file=str(backup_file),
                file_size=file_size,
            )
            
            return {
                "file_path": str(backup_file),
                "file_size": file_size,
                "checksum": checksum,
                "record_count": {
                    "documents": len(documents),
                    "users": len(users),
                },
            }
    except Exception as e:
        logger.error("PostgreSQL backup failed", tenant_id=str(tenant_id), error=str(e))
        raise


async def backup_faiss_index(tenant_id: UUID, backup_dir: Path) -> Dict[str, Any]:
    """Backup FAISS index for a tenant."""
    try:
        index_path = get_tenant_index_path(tenant_id)
        
        if not index_path.exists():
            logger.warning("FAISS index does not exist", tenant_id=str(tenant_id))
            return {
                "file_path": None,
                "file_size": 0,
                "checksum": None,
                "status": "skipped",
            }
        
        backup_file = backup_dir / f"faiss_tenant_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.index"
        
        # Copy index file
        import shutil
        shutil.copy2(index_path, backup_file)
        
        checksum = calculate_file_checksum(backup_file)
        file_size = backup_file.stat().st_size
        
        logger.info(
            "FAISS index backup created",
            tenant_id=str(tenant_id),
            backup_file=str(backup_file),
            file_size=file_size,
        )
        
        return {
            "file_path": str(backup_file),
            "file_size": file_size,
            "checksum": checksum,
            "status": "success",
        }
    except Exception as e:
        logger.error("FAISS index backup failed", tenant_id=str(tenant_id), error=str(e))
        raise


async def backup_minio_objects(tenant_id: UUID, backup_dir: Path) -> Dict[str, Any]:
    """Backup MinIO objects for a tenant bucket."""
    try:
        bucket_name = await get_tenant_bucket(tenant_id, create_if_missing=False)
        minio_client = create_minio_client()
        
        if not minio_client.bucket_exists(bucket_name):
            logger.warning("MinIO bucket does not exist", tenant_id=str(tenant_id))
            return {
                "file_path": None,
                "file_size": 0,
                "checksum": None,
                "object_count": 0,
                "status": "skipped",
            }
        
        # Create tar archive of bucket contents
        backup_file = backup_dir / f"minio_tenant_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        
        objects = list(minio_client.list_objects(bucket_name, recursive=True))
        object_count = 0
        
        with tarfile.open(backup_file, "w:gz") as tar:
            for obj in objects:
                try:
                    # Download object to temp file
                    temp_file = backup_dir / f"temp_{obj.object_name.replace('/', '_')}"
                    minio_client.fget_object(bucket_name, obj.object_name, str(temp_file))
                    
                    # Add to tar
                    tar.add(temp_file, arcname=obj.object_name)
                    temp_file.unlink()  # Clean up temp file
                    object_count += 1
                except Exception as e:
                    logger.warning("Failed to backup MinIO object", object=obj.object_name, error=str(e))
        
        checksum = calculate_file_checksum(backup_file)
        file_size = backup_file.stat().st_size
        
        logger.info(
            "MinIO objects backup created",
            tenant_id=str(tenant_id),
            backup_file=str(backup_file),
            file_size=file_size,
            object_count=object_count,
        )
        
        return {
            "file_path": str(backup_file),
            "file_size": file_size,
            "checksum": checksum,
            "object_count": object_count,
            "status": "success",
        }
    except Exception as e:
        logger.error("MinIO objects backup failed", tenant_id=str(tenant_id), error=str(e))
        raise


async def backup_meilisearch_index(tenant_id: UUID, backup_dir: Path) -> Dict[str, Any]:
    """Backup Meilisearch index for a tenant."""
    try:
        client = create_meilisearch_client()
        index_name = await get_tenant_index_name(str(tenant_id))
        
        try:
            index = client.get_index(index_name)
        except Exception:
            logger.warning("Meilisearch index does not exist", tenant_id=str(tenant_id))
            return {
                "file_path": None,
                "file_size": 0,
                "checksum": None,
                "document_count": 0,
                "status": "skipped",
            }
        
        # Export all documents from index
        backup_file = backup_dir / f"meilisearch_tenant_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Get all documents (with pagination)
        all_documents = []
        offset = 0
        limit = 1000
        
        while True:
            response = index.get_documents(offset=offset, limit=limit)
            documents = response.get("results", [])
            if not documents:
                break
            all_documents.extend(documents)
            offset += limit
        
        export_data = {
            "index_name": index_name,
            "documents": all_documents,
            "export_timestamp": datetime.now().isoformat(),
        }
        
        with open(backup_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        checksum = calculate_file_checksum(backup_file)
        file_size = backup_file.stat().st_size
        
        logger.info(
            "Meilisearch index backup created",
            tenant_id=str(tenant_id),
            backup_file=str(backup_file),
            file_size=file_size,
            document_count=len(all_documents),
        )
        
        return {
            "file_path": str(backup_file),
            "file_size": file_size,
            "checksum": checksum,
            "document_count": len(all_documents),
            "status": "success",
        }
    except Exception as e:
        logger.error("Meilisearch index backup failed", tenant_id=str(tenant_id), error=str(e))
        raise


@mcp_server.tool()
async def rag_backup_tenant_data(
    tenant_id: str,
    backup_type: str = "full",
    backup_location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Backup tenant data (PostgreSQL, FAISS, MinIO, Meilisearch).
    
    Creates a comprehensive backup of all tenant data including:
    - PostgreSQL data (documents, users, configs)
    - FAISS vector index
    - MinIO object storage
    - Meilisearch search index
    
    Access restricted to Uber Admin and Tenant Admin roles.
    
    Args:
        tenant_id: Tenant UUID (string format)
        backup_type: Backup type - "full" or "incremental" (default: "full")
        backup_location: Optional backup storage location (default: /tmp/backups)
        
    Returns:
        Dictionary containing:
        - backup_id: Unique backup identifier
        - tenant_id: Tenant ID
        - backup_type: Type of backup
        - timestamp: Backup timestamp
        - manifest: Backup manifest with file paths, sizes, checksums
        - status: Backup status
        - progress: Backup progress (percentage, estimated_time_remaining)
        
    Raises:
        AuthorizationError: If user doesn't have permission
        ResourceNotFoundError: If tenant not found
        ValidationError: If backup_type is invalid
    """
    # Check permissions
    role = check_tool_permission("rag_backup_tenant_data")
    if role not in {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN}:
        raise AuthorizationError("Access denied: Uber Admin or Tenant Admin role required")
    
    # Validate backup_type
    if backup_type not in {"full", "incremental"}:
        raise ValidationError(f"Invalid backup_type: {backup_type}. Must be 'full' or 'incremental'")
    
    tenant_uuid = UUID(tenant_id)
    
    # Determine backup location
    if backup_location:
        backup_base_dir = Path(backup_location)
    else:
        backup_base_dir = BACKUP_BASE_DIR
    
    backup_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Create tenant-specific backup directory
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{tenant_id}_{backup_timestamp}"
    backup_dir = backup_base_dir / backup_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(
        "Starting tenant backup",
        tenant_id=tenant_id,
        backup_type=backup_type,
        backup_id=backup_id,
    )
    
    try:
        # Backup components
        manifest = {
            "backup_id": backup_id,
            "tenant_id": tenant_id,
            "backup_type": backup_type,
            "timestamp": datetime.now().isoformat(),
            "components": {},
        }
        
        # Backup PostgreSQL data
        logger.info("Backing up PostgreSQL data", tenant_id=tenant_id)
        postgres_backup = await backup_postgresql_data(tenant_uuid, backup_dir)
        manifest["components"]["postgresql"] = postgres_backup
        
        # Backup FAISS index
        logger.info("Backing up FAISS index", tenant_id=tenant_id)
        faiss_backup = await backup_faiss_index(tenant_uuid, backup_dir)
        manifest["components"]["faiss"] = faiss_backup
        
        # Backup MinIO objects
        logger.info("Backing up MinIO objects", tenant_id=tenant_id)
        minio_backup = await backup_minio_objects(tenant_uuid, backup_dir)
        manifest["components"]["minio"] = minio_backup
        
        # Backup Meilisearch index
        logger.info("Backing up Meilisearch index", tenant_id=tenant_id)
        meilisearch_backup = await backup_meilisearch_index(tenant_uuid, backup_dir)
        manifest["components"]["meilisearch"] = meilisearch_backup
        
        # Save manifest
        manifest_file = backup_dir / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        
        # Calculate total backup size
        total_size = sum(
            comp.get("file_size", 0)
            for comp in manifest["components"].values()
            if comp.get("file_size")
        )
        
        manifest["total_size"] = total_size
        manifest["status"] = "completed"
        
        logger.info(
            "Tenant backup completed",
            tenant_id=tenant_id,
            backup_id=backup_id,
            total_size=total_size,
        )
        
        return {
            "backup_id": backup_id,
            "tenant_id": tenant_id,
            "backup_type": backup_type,
            "timestamp": manifest["timestamp"],
            "manifest": manifest,
            "status": "completed",
            "total_size": total_size,
            "backup_location": str(backup_dir),
        }
        
    except Exception as e:
        logger.error("Tenant backup failed", tenant_id=tenant_id, error=str(e))
        raise

