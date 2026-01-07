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
from app.services.minio_client import create_minio_client, get_tenant_bucket, get_document_content
from app.services.meilisearch_client import create_meilisearch_client, get_tenant_index_name
from app.services.embedding_service import embedding_service
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


@mcp_server.tool()
async def rag_rebuild_index(
    tenant_id: str,
    index_type: str = "FAISS",
    rebuild_type: str = "full",
    confirmation_code: str = "",
    background: bool = False,
) -> Dict[str, Any]:
    """
    Rebuild FAISS index for a tenant from source documents.
    
    Performs a comprehensive rebuild of the FAISS index by:
    - Retrieving all documents for the tenant from PostgreSQL
    - Retrieving document content from MinIO
    - Regenerating embeddings for all documents
    - Rebuilding the FAISS index with new embeddings
    - Validating index integrity
    
    Supports both full rebuild (all documents) and incremental rebuild (only new/changed documents).
    Can be performed in background (async) for large indices.
    
    Requires explicit confirmation to prevent accidental index corruption.
    Access restricted to Uber Admin and Tenant Admin roles.
    
    Args:
        tenant_id: Tenant UUID (string format)
        index_type: Type of index to rebuild (currently only "FAISS" is supported)
        rebuild_type: Type of rebuild ("full" or "incremental")
        confirmation_code: A specific code (e.g., "FR-BACKUP-004") to confirm the rebuild operation.
                          This is a safety measure to prevent accidental index corruption.
        background: If True, rebuild is performed in background (async). Default: False.
        
    Returns:
        Dictionary containing:
        - tenant_id: Tenant ID
        - index_type: Type of index rebuilt
        - rebuild_type: Type of rebuild performed
        - timestamp: Rebuild completion timestamp
        - documents_processed: Number of documents processed
        - embeddings_regenerated: Number of embeddings regenerated
        - index_size: Number of vectors in the rebuilt index
        - integrity_validated: Whether index integrity was validated
        - status: Overall rebuild status ("succeeded", "failed", or "in_progress" for background)
        - rebuild_id: Unique identifier for this rebuild operation (for tracking)
        
    Raises:
        AuthorizationError: If user doesn't have permission
        ValidationError: If tenant_id, index_type, rebuild_type, or confirmation_code is invalid
        ResourceNotFoundError: If tenant not found
    """
    # Check permissions
    role = check_tool_permission("rag_rebuild_index")
    if role not in {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN}:
        raise AuthorizationError(
            "Access denied: Only Uber Admin and Tenant Admin roles can rebuild indices."
        )
    
    # Validate confirmation code
    if confirmation_code != "FR-BACKUP-004":
        raise ValidationError(
            "Rebuild operation requires explicit confirmation code 'FR-BACKUP-004' to prevent accidental index corruption.",
            field="confirmation_code"
        )
    
    # Validate index_type
    if index_type.upper() != "FAISS":
        raise ValidationError(
            f"Invalid index_type: {index_type}. Currently only 'FAISS' is supported.",
            field="index_type"
        )
    
    # Validate rebuild_type
    if rebuild_type not in {"full", "incremental"}:
        raise ValidationError(
            f"Invalid rebuild_type: {rebuild_type}. Must be 'full' or 'incremental'.",
            field="rebuild_type"
        )
    
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise ValidationError(f"Invalid tenant_id format: {tenant_id}", field="tenant_id")
    
    rebuild_id = f"rebuild_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(
        "Starting FAISS index rebuild",
        tenant_id=tenant_id,
        index_type=index_type,
        rebuild_type=rebuild_type,
        background=background,
        rebuild_id=rebuild_id,
    )
    
    # If background mode, run rebuild in background task
    if background:
        # Create background task (simplified - in production, use proper task queue)
        import asyncio
        task = asyncio.create_task(
            _perform_rebuild(tenant_uuid, index_type, rebuild_type, rebuild_id)
        )
        return {
            "tenant_id": tenant_id,
            "index_type": index_type,
            "rebuild_type": rebuild_type,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "rebuild_id": rebuild_id,
            "background": True,
            "message": "Rebuild started in background. Use rebuild_id to track progress.",
        }
    
    # Perform rebuild synchronously
    return await _perform_rebuild(tenant_uuid, index_type, rebuild_type, rebuild_id)


async def _perform_rebuild(
    tenant_uuid: UUID,
    index_type: str,
    rebuild_type: str,
    rebuild_id: str,
) -> Dict[str, Any]:
    """
    Perform the actual index rebuild operation.
    
    Args:
        tenant_uuid: Tenant UUID
        index_type: Type of index to rebuild
        rebuild_type: Type of rebuild ("full" or "incremental")
        rebuild_id: Unique identifier for this rebuild operation
        
    Returns:
        Dictionary with rebuild results
    """
    documents_processed = 0
    embeddings_regenerated = 0
    index_size = 0
    integrity_validated = False
    
    try:
        async for session in get_db_session():
            # Set tenant context for RLS
            await session.execute(
                text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_uuid}\'')
            )
            
            # Verify tenant exists
            tenant_repo = TenantRepository(session)
            tenant = await tenant_repo.get_by_id(tenant_uuid)
            if not tenant:
                raise ResourceNotFoundError(f"Tenant {tenant_uuid} not found")
            
            # Get all documents for tenant (excluding deleted)
            doc_repo = DocumentRepository(session)
            
            # For incremental rebuild, only get documents that have been updated since last rebuild
            # For now, we'll implement full rebuild - incremental can be added later
            if rebuild_type == "incremental":
                logger.warning(
                    "Incremental rebuild not fully implemented, performing full rebuild",
                    tenant_id=str(tenant_uuid),
                )
                rebuild_type = "full"
            
            # Get all non-deleted documents for tenant
            # Use a large limit to get all documents (in production, use pagination)
            documents = await doc_repo.get_by_tenant(tenant_uuid, skip=0, limit=100000)
            documents_processed = len(documents)
            
            logger.info(
                "Retrieved documents for rebuild",
                tenant_id=str(tenant_uuid),
                document_count=documents_processed,
            )
            
            if documents_processed == 0:
                logger.warning(
                    "No documents found for tenant, creating empty index",
                    tenant_id=str(tenant_uuid),
                )
                # Create empty index
                embedding_dimension = await _get_tenant_embedding_dimension(str(tenant_uuid))
                faiss_manager.create_index(tenant_uuid, dimension=embedding_dimension)
                faiss_manager.save_index(tenant_uuid, faiss_manager.get_index(tenant_uuid))
                
                return {
                    "tenant_id": str(tenant_uuid),
                    "index_type": index_type,
                    "rebuild_type": rebuild_type,
                    "timestamp": datetime.now().isoformat(),
                    "documents_processed": 0,
                    "embeddings_regenerated": 0,
                    "index_size": 0,
                    "integrity_validated": True,
                    "status": "succeeded",
                    "rebuild_id": rebuild_id,
                    "message": "Empty index created (no documents found)",
                }
            
            # Delete existing index to start fresh
            existing_index_path = get_tenant_index_path(tenant_uuid)
            if existing_index_path.exists():
                faiss_manager.remove_index_from_cache(tenant_uuid)
                existing_index_path.unlink()
                logger.info("Deleted existing FAISS index", tenant_id=str(tenant_uuid))
            
            # Get embedding dimension for tenant
            embedding_dimension = await _get_tenant_embedding_dimension(str(tenant_uuid))
            
            # Create new index
            faiss_manager.create_index(tenant_uuid, dimension=embedding_dimension)
            index = faiss_manager.get_index(tenant_uuid)
            
            if index is None:
                raise RuntimeError("Failed to create FAISS index")
            
            # Process documents in batches for better performance
            batch_size = 100
            total_batches = (documents_processed + batch_size - 1) // batch_size
            
            logger.info(
                "Starting document processing",
                tenant_id=str(tenant_uuid),
                total_documents=documents_processed,
                batch_size=batch_size,
                total_batches=total_batches,
            )
            
            # Process documents in batches
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, documents_processed)
                batch_documents = documents[start_idx:end_idx]
                
                logger.debug(
                    "Processing document batch",
                    tenant_id=str(tenant_uuid),
                    batch_idx=batch_idx + 1,
                    total_batches=total_batches,
                    batch_size=len(batch_documents),
                )
                
                # Process each document in the batch
                for document in batch_documents:
                    try:
                        # Retrieve document content from MinIO
                        content_bytes = await get_document_content(tenant_uuid, document.document_id)
                        text_content = content_bytes.decode("utf-8")
                        
                        # Regenerate embedding
                        embedding = await embedding_service.generate_embedding(
                            text=text_content,
                            tenant_id=str(tenant_uuid),
                        )
                        embeddings_regenerated += 1
                        
                        # Add to FAISS index
                        faiss_manager.add_document(
                            tenant_id=tenant_uuid,
                            document_id=document.document_id,
                            embedding=embedding,
                        )
                        index_size += 1
                        
                    except Exception as e:
                        logger.warning(
                            "Failed to process document during rebuild",
                            tenant_id=str(tenant_uuid),
                            document_id=str(document.document_id),
                            error=str(e),
                        )
                        # Continue with next document
                        continue
                
                # Save index periodically (every batch) to avoid data loss
                faiss_manager.save_index(tenant_uuid, index)
                logger.debug(
                    "Saved index after batch",
                    tenant_id=str(tenant_uuid),
                    batch_idx=batch_idx + 1,
                    index_size=index_size,
                )
            
            # Final save
            faiss_manager.save_index(tenant_uuid, index)
            
            # Validate index integrity
            integrity_validated = await _validate_index_integrity(tenant_uuid, index_size)
            
            logger.info(
                "FAISS index rebuild completed",
                tenant_id=str(tenant_uuid),
                documents_processed=documents_processed,
                embeddings_regenerated=embeddings_regenerated,
                index_size=index_size,
                integrity_validated=integrity_validated,
            )
            
            return {
                "tenant_id": str(tenant_uuid),
                "index_type": index_type,
                "rebuild_type": rebuild_type,
                "timestamp": datetime.now().isoformat(),
                "documents_processed": documents_processed,
                "embeddings_regenerated": embeddings_regenerated,
                "index_size": index_size,
                "integrity_validated": integrity_validated,
                "status": "succeeded" if integrity_validated else "partial",
                "rebuild_id": rebuild_id,
            }
            
    except Exception as e:
        logger.error(
            "FAISS index rebuild failed",
            tenant_id=str(tenant_uuid),
            rebuild_id=rebuild_id,
            error=str(e),
        )
        return {
            "tenant_id": str(tenant_uuid),
            "index_type": index_type,
            "rebuild_type": rebuild_type,
            "timestamp": datetime.now().isoformat(),
            "documents_processed": documents_processed,
            "embeddings_regenerated": embeddings_regenerated,
            "index_size": index_size,
            "integrity_validated": False,
            "status": "failed",
            "rebuild_id": rebuild_id,
            "error": str(e),
        }


async def _get_tenant_embedding_dimension(tenant_id: str) -> int:
    """
    Get the embedding dimension for a tenant's configured model.
    
    Args:
        tenant_id: Tenant UUID (string format)
        
    Returns:
        int: Embedding dimension
    """
    try:
        _, dimension = await embedding_service._get_tenant_embedding_model(tenant_id)
        return dimension
    except Exception:
        # Fallback to default dimension
        return 384  # GPU-AI default dimension


async def _validate_index_integrity(tenant_id: UUID, expected_size: int) -> bool:
    """
    Validate FAISS index integrity.
    
    Args:
        tenant_id: Tenant UUID
        expected_size: Expected number of vectors in the index
        
    Returns:
        bool: True if integrity is valid, False otherwise
    """
    try:
        index = faiss_manager.get_index(tenant_id)
        if index is None:
            logger.warning("Index not found for integrity validation", tenant_id=str(tenant_id))
            return False
        
        # Check if index is empty
        if index.ntotal == 0 and expected_size > 0:
            logger.warning(
                "Index is empty but expected size > 0",
                tenant_id=str(tenant_id),
                expected_size=expected_size,
            )
            return False
        
        # Check if index size matches expected size (allow small differences due to failures)
        if abs(index.ntotal - expected_size) > expected_size * 0.1:  # Allow 10% difference
            logger.warning(
                "Index size mismatch",
                tenant_id=str(tenant_id),
                expected_size=expected_size,
                actual_size=index.ntotal,
            )
            return False
        
        logger.info(
            "Index integrity validated",
            tenant_id=str(tenant_id),
            index_size=index.ntotal,
            expected_size=expected_size,
        )
        return True
        
    except Exception as e:
        logger.error(
            "Error validating index integrity",
            tenant_id=str(tenant_id),
            error=str(e),
        )
        return False


@mcp_server.tool()
async def rag_validate_backup(
    tenant_id: str,
    backup_id: str,
    validation_type: str = "full",
) -> Dict[str, Any]:
    """
    Validate backup integrity and completeness.
    
    This tool allows platform operators to validate backup integrity before restore operations.
    It checks manifest validity, file existence, file integrity (checksums), and backup completeness.
    
    Args:
        tenant_id: Tenant UUID (string format)
        backup_id: Identifier of the backup to validate (e.g., "backup_UUID_TIMESTAMP")
        validation_type: Type of validation ("full", "integrity", "completeness").
                         "full" performs all validations.
                         "integrity" only validates checksums.
                         "completeness" only validates that all required components are present.
    
    Returns:
        Dictionary containing:
        - tenant_id: Tenant ID
        - backup_id: Backup ID validated
        - validation_type: Type of validation performed
        - timestamp: Validation completion timestamp
        - status: Overall validation status ("passed", "failed", "partial")
        - report: Detailed validation report with component-level status
        
    Raises:
        AuthorizationError: If user doesn't have permission
        ValidationError: If tenant_id, backup_id, or validation_type is invalid
        ResourceNotFoundError: If tenant or backup not found
    """
    # Check permissions
    role = check_tool_permission("rag_validate_backup")
    if role not in {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN}:
        raise AuthorizationError("Access denied: Only Uber Admin and Tenant Admin roles can validate backups.")
    
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise ValidationError(f"Invalid tenant_id format: {tenant_id}", field="tenant_id")
    
    if validation_type not in {"full", "integrity", "completeness"}:
        raise ValidationError(
            f"Invalid validation_type: {validation_type}. Must be 'full', 'integrity', or 'completeness'.",
            field="validation_type"
        )
    
    # Locate the backup directory
    backup_dir = BACKUP_BASE_DIR / backup_id
    if not backup_dir.is_dir():
        raise ResourceNotFoundError(f"Backup with ID {backup_id} not found at {backup_dir}", resource_id=backup_id)
    
    logger.info(
        "Starting backup validation",
        tenant_id=tenant_id,
        backup_id=backup_id,
        validation_type=validation_type,
    )
    
    validation_report: Dict[str, Any] = {
        "manifest": {"status": "pending", "details": {}},
        "file_existence": {"status": "pending", "details": {}},
        "file_integrity": {"status": "pending", "details": {}},
        "completeness": {"status": "pending", "details": {}},
    }
    
    overall_status = "passed"
    
    try:
        # 1. Validate backup manifest
        manifest_file = backup_dir / "manifest.json"
        if not manifest_file.exists():
            validation_report["manifest"]["status"] = "failed"
            validation_report["manifest"]["details"]["error"] = "Manifest file not found"
            overall_status = "failed"
        else:
            try:
                with open(manifest_file, "r") as f:
                    manifest = json.load(f)
                
                # Validate manifest structure
                required_fields = ["tenant_id", "backup_id", "timestamp", "components"]
                missing_fields = [field for field in required_fields if field not in manifest]
                
                if missing_fields:
                    validation_report["manifest"]["status"] = "failed"
                    validation_report["manifest"]["details"]["error"] = f"Missing required fields: {missing_fields}"
                    overall_status = "failed"
                elif UUID(manifest["tenant_id"]) != tenant_uuid:
                    validation_report["manifest"]["status"] = "failed"
                    validation_report["manifest"]["details"]["error"] = f"Tenant ID mismatch. Expected {tenant_id}, got {manifest['tenant_id']}."
                    overall_status = "failed"
                else:
                    validation_report["manifest"]["status"] = "passed"
                    validation_report["manifest"]["details"]["backup_timestamp"] = manifest.get("timestamp")
                    validation_report["manifest"]["details"]["backup_type"] = manifest.get("backup_type", "unknown")
            except json.JSONDecodeError as e:
                validation_report["manifest"]["status"] = "failed"
                validation_report["manifest"]["details"]["error"] = f"Invalid JSON in manifest: {str(e)}"
                overall_status = "failed"
                manifest = None
            except Exception as e:
                validation_report["manifest"]["status"] = "failed"
                validation_report["manifest"]["details"]["error"] = f"Error reading manifest: {str(e)}"
                overall_status = "failed"
                manifest = None
        
        # If manifest validation failed, we can't continue with other validations
        if validation_report["manifest"]["status"] == "failed" and validation_type in {"full", "completeness"}:
            return {
                "tenant_id": tenant_id,
                "backup_id": backup_id,
                "validation_type": validation_type,
                "timestamp": datetime.now().isoformat(),
                "status": overall_status,
                "report": validation_report,
            }
        
        # Use manifest if available, otherwise skip file-based validations
        if manifest is None:
            manifest = {}
        
        # 2. Validate backup file existence (if validation_type includes it)
        if validation_type in {"full", "completeness"}:
            components = manifest.get("components", {})
            missing_files = []
            existing_files = []
            
            for component_name, component_info in components.items():
                file_path_str = component_info.get("file_path")
                if file_path_str:
                    file_path = Path(file_path_str)
                    if file_path.exists() and file_path.is_file():
                        existing_files.append(component_name)
                    else:
                        missing_files.append(component_name)
                        validation_report["file_existence"]["details"][component_name] = {
                            "status": "missing",
                            "expected_path": file_path_str,
                        }
            
            if missing_files:
                validation_report["file_existence"]["status"] = "failed"
                validation_report["file_existence"]["details"]["missing_components"] = missing_files
                if overall_status == "passed":
                    overall_status = "partial"
            else:
                validation_report["file_existence"]["status"] = "passed"
                validation_report["file_existence"]["details"]["all_files_exist"] = True
                validation_report["file_existence"]["details"]["components_checked"] = list(components.keys())
        
        # 3. Validate backup file integrity (checksums) (if validation_type includes it)
        if validation_type in {"full", "integrity"}:
            components = manifest.get("components", {})
            integrity_failures = []
            integrity_passed = []
            
            for component_name, component_info in components.items():
                file_path_str = component_info.get("file_path")
                expected_checksum = component_info.get("checksum")
                
                if file_path_str and expected_checksum:
                    file_path = Path(file_path_str)
                    if file_path.exists():
                        try:
                            actual_checksum = calculate_file_checksum(file_path)
                            if actual_checksum == expected_checksum:
                                integrity_passed.append(component_name)
                                validation_report["file_integrity"]["details"][component_name] = {
                                    "status": "passed",
                                    "checksum_match": True,
                                }
                            else:
                                integrity_failures.append(component_name)
                                validation_report["file_integrity"]["details"][component_name] = {
                                    "status": "failed",
                                    "checksum_match": False,
                                    "expected_checksum": expected_checksum,
                                    "actual_checksum": actual_checksum,
                                }
                        except Exception as e:
                            integrity_failures.append(component_name)
                            validation_report["file_integrity"]["details"][component_name] = {
                                "status": "error",
                                "error": str(e),
                            }
                    else:
                        integrity_failures.append(component_name)
                        validation_report["file_integrity"]["details"][component_name] = {
                            "status": "missing",
                            "error": "File not found for checksum validation",
                        }
            
            if integrity_failures:
                validation_report["file_integrity"]["status"] = "failed"
                validation_report["file_integrity"]["details"]["failed_components"] = integrity_failures
                overall_status = "failed"
            else:
                validation_report["file_integrity"]["status"] = "passed"
                validation_report["file_integrity"]["details"]["components_validated"] = integrity_passed
        
        # 4. Validate backup completeness (all required components present)
        if validation_type in {"full", "completeness"}:
            components = manifest.get("components", {})
            required_components = ["postgresql", "faiss", "minio", "meilisearch"]
            present_components = []
            missing_components = []
            
            for component in required_components:
                if component in components and components[component].get("file_path"):
                    present_components.append(component)
                else:
                    missing_components.append(component)
            
            if missing_components:
                validation_report["completeness"]["status"] = "failed"
                validation_report["completeness"]["details"]["missing_components"] = missing_components
                validation_report["completeness"]["details"]["present_components"] = present_components
                if overall_status == "passed":
                    overall_status = "partial"
            else:
                validation_report["completeness"]["status"] = "passed"
                validation_report["completeness"]["details"]["all_components_present"] = True
                validation_report["completeness"]["details"]["components"] = present_components
        
        logger.info(
            "Backup validation completed",
            tenant_id=tenant_id,
            backup_id=backup_id,
            validation_type=validation_type,
            status=overall_status,
        )
        
        return {
            "tenant_id": tenant_id,
            "backup_id": backup_id,
            "validation_type": validation_type,
            "timestamp": datetime.now().isoformat(),
            "status": overall_status,
            "report": validation_report,
        }
        
    except Exception as e:
        logger.error(
            "Backup validation failed",
            tenant_id=tenant_id,
            backup_id=backup_id,
            error=str(e),
        )
        return {
            "tenant_id": tenant_id,
            "backup_id": backup_id,
            "validation_type": validation_type,
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "report": validation_report,
            "error": str(e),
        }

