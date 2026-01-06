"""
Tests for authorization and RBAC middleware.
"""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from uuid import uuid4

import pytest
from fastmcp.server.middleware import MiddlewareContext

from app.mcp.middleware.authorization import (
    AuthorizationMiddleware,
    extract_tool_name_from_context,
    get_role_from_context,
    log_authorization_attempt,
)
from app.mcp.middleware.context import MCPContext
from app.mcp.middleware.rbac import (
    AuthorizationError,
    UserRole,
    can_access_tool,
    check_tool_permission,
    get_required_role_for_tool,
    get_role_capabilities,
    get_role_permissions,
)


class TestUserRole:
    """Tests for UserRole enum."""

    def test_role_values(self):
        """Test role enum values."""
        assert UserRole.UBER_ADMIN.value == "uber_admin"
        assert UserRole.TENANT_ADMIN.value == "tenant_admin"
        assert UserRole.PROJECT_ADMIN.value == "project_admin"
        assert UserRole.END_USER.value == "end_user"

    def test_from_string_valid_roles(self):
        """Test converting valid role strings."""
        assert UserRole.from_string("uber_admin") == UserRole.UBER_ADMIN
        assert UserRole.from_string("tenant_admin") == UserRole.TENANT_ADMIN
        assert UserRole.from_string("project_admin") == UserRole.PROJECT_ADMIN
        assert UserRole.from_string("end_user") == UserRole.END_USER

    def test_from_string_case_insensitive(self):
        """Test case-insensitive role conversion."""
        assert UserRole.from_string("UBER_ADMIN") == UserRole.UBER_ADMIN
        assert UserRole.from_string("Tenant_Admin") == UserRole.TENANT_ADMIN
        assert UserRole.from_string("END_USER") == UserRole.END_USER

    def test_from_string_legacy_roles(self):
        """Test legacy role name mapping."""
        assert UserRole.from_string("user") == UserRole.END_USER
        assert UserRole.from_string("viewer") == UserRole.END_USER

    def test_from_string_invalid_role(self):
        """Test invalid role string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid role"):
            UserRole.from_string("invalid_role")


class TestRolePermissions:
    """Tests for role permission checking functions."""

    def test_get_role_permissions_uber_admin(self):
        """Test getting permissions for uber_admin."""
        permissions = get_role_permissions(UserRole.UBER_ADMIN)
        assert isinstance(permissions, dict)
        # Uber admin should have access to most tools
        assert permissions.get("rag_list_tools", False) is True
        assert permissions.get("rag_register_tenant", False) is True

    def test_get_role_permissions_end_user(self):
        """Test getting permissions for end_user."""
        permissions = get_role_permissions(UserRole.END_USER)
        assert isinstance(permissions, dict)
        # End user should have limited access
        assert permissions.get("rag_list_tools", False) is True
        assert permissions.get("rag_register_tenant", False) is False
        assert permissions.get("rag_ingest", False) is False

    def test_can_access_tool_uber_admin(self):
        """Test uber_admin can access all tools."""
        assert can_access_tool(UserRole.UBER_ADMIN, "rag_list_tools") is True
        assert can_access_tool(UserRole.UBER_ADMIN, "rag_register_tenant") is True
        assert can_access_tool(UserRole.UBER_ADMIN, "rag_ingest") is True

    def test_can_access_tool_end_user(self):
        """Test end_user has limited access."""
        assert can_access_tool(UserRole.END_USER, "rag_list_tools") is True
        assert can_access_tool(UserRole.END_USER, "rag_register_tenant") is False
        assert can_access_tool(UserRole.END_USER, "rag_ingest") is False
        assert can_access_tool(UserRole.END_USER, "rag_search") is True

    def test_can_access_tool_tenant_admin(self):
        """Test tenant_admin access."""
        assert can_access_tool(UserRole.TENANT_ADMIN, "rag_list_tools") is True
        assert can_access_tool(UserRole.TENANT_ADMIN, "rag_register_tenant") is False
        assert can_access_tool(UserRole.TENANT_ADMIN, "rag_ingest") is True

    def test_can_access_tool_unknown_tool(self):
        """Test unknown tool returns False."""
        assert can_access_tool(UserRole.UBER_ADMIN, "unknown_tool") is False

    def test_check_tool_permission_allowed(self):
        """Test check_tool_permission allows authorized access."""
        # Should not raise
        check_tool_permission(UserRole.UBER_ADMIN, "rag_list_tools")
        check_tool_permission(UserRole.END_USER, "rag_list_tools")

    def test_check_tool_permission_denied(self):
        """Test check_tool_permission raises AuthorizationError for unauthorized access."""
        with pytest.raises(AuthorizationError) as exc_info:
            check_tool_permission(UserRole.END_USER, "rag_register_tenant")
        assert "does not have permission" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "FR-ERROR-003"

    def test_get_required_role_for_tool(self):
        """Test getting minimum required role for a tool."""
        role = get_required_role_for_tool("rag_list_tools")
        assert role is not None
        assert isinstance(role, UserRole)
        # Should return the most restrictive role (END_USER)
        assert role == UserRole.END_USER

    def test_get_required_role_for_tool_restricted(self):
        """Test getting minimum required role for restricted tool."""
        role = get_required_role_for_tool("rag_register_tenant")
        assert role is not None
        assert isinstance(role, UserRole)
        # Should return the most restrictive role (UBER_ADMIN)
        assert role == UserRole.UBER_ADMIN

    def test_get_required_role_for_tool_unknown(self):
        """Test getting required roles for unknown tool returns None."""
        roles = get_required_role_for_tool("unknown_tool")
        assert roles is None

    def test_get_role_capabilities(self):
        """Test getting role capabilities."""
        capabilities = get_role_capabilities(UserRole.UBER_ADMIN)
        assert isinstance(capabilities, dict)
        assert "description" in capabilities
        assert "capabilities" in capabilities
        assert "restrictions" in capabilities

        capabilities = get_role_capabilities(UserRole.END_USER)
        assert isinstance(capabilities, dict)
        assert "description" in capabilities
        assert "capabilities" in capabilities
        assert "restrictions" in capabilities


class TestExtractToolNameFromContext:
    """Tests for extract_tool_name_from_context function."""

    def test_extract_from_tool_name_attribute(self):
        """Test extracting tool name from tool_name attribute."""
        context = MagicMock(spec=MiddlewareContext)
        context.tool_name = "rag_list_tools"
        assert extract_tool_name_from_context(context) == "rag_list_tools"

    def test_extract_from_request_tool_name(self):
        """Test extracting tool name from request.tool.name."""
        context = MagicMock(spec=MiddlewareContext)
        context.request = MagicMock()
        context.request.tool = MagicMock()
        context.request.tool.name = "rag_search"
        assert extract_tool_name_from_context(context) == "rag_search"

    def test_extract_from_fastmcp_context_tool_name(self):
        """Test extracting tool name from fastmcp_context.tool_name."""
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = MagicMock()
        context.fastmcp_context.tool_name = "rag_ingest"
        assert extract_tool_name_from_context(context) == "rag_ingest"

    def test_extract_from_fastmcp_context_method(self):
        """Test extracting tool name from fastmcp_context.method."""
        # Create a simple object that mimics the expected structure
        class MockContext:
            pass
        context = MockContext()
        fastmcp_ctx = MockContext()
        fastmcp_ctx.method = "rag_list_documents"
        context.fastmcp_context = fastmcp_ctx
        assert extract_tool_name_from_context(context) == "rag_list_documents"

    def test_extract_from_method_attribute(self):
        """Test extracting tool name from method attribute."""
        # Create a simple object that mimics the expected structure
        class MockContext:
            pass
        context = MockContext()
        context.method = "mem0_get_user_memory"
        assert extract_tool_name_from_context(context) == "mem0_get_user_memory"

    def test_extract_none_when_not_found(self):
        """Test returning None when tool name not found."""
        # Create a simple object with no tool-related attributes
        class MockContext:
            pass
        context = MockContext()
        assert extract_tool_name_from_context(context) is None


class TestGetRoleFromContext:
    """Tests for get_role_from_context function."""

    def test_get_role_from_mcp_context(self):
        """Test extracting role from MCPContext."""
        user_id = uuid4()
        tenant_id = uuid4()
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="uber_admin"
        )
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = mcp_context

        role = get_role_from_context(context)
        assert role == UserRole.UBER_ADMIN

    def test_get_role_from_fastmcp_context(self):
        """Test extracting role from fastmcp_context.auth_context."""
        user_id = uuid4()
        tenant_id = uuid4()
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="tenant_admin"
        )
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = MagicMock()
        context.fastmcp_context.auth_context = mcp_context

        role = get_role_from_context(context)
        assert role == UserRole.TENANT_ADMIN

    def test_get_role_from_dict_context(self):
        """Test extracting role from dict context."""
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = {"role": "end_user"}

        role = get_role_from_context(context)
        assert role == UserRole.END_USER

    def test_get_role_none_when_not_found(self):
        """Test returning None when role not found."""
        context = MagicMock(spec=MiddlewareContext)
        # No auth_context
        role = get_role_from_context(context)
        assert role is None

    def test_get_role_invalid_role_string(self):
        """Test handling invalid role string."""
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = {"role": "invalid_role"}

        # Should return None for invalid role
        role = get_role_from_context(context)
        assert role is None


class TestAuthorizationMiddleware:
    """Tests for AuthorizationMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create AuthorizationMiddleware instance."""
        return AuthorizationMiddleware()

    @pytest.fixture
    def mock_context_with_role(self):
        """Create mock context with authenticated role."""
        user_id = uuid4()
        tenant_id = uuid4()
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="uber_admin"
        )
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = mcp_context
        context.tool_name = "rag_list_tools"
        return context

    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function."""
        return AsyncMock(return_value={"result": "success"})

    @pytest.mark.asyncio
    async def test_middleware_allows_authorized_access(
        self, middleware, mock_context_with_role, mock_call_next
    ):
        """Test middleware allows authorized access."""
        result = await middleware.on_request(mock_context_with_role, mock_call_next)
        assert result == {"result": "success"}
        mock_call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_denies_unauthorized_access(
        self, middleware, mock_context_with_role, mock_call_next
    ):
        """Test middleware denies unauthorized access."""
        # Change role to end_user and tool to restricted tool
        mock_context_with_role.auth_context.role = "end_user"
        mock_context_with_role.tool_name = "rag_register_tenant"

        with pytest.raises(AuthorizationError) as exc_info:
            await middleware.on_request(mock_context_with_role, mock_call_next)
        assert "does not have permission" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "FR-ERROR-003"
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_handles_missing_role(
        self, middleware, mock_call_next
    ):
        """Test middleware handles missing role in context."""
        context = MagicMock(spec=MiddlewareContext)
        # No auth_context
        context.tool_name = "rag_list_tools"

        with pytest.raises(AuthorizationError) as exc_info:
            await middleware.on_request(context, mock_call_next)
        assert "Role not found" in str(exc_info.value)
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_handles_missing_tool_name(
        self, middleware, mock_context_with_role, mock_call_next
    ):
        """Test middleware allows request when tool name not found (non-tool request)."""
        # Remove tool_name and fastmcp_context to ensure no tool name is found
        del mock_context_with_role.tool_name
        if hasattr(mock_context_with_role, "fastmcp_context"):
            delattr(mock_context_with_role, "fastmcp_context")
        if hasattr(mock_context_with_role, "request"):
            delattr(mock_context_with_role, "request")
        if hasattr(mock_context_with_role, "method"):
            delattr(mock_context_with_role, "method")

        result = await middleware.on_request(mock_context_with_role, mock_call_next)
        # Should allow through if no tool to check
        assert result == {"result": "success"}
        mock_call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_stores_authorization_context(
        self, middleware, mock_context_with_role, mock_call_next
    ):
        """Test middleware stores authorization context."""
        await middleware.on_request(mock_context_with_role, mock_call_next)

        # Check that authz_context was stored
        assert hasattr(mock_context_with_role, "authz_context")
        assert mock_context_with_role.authz_context["authorized"] is True
        assert mock_context_with_role.authz_context["role"] == UserRole.UBER_ADMIN
        assert mock_context_with_role.authz_context["tool_name"] == "rag_list_tools"

    @pytest.mark.asyncio
    async def test_middleware_logs_authorization_attempt(
        self, middleware, mock_context_with_role, mock_call_next
    ):
        """Test middleware logs authorization attempt."""
        with patch("app.mcp.middleware.authorization.log_authorization_attempt") as mock_log:
            await middleware.on_request(mock_context_with_role, mock_call_next)

            # Verify audit log was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["success"] is True
            assert call_args[1]["role"] == UserRole.UBER_ADMIN
            assert call_args[1]["tool_name"] == "rag_list_tools"

    @pytest.mark.asyncio
    async def test_middleware_logs_authorization_failure(
        self, middleware, mock_context_with_role, mock_call_next
    ):
        """Test middleware logs authorization failure."""
        mock_context_with_role.auth_context.role = "end_user"
        mock_context_with_role.tool_name = "rag_register_tenant"

        with patch("app.mcp.middleware.authorization.log_authorization_attempt") as mock_log:
            with pytest.raises(AuthorizationError):
                await middleware.on_request(mock_context_with_role, mock_call_next)

            # Verify audit log was called with failure
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["success"] is False
            assert call_args[1]["role"] == UserRole.END_USER
            assert call_args[1]["reason"] is not None


class TestLogAuthorizationAttempt:
    """Tests for log_authorization_attempt function."""

    @pytest.mark.asyncio
    async def test_log_authorization_success(self):
        """Test logging successful authorization."""
        user_id = uuid4()
        tenant_id = uuid4()

        with patch("app.mcp.middleware.authorization.get_db_session") as mock_session:
            mock_session.return_value.__aiter__.return_value = [MagicMock()]
            mock_session.return_value.__aiter__ = lambda self: iter([MagicMock()])

            # Create a proper async generator mock
            async def mock_session_gen():
                session = MagicMock()
                session.commit = AsyncMock()
                yield session

            mock_session.return_value = mock_session_gen()

            with patch("app.mcp.middleware.authorization.AuditLogRepository") as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create = AsyncMock()
                mock_repo_class.return_value = mock_repo

                await log_authorization_attempt(
                    success=True,
                    role=UserRole.UBER_ADMIN,
                    tool_name="rag_list_tools",
                    user_id=user_id,
                    tenant_id=tenant_id,
                )

                # Verify audit log repository was used
                mock_repo.create.assert_called_once()
                call_args = mock_repo.create.call_args
                assert call_args[1]["action"] == "authorize"
                assert call_args[1]["resource_type"] == "authorization"
                assert call_args[1]["resource_id"] == "rag_list_tools"

    @pytest.mark.asyncio
    async def test_log_authorization_failure(self):
        """Test logging failed authorization."""
        user_id = uuid4()
        tenant_id = uuid4()

        with patch("app.mcp.middleware.authorization.get_db_session") as mock_session:
            # Create a proper async generator mock
            async def mock_session_gen():
                session = MagicMock()
                session.commit = AsyncMock()
                yield session

            mock_session.return_value = mock_session_gen()

            with patch("app.mcp.middleware.authorization.AuditLogRepository") as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create = AsyncMock()
                mock_repo_class.return_value = mock_repo

                await log_authorization_attempt(
                    success=False,
                    role=UserRole.END_USER,
                    tool_name="rag_register_tenant",
                    reason="Role 'end_user' is not authorized to access tool 'rag_register_tenant'",
                    user_id=user_id,
                    tenant_id=tenant_id,
                )

                # Verify audit log repository was used
                mock_repo.create.assert_called_once()
                call_args = mock_repo.create.call_args
                assert call_args[1]["action"] == "authorize_failed"
                assert call_args[1]["details"]["success"] is False
                assert call_args[1]["details"]["reason"] is not None


class TestAuthorizationIntegration:
    """Integration tests for authorization flow."""

    @pytest.mark.asyncio
    async def test_full_authorization_flow_uber_admin(self):
        """Test full authorization flow for uber_admin."""
        middleware = AuthorizationMiddleware()
        user_id = uuid4()
        tenant_id = uuid4()

        # Create context with uber_admin role
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="uber_admin"
        )
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = mcp_context
        context.tool_name = "rag_register_tenant"  # Restricted tool

        mock_call_next = AsyncMock(return_value={"result": "success"})

        # Should allow access for uber_admin
        result = await middleware.on_request(context, mock_call_next)
        assert result == {"result": "success"}
        mock_call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_authorization_flow_end_user_denied(self):
        """Test full authorization flow for end_user accessing restricted tool."""
        middleware = AuthorizationMiddleware()
        user_id = uuid4()
        tenant_id = uuid4()

        # Create context with end_user role
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="end_user"
        )
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = mcp_context
        context.tool_name = "rag_register_tenant"  # Restricted tool

        mock_call_next = AsyncMock(return_value={"result": "success"})

        # Should deny access for end_user
        with pytest.raises(AuthorizationError) as exc_info:
            await middleware.on_request(context, mock_call_next)
        assert "does not have permission" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "FR-ERROR-003"
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_full_authorization_flow_end_user_allowed(self):
        """Test full authorization flow for end_user accessing allowed tool."""
        middleware = AuthorizationMiddleware()
        user_id = uuid4()
        tenant_id = uuid4()

        # Create context with end_user role
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="end_user"
        )
        context = MagicMock(spec=MiddlewareContext)
        context.auth_context = mcp_context
        context.tool_name = "rag_list_tools"  # Allowed tool

        mock_call_next = AsyncMock(return_value={"result": "success"})

        # Should allow access for end_user
        result = await middleware.on_request(context, mock_call_next)
        assert result == {"result": "success"}
        mock_call_next.assert_called_once()

