"""
MCP tools for monitoring, analytics, and usage statistics.

Provides tools for retrieving usage statistics, search analytics, memory analytics,
and system health monitoring.
"""

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
from app.mcp.server import mcp_server
from app.services.minio_client import create_minio_client, get_tenant_bucket
from app.services.redis_client import get_redis_client

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

