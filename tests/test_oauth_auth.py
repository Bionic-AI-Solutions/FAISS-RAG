"""
Tests for OAuth 2.0 authentication.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from jose import jwt

from app.config.auth import auth_settings
from app.mcp.middleware import auth as auth_module
from app.mcp.middleware.auth import (
    AuthenticationError,
    authenticate_request,
    extract_bearer_token,
    get_jwks,
    get_signing_key,
    jwk_to_pem,
    validate_oauth_token,
)


@pytest.fixture(autouse=True)
def clear_jwks_cache():
    """Clear JWKS cache before each test."""
    auth_module._jwks_cache = None
    auth_module._jwks_cache_time = 0
    yield
    auth_module._jwks_cache = None
    auth_module._jwks_cache_time = 0


@pytest.fixture
def mock_jwks():
    """Mock JWKS response."""
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-id",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }


@pytest.fixture
def mock_token_claims():
    """Mock JWT token claims."""
    return {
        "sub": str(uuid4()),
        "tenant_id": str(uuid4()),
        "role": "user",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }


class TestExtractBearerToken:
    """Tests for extract_bearer_token function."""

    def test_extract_valid_bearer_token(self):
        """Test extracting valid Bearer token."""
        header = "Bearer test-token-123"
        token = extract_bearer_token(header)
        assert token == "test-token-123"

    def test_extract_token_with_spaces(self):
        """Test extracting token with spaces."""
        header = "Bearer  test-token-123  "
        token = extract_bearer_token(header)
        assert token == "test-token-123"

    def test_no_bearer_prefix(self):
        """Test handling header without Bearer prefix."""
        header = "Token test-token-123"
        token = extract_bearer_token(header)
        assert token is None

    def test_none_header(self):
        """Test handling None header."""
        token = extract_bearer_token(None)
        assert token is None

    def test_empty_header(self):
        """Test handling empty header."""
        token = extract_bearer_token("")
        assert token is None


class TestJWKToPEM:
    """Tests for jwk_to_pem function."""

    def test_rsa_jwk_to_pem_invalid_base64(self):
        """Test converting RSA JWK with invalid base64 raises error."""
        jwk = {
            "kty": "RSA",
            "n": "!!!invalid-base64!!!",
            "e": "AQAB",
        }
        # Should raise an error due to invalid base64
        with pytest.raises(Exception):
            jwk_to_pem(jwk)

    def test_unsupported_key_type(self):
        """Test handling unsupported key type."""
        jwk = {"kty": "UNSUPPORTED"}
        with pytest.raises(ValueError, match="Unsupported key type"):
            jwk_to_pem(jwk)


class TestGetJWKS:
    """Tests for get_jwks function."""

    @pytest.mark.asyncio
    async def test_get_jwks_success(self, mock_jwks):
        """Test successful JWKS retrieval."""
        original_uri = auth_settings.oauth_jwks_uri
        auth_settings.oauth_jwks_uri = "https://example.com/jwks.json"
        
        try:
            with patch("app.mcp.middleware.auth.httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_jwks
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_client_instance
                
                jwks = await get_jwks()
                assert jwks == mock_jwks
        finally:
            auth_settings.oauth_jwks_uri = original_uri

    @pytest.mark.asyncio
    async def test_get_jwks_caching(self, mock_jwks):
        """Test JWKS caching."""
        original_uri = auth_settings.oauth_jwks_uri
        auth_settings.oauth_jwks_uri = "https://example.com/jwks.json"
        
        try:
            get_call_count = 0
            
            async def mock_get(*args, **kwargs):
                nonlocal get_call_count
                get_call_count += 1
                mock_response = MagicMock()
                mock_response.json.return_value = mock_jwks
                mock_response.raise_for_status = MagicMock()
                return mock_response
            
            with patch("app.mcp.middleware.auth.httpx.AsyncClient") as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client_instance.get = AsyncMock(side_effect=mock_get)
                mock_client.return_value = mock_client_instance
                
                # First call
                jwks1 = await get_jwks()
                # Second call should use cache
                jwks2 = await get_jwks()
                
                assert jwks1 == jwks2
                # Should only call HTTP once due to caching
                assert get_call_count == 1
        finally:
            auth_settings.oauth_jwks_uri = original_uri

    @pytest.mark.asyncio
    async def test_get_jwks_no_uri_configured(self):
        """Test handling missing JWKS URI."""
        original_uri = auth_settings.oauth_jwks_uri
        auth_settings.oauth_jwks_uri = ""
        
        try:
            with pytest.raises(AuthenticationError, match="OAuth JWKS URI not configured"):
                await get_jwks()
        finally:
            auth_settings.oauth_jwks_uri = original_uri

    @pytest.mark.asyncio
    async def test_get_jwks_http_error(self):
        """Test handling HTTP error."""
        original_uri = auth_settings.oauth_jwks_uri
        auth_settings.oauth_jwks_uri = "https://example.com/jwks.json"
        
        try:
            with patch("app.mcp.middleware.auth.httpx.AsyncClient") as mock_client:
                import httpx
                
                # Create a proper httpx.HTTPError
                http_error = httpx.HTTPError("Connection error")
                
                mock_client_instance = AsyncMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client_instance.get = AsyncMock(side_effect=http_error)
                mock_client.return_value = mock_client_instance
                
                with pytest.raises(AuthenticationError, match="Failed to fetch JWKS"):
                    await get_jwks()
        finally:
            auth_settings.oauth_jwks_uri = original_uri


class TestValidateOAuthToken:
    """Tests for validate_oauth_token function."""

    @pytest.mark.asyncio
    async def test_validate_token_missing_jwks_uri(self):
        """Test validation with missing JWKS URI."""
        original_uri = auth_settings.oauth_jwks_uri
        auth_settings.oauth_jwks_uri = ""
        
        try:
            # Clear cache first
            auth_module._jwks_cache = None
            auth_module._jwks_cache_time = 0
            
            with pytest.raises(AuthenticationError, match="OAuth JWKS URI not configured"):
                await validate_oauth_token("test-token")
        finally:
            auth_settings.oauth_jwks_uri = original_uri
            auth_module._jwks_cache = None
            auth_module._jwks_cache_time = 0

    @pytest.mark.asyncio
    async def test_validate_token_performance_requirement(self):
        """Test that validation completes within performance requirement."""
        # This is a placeholder test - actual performance testing would require
        # a real OAuth provider or more sophisticated mocking
        assert auth_settings.auth_timeout_ms == 50  # FR-AUTH-001 requirement


class TestAuthenticateRequest:
    """Tests for authenticate_request function."""

    @pytest.mark.asyncio
    async def test_authenticate_no_headers(self):
        """Test authentication with no headers."""
        with pytest.raises(AuthenticationError, match="Authentication required"):
            await authenticate_request()

    @pytest.mark.asyncio
    async def test_authenticate_oauth_disabled(self):
        """Test authentication with OAuth disabled."""
        original_enabled = auth_settings.oauth_enabled
        auth_settings.oauth_enabled = False
        
        try:
            with pytest.raises(AuthenticationError, match="Authentication required"):
                await authenticate_request(authorization_header="Bearer test-token")
        finally:
            auth_settings.oauth_enabled = original_enabled

    @pytest.mark.asyncio
    async def test_authenticate_api_key_fallback_when_oauth_disabled(self):
        """Test that API key authentication is used when OAuth is disabled."""
        from app.mcp.middleware.context import MCPContext
        
        original_oauth = auth_settings.oauth_enabled
        auth_settings.oauth_enabled = False
        
        try:
            # Mock API key validation to succeed
            with patch("app.mcp.middleware.auth.validate_api_key") as mock_validate:
                mock_tenant_id = uuid4()
                mock_user_id = uuid4()
                mock_validate.return_value = {
                    "user_id": mock_user_id,
                    "tenant_id": mock_tenant_id,
                    "role": "api_key_user",
                }
                
                context = await authenticate_request(api_key_header="test-api-key")
                
                assert isinstance(context, MCPContext)
                assert context.user_id == mock_user_id
                assert context.tenant_id == mock_tenant_id
                assert context.role == "api_key_user"
                mock_validate.assert_called_once_with("test-api-key")
        finally:
            auth_settings.oauth_enabled = original_oauth

