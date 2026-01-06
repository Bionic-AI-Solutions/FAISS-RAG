"""
Authentication middleware for OAuth 2.0 and API key authentication.
"""

import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from jose import JWTError, jwt
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

from app.config.auth import auth_settings
from app.db.connection import get_db_session
from app.db.models.audit_log import AuditLog
from app.db.repositories.audit_log_repository import AuditLogRepository
from app.db.repositories.tenant_api_key_repository import TenantApiKeyRepository
from app.db.repositories.user_repository import UserRepository
from app.mcp.middleware.context import MCPContext
from app.utils.errors import AuthenticationError
from app.utils.hashing import hash_api_key, verify_api_key

logger = structlog.get_logger(__name__)

# JWKS cache
_jwks_cache: Optional[dict] = None
_jwks_cache_time: float = 0

# Context variable for storing auth method
from contextvars import ContextVar
_auth_method_context: ContextVar[Optional[str]] = ContextVar("auth_method", default=None)


def get_auth_method_from_context() -> Optional[str]:
    """
    Get auth_method from context variable.
    
    Returns:
        str: Auth method ("oauth", "api_key", or None)
    """
    return _auth_method_context.get()


# AuthenticationError is now imported from app.utils.errors


async def get_jwks() -> dict:
    """
    Get JWKS (JSON Web Key Set) from OAuth provider with caching.
    
    Returns:
        dict: JWKS dictionary
        
    Raises:
        AuthenticationError: If JWKS retrieval fails
    """
    global _jwks_cache, _jwks_cache_time
    
    # Check cache
    current_time = time.time()
    if (
        _jwks_cache is not None
        and (current_time - _jwks_cache_time) < auth_settings.jwks_cache_ttl
    ):
        return _jwks_cache
    
    # Fetch JWKS
    if not auth_settings.oauth_jwks_uri:
        raise AuthenticationError(
            "OAuth JWKS URI not configured", error_code="FR-ERROR-003"
        )
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(auth_settings.oauth_jwks_uri)
            response.raise_for_status()
            jwks = response.json()
            
            # Update cache
            _jwks_cache = jwks
            _jwks_cache_time = current_time
            
            logger.debug("JWKS fetched and cached", jwks_uri=auth_settings.oauth_jwks_uri)
            return jwks
    except httpx.HTTPError as e:
        logger.error("Failed to fetch JWKS", error=str(e), jwks_uri=auth_settings.oauth_jwks_uri)
        raise AuthenticationError(
            f"Failed to fetch JWKS: {str(e)}", error_code="FR-ERROR-003"
        )


def jwk_to_pem(jwk: dict) -> str:
    """
    Convert JWK to PEM format for python-jose.
    
    Args:
        jwk: JWK dictionary
        
    Returns:
        str: PEM-encoded public key
    """
    kty = jwk.get("kty")
    
    if kty == "RSA":
        # Extract modulus and exponent (JWK uses URL-safe base64 without padding)
        def decode_base64url(s: str) -> bytes:
            # Add padding if needed
            padding = 4 - len(s) % 4
            if padding != 4:
                s += "=" * padding
            return base64.urlsafe_b64decode(s)
        
        n = decode_base64url(jwk["n"])
        e = decode_base64url(jwk["e"])
        
        # Create RSA public key
        public_numbers = rsa.RSAPublicNumbers(
            int.from_bytes(e, "big"),
            int.from_bytes(n, "big")
        )
        public_key = public_numbers.public_key(default_backend())
        
        # Serialize to PEM
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode("utf-8")
    
    elif kty == "EC":
        # Extract curve and coordinates (JWK uses URL-safe base64 without padding)
        def decode_base64url(s: str) -> bytes:
            # Add padding if needed
            padding = 4 - len(s) % 4
            if padding != 4:
                s += "=" * padding
            return base64.urlsafe_b64decode(s)
        
        crv = jwk.get("crv", "P-256")
        x = decode_base64url(jwk["x"])
        y = decode_base64url(jwk["y"])
        
        # Map curve name to cryptography curve
        curve_map = {
            "P-256": ec.SECP256R1(),
            "P-384": ec.SECP384R1(),
            "P-521": ec.SECP521R1(),
        }
        curve = curve_map.get(crv)
        if not curve:
            raise ValueError(f"Unsupported EC curve: {crv}")
        
        # Create EC public key
        public_numbers = ec.EllipticCurvePublicNumbers(
            int.from_bytes(x, "big"),
            int.from_bytes(y, "big"),
            curve
        )
        public_key = public_numbers.public_key(default_backend())
        
        # Serialize to PEM
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode("utf-8")
    
    else:
        raise ValueError(f"Unsupported key type: {kty}")


def get_signing_key(token: str, jwks: dict) -> Optional[str]:
    """
    Get signing key from JWKS for token and convert to PEM format.
    
    Args:
        token: JWT token string
        jwks: JWKS dictionary
        
    Returns:
        str: PEM-encoded public key or None if not found
    """
    try:
        # Decode token header without verification
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            return None
        
        # Find key in JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM
                return jwk_to_pem(key)
        
        return None
    except (JWTError, ValueError, KeyError) as e:
        logger.error("Failed to get signing key", error=str(e))
        return None


async def validate_oauth_token(token: str) -> dict:
    """
    Validate OAuth 2.0 JWT token and extract claims.
    
    Args:
        token: Bearer token string
        
    Returns:
        dict: Token claims with user_id, tenant_id, and role
        
    Raises:
        AuthenticationError: If token validation fails
    """
    start_time = time.time()
    
    try:
        # Get JWKS
        jwks = await get_jwks()
        
        # Get signing key
        signing_key = get_signing_key(token, jwks)
        if not signing_key:
            raise AuthenticationError(
                "Unable to find signing key for token", error_code="FR-ERROR-003"
            )
        
        # Decode and verify token
        try:
            # signing_key is now PEM format
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=auth_settings.oauth_algorithms,
                audience=auth_settings.oauth_audience if auth_settings.oauth_audience else None,
                issuer=auth_settings.oauth_issuer if auth_settings.oauth_issuer else None,
            )
        except JWTError as e:
            raise AuthenticationError(
                f"Token validation failed: {str(e)}", error_code="FR-ERROR-003"
            )
        
        # Extract user_id, tenant_id, and role from claims
        user_id_str = claims.get(auth_settings.oauth_user_id_claim)
        tenant_id_str = claims.get(auth_settings.oauth_tenant_id_claim)
        role = claims.get(auth_settings.oauth_role_claim)
        
        # Validate performance requirement (<50ms)
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > auth_settings.auth_timeout_ms:
            logger.warning(
                "OAuth validation exceeded performance requirement",
                elapsed_ms=elapsed_ms,
                threshold_ms=auth_settings.auth_timeout_ms,
            )
        
        # If tenant_id or user_id missing from claims, try user profile lookup
        if not user_id_str or not tenant_id_str:
            if auth_settings.oauth_user_profile_endpoint:
                try:
                    profile = await get_user_profile(token)
                    user_id_str = user_id_str or profile.get("sub") or profile.get("id")
                    tenant_id_str = tenant_id_str or profile.get("tenant_id")
                    role = role or profile.get("role")
                except Exception as e:
                    logger.warning(
                        "User profile lookup failed, using token claims only",
                        error=str(e),
                    )
        
        if not user_id_str:
            raise AuthenticationError(
                "User ID not found in token claims or user profile",
                error_code="FR-ERROR-003",
            )
        
        if not tenant_id_str:
            raise AuthenticationError(
                "Tenant ID not found in token claims or user profile",
                error_code="FR-ERROR-003",
            )
        
        # Convert to UUIDs
        try:
            user_id = UUID(user_id_str)
            tenant_id = UUID(tenant_id_str)
        except ValueError as e:
            raise AuthenticationError(
                f"Invalid UUID format in token claims: {str(e)}",
                error_code="FR-ERROR-003",
            )
        
        logger.debug(
            "OAuth token validated",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            role=role,
            elapsed_ms=elapsed_ms,
        )
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role or "user",  # Default role if not specified
        }
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("OAuth token validation error", error=str(e))
        raise AuthenticationError(
            f"Token validation failed: {str(e)}", error_code="FR-ERROR-003"
        )


async def get_user_profile(token: str) -> dict:
    """
    Get user profile from OAuth provider userinfo endpoint.
    
    Args:
        token: Bearer token string
        
    Returns:
        dict: User profile data
        
    Raises:
        AuthenticationError: If profile retrieval fails
    """
    if not auth_settings.oauth_user_profile_endpoint:
        raise AuthenticationError(
            "User profile endpoint not configured", error_code="FR-ERROR-003"
        )
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                auth_settings.oauth_user_profile_endpoint,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(
            "Failed to fetch user profile",
            error=str(e),
            endpoint=auth_settings.oauth_user_profile_endpoint,
        )
        raise AuthenticationError(
            f"Failed to fetch user profile: {str(e)}", error_code="FR-ERROR-003"
        )


def extract_api_key_from_header(api_key_header: Optional[str]) -> Optional[str]:
    """
    Extract API key from header value.
    
    Args:
        api_key_header: API key header value (can be from X-API-Key or Authorization header)
        
    Returns:
        str: API key or None if not found
    """
    if not api_key_header:
        return None
    
    # If it's from Authorization header with "Bearer " prefix, remove it
    if api_key_header.startswith("Bearer "):
        return api_key_header[7:].strip()
    
    # Otherwise, return as-is (from X-API-Key header)
    return api_key_header.strip()


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        authorization_header: Authorization header value
        
    Returns:
        str: Bearer token or None if not found
    """
    if not authorization_header:
        return None
    
    if not authorization_header.startswith("Bearer "):
        return None
    
    return authorization_header[7:].strip()


async def validate_api_key(api_key: str) -> dict:
    """
    Validate API key and extract tenant_id and user_id.
    
    Args:
        api_key: API key string
        
    Returns:
        dict: Claims with user_id, tenant_id, and role
        
    Raises:
        AuthenticationError: If API key validation fails
    """
    start_time = time.time()
    
    try:
        # Get database session (async generator)
        async for session in get_db_session():
            api_key_repo = TenantApiKeyRepository(session)
            user_repo = UserRepository(session)
            
            # Get all active API keys
            # Note: This approach requires checking all keys (bcrypt hashes can't be directly looked up)
            # For production, consider using a fast hash prefix (SHA-256) for lookup + bcrypt for verification
            # For MVP, we'll limit to first 100 active keys for performance (FR-AUTH-002: <50ms requirement)
            active_keys = await api_key_repo.get_active_keys()
            
            # Limit to first 100 keys for performance
            if len(active_keys) > 100:
                logger.warning(
                    "Too many active API keys, limiting validation to first 100",
                    total_keys=len(active_keys),
                )
                active_keys = active_keys[:100]
            
            # Try to find matching key
            matching_key = None
            for key in active_keys:
                try:
                    if verify_api_key(api_key, key.key_hash):
                        matching_key = key
                        break
                except Exception:
                    # Continue to next key if verification fails
                    continue
            
            if not matching_key:
                raise AuthenticationError(
                    "Invalid API key", error_code="FR-ERROR-003"
                )
            
            # Check expiration
            if matching_key.expires_at:
                # Compare with current UTC time
                if matching_key.expires_at < datetime.now(timezone.utc):
                    raise AuthenticationError(
                        "API key has expired", error_code="FR-ERROR-003"
                    )
            
            # Extract tenant_id
            tenant_id = matching_key.tenant_id
            
            # Get associated user_id
            # API keys can be associated with a specific user or use a system user
            # For now, we'll get the first user for the tenant
            # In a real implementation, API keys might have a user_id field
            users = await user_repo.get_by_tenant(tenant_id, limit=1)
            if users:
                user_id = users[0].user_id
                role = users[0].role
            else:
                # No user found - this shouldn't happen in normal operation
                raise AuthenticationError(
                    "No user found for tenant associated with API key",
                    error_code="FR-ERROR-003",
                )
            
            # Validate performance requirement (<50ms)
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > auth_settings.auth_timeout_ms:
                logger.warning(
                    "API key validation exceeded performance requirement",
                    elapsed_ms=elapsed_ms,
                    threshold_ms=auth_settings.auth_timeout_ms,
                )
            
            logger.debug(
                "API key validated",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
                role=role,
                elapsed_ms=elapsed_ms,
            )
            
            return {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role": role or "user",
            }
            break  # Exit after first iteration (async generator yields once)
            
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("API key validation error", error=str(e))
        raise AuthenticationError(
            f"API key validation failed: {str(e)}", error_code="FR-ERROR-003"
        )


async def log_authentication_attempt(
    user_id: Optional[UUID],
    tenant_id: Optional[UUID],
    auth_method: str,
    success: bool,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Log authentication attempt to audit log.
    
    Args:
        user_id: User ID (if authentication succeeded)
        tenant_id: Tenant ID (if authentication succeeded)
        auth_method: Authentication method ("oauth" or "api_key")
        success: Whether authentication succeeded
        reason: Failure reason (if authentication failed)
        ip_address: IP address of the request
    """
    try:
        async for session in get_db_session():
            audit_repo = AuditLogRepository(session)
            
            # Create audit log entry using repository create method
            await audit_repo.create(
                tenant_id=tenant_id,
                user_id=user_id,
                action="authenticate" if success else "authenticate_failed",
                resource_type="authentication",
                resource_id=None,
                details={
                    "auth_method": auth_method,
                    "success": success,
                    "reason": reason,
                    "ip_address": ip_address,
                },
            )
            await session.commit()
            break  # Exit after first iteration
    except Exception as e:
        # Don't fail authentication if audit logging fails
        logger.error(
            "Failed to log authentication attempt",
            error=str(e),
            user_id=str(user_id) if user_id else None,
            tenant_id=str(tenant_id) if tenant_id else None,
        )


async def authenticate_request(
    authorization_header: Optional[str] = None,
    api_key_header: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> MCPContext:
    """
    Authenticate request using OAuth 2.0 or API key.
    
    Tries OAuth 2.0 first, falls back to API key if OAuth fails or is disabled.
    
    Args:
        authorization_header: Authorization header value (Bearer token)
        api_key_header: API key header value
        
    Returns:
        MCPContext: Authenticated context with user_id, tenant_id, and role
        
    Raises:
        AuthenticationError: If authentication fails
    """
    start_time = time.time()
    
    # Try OAuth 2.0 first
    if auth_settings.oauth_enabled and authorization_header:
        try:
            token = extract_bearer_token(authorization_header)
            if token:
                claims = await validate_oauth_token(token)
                context = MCPContext(
                    tenant_id=claims["tenant_id"],
                    user_id=claims["user_id"],
                    role=claims["role"],
                )
                # Set auth_method in context variable
                _auth_method_context.set("oauth")
                # Log successful OAuth authentication
                await log_authentication_attempt(
                    user_id=context.user_id,
                    tenant_id=context.tenant_id,
                    auth_method="oauth",
                    success=True,
                    ip_address=ip_address,
                )
                return context
        except AuthenticationError as e:
            # Log failed OAuth authentication
            await log_authentication_attempt(
                user_id=None,
                tenant_id=None,
                auth_method="oauth",
                success=False,
                reason=str(e),
                ip_address=ip_address,
            )
            logger.debug("OAuth authentication failed, trying API key", error=str(e))
            # Fall through to API key authentication
    
    # Try API key authentication
    if auth_settings.api_key_enabled and api_key_header:
        api_key = extract_api_key_from_header(api_key_header)
        if api_key:
            try:
                claims = await validate_api_key(api_key)
                context = MCPContext(
                    tenant_id=claims["tenant_id"],
                    user_id=claims["user_id"],
                    role=claims["role"],
                )
                # Set auth_method in context variable
                _auth_method_context.set("api_key")
                # Log successful API key authentication
                await log_authentication_attempt(
                    user_id=context.user_id,
                    tenant_id=context.tenant_id,
                    auth_method="api_key",
                    success=True,
                    ip_address=ip_address,
                )
                return context
            except AuthenticationError as e:
                # Log failed API key authentication
                await log_authentication_attempt(
                    user_id=None,
                    tenant_id=None,
                    auth_method="api_key",
                    success=False,
                    reason=str(e),
                    ip_address=ip_address,
                )
                raise
    
    # No authentication method succeeded
    error = AuthenticationError(
        "Authentication required: OAuth 2.0 Bearer token or API key",
        error_code="FR-ERROR-003",
    )
    # Log failed authentication (no method provided)
    await log_authentication_attempt(
        user_id=None,
        tenant_id=None,
        auth_method="none",
        success=False,
        reason="No authentication method provided",
        ip_address=ip_address,
    )
    raise error


class AuthenticationMiddleware(Middleware):
    """
    Authentication middleware for FastMCP server.
    
    Executes first in the middleware stack to authenticate all requests.
    Tries OAuth 2.0 first, falls back to API key authentication.
    Stores authenticated context for downstream middleware and tools.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Authenticate request before tool execution.
        
        Args:
            context: Middleware context with FastMCP request information
            call_next: Next middleware or tool handler
            
        Returns:
            Response from next middleware/tool
            
        Raises:
            AuthenticationError: If authentication fails (prevents tool execution)
        """
        try:
            # Get HTTP headers from request
            # FastMCP provides get_http_headers() for HTTP transport
            headers = {}
            try:
                headers = get_http_headers()
            except Exception:
                # If HTTP headers not available (e.g., SSE transport), try context
                if hasattr(context, "fastmcp_context") and hasattr(context.fastmcp_context, "request_context"):
                    # Try to get headers from request context if available
                    pass
            
            # Extract authentication headers
            authorization_header = headers.get("Authorization") or headers.get("authorization")
            api_key_header = headers.get("X-API-Key") or headers.get("x-api-key")
            
            # Extract IP address from headers
            ip_address = (
                headers.get("X-Forwarded-For") or
                headers.get("X-Real-IP") or
                headers.get("Remote-Addr") or
                None
            )
            # If X-Forwarded-For contains multiple IPs, take the first one
            if ip_address and "," in ip_address:
                ip_address = ip_address.split(",")[0].strip()
            
            # Authenticate request
            auth_context = await authenticate_request(
                authorization_header=authorization_header,
                api_key_header=api_key_header,
                ip_address=ip_address,
            )
            
            # Set auth_method in context variable
            auth_method = "oauth" if authorization_header else ("api_key" if api_key_header else None)
            if auth_method:
                _auth_method_context.set(auth_method)
            
            # Store authenticated context in middleware context for downstream use
            # FastMCP middleware context can store custom attributes
            if not hasattr(context, "auth_context"):
                context.auth_context = auth_context
            
            # Also store in FastMCP context if available
            if hasattr(context, "fastmcp_context"):
                if not hasattr(context.fastmcp_context, "auth_context"):
                    context.fastmcp_context.auth_context = auth_context
                
                # Store user_id and tenant_id for easy access
                context.fastmcp_context.user_id = str(auth_context.user_id)
                context.fastmcp_context.tenant_id = str(auth_context.tenant_id)
                context.fastmcp_context.role = auth_context.role
            
            logger.debug(
                "Request authenticated",
                user_id=str(auth_context.user_id),
                tenant_id=str(auth_context.tenant_id),
                role=auth_context.role,
            )
            
            # Continue to next middleware/tool
            return await call_next(context)
            
        except AuthenticationError as e:
            # Authentication failed - prevent tool execution
            logger.warning(
                "Authentication failed",
                error=e.message,
                error_code=e.error_code,
            )
            
            # Return error response (FastMCP will handle this as MCP error)
            # For HTTP transport, this will be converted to 401 Unauthorized
            raise ValueError(
                f"Authentication failed: {e.message} (Error code: {e.error_code})"
            )
        except Exception as e:
            logger.error(
                "Unexpected error in authentication middleware",
                error=str(e),
            )
            raise ValueError(f"Authentication error: {str(e)}")

