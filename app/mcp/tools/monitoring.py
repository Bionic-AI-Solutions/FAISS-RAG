"""
MCP tools for monitoring, analytics, and usage statistics.

Provides tools for retrieving usage statistics, search analytics, memory analytics,
and system health monitoring.
"""

import asyncio
import json
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db_session
from app.db.models.audit_log import AuditLog
from app.db.models.document import Document
from app.db.repositories.audit_log_repository import AuditLogRepository
from app.mcp.middleware.rbac import UserRole, check_tool_permission, AuthorizationError
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
)
from app.utils.errors import ValidationError
from app.mcp.server import mcp_server
from app.services.minio_client import create_minio_client, get_tenant_bucket
from app.services.redis_client import get_redis_client
from app.services.health import check_all_services_health
from app.services.faiss_manager import faiss_manager, get_tenant_index_path
from app.services.meilisearch_client import create_meilisearch_client, get_tenant_index_name

logger = structlog.get_logger(__name__)

# Cache TTL for usage statistics (5 minutes for near real-time updates)
USAGE_STATS_CACHE_TTL = 300  # 5 minutes


async def _get_cached_stats(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached statistics from Redis."""
    try:
        redis_client = await get_redis_client()
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.warning("Failed to get cached stats", cache_key=cache_key, error=str(e))
    return None


async def _cache_stats(cache_key: str, stats: Dict[str, Any]) -> None:
    """Cache statistics in Redis."""
    try:
        redis_client = await get_redis_client()
        await redis_client.setex(
            cache_key,
            USAGE_STATS_CACHE_TTL,
            json.dumps(stats),
        )
    except Exception as e:
        logger.warning("Failed to cache stats", cache_key=cache_key, error=str(e))


async def _calculate_storage_usage(tenant_id: UUID) -> int:
    """
    Calculate total storage usage for a tenant in bytes.
    
    Includes:
    - MinIO object storage (document content)
    - PostgreSQL metadata (approximate)
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        Total storage usage in bytes
    """
    total_size = 0
    
    try:
        # Get MinIO bucket and calculate object sizes
        bucket_name = await get_tenant_bucket(tenant_id, create_if_missing=False)
        minio_client = create_minio_client()
        
        if minio_client.bucket_exists(bucket_name):
            objects = minio_client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                total_size += obj.size
    except Exception as e:
        logger.warning(
            "Failed to calculate MinIO storage",
            tenant_id=str(tenant_id),
            error=str(e),
        )
    
    # Add approximate PostgreSQL metadata size
    # Each document record is roughly 1KB (conservative estimate)
    try:
        async for session in get_db_session():
            try:
                query = select(func.count(Document.document_id)).where(
                    Document.tenant_id == tenant_id
                )
                result = await session.execute(query)
                doc_count = result.scalar() or 0
                total_size += doc_count * 1024  # 1KB per document metadata
            finally:
                await session.close()
            break
    except Exception as e:
        logger.warning(
            "Failed to calculate PostgreSQL storage",
            tenant_id=str(tenant_id),
            error=str(e),
        )
    
    return total_size


async def _aggregate_usage_statistics(
    tenant_id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    metrics_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Aggregate usage statistics from audit logs and system metrics.
    
    Args:
        tenant_id: Tenant ID
        start_time: Start timestamp for date range filtering
        end_time: End timestamp for date range filtering
        metrics_filter: Optional list of metrics to include (if None, include all)
        
    Returns:
        Dictionary with aggregated statistics
    """
    async for session in get_db_session():
        try:
            # Build base query filters
            filters = [AuditLog.tenant_id == tenant_id]
            
            if start_time:
                filters.append(AuditLog.timestamp >= start_time)
            if end_time:
                filters.append(AuditLog.timestamp <= end_time)
            
            # Aggregate search operations
            # Get all search logs and filter by success in Python (more reliable for testing)
            search_query = select(AuditLog).where(
                and_(
                    *filters,
                    AuditLog.action == "rag_search",
                )
            )
            search_logs_result = await session.execute(search_query)
            search_logs = search_logs_result.scalars().all()
            # Filter by success in Python
            total_searches = sum(
                1 for log in search_logs
                if log.details and isinstance(log.details, dict) and log.details.get("success", True)
            )
            
            # Aggregate memory operations (all mem0_* actions)
            memory_query = select(AuditLog).where(
                and_(
                    *filters,
                    AuditLog.action.like("mem0_%"),
                )
            )
            memory_logs_result = await session.execute(memory_query)
            memory_logs = memory_logs_result.scalars().all()
            # Filter by success in Python
            total_memory_operations = sum(
                1 for log in memory_logs
                if log.details and isinstance(log.details, dict) and log.details.get("success", True)
            )
            
            # Aggregate document operations (rag_ingest, rag_delete_document, etc.)
            document_actions = ["rag_ingest", "rag_delete_document", "rag_get_document", "rag_list_documents"]
            document_query = select(AuditLog).where(
                and_(
                    *filters,
                    AuditLog.action.in_(document_actions),
                )
            )
            document_logs_result = await session.execute(document_query)
            document_logs = document_logs_result.scalars().all()
            # Filter by success in Python
            total_document_operations = sum(
                1 for log in document_logs
                if log.details and isinstance(log.details, dict) and log.details.get("success", True)
            )
            
            # Count active users (distinct user_ids in date range)
            active_users_query = (
                select(func.count(distinct(AuditLog.user_id)))
                .where(and_(*filters, AuditLog.user_id.isnot(None)))
            )
            active_users_result = await session.execute(active_users_query)
            active_users = active_users_result.scalar() or 0
            
            # Calculate storage usage
            storage_usage = await _calculate_storage_usage(tenant_id)
            
            stats = {
                "total_searches": total_searches,
                "total_memory_operations": total_memory_operations,
                "total_document_operations": total_document_operations,
                "active_users": active_users,
                "storage_usage": storage_usage,
                "storage_usage_mb": round(storage_usage / (1024 * 1024), 2),
            }
            
            # Filter metrics if metrics_filter is provided
            if metrics_filter:
                filtered_stats = {
                    key: value
                    for key, value in stats.items()
                    if key in metrics_filter or key == "storage_usage_mb"  # Always include human-readable storage
                }
                # Ensure storage_usage is included if storage_usage_mb is requested
                if "storage_usage_mb" in metrics_filter and "storage_usage" not in metrics_filter:
                    filtered_stats["storage_usage"] = stats["storage_usage"]
                stats = filtered_stats
            
            return stats
        finally:
            await session.close()
        break


@mcp_server.tool()
async def rag_get_usage_stats(
    tenant_id: Optional[str] = None,
    date_range: Optional[str] = None,
    metrics_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve usage statistics for a tenant.
    
    Aggregates statistics from audit logs and system metrics including:
    - Total searches
    - Total memory operations
    - Total document operations
    - Active users
    - Storage usage
    
    Supports date range filtering and optional metrics filtering.
    Results are cached for 5 minutes for performance.
    
    Args:
        tenant_id: Tenant ID (UUID string). If not provided, uses tenant from context.
                   Uber Admin can query any tenant; Tenant Admin can only query their own tenant.
        date_range: Optional date range in format "start_time,end_time" (ISO 8601 format).
                    If not provided, defaults to last 30 days.
        metrics_filter: Optional comma-separated list of metrics to include.
                       Valid values: total_searches, total_memory_operations, total_document_operations,
                       active_users, storage_usage, storage_usage_mb
                       If not provided, all metrics are included.
    
    Returns:
        Dictionary containing usage statistics:
        {
            "tenant_id": "...",
            "date_range": {
                "start_time": "...",
                "end_time": "..."
            },
            "statistics": {
                "total_searches": 1234,
                "total_memory_operations": 567,
                "total_document_operations": 89,
                "active_users": 12,
                "storage_usage": 1048576,  # bytes
                "storage_usage_mb": 1.0
            },
            "cached": false,
            "timestamp": "..."
        }
    
    Raises:
        AuthorizationError: If user doesn't have permission
        ValueError: If tenant_id, date_range, or metrics_filter is invalid
    """
    # Check permissions
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context.")
    
    try:
        check_tool_permission(current_role, "rag_get_usage_stats")
    except AuthorizationError as e:
        raise AuthorizationError(f"Access denied: {str(e)}")
    
    # Get tenant ID
    current_tenant_id = get_tenant_id_from_context()
    
    query_tenant_id = None
    if tenant_id:
        try:
            query_tenant_id = UUID(tenant_id)
        except ValueError:
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")
        
        # Tenant Admin can only query their own tenant
        if current_role == UserRole.TENANT_ADMIN:
            if query_tenant_id != current_tenant_id:
                raise AuthorizationError(
                    "Tenant Admin can only query usage statistics for their own tenant"
                )
    else:
        # Use tenant from context
        if current_role == UserRole.TENANT_ADMIN:
            query_tenant_id = current_tenant_id
            if not query_tenant_id:
                raise ValueError("Tenant ID is required for Tenant Admin")
        elif current_role == UserRole.UBER_ADMIN:
            raise ValueError("Uber Admin must provide tenant_id parameter")
        else:
            raise AuthorizationError("Access denied: Only Tenant Admin and Uber Admin can query usage statistics")
    
    # Parse date range
    start_time = None
    end_time = None
    
    if date_range:
        try:
            parts = date_range.split(",")
            if len(parts) != 2:
                raise ValueError("date_range must be in format 'start_time,end_time'")
            start_time_str = parts[0].strip()
            end_time_str = parts[1].strip()
            
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid date_range format: {date_range}. Use ISO 8601 format. Error: {str(e)}")
    else:
        # Default to last 30 days
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
    
    # Parse metrics filter
    metrics_list = None
    if metrics_filter:
        metrics_list = [m.strip() for m in metrics_filter.split(",")]
        valid_metrics = {
            "total_searches",
            "total_memory_operations",
            "total_document_operations",
            "active_users",
            "storage_usage",
            "storage_usage_mb",
        }
        invalid_metrics = [m for m in metrics_list if m not in valid_metrics]
        if invalid_metrics:
            raise ValueError(
                f"Invalid metrics in metrics_filter: {invalid_metrics}. "
                f"Valid values: {', '.join(valid_metrics)}"
            )
    
    # Build cache key
    cache_key = f"usage_stats:{query_tenant_id}:{start_time.isoformat()}:{end_time.isoformat()}"
    if metrics_list:
        cache_key += f":{','.join(sorted(metrics_list))}"
    
    # Try to get from cache
    cached_stats = await _get_cached_stats(cache_key)
    if cached_stats:
        logger.debug("Usage statistics retrieved from cache", tenant_id=str(query_tenant_id))
        return {
            **cached_stats,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # Aggregate statistics
    logger.info(
        "Aggregating usage statistics",
        tenant_id=str(query_tenant_id),
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
    )
    
    stats = await _aggregate_usage_statistics(
        tenant_id=query_tenant_id,
        start_time=start_time,
        end_time=end_time,
        metrics_filter=metrics_list,
    )
    
    # Prepare response
    result = {
        "tenant_id": str(query_tenant_id),
        "date_range": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        "statistics": stats,
        "cached": False,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Cache the result
    await _cache_stats(cache_key, result)
    
    logger.info(
        "Usage statistics aggregated",
        tenant_id=str(query_tenant_id),
        total_searches=stats.get("total_searches", 0),
        total_memory_operations=stats.get("total_memory_operations", 0),
        total_document_operations=stats.get("total_document_operations", 0),
        active_users=stats.get("active_users", 0),
        storage_usage_mb=stats.get("storage_usage_mb", 0),
    )
    
    return result


async def _aggregate_search_analytics(
    tenant_id: UUID,
    start_time: datetime,
    end_time: datetime,
    session: AsyncSession,
    user_id: Optional[UUID] = None,
    document_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Aggregate search analytics from audit logs.
    
    Args:
        tenant_id: Tenant ID
        start_time: Start of the date range
        end_time: End of the date range
        session: SQLAlchemy async session
        user_id: Optional user ID filter
        document_type: Optional document type filter
        
    Returns:
        dict: Aggregated search analytics
    """
    filters = [
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == "rag_search",
        AuditLog.timestamp >= start_time,
        AuditLog.timestamp <= end_time,
    ]
    
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    
    # Fetch all relevant audit logs for search operations
    audit_logs_query = select(AuditLog).where(and_(*filters))
    audit_logs_result = await session.execute(audit_logs_query)
    all_audit_logs = audit_logs_result.scalars().all()
    
    # Filter for successful post-execution logs only
    search_logs = [
        log for log in all_audit_logs
        if log.details
        and log.details.get("phase") == "post_execution"
        and log.details.get("execution_success", False)
    ]
    
    if not search_logs:
        return {
            "total_searches": 0,
            "average_response_time": 0.0,
            "top_queries": [],
            "zero_result_queries": [],
            "search_trends": {},
        }
    
    # Extract metrics from logs
    total_searches = len(search_logs)
    response_times = []
    queries = []
    zero_result_queries = []
    search_trends: Dict[str, int] = {}  # Date -> count
    
    for log in search_logs:
        details = log.details or {}
        
        # Extract response time
        duration_ms = details.get("duration_ms", 0)
        if duration_ms:
            response_times.append(duration_ms)
        
        # Extract search query from request_params
        request_params = details.get("request_params", {})
        query = request_params.get("search_query") or request_params.get("query", "")
        if query:
            queries.append(query)
        
        # Check for zero results (from result_summary or details)
        result_summary = details.get("result_summary", "")
        total_results = None
        if result_summary:
            # Try to extract total_results from result_summary
            # Format: "{'total_results': 0, ...}"
            if "'total_results': 0" in result_summary or '"total_results": 0' in result_summary:
                total_results = 0
            elif "'total_results':" in result_summary or '"total_results":' in result_summary:
                # Try to extract number
                match = re.search(r"'total_results':\s*(\d+)", result_summary)
                if not match:
                    match = re.search(r'"total_results":\s*(\d+)', result_summary)
                if match:
                    total_results = int(match.group(1))
        
        # If we can't determine total_results, check if result_summary suggests zero results
        if total_results == 0 and query:
            zero_result_queries.append(query)
        
        # Filter by document_type if specified
        if document_type:
            doc_type_filter = request_params.get("document_type")
            if doc_type_filter != document_type:
                continue
        
        # Aggregate trends by date (YYYY-MM-DD)
        date_key = log.timestamp.date().isoformat()
        search_trends[date_key] = search_trends.get(date_key, 0) + 1
    
    # Calculate average response time
    average_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    
    # Get top queries (most frequent)
    query_counts = Counter(queries)
    top_queries = [
        {"query": query, "count": count}
        for query, count in query_counts.most_common(10)
    ]
    
    # Get unique zero result queries
    zero_result_queries_unique = list(set(zero_result_queries))[:10]
    
    return {
        "total_searches": total_searches,
        "average_response_time": round(average_response_time, 2),
        "top_queries": top_queries,
        "zero_result_queries": zero_result_queries_unique,
        "search_trends": search_trends,
    }


@mcp_server.tool()
async def rag_get_search_analytics(
    tenant_id: Optional[str] = None,
    date_range: Optional[str] = None,
    user_id: Optional[str] = None,
    document_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve search analytics for a tenant.
    
    Aggregates search analytics from audit logs including:
    - Total searches
    - Average response time
    - Top queries (most frequent)
    - Zero result queries
    - Search trends over time
    
    Supports filtering by date range, user_id, and document_type.
    Results are cached for 5 minutes for performance.
    
    Args:
        tenant_id: Tenant ID (UUID string). If not provided, uses tenant from context.
                   Uber Admin can query any tenant; Tenant Admin can only query their own tenant.
        date_range: Optional date range in format "start_time,end_time" (ISO 8601 format).
                    If not provided, defaults to last 30 days.
        user_id: Optional user ID (UUID string) to filter searches by specific user.
        document_type: Optional document type filter (e.g., "text", "pdf", "markdown").
    
    Returns:
        Dictionary containing search analytics:
        {
            "tenant_id": "...",
            "date_range": {
                "start_time": "...",
                "end_time": "..."
            },
            "analytics": {
                "total_searches": 1234,
                "average_response_time": 45.67,  # milliseconds
                "top_queries": [
                    {"query": "example query", "count": 42},
                    ...
                ],
                "zero_result_queries": ["query1", "query2", ...],
                "search_trends": {
                    "2025-01-15": 50,
                    "2025-01-16": 75,
                    ...
                }
            },
            "filters": {
                "user_id": "...",
                "document_type": "..."
            },
            "cached": false,
            "timestamp": "..."
        }
    
    Raises:
        AuthorizationError: If user doesn't have permission
        ValueError: If tenant_id, date_range, user_id, or document_type is invalid
    """
    # Check permissions
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context.")
    
    try:
        check_tool_permission(current_role, "rag_get_search_analytics")
    except AuthorizationError as e:
        raise AuthorizationError(f"Access denied: {str(e)}")
    
    # Get tenant ID
    current_tenant_id = get_tenant_id_from_context()
    
    query_tenant_id = None
    if tenant_id:
        try:
            query_tenant_id = UUID(tenant_id)
        except ValueError:
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")
        
        # Tenant Admin can only query their own tenant
        if current_role == UserRole.TENANT_ADMIN and query_tenant_id != current_tenant_id:
            raise AuthorizationError(
                "Tenant Admin can only query search analytics for their own tenant."
            )
    else:
        # If no tenant_id provided, use current tenant from context for Tenant Admin
        if current_role == UserRole.TENANT_ADMIN:
            query_tenant_id = current_tenant_id
        elif current_role != UserRole.UBER_ADMIN:
            # For other roles (e.g., END_USER), tenant_id is mandatory
            raise ValueError("Tenant ID is required for this role.")
    
    if not query_tenant_id and current_role != UserRole.UBER_ADMIN:
        raise ValueError("Tenant ID must be provided or available in context.")
    
    # Parse date range
    start_datetime: datetime
    end_datetime: datetime
    
    if date_range:
        try:
            start_time_str, end_time_str = date_range.split(",")
            start_datetime = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            end_datetime = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(
                f"Invalid date_range format: {date_range}. Use 'start_time,end_time' in ISO 8601 format."
            )
    else:
        # Default to last 30 days
        end_datetime = datetime.utcnow()
        start_datetime = end_datetime - timedelta(days=30)
    
    # Parse user_id filter
    query_user_id: Optional[UUID] = None
    if user_id:
        try:
            query_user_id = UUID(user_id)
        except ValueError:
            raise ValueError(f"Invalid user_id format: {user_id}")
    
    # Build cache key
    cache_key = (
        f"search_analytics:{query_tenant_id}:"
        f"{start_datetime.isoformat()}:{end_datetime.isoformat()}"
    )
    if query_user_id:
        cache_key += f":user:{query_user_id}"
    if document_type:
        cache_key += f":doc_type:{document_type}"
    
    # Try to get from cache
    cached_analytics = await _get_cached_stats(cache_key)
    if cached_analytics:
        logger.info("Returning cached search analytics", tenant_id=str(query_tenant_id))
        return {
            **cached_analytics,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    logger.info(
        "Aggregating search analytics",
        tenant_id=str(query_tenant_id),
        start_time=start_datetime,
        end_time=end_datetime,
        user_id=str(query_user_id) if query_user_id else None,
        document_type=document_type,
    )
    
    async for session in get_db_session():
        try:
            analytics = await _aggregate_search_analytics(
                tenant_id=query_tenant_id,
                start_time=start_datetime,
                end_time=end_datetime,
                session=session,
                user_id=query_user_id,
                document_type=document_type,
            )
            
            # Prepare response
            result = {
                "tenant_id": str(query_tenant_id),
                "date_range": {
                    "start_time": start_datetime.isoformat(),
                    "end_time": end_datetime.isoformat(),
                },
                "analytics": analytics,
                "filters": {
                    "user_id": str(query_user_id) if query_user_id else None,
                    "document_type": document_type,
                },
                "cached": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Cache the result
            await _cache_stats(cache_key, result)
            
            logger.info(
                "Search analytics aggregated",
                tenant_id=str(query_tenant_id),
                total_searches=analytics["total_searches"],
                average_response_time=analytics["average_response_time"],
            )
            
            return result
        finally:
            await session.close()
        break


async def _aggregate_memory_analytics(
    tenant_id: UUID,
    start_time: datetime,
    end_time: datetime,
    session: AsyncSession,
    user_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Aggregate memory analytics from audit logs.
    
    Args:
        tenant_id: Tenant ID
        start_time: Start of the date range
        end_time: End of the date range
        session: SQLAlchemy async session
        user_id: Optional user ID filter
        
    Returns:
        dict: Aggregated memory analytics
    """
    filters = [
        AuditLog.tenant_id == tenant_id,
        AuditLog.action.like("mem0_%"),
        AuditLog.timestamp >= start_time,
        AuditLog.timestamp <= end_time,
    ]
    
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    
    # Fetch all relevant audit logs for memory operations
    audit_logs_query = select(AuditLog).where(and_(*filters))
    audit_logs_result = await session.execute(audit_logs_query)
    all_audit_logs = audit_logs_result.scalars().all()
    
    # Filter for successful post-execution logs only
    memory_logs = [
        log for log in all_audit_logs
        if log.details
        and log.details.get("phase") == "post_execution"
        and log.details.get("execution_success", False)
    ]
    
    if not memory_logs:
        return {
            "total_memories": 0,
            "active_users": 0,
            "memory_usage_trends": {},
            "top_memory_keys": [],
            "memory_access_patterns": {
                "mem0_get_user_memory": 0,
                "mem0_update_memory": 0,
                "mem0_search_memory": 0,
            },
        }
    
    # Extract metrics from logs
    total_memories = len(memory_logs)
    active_user_ids = set()
    memory_keys = []
    access_patterns = {
        "mem0_get_user_memory": 0,
        "mem0_update_memory": 0,
        "mem0_search_memory": 0,
    }
    memory_trends: Dict[str, int] = {}  # Date -> count
    
    for log in memory_logs:
        # Track active users
        if log.user_id:
            active_user_ids.add(log.user_id)
        
        # Track access patterns
        action = log.action
        if action in access_patterns:
            access_patterns[action] += 1
        
        # Extract memory_key from request_params or resource_id
        request_params = log.details.get("request_params", {})
        memory_key = request_params.get("memory_key") or log.resource_id
        if memory_key:
            memory_keys.append(memory_key)
        
        # Aggregate trends by date (YYYY-MM-DD)
        date_key = log.timestamp.date().isoformat()
        memory_trends[date_key] = memory_trends.get(date_key, 0) + 1
    
    # Get top memory keys (most frequent)
    memory_key_counts = Counter(memory_keys)
    top_memory_keys = [
        {"memory_key": key, "count": count}
        for key, count in memory_key_counts.most_common(10)
    ]
    
    return {
        "total_memories": total_memories,
        "active_users": len(active_user_ids),
        "memory_usage_trends": memory_trends,
        "top_memory_keys": top_memory_keys,
        "memory_access_patterns": access_patterns,
    }


@mcp_server.tool()
async def rag_get_memory_analytics(
    tenant_id: Optional[str] = None,
    date_range: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve memory analytics for a tenant.
    
    Aggregates memory analytics from audit logs including:
    - Total memory operations
    - Active users with memory operations
    - Memory usage trends over time
    - Top memory keys (most frequently accessed)
    - Memory access patterns (get, update, search)
    
    Supports filtering by date range and user_id.
    Results are cached for 5 minutes for performance.
    
    Args:
        tenant_id: Tenant ID (UUID string). If not provided, uses tenant from context.
                   Uber Admin can query any tenant; Tenant Admin can only query their own tenant.
        date_range: Optional date range in format "start_time,end_time" (ISO 8601 format).
                    If not provided, defaults to last 30 days.
        user_id: Optional user ID (UUID string) to filter memory operations by specific user.
    
    Returns:
        Dictionary containing memory analytics:
        {
            "tenant_id": "...",
            "date_range": {
                "start_time": "...",
                "end_time": "..."
            },
            "analytics": {
                "total_memories": 1234,
                "active_users": 45,
                "memory_usage_trends": {
                    "2025-01-15": 50,
                    "2025-01-16": 75,
                    ...
                },
                "top_memory_keys": [
                    {"memory_key": "user_preference", "count": 42},
                    ...
                ],
                "memory_access_patterns": {
                    "mem0_get_user_memory": 800,
                    "mem0_update_memory": 300,
                    "mem0_search_memory": 134
                }
            },
            "filters": {
                "user_id": "..."
            },
            "cached": false,
            "timestamp": "..."
        }
    
    Raises:
        AuthorizationError: If user doesn't have permission
        ValueError: If tenant_id, date_range, or user_id is invalid
    """
    # Check permissions
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context.")
    
    try:
        check_tool_permission(current_role, "rag_get_memory_analytics")
    except AuthorizationError as e:
        raise AuthorizationError(f"Access denied: {str(e)}")
    
    # Get tenant ID
    current_tenant_id = get_tenant_id_from_context()
    
    query_tenant_id = None
    if tenant_id:
        try:
            query_tenant_id = UUID(tenant_id)
        except ValueError:
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")
        
        # Tenant Admin can only query their own tenant
        if current_role == UserRole.TENANT_ADMIN and query_tenant_id != current_tenant_id:
            raise AuthorizationError(
                "Tenant Admin can only query memory analytics for their own tenant."
            )
    else:
        # If no tenant_id provided, use current tenant from context for Tenant Admin
        if current_role == UserRole.TENANT_ADMIN:
            query_tenant_id = current_tenant_id
        elif current_role != UserRole.UBER_ADMIN:
            # For other roles (e.g., END_USER), tenant_id is mandatory
            raise ValueError("Tenant ID is required for this role.")
    
    if not query_tenant_id and current_role != UserRole.UBER_ADMIN:
        raise ValueError("Tenant ID must be provided or available in context.")
    
    # Parse date range
    start_datetime: datetime
    end_datetime: datetime
    
    if date_range:
        try:
            start_time_str, end_time_str = date_range.split(",")
            start_datetime = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            end_datetime = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(
                f"Invalid date_range format: {date_range}. Use 'start_time,end_time' in ISO 8601 format."
            )
    else:
        # Default to last 30 days
        end_datetime = datetime.utcnow()
        start_datetime = end_datetime - timedelta(days=30)
    
    # Parse user_id filter
    query_user_id: Optional[UUID] = None
    if user_id:
        try:
            query_user_id = UUID(user_id)
        except ValueError:
            raise ValueError(f"Invalid user_id format: {user_id}")
    
    # Build cache key
    cache_key = (
        f"memory_analytics:{query_tenant_id}:"
        f"{start_datetime.isoformat()}:{end_datetime.isoformat()}"
    )
    if query_user_id:
        cache_key += f":user:{query_user_id}"
    
    # Try to get from cache
    cached_analytics = await _get_cached_stats(cache_key)
    if cached_analytics:
        logger.info("Returning cached memory analytics", tenant_id=str(query_tenant_id))
        return {
            **cached_analytics,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    logger.info(
        "Aggregating memory analytics",
        tenant_id=str(query_tenant_id),
        start_time=start_datetime,
        end_time=end_datetime,
        user_id=str(query_user_id) if query_user_id else None,
    )
    
    async for session in get_db_session():
        try:
            analytics = await _aggregate_memory_analytics(
                tenant_id=query_tenant_id,
                start_time=start_datetime,
                end_time=end_datetime,
                session=session,
                user_id=query_user_id,
            )
            
            # Prepare response
            result = {
                "tenant_id": str(query_tenant_id),
                "date_range": {
                    "start_time": start_datetime.isoformat(),
                    "end_time": end_datetime.isoformat(),
                },
                "analytics": analytics,
                "filters": {
                    "user_id": str(query_user_id) if query_user_id else None,
                },
                "cached": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Cache the result
            await _cache_stats(cache_key, result)
            
            logger.info(
                "Memory analytics aggregated",
                tenant_id=str(query_tenant_id),
                total_memories=analytics["total_memories"],
                active_users=analytics["active_users"],
            )
            
            return result
        finally:
            await session.close()
        break


async def _collect_performance_metrics(
    session: AsyncSession,
    time_window_minutes: int = 5,
) -> Dict[str, Any]:
    """
    Collect performance metrics from audit logs for the last N minutes.
    
    Args:
        session: Database session
        time_window_minutes: Time window in minutes (default: 5)
    
    Returns:
        Dictionary with performance metrics:
        {
            "average_response_time_ms": float,
            "p95_response_time_ms": float,
            "p99_response_time_ms": float,
            "total_requests": int,
            "requests_per_second": float,
        }
    """
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # Query audit logs for the time window
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time,
                )
            )
            .order_by(AuditLog.timestamp.desc())
        )
        
        result = await session.execute(query)
        all_logs = result.scalars().all()
        
        # Filter for successful post-execution requests and extract response times
        response_times = []
        total_requests = 0
        
        for log in all_logs:
            if (
                log.details
                and log.details.get("phase") == "post_execution"
                and log.details.get("execution_success", False)
            ):
                total_requests += 1
                # Extract response time from details
                response_time = log.details.get("response_time_ms")
                if response_time is not None:
                    response_times.append(response_time)
        
        if not response_times:
            return {
                "average_response_time_ms": 0.0,
                "p95_response_time_ms": 0.0,
                "p99_response_time_ms": 0.0,
                "total_requests": total_requests,
                "requests_per_second": 0.0,
            }
        
        # Calculate statistics
        response_times_sorted = sorted(response_times)
        avg_response_time = sum(response_times) / len(response_times)
        
        # Calculate percentiles
        p95_index = int(len(response_times_sorted) * 0.95)
        p99_index = int(len(response_times_sorted) * 0.99)
        
        p95_response_time = response_times_sorted[min(p95_index, len(response_times_sorted) - 1)]
        p99_response_time = response_times_sorted[min(p99_index, len(response_times_sorted) - 1)]
        
        # Calculate requests per second
        time_window_seconds = time_window_minutes * 60
        requests_per_second = total_requests / time_window_seconds if time_window_seconds > 0 else 0.0
        
        return {
            "average_response_time_ms": round(avg_response_time, 2),
            "p95_response_time_ms": round(p95_response_time, 2),
            "p99_response_time_ms": round(p99_response_time, 2),
            "total_requests": total_requests,
            "requests_per_second": round(requests_per_second, 2),
        }
    except Exception as e:
        logger.error("Failed to collect performance metrics", error=str(e))
        return {
            "average_response_time_ms": 0.0,
            "p95_response_time_ms": 0.0,
            "p99_response_time_ms": 0.0,
            "total_requests": 0,
            "requests_per_second": 0.0,
        }


async def _calculate_error_rates(
    session: AsyncSession,
    time_window_minutes: int = 5,
) -> Dict[str, Any]:
    """
    Calculate error rates from audit logs for the last N minutes.
    
    Args:
        session: Database session
        time_window_minutes: Time window in minutes (default: 5)
    
    Returns:
        Dictionary with error rates:
        {
            "total_requests": int,
            "successful_requests": int,
            "failed_requests": int,
            "error_rate_percent": float,
            "errors_by_type": Dict[str, int],
        }
    """
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # Query audit logs for the time window
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time,
                )
            )
        )
        
        result = await session.execute(query)
        all_logs = result.scalars().all()
        
        # Filter for post-execution logs only
        logs = [
            log
            for log in all_logs
            if log.details and log.details.get("phase") == "post_execution"
        ]
        
        total_requests = len(logs)
        successful_requests = 0
        failed_requests = 0
        errors_by_type = Counter()
        
        for log in logs:
            if log.details:
                success = log.details.get("execution_success", False)
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    # Extract error type from details
                    error_type = log.details.get("error_type", "unknown")
                    errors_by_type[error_type] += 1
        
        error_rate_percent = (
            (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "error_rate_percent": round(error_rate_percent, 2),
            "errors_by_type": dict(errors_by_type),
        }
    except Exception as e:
        logger.error("Failed to calculate error rates", error=str(e))
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "error_rate_percent": 0.0,
            "errors_by_type": {},
        }


def _generate_health_summary_and_recommendations(
    component_status: Dict[str, Any],
    performance_metrics: Dict[str, Any],
    error_rates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate health summary and recommendations based on component status, performance, and error rates.
    
    Args:
        component_status: Component health status from check_all_services_health
        performance_metrics: Performance metrics from audit logs
        error_rates: Error rates from audit logs
    
    Returns:
        Dictionary with summary and recommendations:
        {
            "overall_status": str,  # "healthy", "degraded", "unhealthy"
            "summary": str,
            "degraded_components": List[str],
            "unhealthy_components": List[str],
            "recommendations": List[str],
        }
    """
    services = component_status.get("services", {})
    degraded_components = []
    unhealthy_components = []
    
    # Identify degraded and unhealthy components
    for service_name, service_status in services.items():
        if not service_status.get("status", False):
            unhealthy_components.append(service_name)
        elif "degraded" in service_status.get("message", "").lower():
            degraded_components.append(service_name)
    
    # Determine overall status
    if unhealthy_components:
        overall_status = "unhealthy"
    elif degraded_components:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    # Check performance metrics
    p95_response_time = performance_metrics.get("p95_response_time_ms", 0.0)
    if p95_response_time > 1000:  # > 1 second
        if overall_status == "healthy":
            overall_status = "degraded"
        recommendations = [
            f"High p95 response time ({p95_response_time}ms). Consider optimizing queries or scaling resources.",
        ]
    else:
        recommendations = []
    
    # Check error rates
    error_rate = error_rates.get("error_rate_percent", 0.0)
    if error_rate > 5.0:  # > 5% error rate
        if overall_status == "healthy":
            overall_status = "degraded"
        recommendations.append(
            f"High error rate ({error_rate}%). Investigate error patterns and system stability.",
        )
    elif error_rate > 1.0:  # > 1% error rate
        recommendations.append(
            f"Elevated error rate ({error_rate}%). Monitor closely for degradation.",
        )
    
    # Add component-specific recommendations
    if unhealthy_components:
        recommendations.append(
            f"Critical: {', '.join(unhealthy_components)} are unhealthy. Immediate attention required.",
        )
    if degraded_components:
        recommendations.append(
            f"Warning: {', '.join(degraded_components)} are degraded. Monitor and investigate.",
        )
    
    # Generate summary
    if overall_status == "healthy":
        summary = "All systems operational. No issues detected."
    elif overall_status == "degraded":
        summary = f"System is degraded. {len(degraded_components)} component(s) experiencing issues."
    else:
        summary = f"System is unhealthy. {len(unhealthy_components)} critical component(s) are down."
    
    if not recommendations:
        recommendations = ["No immediate action required. System is operating normally."]
    
    return {
        "overall_status": overall_status,
        "summary": summary,
        "degraded_components": degraded_components,
        "unhealthy_components": unhealthy_components,
        "recommendations": recommendations,
    }


@mcp_server.tool()
async def rag_get_system_health() -> Dict[str, Any]:
    """
    Retrieve overall system health status.
    
    Aggregates health from all components (PostgreSQL, FAISS, Mem0, Redis, Meilisearch, MinIO),
    collects performance metrics, calculates error rates, and provides health summary and recommendations.
    
    Results are cached for 30 seconds for performance (health checks should be near real-time).
    
    Returns:
        Dictionary containing system health:
        {
            "overall_status": "healthy" | "degraded" | "unhealthy",
            "component_status": {
                "postgresql": {"status": bool, "message": str},
                "redis": {"status": bool, "message": str},
                "minio": {"status": bool, "message": str},
                "meilisearch": {"status": bool, "message": str},
                "mem0": {"status": bool, "message": str},
                "faiss": {"status": bool, "message": str},
            },
            "performance_metrics": {
                "average_response_time_ms": float,
                "p95_response_time_ms": float,
                "p99_response_time_ms": float,
                "total_requests": int,
                "requests_per_second": float,
            },
            "error_rates": {
                "total_requests": int,
                "successful_requests": int,
                "failed_requests": int,
                "error_rate_percent": float,
                "errors_by_type": Dict[str, int],
            },
            "health_summary": {
                "overall_status": str,
                "summary": str,
                "degraded_components": List[str],
                "unhealthy_components": List[str],
                "recommendations": List[str],
            },
            "cached": bool,
            "timestamp": str,
        }
    
    Raises:
        AuthorizationError: If user doesn't have permission (Uber Admin only)
    """
    # Check permissions (Uber Admin only)
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context.")
    
    try:
        check_tool_permission(current_role, "rag_get_system_health")
    except AuthorizationError as e:
        raise AuthorizationError(f"Access denied: {str(e)}")
    
    # Check cache (30 second TTL for near real-time health checks)
    cache_key = "system_health"
    cached_health = await _get_cached_stats(cache_key)
    if cached_health:
        logger.debug("System health retrieved from cache")
        return {
            **cached_health,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    logger.info("Collecting system health status")
    
    # Check all services health in parallel
    component_status = await check_all_services_health()
    
    # Collect performance metrics and error rates from audit logs
    async for session in get_db_session():
        try:
            performance_metrics = await _collect_performance_metrics(session, time_window_minutes=5)
            error_rates = await _calculate_error_rates(session, time_window_minutes=5)
            
            # Generate health summary and recommendations
            health_summary = _generate_health_summary_and_recommendations(
                component_status,
                performance_metrics,
                error_rates,
            )
            
            # Prepare response
            result = {
                "overall_status": health_summary["overall_status"],
                "component_status": component_status.get("services", {}),
                "performance_metrics": performance_metrics,
                "error_rates": error_rates,
                "health_summary": health_summary,
                "cached": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Cache the result (30 second TTL - use shorter TTL for health checks)
            # Override the default cache TTL for this specific key
            try:
                redis_client = await get_redis_client()
                await redis_client.setex(
                    cache_key,
                    30,  # 30 seconds for near real-time health checks
                    json.dumps(result),
                )
            except Exception as e:
                logger.warning("Failed to cache system health", error=str(e))
            
            logger.info(
                "System health collected",
                overall_status=health_summary["overall_status"],
                unhealthy_components=len(health_summary["unhealthy_components"]),
                degraded_components=len(health_summary["degraded_components"]),
            )
            
            return result
        finally:
            await session.close()
        break


async def _check_tenant_faiss_health(tenant_id: UUID) -> Dict[str, Any]:
    """
    Check tenant-specific FAISS index health.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        dict: Health status for tenant's FAISS index
    """
    try:
        index_file = get_tenant_index_path(tenant_id)
        
        if not index_file.exists():
            return {
                "status": False,
                "message": f"FAISS index not found for tenant {tenant_id}",
            }
        
        # Check index file properties (size, readability)
        try:
            index_size = index_file.stat().st_size
            if index_size == 0:
                return {
                    "status": False,
                    "message": f"FAISS index file is empty for tenant {tenant_id}",
                }
            
            # Try to read a small portion to verify it's readable
            with open(index_file, "rb") as f:
                f.read(1)  # Read first byte to verify file is readable
            
            return {
                "status": True,
                "message": f"FAISS index is operational (Size: {index_size} bytes)",
            }
        except PermissionError as e:
            return {
                "status": False,
                "message": f"FAISS index file not readable for tenant {tenant_id}: {str(e)}",
            }
        except Exception as e:
            return {
                "status": False,
                "message": f"FAISS index health check failed: {str(e)}",
            }
    except Exception as e:
        return {
            "status": False,
            "message": f"FAISS health check error: {str(e)}",
        }


async def _check_tenant_minio_health(tenant_id: UUID) -> Dict[str, Any]:
    """
    Check tenant-specific MinIO bucket health.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        dict: Health status for tenant's MinIO bucket
    """
    try:
        bucket_name = await get_tenant_bucket(tenant_id, create_if_missing=False)
        client = create_minio_client()
        
        if not client.bucket_exists(bucket_name):
            return {
                "status": False,
                "message": f"MinIO bucket '{bucket_name}' not found for tenant {tenant_id}",
            }
        
        # Try to list objects to verify bucket is accessible
        try:
            objects = list(client.list_objects(bucket_name, recursive=False, max_keys=1))
            return {
                "status": True,
                "message": f"MinIO bucket '{bucket_name}' is operational",
            }
        except Exception as e:
            return {
                "status": False,
                "message": f"MinIO bucket health check failed: {str(e)}",
            }
    except Exception as e:
        return {
            "status": False,
            "message": f"MinIO health check error: {str(e)}",
        }


async def _check_tenant_meilisearch_health(tenant_id: UUID) -> Dict[str, Any]:
    """
    Check tenant-specific Meilisearch index health.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        dict: Health status for tenant's Meilisearch index
    """
    try:
        client = create_meilisearch_client()
        index_name = await get_tenant_index_name(str(tenant_id))
        
        try:
            index = client.get_index(index_name)
            # Try to get index stats to verify it's accessible
            stats = index.get_stats()
            return {
                "status": True,
                "message": f"Meilisearch index '{index_name}' is operational (Documents: {stats.get('numberOfDocuments', 0)})",
            }
        except Exception as e:
            # Index doesn't exist or is inaccessible
            return {
                "status": False,
                "message": f"Meilisearch index '{index_name}' not found or inaccessible: {str(e)}",
            }
    except Exception as e:
        return {
            "status": False,
            "message": f"Meilisearch health check error: {str(e)}",
        }


async def _collect_tenant_performance_metrics(
    session: AsyncSession,
    tenant_id: UUID,
    time_window_minutes: int = 5,
) -> Dict[str, Any]:
    """
    Collect tenant-specific performance metrics from audit logs.
    
    Args:
        session: Database session
        tenant_id: Tenant ID
        time_window_minutes: Time window in minutes (default: 5)
    
    Returns:
        Dictionary with performance metrics filtered by tenant_id
    """
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # Query audit logs for the time window, filtered by tenant_id
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time,
                    AuditLog.tenant_id == tenant_id,
                )
            )
            .order_by(AuditLog.timestamp.desc())
        )
        
        result = await session.execute(query)
        all_logs = result.scalars().all()
        
        # Filter for successful post-execution requests and extract response times
        response_times = []
        total_requests = 0
        
        for log in all_logs:
            if (
                log.details
                and log.details.get("phase") == "post_execution"
                and log.details.get("execution_success", False)
            ):
                total_requests += 1
                if "response_time_ms" in log.details:
                    response_times.append(log.details["response_time_ms"])
        
        # Calculate metrics
        if response_times:
            import numpy as np
            average_response_time = sum(response_times) / len(response_times)
            p95_response_time = float(np.percentile(response_times, 95))
            p99_response_time = float(np.percentile(response_times, 99))
        else:
            average_response_time = 0.0
            p95_response_time = 0.0
            p99_response_time = 0.0
        
        # Calculate requests per second
        time_window_seconds = time_window_minutes * 60
        requests_per_second = (
            total_requests / time_window_seconds if time_window_seconds > 0 else 0.0
        )
        
        return {
            "average_response_time_ms": round(average_response_time, 2),
            "p95_response_time_ms": round(p95_response_time, 2),
            "p99_response_time_ms": round(p99_response_time, 2),
            "total_requests": total_requests,
            "requests_per_second": round(requests_per_second, 2),
        }
    except Exception as e:
        logger.error("Failed to collect tenant performance metrics", tenant_id=str(tenant_id), error=str(e))
        return {
            "average_response_time_ms": 0.0,
            "p95_response_time_ms": 0.0,
            "p99_response_time_ms": 0.0,
            "total_requests": 0,
            "requests_per_second": 0.0,
        }


async def _calculate_tenant_error_rates(
    session: AsyncSession,
    tenant_id: UUID,
    time_window_minutes: int = 5,
) -> Dict[str, Any]:
    """
    Calculate tenant-specific error rates from audit logs.
    
    Args:
        session: Database session
        tenant_id: Tenant ID
        time_window_minutes: Time window in minutes (default: 5)
    
    Returns:
        Dictionary with error rates filtered by tenant_id
    """
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # Query audit logs for the time window, filtered by tenant_id
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_time,
                    AuditLog.timestamp <= end_time,
                    AuditLog.tenant_id == tenant_id,
                )
            )
        )
        
        result = await session.execute(query)
        all_logs = result.scalars().all()
        
        # Filter for post-execution logs only
        logs = [
            log
            for log in all_logs
            if log.details and log.details.get("phase") == "post_execution"
        ]
        
        total_requests = len(logs)
        successful_requests = 0
        failed_requests = 0
        errors_by_type = Counter()
        
        for log in logs:
            if log.details.get("execution_success", False):
                successful_requests += 1
            else:
                failed_requests += 1
                # Extract error type from details
                error_type = log.details.get("error_type", "unknown")
                errors_by_type[error_type] += 1
        
        error_rate_percent = (
            (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "error_rate_percent": round(error_rate_percent, 2),
            "errors_by_type": dict(errors_by_type),
        }
    except Exception as e:
        logger.error("Failed to calculate tenant error rates", tenant_id=str(tenant_id), error=str(e))
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "error_rate_percent": 0.0,
            "errors_by_type": {},
        }


def _generate_tenant_health_summary_and_recommendations(
    component_status: Dict[str, Any],
    performance_metrics: Dict[str, Any],
    error_rates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate tenant health summary and recommendations.
    
    Args:
        component_status: Tenant-specific component health status
        performance_metrics: Tenant-specific performance metrics
        error_rates: Tenant-specific error rates
    
    Returns:
        Dictionary with summary and recommendations
    """
    degraded_components = []
    unhealthy_components = []
    
    # Identify degraded and unhealthy components
    for component_name, component_status_info in component_status.items():
        if not component_status_info.get("status", False):
            unhealthy_components.append(component_name)
        elif "degraded" in component_status_info.get("message", "").lower():
            degraded_components.append(component_name)
    
    # Determine overall status
    if unhealthy_components:
        overall_status = "unhealthy"
    elif degraded_components:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    recommendations = []
    
    # Check performance metrics
    p95_response_time = performance_metrics.get("p95_response_time_ms", 0.0)
    if p95_response_time > 1000:  # > 1 second
        if overall_status == "healthy":
            overall_status = "degraded"
        recommendations.append(
            f"High p95 response time ({p95_response_time}ms). Consider optimizing queries or scaling resources.",
        )
    
    # Check error rates
    error_rate = error_rates.get("error_rate_percent", 0.0)
    if error_rate > 5.0:  # > 5% error rate
        if overall_status == "healthy":
            overall_status = "degraded"
        recommendations.append(
            f"High error rate ({error_rate}%). Investigate error patterns and system stability.",
        )
    elif error_rate > 1.0:  # > 1% error rate
        recommendations.append(
            f"Elevated error rate ({error_rate}%). Monitor closely for degradation.",
        )
    
    # Add component-specific recommendations
    if unhealthy_components:
        recommendations.append(
            f"Critical: {', '.join(unhealthy_components)} are unhealthy. Immediate attention required.",
        )
    if degraded_components:
        recommendations.append(
            f"Warning: {', '.join(degraded_components)} are degraded. Monitor and investigate.",
        )
    
    # Generate summary
    if overall_status == "healthy":
        summary = "Tenant operations are healthy. No issues detected."
    elif overall_status == "degraded":
        summary = f"Tenant is experiencing degraded performance. {len(degraded_components)} component(s) experiencing issues."
    else:
        summary = f"Tenant is unhealthy. {len(unhealthy_components)} critical component(s) are down."
    
    if not recommendations:
        recommendations = ["No immediate action required. Tenant is operating normally."]
    
    return {
        "overall_status": overall_status,
        "summary": summary,
        "degraded_components": degraded_components,
        "unhealthy_components": unhealthy_components,
        "recommendations": recommendations,
    }


@mcp_server.tool()
async def rag_get_tenant_health(tenant_id: str) -> Dict[str, Any]:
    """
    Retrieve tenant-specific health status.
    
    Aggregates health from tenant-specific components (FAISS index, MinIO bucket, Meilisearch index),
    collects tenant-specific usage and performance metrics, calculates error rates, and provides
    health summary and recommendations.
    
    Results are cached for 30 seconds for performance (health checks should be near real-time).
    
    Args:
        tenant_id: Tenant UUID (string format)
    
    Returns:
        Dictionary containing tenant health:
        {
            "tenant_id": str,
            "tenant_status": "healthy" | "degraded" | "unhealthy",
            "component_status": {
                "faiss": {"status": bool, "message": str},
                "minio": {"status": bool, "message": str},
                "meilisearch": {"status": bool, "message": str},
            },
            "usage_metrics": {
                "total_documents": int,
                "total_searches": int,
                "total_memory_operations": int,
                "storage_usage_bytes": int,
            },
            "performance_metrics": {
                "average_response_time_ms": float,
                "p95_response_time_ms": float,
                "p99_response_time_ms": float,
                "total_requests": int,
                "requests_per_second": float,
            },
            "error_rates": {
                "total_requests": int,
                "successful_requests": int,
                "failed_requests": int,
                "error_rate_percent": float,
                "errors_by_type": Dict[str, int],
            },
            "health_summary": {
                "overall_status": str,
                "summary": str,
                "degraded_components": List[str],
                "unhealthy_components": List[str],
                "recommendations": List[str],
            },
            "cached": bool,
            "timestamp": str,
        }
    
    Raises:
        AuthorizationError: If user doesn't have permission (Uber Admin or Tenant Admin only)
        ValidationError: If tenant_id is invalid
    """
    # Check permissions (Uber Admin or Tenant Admin)
    current_role = get_role_from_context()
    if not current_role:
        raise AuthorizationError("Role not found in context.")
    
    try:
        check_tool_permission(current_role, "rag_get_tenant_health")
    except AuthorizationError as e:
        raise AuthorizationError(f"Access denied: {str(e)}")
    
    # Validate tenant_id
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise ValidationError(f"Invalid tenant_id format: {tenant_id}", field="tenant_id")
    
    # For Tenant Admin, ensure they can only access their own tenant
    context_tenant_id = get_tenant_id_from_context()
    if current_role == UserRole.TENANT_ADMIN and context_tenant_id != tenant_uuid:
        raise AuthorizationError(
            f"Tenant Admin can only access their own tenant. Requested: {tenant_id}, Context: {context_tenant_id}"
        )
    
    # Check cache (30 second TTL for near real-time health checks)
    cache_key = f"tenant_health:{tenant_id}"
    cached_health = await _get_cached_stats(cache_key)
    if cached_health:
        logger.debug("Tenant health retrieved from cache", tenant_id=tenant_id)
        return {
            **cached_health,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    logger.info("Collecting tenant health status", tenant_id=tenant_id)
    
    # Check tenant-specific components in parallel
    faiss_health, minio_health, meilisearch_health = await asyncio.gather(
        _check_tenant_faiss_health(tenant_uuid),
        _check_tenant_minio_health(tenant_uuid),
        _check_tenant_meilisearch_health(tenant_uuid),
        return_exceptions=True,
    )
    
    component_status = {
        "faiss": faiss_health if not isinstance(faiss_health, Exception) else {"status": False, "message": str(faiss_health)},
        "minio": minio_health if not isinstance(minio_health, Exception) else {"status": False, "message": str(minio_health)},
        "meilisearch": meilisearch_health if not isinstance(meilisearch_health, Exception) else {"status": False, "message": str(meilisearch_health)},
    }
    
    # Collect tenant-specific usage metrics
    usage_metrics = {
        "total_documents": 0,
        "total_searches": 0,
        "total_memory_operations": 0,
        "storage_usage_bytes": 0,
    }
    
    try:
        # Get document count
        async for session in get_db_session():
            try:
                doc_count_query = select(func.count(Document.id)).where(Document.tenant_id == tenant_uuid)
                doc_count_result = await session.execute(doc_count_query)
                usage_metrics["total_documents"] = doc_count_result.scalar() or 0
            except Exception as e:
                logger.warning("Failed to get document count", tenant_id=tenant_id, error=str(e))
            finally:
                await session.close()
            break
        
        # Get storage usage
        usage_metrics["storage_usage_bytes"] = await _calculate_storage_usage(tenant_uuid)
        
        # Get search and memory operation counts from audit logs (last 24 hours)
        async for session in get_db_session():
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)
                
                # Count searches
                search_query = (
                    select(func.count(AuditLog.id))
                    .where(
                        and_(
                            AuditLog.timestamp >= start_time,
                            AuditLog.timestamp <= end_time,
                            AuditLog.tenant_id == tenant_uuid,
                            AuditLog.action == "rag_search",
                        )
                    )
                )
                search_result = await session.execute(search_query)
                usage_metrics["total_searches"] = search_result.scalar() or 0
                
                # Count memory operations
                memory_query = (
                    select(func.count(AuditLog.id))
                    .where(
                        and_(
                            AuditLog.timestamp >= start_time,
                            AuditLog.timestamp <= end_time,
                            AuditLog.tenant_id == tenant_uuid,
                            AuditLog.action.in_(["rag_get_user_memory", "rag_update_memory"]),
                        )
                    )
                )
                memory_result = await session.execute(memory_query)
                usage_metrics["total_memory_operations"] = memory_result.scalar() or 0
            except Exception as e:
                logger.warning("Failed to get usage metrics", tenant_id=tenant_id, error=str(e))
            finally:
                await session.close()
            break
    except Exception as e:
        logger.warning("Failed to collect usage metrics", tenant_id=tenant_id, error=str(e))
    
    # Collect tenant-specific performance metrics and error rates from audit logs
    async for session in get_db_session():
        try:
            performance_metrics = await _collect_tenant_performance_metrics(session, tenant_uuid, time_window_minutes=5)
            error_rates = await _calculate_tenant_error_rates(session, tenant_uuid, time_window_minutes=5)
            
            # Generate health summary and recommendations
            health_summary = _generate_tenant_health_summary_and_recommendations(
                component_status,
                performance_metrics,
                error_rates,
            )
            
            # Prepare response
            result = {
                "tenant_id": tenant_id,
                "tenant_status": health_summary["overall_status"],
                "component_status": component_status,
                "usage_metrics": usage_metrics,
                "performance_metrics": performance_metrics,
                "error_rates": error_rates,
                "health_summary": health_summary,
                "cached": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Cache the result (30 second TTL - use shorter TTL for health checks)
            try:
                redis_client = await get_redis_client()
                await redis_client.setex(
                    cache_key,
                    30,  # 30 seconds for near real-time health checks
                    json.dumps(result),
                )
            except Exception as e:
                logger.warning("Failed to cache tenant health", tenant_id=tenant_id, error=str(e))
            
            logger.info(
                "Tenant health collected",
                tenant_id=tenant_id,
                tenant_status=health_summary["overall_status"],
                unhealthy_components=len(health_summary["unhealthy_components"]),
                degraded_components=len(health_summary["degraded_components"]),
            )
            
            return result
        finally:
            await session.close()
        break

