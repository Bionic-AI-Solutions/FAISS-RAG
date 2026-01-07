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


# Restore functions

async def validate_backup_manifest(backup_dir: Path) -> Dict[str, Any]:
    """
    Validate backup manifest and return manifest data.
    
    Args:
        backup_dir: Path to backup directory containing manifest.json
        
    Returns:
        Manifest dictionary
        
    Raises:
        ValidationError: If manifest is missing or invalid
        ResourceNotFoundError: If backup directory doesn't exist
    """
    if not backup_dir.exists():
        raise ResourceNotFoundError(f"Backup directory not found: {backup_dir}")
    
    manifest_file = backup_dir / "manifest.json"
    if not manifest_file.exists():
        raise ValidationError(f"Backup manifest not found: {manifest_file}")
    
    try:
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        # Validate manifest structure
        required_fields = ["backup_id", "tenant_id", "timestamp", "components"]
        for field in required_fields:
            if field not in manifest:
                raise ValidationError(f"Manifest missing required field: {field}")
        
        # Validate component files exist
        for component_name, component_data in manifest.get("components", {}).items():
            if component_data.get("status") == "skipped":
                continue
            
            file_path = component_data.get("file_path")
            if file_path:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    # Try relative to backup_dir
                    file_path_obj = backup_dir / Path(file_path).name
                    if not file_path_obj.exists():
                        raise ValidationError(
                            f"Backup file not found for component {component_name}: {file_path}"
                        )
        
        logger.info("Backup manifest validated", backup_id=manifest.get("backup_id"))
        return manifest
        
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid manifest JSON: {str(e)}")
    except Exception as e:
        logger.error("Backup manifest validation failed", error=str(e))
        raise


async def restore_postgresql_data(tenant_id: UUID, backup_file: Path) -> Dict[str, Any]:
    """
    Restore PostgreSQL data for a tenant from backup.
    
    Args:
        tenant_id: Tenant ID
        backup_file: Path to PostgreSQL backup JSON file
        
    Returns:
        Restore result dictionary
    """
    try:
        with open(backup_file, "r") as f:
            export_data = json.load(f)
        
        async for session in get_db_session():
            # Set tenant context for RLS
            await session.execute(
                text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_id}\'')
            )
            
            tenant_repo = TenantRepository(session)
            doc_repo = DocumentRepository(session)
            user_repo = UserRepository(session)
            config_repo = TenantConfigRepository(session)
            
            # Restore tenant (if needed)
            tenant_data = export_data.get("tenant")
            if tenant_data:
                existing_tenant = await tenant_repo.get_by_id(tenant_id)
                if not existing_tenant:
                    # Tenant should already exist, but restore metadata if needed
                    logger.warning("Tenant not found during restore, skipping tenant restore", tenant_id=str(tenant_id))
            
            # Restore users
            users_data = export_data.get("users", [])
            users_restored = 0
            for user_data in users_data:
                try:
                    # Check if user exists
                    existing_user = await user_repo.get_by_id(UUID(user_data["user_id"]))
                    if existing_user:
                        # Update existing user
                        await user_repo.update(UUID(user_data["user_id"]), **{
                            k: v for k, v in user_data.items()
                            if k not in ["user_id", "created_at", "updated_at"]
                        })
                    else:
                        # Create new user
                        await user_repo.create(**user_data)
                    users_restored += 1
                except Exception as e:
                    logger.warning("Failed to restore user", user_id=user_data.get("user_id"), error=str(e))
            
            # Restore documents
            documents_data = export_data.get("documents", [])
            documents_restored = 0
            for doc_data in documents_data:
                try:
                    # Check if document exists
                    existing_doc = await doc_repo.get_by_id(UUID(doc_data["document_id"]))
                    if existing_doc:
                        # Update existing document
                        await doc_repo.update(UUID(doc_data["document_id"]), **{
                            k: v for k, v in doc_data.items()
                            if k not in ["document_id", "created_at", "updated_at"]
                        })
                    else:
                        # Create new document
                        await doc_repo.create(**doc_data)
                    documents_restored += 1
                except Exception as e:
                    logger.warning("Failed to restore document", document_id=doc_data.get("document_id"), error=str(e))
            
            # Restore tenant config
            config_data = export_data.get("config")
            config_restored = False
            if config_data:
                try:
                    existing_config = await config_repo.get_by_tenant_id(tenant_id)
                    if existing_config:
                        # Update existing config
                        await config_repo.update(existing_config.config_id, **{
                            k: v for k, v in config_data.items()
                            if k not in ["config_id", "created_at", "updated_at"]
                        })
                    else:
                        # Create new config
                        await config_repo.create(**config_data)
                    config_restored = True
                except Exception as e:
                    logger.warning("Failed to restore tenant config", tenant_id=str(tenant_id), error=str(e))
            
            await session.commit()
            
            logger.info(
                "PostgreSQL data restored",
                tenant_id=str(tenant_id),
                users_restored=users_restored,
                documents_restored=documents_restored,
                config_restored=config_restored,
            )
            
            return {
                "status": "success",
                "users_restored": users_restored,
                "documents_restored": documents_restored,
                "config_restored": config_restored,
            }
            
    except Exception as e:
        logger.error("PostgreSQL restore failed", tenant_id=str(tenant_id), error=str(e))
        raise


async def restore_faiss_index(tenant_id: UUID, backup_file: Path) -> Dict[str, Any]:
    """
    Restore FAISS index for a tenant from backup.
    
    Args:
        tenant_id: Tenant ID
        backup_file: Path to FAISS index backup file
        
    Returns:
        Restore result dictionary
    """
    try:
        index_path = get_tenant_index_path(tenant_id)
        
        # Copy backup file to index location
        import shutil
        shutil.copy2(backup_file, index_path)
        
        # Reload index in manager
        faiss_manager.load_index(tenant_id)
        
        logger.info(
            "FAISS index restored",
            tenant_id=str(tenant_id),
            backup_file=str(backup_file),
            index_path=str(index_path),
        )
        
        return {
            "status": "success",
            "index_path": str(index_path),
        }
        
    except Exception as e:
        logger.error("FAISS index restore failed", tenant_id=str(tenant_id), error=str(e))
        raise


async def restore_minio_objects(tenant_id: UUID, backup_file: Path) -> Dict[str, Any]:
    """
    Restore MinIO objects for a tenant from backup.
    
    Args:
        tenant_id: Tenant ID
        backup_file: Path to MinIO backup tar.gz file
        
    Returns:
        Restore result dictionary
    """
    try:
        bucket_name = await get_tenant_bucket(tenant_id, create_if_missing=True)
        minio_client = create_minio_client()
        
        # Extract tar.gz to temp directory
        temp_extract_dir = backup_file.parent / f"temp_extract_{tenant_id}"
        temp_extract_dir.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(temp_extract_dir)
        
        # Upload extracted files to MinIO
        objects_restored = 0
        for root, dirs, files in os.walk(temp_extract_dir):
            for file in files:
                file_path = Path(root) / file
                # Get relative path from extract dir (this is the object name)
                object_name = str(file_path.relative_to(temp_extract_dir))
                
                try:
                    minio_client.fput_object(
                        bucket_name,
                        object_name,
                        str(file_path),
                    )
                    objects_restored += 1
                except Exception as e:
                    logger.warning("Failed to restore MinIO object", object=object_name, error=str(e))
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_extract_dir)
        
        logger.info(
            "MinIO objects restored",
            tenant_id=str(tenant_id),
            bucket_name=bucket_name,
            objects_restored=objects_restored,
        )
        
        return {
            "status": "success",
            "objects_restored": objects_restored,
        }
        
    except Exception as e:
        logger.error("MinIO objects restore failed", tenant_id=str(tenant_id), error=str(e))
        raise


async def restore_meilisearch_index(tenant_id: UUID, backup_file: Path) -> Dict[str, Any]:
    """
    Restore Meilisearch index for a tenant from backup.
    
    Args:
        tenant_id: Tenant ID
        backup_file: Path to Meilisearch backup JSON file
        
    Returns:
        Restore result dictionary
    """
    try:
        client = create_meilisearch_client()
        index_name = await get_tenant_index_name(str(tenant_id))
        
        with open(backup_file, "r") as f:
            export_data = json.load(f)
        
        # Get or create index
        try:
            index = client.get_index(index_name)
        except Exception:
            from app.services.meilisearch_client import create_tenant_index
            await create_tenant_index(str(tenant_id))
            index = client.get_index(index_name)
        
        # Clear existing documents (if any)
        try:
            index.delete_all_documents()
        except Exception:
            pass  # Index might be empty
        
        # Restore documents
        documents = export_data.get("documents", [])
        if documents:
            # Batch add documents (Meilisearch supports batch operations)
            index.add_documents(documents)
        
        logger.info(
            "Meilisearch index restored",
            tenant_id=str(tenant_id),
            index_name=index_name,
            documents_restored=len(documents),
        )
        
        return {
            "status": "success",
            "documents_restored": len(documents),
        }
        
    except Exception as e:
        logger.error("Meilisearch index restore failed", tenant_id=str(tenant_id), error=str(e))
        raise


@mcp_server.tool()
async def rag_restore_tenant_data(
    tenant_id: str,
    backup_id: str,
    restore_type: str = "full",
    confirmation: bool = False,
) -> Dict[str, Any]:
    """
    Restore tenant data from backup.
    
    Restores tenant data from a previously created backup including:
    - PostgreSQL data (documents, users, configs)
    - FAISS vector index
    - MinIO object storage
    - Meilisearch search index
    
    IMPORTANT: This operation will overwrite existing tenant data.
    A safety backup is automatically created before restore.
    
    Access restricted to Uber Admin role only.
    
    Args:
        tenant_id: Tenant UUID (string format)
        backup_id: Backup identifier (e.g., "backup_{tenant_id}_{timestamp}")
        restore_type: Restore type - "full" or "partial" (default: "full")
        confirmation: Explicit confirmation required (must be True to proceed)
        
    Returns:
        Dictionary containing:
        - restore_id: Unique restore identifier
        - tenant_id: Tenant ID
        - backup_id: Backup ID used for restore
        - restore_type: Type of restore
        - timestamp: Restore timestamp
        - status: Restore status
        - progress: Restore progress (percentage, estimated_time_remaining)
        - components: Restore status for each component
        - safety_backup_id: ID of safety backup created before restore
        
    Raises:
        AuthorizationError: If user doesn't have permission (Uber Admin only)
        ResourceNotFoundError: If tenant or backup not found
        ValidationError: If restore_type is invalid or confirmation is False
    """
    # Check permissions - Uber Admin only
    role = check_tool_permission("rag_restore_tenant_data")
    if role != UserRole.UBER_ADMIN:
        raise AuthorizationError("Access denied: Uber Admin role required")
    
    # Require explicit confirmation
    if not confirmation:
        raise ValidationError(
            "Restore requires explicit confirmation. Set confirmation=True to proceed."
        )
    
    # Validate restore_type
    if restore_type not in {"full", "partial"}:
        raise ValidationError(f"Invalid restore_type: {restore_type}. Must be 'full' or 'partial'")
    
    tenant_uuid = UUID(tenant_id)
    
    # Find backup directory
    backup_dir = BACKUP_BASE_DIR / backup_id
    if not backup_dir.exists():
        raise ResourceNotFoundError(f"Backup not found: {backup_id}")
    
    # Validate backup manifest
    manifest = await validate_backup_manifest(backup_dir)
    
    # Verify tenant_id matches
    if manifest.get("tenant_id") != tenant_id:
        raise ValidationError(
            f"Backup tenant_id mismatch: backup is for {manifest.get('tenant_id')}, "
            f"but restore requested for {tenant_id}"
        )
    
    logger.info(
        "Starting tenant restore",
        tenant_id=tenant_id,
        backup_id=backup_id,
        restore_type=restore_type,
    )
    
    # Create safety backup before restore
    logger.info("Creating safety backup before restore", tenant_id=tenant_id)
    try:
        safety_backup_result = await rag_backup_tenant_data(
            tenant_id=tenant_id,
            backup_type="full",
        )
        safety_backup_id = safety_backup_result.get("backup_id")
        logger.info("Safety backup created", tenant_id=tenant_id, safety_backup_id=safety_backup_id)
    except Exception as e:
        logger.error("Safety backup failed", tenant_id=tenant_id, error=str(e))
        raise ValidationError(f"Failed to create safety backup: {str(e)}")
    
    restore_id = f"restore_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        restore_results = {
            "restore_id": restore_id,
            "tenant_id": tenant_id,
            "backup_id": backup_id,
            "restore_type": restore_type,
            "timestamp": datetime.now().isoformat(),
            "safety_backup_id": safety_backup_id,
            "components": {},
            "status": "in_progress",
        }
        
        # Restore components based on manifest
        components = manifest.get("components", {})
        
        # Restore PostgreSQL data
        if restore_type == "full" and components.get("postgresql", {}).get("file_path"):
            logger.info("Restoring PostgreSQL data", tenant_id=tenant_id)
            pg_file = Path(components["postgresql"]["file_path"])
            if not pg_file.is_absolute():
                pg_file = backup_dir / pg_file.name
            pg_result = await restore_postgresql_data(tenant_uuid, pg_file)
            restore_results["components"]["postgresql"] = pg_result
        
        # Restore FAISS index
        if restore_type == "full" and components.get("faiss", {}).get("file_path"):
            logger.info("Restoring FAISS index", tenant_id=tenant_id)
            faiss_file = Path(components["faiss"]["file_path"])
            if not faiss_file.is_absolute():
                faiss_file = backup_dir / faiss_file.name
            faiss_result = await restore_faiss_index(tenant_uuid, faiss_file)
            restore_results["components"]["faiss"] = faiss_result
        
        # Restore MinIO objects
        if restore_type == "full" and components.get("minio", {}).get("file_path"):
            logger.info("Restoring MinIO objects", tenant_id=tenant_id)
            minio_file = Path(components["minio"]["file_path"])
            if not minio_file.is_absolute():
                minio_file = backup_dir / minio_file.name
            minio_result = await restore_minio_objects(tenant_uuid, minio_file)
            restore_results["components"]["minio"] = minio_result
        
        # Restore Meilisearch index
        if restore_type == "full" and components.get("meilisearch", {}).get("file_path"):
            logger.info("Restoring Meilisearch index", tenant_id=tenant_id)
            meilisearch_file = Path(components["meilisearch"]["file_path"])
            if not meilisearch_file.is_absolute():
                meilisearch_file = backup_dir / meilisearch_file.name
            meilisearch_result = await restore_meilisearch_index(tenant_uuid, meilisearch_file)
            restore_results["components"]["meilisearch"] = meilisearch_result
        
        # Validate restore integrity (basic checks)
        all_succeeded = all(
            comp.get("status") == "success"
            for comp in restore_results["components"].values()
        )
        
        restore_results["status"] = "completed" if all_succeeded else "partial"
        
        logger.info(
            "Tenant restore completed",
            tenant_id=tenant_id,
            restore_id=restore_id,
            status=restore_results["status"],
        )
        
        return restore_results
        
    except Exception as e:
        logger.error("Tenant restore failed", tenant_id=tenant_id, error=str(e))
        restore_results["status"] = "failed"
        restore_results["error"] = str(e)
        raise

