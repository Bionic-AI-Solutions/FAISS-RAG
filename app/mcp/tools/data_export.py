"""
MCP tools for data export operations (Epic 9).

Provides tenant and user data export tools for compliance (GDPR, HIPAA, SOC 2).
Access restricted to Uber Admin and Tenant Admin roles.
"""

import csv
import json
import os
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import text

from app.db.connection import get_db_session
from app.db.repositories.audit_log_repository import AuditLogRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.tenant_repository import TenantRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.mcp.middleware.rbac import UserRole, check_tool_permission
from app.mcp.middleware.tenant import get_tenant_id_from_context, get_role_from_context
from app.mcp.server import mcp_server
from app.services.mem0_client import Mem0Client
from app.services.redis_client import get_redis_client
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError
from app.utils.redis_keys import RedisKeyPatterns

logger = structlog.get_logger(__name__)

# Export configuration
EXPORT_BASE_DIR = Path(os.getenv("EXPORT_BASE_DIR", "/tmp/exports"))
EXPORT_BASE_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_EXPIRATION_DAYS = int(os.getenv("EXPORT_EXPIRATION_DAYS", "30"))  # Default 30 days

# Initialize Mem0 client singleton
mem0_client = Mem0Client()


def _convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert object to dictionary, handling various types."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_dict(item) for item in obj]
    elif isinstance(obj, (datetime, UUID)):
        return str(obj)
    else:
        return obj


async def _export_tenant_documents(
    tenant_id: UUID,
    date_range: Optional[Dict[str, datetime]] = None,
    data_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Export tenant documents."""
    async for session in get_db_session():
        await session.execute(
            text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_id}\'')
        )
        
        doc_repo = DocumentRepository(session)
        documents = await doc_repo.get_by_tenant(tenant_id, skip=0, limit=10000)
        
        # Apply date range filter if provided
        if date_range:
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            documents = [
                doc for doc in documents
                if (not start_date or doc.created_at >= start_date)
                and (not end_date or doc.created_at <= end_date)
            ]
        
        # Apply data type filter if provided
        if data_type:
            documents = [doc for doc in documents if doc.document_type == data_type]
        
        return [_convert_to_dict(doc) for doc in documents]


async def _export_tenant_memories(
    tenant_id: UUID,
    date_range: Optional[Dict[str, datetime]] = None,
) -> List[Dict[str, Any]]:
    """Export tenant memories from Mem0 and Redis."""
    memories = []
    
    try:
        # Ensure Mem0 client is initialized
        await mem0_client.initialize()
        
        # Get all users for tenant
        async for session in get_db_session():
            await session.execute(
                text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_id}\'')
            )
            
            user_repo = UserRepository(session)
            users = await user_repo.get_all(skip=0, limit=10000, tenant_id=tenant_id)
            
            # Get memories for each user
            for user in users:
                try:
                    # Try Mem0 search_memory with broad query to get all memories
                    search_result = await mem0_client.search_memory(
                        query="*",  # Broad query to get all memories
                        user_id=str(user.user_id),
                        limit=1000,  # High limit to get all memories
                    )
                    
                    if search_result.get("success"):
                        mem0_results = search_result.get("results", [])
                        
                        for result in mem0_results:
                            memory_dict = {
                                "user_id": str(user.user_id),
                                "tenant_id": str(tenant_id),
                                "memory_key": result.get("memory_key") or result.get("key") or "unknown",
                                "memory_value": result.get("memory") or result.get("value") or result.get("content"),
                                "timestamp": result.get("timestamp") or result.get("created_at") or datetime.utcnow().isoformat(),
                                "source": "mem0",
                                "metadata": result.get("metadata", {}),
                            }
                            
                            # Apply date range filter if provided
                            if date_range:
                                memory_timestamp_str = memory_dict.get("timestamp")
                                if memory_timestamp_str:
                                    try:
                                        if isinstance(memory_timestamp_str, str):
                                            memory_timestamp = datetime.fromisoformat(memory_timestamp_str.replace("Z", "+00:00"))
                                        else:
                                            memory_timestamp = memory_timestamp_str
                                        
                                        start_date = date_range.get("start")
                                        end_date = date_range.get("end")
                                        if (start_date and memory_timestamp < start_date) or (end_date and memory_timestamp > end_date):
                                            continue
                                    except (ValueError, AttributeError):
                                        pass  # Skip if timestamp parsing fails
                            
                            memories.append(memory_dict)
                    else:
                        # Mem0 search failed, fallback to Redis
                        raise Exception("Mem0 search returned unsuccessful result")
                        
                except Exception as e:
                    logger.warning("Failed to get memories from Mem0, trying Redis", user_id=str(user.user_id), error=str(e))
                    # Fallback to Redis
                    try:
                        redis_client = await get_redis_client()
                        memory_keys = await redis_client.keys(
                            RedisKeyPatterns.memory_key(str(tenant_id), str(user.user_id), "*")
                        )
                        
                        for key in memory_keys:
                            memory_data = await redis_client.get(key)
                            if memory_data:
                                try:
                                    memory_dict = json.loads(memory_data)
                                    memory_dict["user_id"] = str(user.user_id)
                                    memory_dict["tenant_id"] = str(tenant_id)
                                    memory_dict["source"] = "redis_fallback"
                                    memories.append(memory_dict)
                                except json.JSONDecodeError:
                                    logger.warning("Failed to parse memory data from Redis", key=key)
                    except Exception as e2:
                        logger.warning("Failed to get memories from Redis", user_id=str(user.user_id), error=str(e2))
    
    except Exception as e:
        logger.error("Failed to export tenant memories", tenant_id=str(tenant_id), error=str(e))
    
    return memories


async def _export_tenant_audit_logs(
    tenant_id: UUID,
    date_range: Optional[Dict[str, datetime]] = None,
) -> List[Dict[str, Any]]:
    """Export tenant audit logs."""
    async for session in get_db_session():
        await session.execute(
            text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_id}\'')
        )
        
        audit_repo = AuditLogRepository(session)
        
        if date_range:
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            if start_date and end_date:
                logs = await audit_repo.get_by_time_range(
                    start_time=start_date,
                    end_time=end_date,
                    tenant_id=tenant_id,
                    skip=0,
                    limit=10000,
                )
            else:
                # Get all logs if date range incomplete
                logs = await audit_repo.get_by_time_range(
                    start_time=datetime.now() - timedelta(days=365),
                    end_time=datetime.now(),
                    tenant_id=tenant_id,
                    skip=0,
                    limit=10000,
                )
        else:
            # Get all logs (last 365 days)
            logs = await audit_repo.get_by_time_range(
                start_time=datetime.now() - timedelta(days=365),
                end_time=datetime.now(),
                tenant_id=tenant_id,
                skip=0,
                limit=10000,
            )
        
        return [_convert_to_dict(log) for log in logs]


def _write_json_export(data: Dict[str, Any], export_file: Path) -> None:
    """Write data to JSON file."""
    with open(export_file, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _write_csv_export(data: Dict[str, Any], export_dir: Path) -> None:
    """Write data to CSV files (one per data type)."""
    for data_type, items in data.items():
        if not items or not isinstance(items, list):
            continue
        
        csv_file = export_dir / f"{data_type}.csv"
        
        if not items:
            continue
        
        # Get all unique keys from all items
        all_keys = set()
        for item in items:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        # Write CSV
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            
            for item in items:
                if isinstance(item, dict):
                    # Flatten nested dicts and convert to strings
                    row = {}
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            row[key] = json.dumps(value)
                        else:
                            row[key] = str(value) if value is not None else ""
                    writer.writerow(row)


@mcp_server.tool()
async def rag_export_tenant_data(
    tenant_id: str,
    export_format: str = "JSON",
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    data_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export tenant data for compliance and data portability.
    
    Exports all tenant data including:
    - Documents (all tenant documents)
    - Memories (user memories from Mem0/Redis)
    - Configurations (tenant configuration)
    - Audit logs (tenant audit trail)
    
    Supports filtering by date range and data type.
    Creates export package with manifest and stores in secure location with expiration.
    
    Access restricted to Uber Admin and Tenant Admin roles.
    
    Args:
        tenant_id: Tenant UUID (string format)
        export_format: Export format - "JSON" or "CSV" (default: "JSON")
        date_range_start: Optional start date for filtering (ISO 8601 format)
        date_range_end: Optional end date for filtering (ISO 8601 format)
        data_type: Optional data type filter (e.g., "document", "memory", "audit_log")
        
    Returns:
        Dictionary containing:
        - export_id: Unique export identifier
        - tenant_id: Tenant ID
        - export_format: Format used
        - export_timestamp: Export timestamp
        - expiration_date: Export expiration date
        - manifest: Export manifest with file paths, sizes, record counts
        - download_url: URL or path to download export (if available)
        - status: Export status
        
    Raises:
        AuthorizationError: If user doesn't have permission
        ResourceNotFoundError: If tenant not found
        ValidationError: If export_format or date range is invalid
    """
    # Check permissions
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context")
    check_tool_permission(current_role, "rag_export_tenant_data")
    if current_role not in {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN}:
        raise AuthorizationError("Access denied: Uber Admin or Tenant Admin role required")
    
    # Validate export_format
    if export_format.upper() not in {"JSON", "CSV"}:
        raise ValidationError(f"Invalid export_format: {export_format}. Must be 'JSON' or 'CSV'")
    
    tenant_uuid = UUID(tenant_id)
    
    # Validate tenant access (Tenant Admin can only export their own tenant)
    context_tenant_id = get_tenant_id_from_context()
    if current_role == UserRole.TENANT_ADMIN and context_tenant_id != tenant_uuid:
        raise AuthorizationError("Access denied: Tenant Admin can only export their own tenant data")
    
    # Parse date range if provided
    date_range = None
    if date_range_start or date_range_end:
        try:
            start_date = None
            end_date = None
            if date_range_start:
                start_date = datetime.fromisoformat(date_range_start.replace("Z", "+00:00"))
            if date_range_end:
                end_date = datetime.fromisoformat(date_range_end.replace("Z", "+00:00"))
            
            if start_date and end_date and start_date > end_date:
                raise ValidationError("date_range_start must be before date_range_end")
            
            date_range = {"start": start_date, "end": end_date}
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}")
    
    # Verify tenant exists
    async for session in get_db_session():
        await session.execute(
            text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_uuid}\'')
        )
        
        tenant_repo = TenantRepository(session)
        tenant = await tenant_repo.get_by_id(tenant_uuid)
        if not tenant:
            raise ResourceNotFoundError(f"Tenant {tenant_id} not found")
    
    # Create export directory
    export_timestamp = datetime.now()
    export_id = f"export_{tenant_id}_{export_timestamp.strftime('%Y%m%d_%H%M%S')}"
    export_dir = EXPORT_BASE_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Export tenant data
        logger.info("Starting tenant data export", tenant_id=tenant_id, export_format=export_format)
        
        # Export documents
        documents = []
        if not data_type or data_type == "document":
            documents = await _export_tenant_documents(tenant_uuid, date_range, data_type)
        
        # Export memories
        memories = []
        if not data_type or data_type == "memory":
            memories = await _export_tenant_memories(tenant_uuid, date_range)
        
        # Export audit logs
        audit_logs = []
        if not data_type or data_type == "audit_log":
            audit_logs = await _export_tenant_audit_logs(tenant_uuid, date_range)
        
        # Export tenant configuration
        config = None
        if not data_type or data_type == "configuration":
            async for session in get_db_session():
                await session.execute(
                    text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_uuid}\'')
                )
                
                config_repo = TenantConfigRepository(session)
                config = await config_repo.get_by_tenant_id(tenant_uuid)
        
        # Get tenant info
        tenant_info = None
        async for session in get_db_session():
            await session.execute(
                text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_uuid}\'')
            )
            
            tenant_repo = TenantRepository(session)
            tenant = await tenant_repo.get_by_id(tenant_uuid)
            if tenant:
                tenant_info = _convert_to_dict(tenant)
        
        # Prepare export data
        export_data = {
            "tenant": tenant_info,
            "documents": documents,
            "memories": memories,
            "audit_logs": audit_logs,
            "configuration": _convert_to_dict(config) if config else None,
            "export_metadata": {
                "export_id": export_id,
                "export_timestamp": export_timestamp.isoformat(),
                "export_format": export_format.upper(),
                "date_range": {
                    "start": date_range_start,
                    "end": date_range_end,
                } if date_range else None,
                "data_type_filter": data_type,
            },
        }
        
        # Write export files
        if export_format.upper() == "JSON":
            export_file = export_dir / "export.json"
            _write_json_export(export_data, export_file)
        else:  # CSV
            _write_csv_export(export_data, export_dir)
            # Also create a manifest JSON file
            manifest_file = export_dir / "manifest.json"
            _write_json_export({
                "export_id": export_id,
                "export_timestamp": export_timestamp.isoformat(),
                "export_format": "CSV",
                "files": [f"{data_type}.csv" for data_type in ["documents", "memories", "audit_logs", "configuration"] if export_data.get(data_type)],
            }, manifest_file)
        
        # Create export package (tar.gz)
        package_file = EXPORT_BASE_DIR / f"{export_id}.tar.gz"
        with tarfile.open(package_file, "w:gz") as tar:
            tar.add(export_dir, arcname=export_id)
        
        # Calculate expiration date
        expiration_date = export_timestamp + timedelta(days=EXPORT_EXPIRATION_DAYS)
        
        # Create manifest
        manifest = {
            "export_id": export_id,
            "tenant_id": tenant_id,
            "export_format": export_format.upper(),
            "export_timestamp": export_timestamp.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "package_file": str(package_file),
            "package_size": package_file.stat().st_size,
            "record_counts": {
                "documents": len(documents),
                "memories": len(memories),
                "audit_logs": len(audit_logs),
            },
            "filters": {
                "date_range": {
                    "start": date_range_start,
                    "end": date_range_end,
                } if date_range else None,
                "data_type": data_type,
            },
        }
        
        # Save manifest
        manifest_file = export_dir / "manifest.json"
        _write_json_export(manifest, manifest_file)
        
        logger.info(
            "Tenant data export completed",
            tenant_id=tenant_id,
            export_id=export_id,
            package_file=str(package_file),
        )
        
        return {
            "export_id": export_id,
            "tenant_id": tenant_id,
            "export_format": export_format.upper(),
            "export_timestamp": export_timestamp.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "manifest": manifest,
            "download_path": str(package_file),  # In production, this would be a secure URL
            "status": "completed",
        }
    
    except Exception as e:
        logger.error("Tenant data export failed", tenant_id=tenant_id, error=str(e))
        # Cleanup on failure
        if export_dir.exists():
            import shutil
            shutil.rmtree(export_dir)
        raise


@mcp_server.tool()
async def rag_export_user_data(
    user_id: str,
    tenant_id: str,
    export_format: str = "JSON",
) -> Dict[str, Any]:
    """
    Export user data for GDPR compliance (right to data portability).
    
    Exports all user-specific data including:
    - Memories (user memories from Mem0/Redis)
    - Session context (interrupted queries, session data)
    - Audit logs (user-specific audit trail)
    
    Creates export package with manifest and stores in secure location with expiration.
    
    Access restricted to user's own data (or Tenant Admin for user management).
    
    Args:
        user_id: User UUID (string format)
        tenant_id: Tenant UUID (string format)
        export_format: Export format - "JSON" or "CSV" (default: "JSON")
        
    Returns:
        Dictionary containing:
        - export_id: Unique export identifier
        - user_id: User ID
        - tenant_id: Tenant ID
        - export_format: Format used
        - export_timestamp: Export timestamp
        - expiration_date: Export expiration date
        - manifest: Export manifest with file paths, sizes, record counts
        - download_url: URL or path to download export (if available)
        - status: Export status
        
    Raises:
        AuthorizationError: If user tries to export another user's data (and is not Tenant Admin)
        ResourceNotFoundError: If user or tenant not found
        ValidationError: If export_format is invalid
    """
    # Check permissions
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context")
    check_tool_permission(current_role, "rag_export_user_data")
    
    user_uuid = UUID(user_id)
    tenant_uuid = UUID(tenant_id)
    
    # Validate user access (users can only export their own data, unless Tenant Admin)
    context_user_id = get_user_id_from_context()
    context_tenant_id = get_tenant_id_from_context()
    
    if current_role == UserRole.END_USER:
        if not context_user_id or UUID(context_user_id) != user_uuid:
            raise AuthorizationError("Access denied: Users can only export their own data")
        if context_tenant_id and context_tenant_id != tenant_uuid:
            raise AuthorizationError("Access denied: Tenant ID mismatch")
    elif current_role not in {UserRole.UBER_ADMIN, UserRole.TENANT_ADMIN}:
        raise AuthorizationError("Access denied: Uber Admin or Tenant Admin role required")
    
    # Tenant Admin can only export users from their own tenant
    if current_role == UserRole.TENANT_ADMIN:
        if context_tenant_id and context_tenant_id != tenant_uuid:
            raise AuthorizationError("Access denied: Tenant Admin can only export users from their own tenant")
    
    # Validate export_format
    if export_format.upper() not in {"JSON", "CSV"}:
        raise ValidationError(f"Invalid export_format: {export_format}. Must be 'JSON' or 'CSV'")
    
    # Verify user and tenant exist
    async for session in get_db_session():
        await session.execute(
            text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_uuid}\'')
        )
        
        tenant_repo = TenantRepository(session)
        tenant = await tenant_repo.get_by_id(tenant_uuid)
        if not tenant:
            raise ResourceNotFoundError(f"Tenant {tenant_id} not found")
        
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_uuid)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        if user.tenant_id != tenant_uuid:
            raise ValidationError(f"User {user_id} does not belong to tenant {tenant_id}")
    
    # Create export directory
    export_timestamp = datetime.now()
    export_id = f"export_user_{user_id}_{export_timestamp.strftime('%Y%m%d_%H%M%S')}"
    export_dir = EXPORT_BASE_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Export user data
        logger.info("Starting user data export", user_id=user_id, tenant_id=tenant_id, export_format=export_format)
        
        # Export memories
        memories = []
        try:
            await mem0_client.initialize()
            search_result = await mem0_client.search_memory(
                query="*",
                user_id=user_id,
                limit=1000,
            )
            
            if search_result.get("success"):
                mem0_results = search_result.get("results", [])
                for result in mem0_results:
                    memory_dict = {
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "memory_key": result.get("memory_key") or result.get("key") or "unknown",
                        "memory_value": result.get("memory") or result.get("value") or result.get("content"),
                        "timestamp": result.get("timestamp") or result.get("created_at") or datetime.utcnow().isoformat(),
                        "source": "mem0",
                        "metadata": result.get("metadata", {}),
                    }
                    memories.append(memory_dict)
            else:
                # Fallback to Redis
                redis_client = await get_redis_client()
                memory_keys = await redis_client.keys(
                    RedisKeyPatterns.memory_key(tenant_id, user_id, "*")
                )
                for key in memory_keys:
                    memory_data = await redis_client.get(key)
                    if memory_data:
                        try:
                            memory_dict = json.loads(memory_data)
                            memory_dict["user_id"] = user_id
                            memory_dict["tenant_id"] = tenant_id
                            memory_dict["source"] = "redis_fallback"
                            memories.append(memory_dict)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.warning("Failed to export user memories", user_id=user_id, error=str(e))
        
        # Export session context (interrupted queries)
        session_context = []
        try:
            redis_client = await get_redis_client()
            session_key = f"session:{tenant_id}:{user_id}:interrupted"
            interrupted_data = await redis_client.get(session_key)
            if interrupted_data:
                try:
                    session_context = json.loads(interrupted_data)
                    if not isinstance(session_context, list):
                        session_context = [session_context]
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.warning("Failed to export session context", user_id=user_id, error=str(e))
        
        # Export user-specific audit logs
        audit_logs = []
        try:
            async for session in get_db_session():
                await session.execute(
                    text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_uuid}\'')
                )
                
                audit_repo = AuditLogRepository(session)
                # Get all audit logs for this user (last 365 days)
                logs = await audit_repo.get_by_time_range(
                    start_time=datetime.now() - timedelta(days=365),
                    end_time=datetime.now(),
                    tenant_id=tenant_uuid,
                    skip=0,
                    limit=10000,
                )
                
                # Filter by user_id
                user_logs = [log for log in logs if log.user_id == user_uuid]
                audit_logs = [_convert_to_dict(log) for log in user_logs]
        except Exception as e:
            logger.warning("Failed to export user audit logs", user_id=user_id, error=str(e))
        
        # Prepare export data
        export_data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "memories": memories,
            "session_context": session_context,
            "audit_logs": audit_logs,
            "export_metadata": {
                "export_id": export_id,
                "export_timestamp": export_timestamp.isoformat(),
                "export_format": export_format.upper(),
            },
        }
        
        # Write export files
        if export_format.upper() == "JSON":
            export_file = export_dir / "export.json"
            _write_json_export(export_data, export_file)
        else:  # CSV
            _write_csv_export(export_data, export_dir)
            # Also create a manifest JSON file
            manifest_file = export_dir / "manifest.json"
            _write_json_export({
                "export_id": export_id,
                "export_timestamp": export_timestamp.isoformat(),
                "export_format": "CSV",
                "files": [f"{data_type}.csv" for data_type in ["memories", "session_context", "audit_logs"] if export_data.get(data_type)],
            }, manifest_file)
        
        # Create export package (tar.gz)
        package_file = EXPORT_BASE_DIR / f"{export_id}.tar.gz"
        with tarfile.open(package_file, "w:gz") as tar:
            tar.add(export_dir, arcname=export_id)
        
        # Calculate expiration date
        expiration_date = export_timestamp + timedelta(days=EXPORT_EXPIRATION_DAYS)
        
        # Create manifest
        manifest = {
            "export_id": export_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "export_format": export_format.upper(),
            "export_timestamp": export_timestamp.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "package_file": str(package_file),
            "package_size": package_file.stat().st_size,
            "record_counts": {
                "memories": len(memories),
                "session_context": len(session_context) if isinstance(session_context, list) else 1 if session_context else 0,
                "audit_logs": len(audit_logs),
            },
        }
        
        # Save manifest
        manifest_file = export_dir / "manifest.json"
        _write_json_export(manifest, manifest_file)
        
        logger.info(
            "User data export completed",
            user_id=user_id,
            tenant_id=tenant_id,
            export_id=export_id,
            package_file=str(package_file),
        )
        
        return {
            "export_id": export_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "export_format": export_format.upper(),
            "export_timestamp": export_timestamp.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "manifest": manifest,
            "download_path": str(package_file),  # In production, this would be a secure URL
            "status": "completed",
        }
    
    except Exception as e:
        logger.error("User data export failed", user_id=user_id, tenant_id=tenant_id, error=str(e))
        # Cleanup on failure
        if export_dir.exists():
            import shutil
            shutil.rmtree(export_dir)
        raise

