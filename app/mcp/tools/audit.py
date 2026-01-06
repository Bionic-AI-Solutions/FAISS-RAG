"""
MCP tools for audit log querying.

Provides rag_query_audit_logs tool for querying audit logs with filtering and pagination.
Access restricted to Tenant Admin and Uber Admin roles only.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from fastmcp.server.dependencies import get_http_headers

from app.db.connection import get_db_session
from app.db.models.audit_log import AuditLog
from app.db.repositories.audit_log_repository import AuditLogRepository
from app.mcp.middleware.rbac import UserRole, check_tool_permission
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.mcp.server import mcp_server

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_query_audit_logs(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    role: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    result_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Query audit logs with filtering and pagination.
    
    Supports filtering by:
    - Timestamp range (start_time, end_time in ISO 8601 format)
    - Actor (user_id, tenant_id, role)
    - Action type (action_type)
    - Resource (resource_type, resource_id)
    - Result status (result_status: "success" or "failure")
    
    Supports pagination with limit and offset.
    
    Access restricted to Tenant Admin and Uber Admin roles only.
    
    Args:
        start_time: Start timestamp (ISO 8601 format, e.g., "2025-01-15T00:00:00Z")
        end_time: End timestamp (ISO 8601 format, e.g., "2025-01-15T23:59:59Z")
        user_id: Filter by user ID (UUID string)
        tenant_id: Filter by tenant ID (UUID string)
        role: Filter by role (e.g., "tenant_admin", "uber_admin")
        action_type: Filter by action type (e.g., "rag_search", "mem0_add_memory")
        resource_type: Filter by resource type (e.g., "document", "memory", "search")
        resource_id: Filter by resource ID
        result_status: Filter by result status ("success" or "failure")
        limit: Maximum number of results to return (default: 100, max: 1000)
        offset: Number of results to skip (default: 0)
        
    Returns:
        dict: Query results with logs and pagination info:
        {
            "logs": [
                {
                    "log_id": "...",
                    "timestamp": "...",
                    "tenant_id": "...",
                    "user_id": "...",
                    "action": "...",
                    "resource_type": "...",
                    "resource_id": "...",
                    "details": {...},
                    "success": true/false
                },
                ...
            ],
            "total": 123,
            "limit": 100,
            "offset": 0,
            "has_more": true/false
        }
        
    Raises:
        ValueError: If access is denied (not Tenant Admin or Uber Admin)
        ValueError: If invalid filter parameters provided
    """
    # Check role permission (Tenant Admin or Uber Admin only)
    current_role = get_role_from_context()
    if not current_role:
        raise ValueError("Role not found in context")
    
    # Check if role has permission (Tenant Admin or Uber Admin)
    from app.mcp.middleware.rbac import AuthorizationError, check_tool_permission
    try:
        check_tool_permission(current_role, "rag_query_audit_logs")
    except AuthorizationError as e:
        raise ValueError(f"Access denied: {str(e)}")
    
    # Get current tenant_id and user_id from context
    current_tenant_id = get_tenant_id_from_context()
    current_user_id = get_user_id_from_context()
    
    # Tenant Admin can only query their own tenant's logs
    # Uber Admin can query all logs
    query_tenant_id = None
    if current_role == UserRole.TENANT_ADMIN:
        # Tenant Admin restricted to their own tenant
        query_tenant_id = current_tenant_id
        if tenant_id and UUID(tenant_id) != current_tenant_id:
            raise ValueError(
                "Tenant Admin can only query audit logs for their own tenant"
            )
    elif current_role == UserRole.UBER_ADMIN:
        # Uber Admin can query any tenant (or all tenants if tenant_id not specified)
        if tenant_id:
            query_tenant_id = UUID(tenant_id)
    else:
        raise ValueError("Access denied: Only Tenant Admin and Uber Admin can query audit logs")
    
    # Validate limit
    if limit < 1 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")
    
    if offset < 0:
        raise ValueError("Offset must be >= 0")
    
    # Parse timestamps
    start_datetime = None
    end_datetime = None
    
    if start_time:
        try:
            start_datetime = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid start_time format: {start_time}. Use ISO 8601 format.")
    
    if end_time:
        try:
            end_datetime = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid end_time format: {end_time}. Use ISO 8601 format.")
    
    # Parse UUIDs
    query_user_id = None
    if user_id:
        try:
            query_user_id = UUID(user_id)
        except ValueError:
            raise ValueError(f"Invalid user_id format: {user_id}")
    
    # Query audit logs
    try:
        async for session in get_db_session():
            try:
                audit_repo = AuditLogRepository(session)
                
                # Build query filters
                # Use repository methods to query
                logs = []
                total = 0
                
                # If time range specified, use get_by_time_range
                if start_datetime and end_datetime:
                    logs = await audit_repo.get_by_time_range(
                        start_time=start_datetime,
                        end_time=end_datetime,
                        tenant_id=query_tenant_id,
                        skip=offset,
                        limit=limit,
                    )
                    # Get total count (simplified - would need separate count query for production)
                    total = len(logs) + offset  # Approximation
                elif action_type:
                    # Use get_by_action
                    logs = await audit_repo.get_by_action(
                        action=action_type,
                        tenant_id=query_tenant_id,
                        skip=offset,
                        limit=limit,
                    )
                    total = len(logs) + offset  # Approximation
                elif resource_type and resource_id:
                    # Use get_by_resource
                    logs = await audit_repo.get_by_resource(
                        resource_type=resource_type,
                        resource_id=resource_id,
                        tenant_id=query_tenant_id,
                    )
                    total = len(logs)
                else:
                    # Use async SQLAlchemy 2.0 select syntax
                    query = select(AuditLog)
                    count_query = select(func.count()).select_from(AuditLog)
                    
                    # Build filter conditions
                    filters = []
                    
                    if query_tenant_id:
                        filters.append(AuditLog.tenant_id == query_tenant_id)
                    if query_user_id:
                        filters.append(AuditLog.user_id == query_user_id)
                    if action_type:
                        filters.append(AuditLog.action == action_type)
                    if resource_type:
                        filters.append(AuditLog.resource_type == resource_type)
                    if resource_id:
                        filters.append(AuditLog.resource_id == resource_id)
                    if start_datetime:
                        filters.append(AuditLog.timestamp >= start_datetime)
                    if end_datetime:
                        filters.append(AuditLog.timestamp <= end_datetime)
                    
                    # Apply result_status filter (from details JSON)
                    if result_status:
                        if result_status == "success":
                            filters.append(
                                AuditLog.details["success"].astext == "true"
                            )
                        elif result_status == "failure":
                            filters.append(
                                AuditLog.details["success"].astext == "false"
                            )
                    
                    # Apply role filter (from details JSON)
                    if role:
                        filters.append(AuditLog.details["role"].astext == role)
                    
                    # Apply filters to both queries
                    if filters:
                        query = query.where(and_(*filters))
                        count_query = count_query.where(and_(*filters))
                    
                    # Order by timestamp descending
                    query = query.order_by(AuditLog.timestamp.desc())
                    
                    # Get total count
                    total_result = await session.execute(count_query)
                    total = total_result.scalar() or 0
                    
                    # Apply pagination
                    query = query.offset(offset).limit(limit)
                    logs_result = await session.execute(query)
                    logs = list(logs_result.scalars().all())
                
                # Format results
                formatted_logs = []
                for log in logs:
                    log_dict = {
                        "log_id": str(log.log_id),
                        "timestamp": log.timestamp.isoformat(),
                        "tenant_id": str(log.tenant_id) if log.tenant_id else None,
                        "user_id": str(log.user_id) if log.user_id else None,
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "details": log.details or {},
                    }
                    
                    # Extract success from details
                    if log.details and isinstance(log.details, dict):
                        log_dict["success"] = log.details.get("success", True)
                        log_dict["role"] = log.details.get("role")
                        log_dict["auth_method"] = log.details.get("auth_method")
                    else:
                        log_dict["success"] = True
                    
                    formatted_logs.append(log_dict)
                
                # Determine if there are more results
                has_more = (offset + len(formatted_logs)) < total
                
                logger.info(
                    "Audit logs queried",
                    tenant_id=str(query_tenant_id) if query_tenant_id else None,
                    user_id=str(query_user_id) if query_user_id else None,
                    action_type=action_type,
                    total=total,
                    returned=len(formatted_logs),
                )
                
                return {
                    "logs": formatted_logs,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": has_more,
                }
            finally:
                await session.close()
            break  # Only use first session from generator
    except Exception as e:
        logger.error(
            "Error querying audit logs",
            error=str(e),
            tenant_id=str(query_tenant_id) if query_tenant_id else None,
        )
        raise ValueError(f"Error querying audit logs: {str(e)}")


