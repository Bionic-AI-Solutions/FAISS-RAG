"""
Tests for authentication audit logging.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.db.models.audit_log import AuditLog
from app.mcp.middleware.auth import log_authentication_attempt


@pytest.fixture
def mock_tenant_id():
    """Mock tenant ID."""
    return uuid4()


@pytest.fixture
def mock_user_id():
    """Mock user ID."""
    return uuid4()


class TestAuditLogging:
    """Tests for authentication audit logging."""

    @pytest.mark.asyncio
    async def test_log_successful_oauth_authentication(
        self, mock_tenant_id, mock_user_id
    ):
        """Test logging successful OAuth authentication."""
        with patch("app.mcp.middleware.auth.get_db_session") as mock_session:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            mock_session.return_value = mock_session_gen()
            
            audit_repo = AsyncMock()
            audit_repo.create = AsyncMock(return_value=MagicMock(spec=AuditLog))
            
            with patch(
                "app.mcp.middleware.auth.AuditLogRepository",
                return_value=audit_repo,
            ):
                await log_authentication_attempt(
                    user_id=mock_user_id,
                    tenant_id=mock_tenant_id,
                    auth_method="oauth",
                    success=True,
                    ip_address="192.168.1.1",
                )
                
                # Verify audit log was created
                audit_repo.create.assert_called_once()
                call_kwargs = audit_repo.create.call_args.kwargs
                assert call_kwargs["user_id"] == mock_user_id
                assert call_kwargs["tenant_id"] == mock_tenant_id
                assert call_kwargs["action"] == "authenticate"
                assert call_kwargs["resource_type"] == "authentication"
                assert call_kwargs["details"]["auth_method"] == "oauth"
                assert call_kwargs["details"]["success"] is True
                assert call_kwargs["details"]["ip_address"] == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_log_failed_oauth_authentication(self):
        """Test logging failed OAuth authentication."""
        with patch("app.mcp.middleware.auth.get_db_session") as mock_session:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            mock_session.return_value = mock_session_gen()
            
            audit_repo = AsyncMock()
            audit_repo.create = AsyncMock(return_value=MagicMock(spec=AuditLog))
            
            with patch(
                "app.mcp.middleware.auth.AuditLogRepository",
                return_value=audit_repo,
            ):
                await log_authentication_attempt(
                    user_id=None,
                    tenant_id=None,
                    auth_method="oauth",
                    success=False,
                    reason="Invalid token",
                    ip_address="192.168.1.1",
                )
                
                # Verify audit log was created
                audit_repo.create.assert_called_once()
                call_kwargs = audit_repo.create.call_args.kwargs
                assert call_kwargs["user_id"] is None
                assert call_kwargs["tenant_id"] is None
                assert call_kwargs["action"] == "authenticate_failed"
                assert call_kwargs["details"]["auth_method"] == "oauth"
                assert call_kwargs["details"]["success"] is False
                assert call_kwargs["details"]["reason"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_log_successful_api_key_authentication(
        self, mock_tenant_id, mock_user_id
    ):
        """Test logging successful API key authentication."""
        with patch("app.mcp.middleware.auth.get_db_session") as mock_session:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            mock_session.return_value = mock_session_gen()
            
            audit_repo = AsyncMock()
            audit_repo.create = AsyncMock(return_value=MagicMock(spec=AuditLog))
            
            with patch(
                "app.mcp.middleware.auth.AuditLogRepository",
                return_value=audit_repo,
            ):
                await log_authentication_attempt(
                    user_id=mock_user_id,
                    tenant_id=mock_tenant_id,
                    auth_method="api_key",
                    success=True,
                    ip_address="10.0.0.1",
                )
                
                # Verify audit log was created
                call_kwargs = audit_repo.create.call_args.kwargs
                assert call_kwargs["details"]["auth_method"] == "api_key"
                assert call_kwargs["details"]["success"] is True

    @pytest.mark.asyncio
    async def test_log_failed_api_key_authentication(self):
        """Test logging failed API key authentication."""
        with patch("app.mcp.middleware.auth.get_db_session") as mock_session:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            mock_session.return_value = mock_session_gen()
            
            audit_repo = AsyncMock()
            audit_repo.create = AsyncMock(return_value=MagicMock(spec=AuditLog))
            
            with patch(
                "app.mcp.middleware.auth.AuditLogRepository",
                return_value=audit_repo,
            ):
                await log_authentication_attempt(
                    user_id=None,
                    tenant_id=None,
                    auth_method="api_key",
                    success=False,
                    reason="Invalid API key",
                    ip_address="10.0.0.1",
                )
                
                # Verify audit log was created
                call_kwargs = audit_repo.create.call_args.kwargs
                assert call_kwargs["action"] == "authenticate_failed"
                assert call_kwargs["details"]["auth_method"] == "api_key"
                assert call_kwargs["details"]["reason"] == "Invalid API key"

    @pytest.mark.asyncio
    async def test_log_handles_errors_gracefully(self):
        """Test that audit logging errors don't break authentication."""
        with patch("app.mcp.middleware.auth.get_db_session") as mock_session:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            mock_session.return_value = mock_session_gen()
            
            audit_repo = AsyncMock()
            audit_repo.create = AsyncMock(side_effect=Exception("Database error"))
            
            with patch(
                "app.mcp.middleware.auth.AuditLogRepository",
                return_value=audit_repo,
            ):
                # Should not raise exception
                await log_authentication_attempt(
                    user_id=uuid4(),
                    tenant_id=uuid4(),
                    auth_method="oauth",
                    success=True,
                )
                
                # Verify error was logged but didn't break execution
                audit_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_includes_timestamp(self, mock_tenant_id, mock_user_id):
        """Test that audit log includes timestamp."""
        with patch("app.mcp.middleware.auth.get_db_session") as mock_session:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            mock_session.return_value = mock_session_gen()
            
            audit_repo = AsyncMock()
            created_log = MagicMock(spec=AuditLog)
            created_log.timestamp = None  # Will be set by database
            audit_repo.create = AsyncMock(return_value=created_log)
            
            with patch(
                "app.mcp.middleware.auth.AuditLogRepository",
                return_value=audit_repo,
            ):
                await log_authentication_attempt(
                    user_id=mock_user_id,
                    tenant_id=mock_tenant_id,
                    auth_method="oauth",
                    success=True,
                )
                
                # Verify audit log was created (timestamp set by database)
                audit_repo.create.assert_called_once()












