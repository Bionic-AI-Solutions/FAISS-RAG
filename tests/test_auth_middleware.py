"""
Tests for authentication middleware integration.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.config.auth import auth_settings
from app.mcp.middleware.auth import AuthenticationError, AuthenticationMiddleware
from app.mcp.middleware.context import MCPContext


@pytest.fixture
def mock_middleware_context():
    """Mock MiddlewareContext."""
    context = MagicMock()
    context.fastmcp_context = MagicMock()
    context.fastmcp_context.request_context = None
    return context


@pytest.fixture
def mock_call_next():
    """Mock call_next function."""
    return AsyncMock(return_value={"result": "success"})


class TestAuthenticationMiddleware:
    """Tests for AuthenticationMiddleware class."""

    @pytest.mark.asyncio
    async def test_middleware_executes_first(self, mock_middleware_context, mock_call_next):
        """Test that middleware executes before tool execution."""
        middleware = AuthenticationMiddleware()
        
        with patch("app.mcp.middleware.auth.get_http_headers", return_value={"Authorization": "Bearer test-token"}):
            with patch(
                "app.mcp.middleware.auth.authenticate_request",
                return_value=MCPContext(
                    tenant_id=uuid4(),
                    user_id=uuid4(),
                    role="user",
                ),
            ):
                result = await middleware.on_request(mock_middleware_context, mock_call_next)
                
                # Verify call_next was called (middleware didn't block)
                mock_call_next.assert_called_once()
                assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_middleware_stores_auth_context(self, mock_middleware_context, mock_call_next):
        """Test that middleware stores authenticated context."""
        middleware = AuthenticationMiddleware()
        tenant_id = uuid4()
        user_id = uuid4()
        role = "user"
        
        auth_context = MCPContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
        )
        
        # Use a real object instead of MagicMock to properly test attribute assignment
        from types import SimpleNamespace
        real_context = SimpleNamespace()
        real_context.fastmcp_context = SimpleNamespace()
        real_context.fastmcp_context.request_context = None
        
        with patch("app.mcp.middleware.auth.get_http_headers", return_value={"Authorization": "Bearer test-token"}):
            with patch(
                "app.mcp.middleware.auth.authenticate_request",
                return_value=auth_context,
            ):
                await middleware.on_request(real_context, mock_call_next)
                
                # Verify context was stored
                assert hasattr(real_context, "auth_context")
                assert real_context.auth_context == auth_context
                
                # Verify FastMCP context was updated
                assert hasattr(real_context.fastmcp_context, "auth_context")
                assert real_context.fastmcp_context.user_id == str(user_id)
                assert real_context.fastmcp_context.tenant_id == str(tenant_id)
                assert real_context.fastmcp_context.role == role

    @pytest.mark.asyncio
    async def test_middleware_prevents_execution_on_auth_failure(
        self, mock_middleware_context, mock_call_next
    ):
        """Test that middleware prevents tool execution on authentication failure."""
        middleware = AuthenticationMiddleware()
        
        with patch("app.mcp.middleware.auth.get_http_headers", return_value={}):
            with patch(
                "app.mcp.middleware.auth.authenticate_request",
                side_effect=AuthenticationError("Authentication required", error_code="FR-ERROR-003"),
            ):
                with pytest.raises(ValueError, match="Authentication failed"):
                    await middleware.on_request(mock_middleware_context, mock_call_next)
                
                # Verify call_next was NOT called (execution prevented)
                mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_tries_oauth_first(self, mock_middleware_context, mock_call_next):
        """Test that middleware tries OAuth 2.0 authentication first."""
        middleware = AuthenticationMiddleware()
        
        headers = {"Authorization": "Bearer oauth-token"}
        
        with patch("app.mcp.middleware.auth.get_http_headers", return_value=headers):
            with patch(
                "app.mcp.middleware.auth.authenticate_request",
                return_value=MCPContext(
                    tenant_id=uuid4(),
                    user_id=uuid4(),
                    role="user",
                ),
            ) as mock_auth:
                await middleware.on_request(mock_middleware_context, mock_call_next)
                
                # Verify authenticate_request was called with OAuth header
                mock_auth.assert_called_once()
                call_args = mock_auth.call_args
                assert call_args.kwargs.get("authorization_header") == "Bearer oauth-token"

    @pytest.mark.asyncio
    async def test_middleware_falls_back_to_api_key(self, mock_middleware_context, mock_call_next):
        """Test that middleware falls back to API key if OAuth fails."""
        middleware = AuthenticationMiddleware()
        
        headers = {"X-API-Key": "test-api-key"}
        
        with patch("app.mcp.middleware.auth.get_http_headers", return_value=headers):
            with patch(
                "app.mcp.middleware.auth.authenticate_request",
                return_value=MCPContext(
                    tenant_id=uuid4(),
                    user_id=uuid4(),
                    role="user",
                ),
            ) as mock_auth:
                await middleware.on_request(mock_middleware_context, mock_call_next)
                
                # Verify authenticate_request was called with API key header
                mock_auth.assert_called_once()
                call_args = mock_auth.call_args
                assert call_args.kwargs.get("api_key_header") == "test-api-key"

    @pytest.mark.asyncio
    async def test_middleware_handles_missing_headers(self, mock_middleware_context, mock_call_next):
        """Test that middleware handles missing headers gracefully."""
        middleware = AuthenticationMiddleware()
        
        with patch("app.mcp.middleware.auth.get_http_headers", return_value={}):
            with patch(
                "app.mcp.middleware.auth.authenticate_request",
                side_effect=AuthenticationError("Authentication required", error_code="FR-ERROR-003"),
            ):
                with pytest.raises(ValueError, match="Authentication failed"):
                    await middleware.on_request(mock_middleware_context, mock_call_next)

