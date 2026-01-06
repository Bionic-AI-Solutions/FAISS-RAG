"""
Unit tests for rate limiting middleware.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.mcp.middleware.rate_limit import (
    RateLimitExceededError,
    RateLimitMiddleware,
    check_rate_limit,
)
from app.mcp.middleware.tenant import (
    _role_context,
    _tenant_id_context,
    _user_id_context,
)


class TestCheckRateLimit:
    """Test rate limit checking function."""
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_request(self):
        """Test that check_rate_limit allows request when under limit."""
        tenant_id = uuid4()
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard = AsyncMock(return_value=5)  # 5 requests, limit is 1000
        mock_redis.zadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.zrange = AsyncMock(return_value=[])  # No old requests
        
        with patch("app.mcp.middleware.rate_limit.get_redis_client", return_value=mock_redis):
            allowed, remaining, reset_time, retry_after = await check_rate_limit(
                tenant_id=tenant_id,
                limit=1000,
                window_seconds=60,
            )
            
            assert allowed is True
            assert remaining == 994  # 1000 - 5 - 1
            assert retry_after == 0
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_when_exceeded(self):
        """Test that check_rate_limit blocks request when limit exceeded."""
        tenant_id = uuid4()
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard = AsyncMock(return_value=1000)  # At limit
        mock_redis.zrange = AsyncMock(return_value=[("req1", 1000)])  # Oldest request at timestamp 1000
        
        with patch("app.mcp.middleware.rate_limit.get_redis_client", return_value=mock_redis):
            allowed, remaining, reset_time, retry_after = await check_rate_limit(
                tenant_id=tenant_id,
                limit=1000,
                window_seconds=60,
            )
            
            assert allowed is False
            assert remaining == 0
            assert retry_after > 0
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_fails_open_on_redis_error(self):
        """Test that check_rate_limit fails open (allows request) on Redis error."""
        tenant_id = uuid4()
        
        # Mock Redis client to raise error
        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch("app.mcp.middleware.rate_limit.get_redis_client", return_value=mock_redis):
            allowed, remaining, reset_time, retry_after = await check_rate_limit(
                tenant_id=tenant_id,
                limit=1000,
                window_seconds=60,
            )
            
            # Should fail open (allow request)
            assert allowed is True


class TestRateLimitMiddleware:
    """Test rate limit middleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_allows_request_under_limit(self):
        """Test that middleware allows request when under rate limit."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Set context variables
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("tenant_admin")
        
        # Mock context
        context = MagicMock()
        
        # Mock call_next
        call_next = AsyncMock(return_value={"result": "success"})
        
        # Mock check_rate_limit to allow request
        with patch("app.mcp.middleware.rate_limit.check_rate_limit") as mock_check:
            mock_check.return_value = (True, 999, 1000, 0)  # allowed, remaining, reset_time, retry_after
            
            middleware = RateLimitMiddleware(limit=1000, window_seconds=60)
            result = await middleware.on_request(context, call_next)
            
            assert call_next.called
            assert result == {"result": "success"}
            # Verify rate_limit_info was set (for response headers)
            assert hasattr(context, "rate_limit_info")
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_request_when_exceeded(self):
        """Test that middleware blocks request when rate limit exceeded."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Set context variables
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("tenant_admin")
        
        # Mock context
        context = MagicMock()
        
        # Mock call_next
        call_next = AsyncMock()
        
        # Mock check_rate_limit to block request
        with patch("app.mcp.middleware.rate_limit.check_rate_limit") as mock_check:
            mock_check.return_value = (False, 0, 1000, 30)  # not allowed, remaining=0, reset_time, retry_after=30
            
            # Mock log_audit_event
            with patch("app.mcp.middleware.rate_limit.log_audit_event") as mock_log:
                middleware = RateLimitMiddleware(limit=1000, window_seconds=60)
                
                with pytest.raises(RateLimitExceededError) as exc_info:
                    await middleware.on_request(context, call_next)
                
                assert "Rate limit exceeded" in str(exc_info.value)
                assert exc_info.value.retry_after == 30
                assert exc_info.value.error_code == "FR-ERROR-004"
                
                # Verify audit logging was called
                assert mock_log.called
    
    @pytest.mark.asyncio
    async def test_middleware_allows_request_when_no_tenant_id(self):
        """Test that middleware allows request when tenant_id not in context."""
        # Clear tenant_id from context
        _tenant_id_context.set(None)
        
        # Mock context
        context = MagicMock()
        
        # Mock call_next
        call_next = AsyncMock(return_value={"result": "success"})
        
        middleware = RateLimitMiddleware(limit=1000, window_seconds=60)
        result = await middleware.on_request(context, call_next)
        
        assert call_next.called
        assert result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_middleware_uses_settings_defaults(self):
        """Test that middleware uses settings defaults when not specified."""
        with patch("app.mcp.middleware.rate_limit.settings") as mock_settings:
            mock_settings.rate_limit_per_minute = 500
            mock_settings.rate_limit_window_seconds = 120
            
            middleware = RateLimitMiddleware()
            
            assert middleware.limit == 500
            assert middleware.window_seconds == 120

