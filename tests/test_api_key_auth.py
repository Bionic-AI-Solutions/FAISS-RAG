"""
Tests for API key authentication.
"""

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.config.auth import auth_settings
from app.db.models.tenant_api_key import TenantApiKey
from app.db.models.user import User
from app.mcp.middleware.auth import (
    AuthenticationError,
    authenticate_request,
    extract_api_key_from_header,
    validate_api_key,
)
from app.utils.hashing import hash_api_key, verify_api_key


@pytest.fixture
def mock_api_key():
    """Mock API key."""
    return "test-api-key-12345"


@pytest.fixture
def mock_hashed_key(mock_api_key):
    """Mock hashed API key."""
    return hash_api_key(mock_api_key)


@pytest.fixture
def mock_tenant_id():
    """Mock tenant ID."""
    return uuid4()


@pytest.fixture
def mock_user_id():
    """Mock user ID."""
    return uuid4()


@pytest.fixture
def mock_api_key_record(mock_tenant_id, mock_hashed_key):
    """Mock TenantApiKey record."""
    key = MagicMock(spec=TenantApiKey)
    key.key_id = uuid4()
    key.tenant_id = mock_tenant_id
    key.key_hash = mock_hashed_key
    key.name = "Test API Key"
    key.expires_at = None  # Never expires
    return key


@pytest.fixture
def mock_user_record(mock_tenant_id, mock_user_id):
    """Mock User record."""
    user = MagicMock(spec=User)
    user.user_id = mock_user_id
    user.tenant_id = mock_tenant_id
    user.email = "test@example.com"
    user.role = "user"
    return user


class TestExtractAPIKeyFromHeader:
    """Tests for extract_api_key_from_header function."""

    def test_extract_from_x_api_key_header(self):
        """Test extracting API key from X-API-Key header."""
        header = "test-api-key-12345"
        key = extract_api_key_from_header(header)
        assert key == "test-api-key-12345"

    def test_extract_from_authorization_bearer(self):
        """Test extracting API key from Authorization Bearer header."""
        header = "Bearer test-api-key-12345"
        key = extract_api_key_from_header(header)
        assert key == "test-api-key-12345"

    def test_extract_with_spaces(self):
        """Test extracting API key with spaces."""
        header = "  test-api-key-12345  "
        key = extract_api_key_from_header(header)
        assert key == "test-api-key-12345"

    def test_none_header(self):
        """Test handling None header."""
        key = extract_api_key_from_header(None)
        assert key is None

    def test_empty_header(self):
        """Test handling empty header."""
        key = extract_api_key_from_header("")
        assert key is None


class TestHashAPIKey:
    """Tests for API key hashing."""

    def test_hash_api_key(self, mock_api_key):
        """Test hashing an API key."""
        hashed = hash_api_key(mock_api_key)
        assert hashed != mock_api_key
        assert len(hashed) > 0

    def test_verify_api_key(self, mock_api_key):
        """Test verifying an API key."""
        hashed = hash_api_key(mock_api_key)
        assert verify_api_key(mock_api_key, hashed) is True

    def test_verify_wrong_key(self, mock_api_key):
        """Test verifying wrong API key."""
        hashed = hash_api_key(mock_api_key)
        assert verify_api_key("wrong-key", hashed) is False


class TestValidateAPIKey:
    """Tests for validate_api_key function."""

    @pytest.mark.asyncio
    async def test_validate_api_key_success(
        self, mock_api_key, mock_api_key_record, mock_user_record, mock_tenant_id, mock_user_id
    ):
        """Test successful API key validation."""
        # Mock database session (async generator)
        async def mock_session_gen():
            mock_session_instance = AsyncMock()
            yield mock_session_instance
        
        with patch("app.mcp.middleware.auth.get_db_session", return_value=mock_session_gen()):
            # Mock repositories
            api_key_repo = AsyncMock()
            api_key_repo.get_active_keys = AsyncMock(return_value=[mock_api_key_record])
            
            user_repo = AsyncMock()
            user_repo.get_by_tenant = AsyncMock(return_value=[mock_user_record])
            
            with patch(
                "app.mcp.middleware.auth.TenantApiKeyRepository",
                return_value=api_key_repo,
            ), patch(
                "app.mcp.middleware.auth.UserRepository",
                return_value=user_repo,
            ), patch("app.mcp.middleware.auth.verify_api_key", return_value=True):
                claims = await validate_api_key(mock_api_key)
                assert claims["tenant_id"] == mock_tenant_id
                assert claims["user_id"] == mock_user_id
                assert claims["role"] == "user"

    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, mock_api_key):
        """Test validation with invalid API key."""
        async def mock_session_gen():
            mock_session_instance = AsyncMock()
            yield mock_session_instance
        
        with patch("app.mcp.middleware.auth.get_db_session", return_value=mock_session_gen()):
            api_key_repo = AsyncMock()
            api_key_repo.get_active_keys = AsyncMock(return_value=[])
            
            with patch(
                "app.mcp.middleware.auth.TenantApiKeyRepository",
                return_value=api_key_repo,
            ):
                with pytest.raises(AuthenticationError, match="Invalid API key"):
                    await validate_api_key("invalid-key")

    @pytest.mark.asyncio
    async def test_validate_api_key_expired(
        self, mock_api_key, mock_api_key_record, mock_tenant_id
    ):
        """Test validation with expired API key."""
        # Set expiration to past
        mock_api_key_record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        async def mock_session_gen():
            mock_session_instance = AsyncMock()
            yield mock_session_instance
        
        with patch("app.mcp.middleware.auth.get_db_session", return_value=mock_session_gen()):
            api_key_repo = AsyncMock()
            api_key_repo.get_active_keys = AsyncMock(return_value=[mock_api_key_record])
            
            with patch(
                "app.mcp.middleware.auth.TenantApiKeyRepository",
                return_value=api_key_repo,
            ), patch("app.mcp.middleware.auth.verify_api_key", return_value=True):
                with pytest.raises(AuthenticationError, match="API key has expired"):
                    await validate_api_key(mock_api_key)

    @pytest.mark.asyncio
    async def test_validate_api_key_no_user(
        self, mock_api_key, mock_api_key_record, mock_tenant_id
    ):
        """Test validation when no user found for tenant."""
        async def mock_session_gen():
            mock_session_instance = AsyncMock()
            yield mock_session_instance
        
        with patch("app.mcp.middleware.auth.get_db_session", return_value=mock_session_gen()):
            api_key_repo = AsyncMock()
            api_key_repo.get_active_keys = AsyncMock(return_value=[mock_api_key_record])
            
            user_repo = AsyncMock()
            user_repo.get_by_tenant = AsyncMock(return_value=[])  # No users
            
            with patch(
                "app.mcp.middleware.auth.TenantApiKeyRepository",
                return_value=api_key_repo,
            ), patch(
                "app.mcp.middleware.auth.UserRepository",
                return_value=user_repo,
            ), patch("app.mcp.middleware.auth.verify_api_key", return_value=True):
                with pytest.raises(
                    AuthenticationError, match="No user found for tenant"
                ):
                    await validate_api_key(mock_api_key)

    @pytest.mark.asyncio
    async def test_validate_api_key_performance_requirement(
        self, mock_api_key, mock_api_key_record, mock_user_record, mock_tenant_id, mock_user_id
    ):
        """Test that validation completes within performance requirement."""
        async def mock_session_gen():
            mock_session_instance = AsyncMock()
            yield mock_session_instance
        
        with patch("app.mcp.middleware.auth.get_db_session", return_value=mock_session_gen()):
            api_key_repo = AsyncMock()
            api_key_repo.get_active_keys = AsyncMock(return_value=[mock_api_key_record])
            
            user_repo = AsyncMock()
            user_repo.get_by_tenant = AsyncMock(return_value=[mock_user_record])
            
            with patch(
                "app.mcp.middleware.auth.TenantApiKeyRepository",
                return_value=api_key_repo,
            ), patch(
                "app.mcp.middleware.auth.UserRepository",
                return_value=user_repo,
            ), patch("app.mcp.middleware.auth.verify_api_key", return_value=True):
                start = time.time()
                await validate_api_key(mock_api_key)
                elapsed_ms = (time.time() - start) * 1000
                
                # Should complete within reasonable time (allowing some margin for test overhead)
                assert elapsed_ms < 1000  # 1 second for test environment


class TestAuthenticateRequest:
    """Tests for authenticate_request function."""

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key(
        self, mock_api_key, mock_api_key_record, mock_user_record, mock_tenant_id, mock_user_id
    ):
        """Test authentication with API key."""
        original_enabled = auth_settings.api_key_enabled
        auth_settings.api_key_enabled = True
        
        try:
            async def mock_session_gen():
                mock_session_instance = AsyncMock()
                yield mock_session_instance
            
            with patch("app.mcp.middleware.auth.get_db_session", return_value=mock_session_gen()):
                api_key_repo = AsyncMock()
                api_key_repo.get_active_keys = AsyncMock(return_value=[mock_api_key_record])
                
                user_repo = AsyncMock()
                user_repo.get_by_tenant = AsyncMock(return_value=[mock_user_record])
                
                with patch(
                    "app.mcp.middleware.auth.TenantApiKeyRepository",
                    return_value=api_key_repo,
                ), patch(
                    "app.mcp.middleware.auth.UserRepository",
                    return_value=user_repo,
                ), patch("app.mcp.middleware.auth.verify_api_key", return_value=True):
                    context = await authenticate_request(api_key_header=mock_api_key)
                    assert context.tenant_id == mock_tenant_id
                    assert context.user_id == mock_user_id
                    assert context.role == "user"
        finally:
            auth_settings.api_key_enabled = original_enabled

    @pytest.mark.asyncio
    async def test_authenticate_api_key_disabled(self, mock_api_key):
        """Test authentication with API key disabled."""
        original_enabled = auth_settings.api_key_enabled
        auth_settings.api_key_enabled = False
        
        try:
            with pytest.raises(AuthenticationError, match="Authentication required"):
                await authenticate_request(api_key_header=mock_api_key)
        finally:
            auth_settings.api_key_enabled = original_enabled

