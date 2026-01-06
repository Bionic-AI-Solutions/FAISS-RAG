"""
Rate limiting middleware for per-tenant rate limiting.

Implements Redis-based sliding window algorithm for rate limiting.
Enforces per-tenant rate limits (default: 1000 hits/minute).
Returns 429 Too Many Requests with Retry-After header on violation.
"""

import asyncio
import time
from typing import Optional
from uuid import UUID

import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.config.settings import settings
from app.mcp.middleware.audit import log_audit_event
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.services.redis_client import get_redis_client
from app.utils.errors import RateLimitExceededError
from app.utils.redis_keys import RedisKeyPatterns

logger = structlog.get_logger(__name__)


async def check_rate_limit(
    tenant_id: UUID,
    limit: int = 1000,
    window_seconds: int = 60,
) -> tuple[bool, int, int, int]:
    """
    Check rate limit using Redis-based sliding window algorithm.
    
    Uses a sorted set in Redis to track requests within the time window.
    Each request is added with a score equal to the current timestamp.
    Requests older than the window are removed, and the count is checked.
    
    Args:
        tenant_id: Tenant ID for rate limit key
        limit: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds (default: 60 for 1 minute)
        
    Returns:
        tuple: (allowed, remaining, reset_time, retry_after)
            - allowed: True if request is allowed, False if rate limit exceeded
            - remaining: Number of requests remaining in the window
            - reset_time: Unix timestamp when the rate limit window resets
            - retry_after: Seconds until the rate limit window resets
    """
    try:
        redis_client = await get_redis_client()
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        # Generate rate limit key using tenant_id
        rate_limit_key = RedisKeyPatterns.rate_limit_key("tenant", tenant_id)
        
        # Use Redis sorted set to track requests
        # Key: tenant:{tenant_id}:rate_limit:tenant
        # Score: timestamp of request
        # Value: request identifier (we'll use timestamp as value too)
        
        # Remove old entries (outside the window)
        await redis_client.zremrangebyscore(
            rate_limit_key,
            min=0,
            max=window_start,
        )
        
        # Count current requests in the window
        current_count = await redis_client.zcard(rate_limit_key)
        
        # Check if limit exceeded
        if current_count >= limit:
            # Calculate reset time (oldest request in window + window_seconds)
            oldest_request = await redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
            if oldest_request:
                oldest_timestamp = int(oldest_request[0][1])
                reset_time = oldest_timestamp + window_seconds
            else:
                reset_time = current_time + window_seconds
            
            retry_after = max(1, reset_time - current_time)
            return (False, 0, reset_time, retry_after)
        
        # Add current request to the sorted set
        await redis_client.zadd(
            rate_limit_key,
            {str(current_time): current_time},
        )
        
        # Set TTL on the key to auto-cleanup (window_seconds + 1 minute buffer)
        await redis_client.expire(rate_limit_key, window_seconds + 60)
        
        # Calculate reset time (oldest request + window_seconds, or current_time + window_seconds if no old requests)
        oldest_request = await redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
        if oldest_request:
            oldest_timestamp = int(oldest_request[0][1])
            reset_time = oldest_timestamp + window_seconds
        else:
            reset_time = current_time + window_seconds
        
        remaining = limit - current_count - 1  # -1 because we just added this request
        return (True, remaining, reset_time, 0)
        
    except Exception as e:
        # If Redis is unavailable, log error but allow request (fail open)
        logger.error(
            "Rate limit check failed, allowing request",
            error=str(e),
            tenant_id=str(tenant_id),
        )
        # Fail open: allow request if rate limiting fails
        return (True, limit - 1, int(time.time()) + window_seconds, 0)


class RateLimitMiddleware(Middleware):
    """
    Rate limiting middleware for FastMCP server.
    
    Executes after authentication and tenant extraction to ensure we have tenant_id.
    Enforces per-tenant rate limits using Redis-based sliding window algorithm.
    """
    
    def __init__(self, limit: Optional[int] = None, window_seconds: Optional[int] = None):
        """
        Initialize rate limit middleware.
        
        Args:
            limit: Maximum number of requests allowed in the window (default: from settings)
            window_seconds: Time window in seconds (default: from settings)
        """
        self.limit = limit or settings.rate_limit_per_minute
        self.window_seconds = window_seconds or settings.rate_limit_window_seconds
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Check rate limit before tool execution.
        
        Args:
            context: Middleware context with FastMCP request information
            call_next: Next middleware or tool handler
            
        Returns:
            Response from next middleware/tool
            
        Raises:
            RateLimitExceededError: If rate limit is exceeded (429 Too Many Requests)
        """
        # Extract tenant_id from context
        tenant_id = get_tenant_id_from_context()
        user_id = get_user_id_from_context()
        role = get_role_from_context()
        
        if not tenant_id:
            # If no tenant_id, allow through (shouldn't happen after tenant extraction middleware)
            logger.warning("No tenant_id in context for rate limiting, allowing request")
            return await call_next(context)
        
        # Check rate limit
        allowed, remaining, reset_time, retry_after = await check_rate_limit(
            tenant_id=tenant_id,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )
        
        # Store rate limit info in context for response headers
        if not hasattr(context, "rate_limit_info"):
            context.rate_limit_info = {
                "limit": self.limit,
                "remaining": remaining,
                "reset_time": reset_time,
            }
        
        if not allowed:
            # Rate limit exceeded - log to audit and raise error
            logger.warning(
                "Rate limit exceeded",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
                limit=self.limit,
                window_seconds=self.window_seconds,
                retry_after=retry_after,
            )
            
            # Log rate limit violation to audit logs
            asyncio.create_task(
                log_audit_event(
                    action="rate_limit_exceeded",
                    resource_type="rate_limit",
                    resource_id=str(tenant_id),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role=role,
                    success=False,
                    details={
                        "limit": self.limit,
                        "window_seconds": self.window_seconds,
                        "retry_after": retry_after,
                        "reset_time": reset_time,
                    },
                )
            )
            
            # Raise error with retry_after and rate limit info
            raise RateLimitExceededError(
                message=f"Rate limit exceeded: {self.limit} requests per {self.window_seconds} seconds. Retry after {retry_after} seconds.",
                retry_after=retry_after,
                limit=self.limit,
                remaining=remaining,
                reset_time=reset_time,
            )
        
        # Rate limit not exceeded - continue to next middleware/tool
        logger.debug(
            "Rate limit check passed",
            tenant_id=str(tenant_id),
            remaining=remaining,
            limit=self.limit,
        )
        
        return await call_next(context)

