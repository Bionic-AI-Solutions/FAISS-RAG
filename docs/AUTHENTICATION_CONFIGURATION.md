# Authentication Configuration Guide

This document describes the authentication configuration for the Mem0-RAG system, including OAuth 2.0 and API key authentication settings.

## Overview

The authentication system supports two methods:
1. **OAuth 2.0**: JWT token-based authentication with JWKS validation
2. **API Key**: Tenant-based API key authentication with bcrypt hashing

## Configuration File

All authentication settings are defined in `app/config/auth.py` using Pydantic Settings, which automatically loads from environment variables.

## Environment Variables

### OAuth 2.0 Configuration

```bash
# Enable/disable OAuth 2.0 authentication
OAUTH_ENABLED=true

# OAuth provider issuer URL (e.g., https://auth.example.com)
OAUTH_ISSUER=https://auth.example.com

# OAuth JWKS endpoint URL (e.g., https://auth.example.com/.well-known/jwks.json)
OAUTH_JWKS_URI=https://auth.example.com/.well-known/jwks.json

# OAuth token audience (expected audience claim)
OAUTH_AUDIENCE=mem0-rag-api

# Supported JWT algorithms (comma-separated, e.g., RS256,ES256)
OAUTH_ALGORITHMS=RS256,ES256

# JWT claim names for user ID, tenant ID, and role
OAUTH_USER_ID_CLAIM=sub
OAUTH_TENANT_ID_CLAIM=tenant_id
OAUTH_ROLE_CLAIM=role

# OAuth provider user profile endpoint for fallback lookup
# (e.g., https://auth.example.com/userinfo)
OAUTH_USER_PROFILE_ENDPOINT=https://auth.example.com/userinfo
```

### API Key Configuration

```bash
# Enable/disable API key authentication
API_KEY_ENABLED=true

# HTTP header name for API key
API_KEY_HEADER=X-API-Key

# API key hashing algorithm (bcrypt or argon2)
API_KEY_HASH_ALGORITHM=bcrypt
```

### Performance Configuration

```bash
# Maximum authentication time in milliseconds (FR-AUTH-001, FR-AUTH-002)
AUTH_TIMEOUT_MS=50

# JWKS cache TTL in seconds
JWKS_CACHE_TTL=3600
```

## Default Values

If environment variables are not set, the following defaults are used:

- `OAUTH_ENABLED`: `true`
- `OAUTH_ISSUER`: `""` (empty, must be configured)
- `OAUTH_JWKS_URI`: `""` (empty, must be configured)
- `OAUTH_AUDIENCE`: `""` (empty, optional)
- `OAUTH_ALGORITHMS`: `["RS256", "ES256"]`
- `OAUTH_USER_ID_CLAIM`: `"sub"`
- `OAUTH_TENANT_ID_CLAIM`: `"tenant_id"`
- `OAUTH_ROLE_CLAIM`: `"role"`
- `OAUTH_USER_PROFILE_ENDPOINT`: `""` (empty, optional fallback)
- `API_KEY_ENABLED`: `true`
- `API_KEY_HEADER`: `"X-API-Key"`
- `API_KEY_HASH_ALGORITHM`: `"bcrypt"`
- `AUTH_TIMEOUT_MS`: `50`
- `JWKS_CACHE_TTL`: `3600`

## Configuration Example

Create a `.env` file in the project root with your authentication settings:

```bash
# OAuth 2.0 Configuration
OAUTH_ENABLED=true
OAUTH_ISSUER=https://auth.example.com
OAUTH_JWKS_URI=https://auth.example.com/.well-known/jwks.json
OAUTH_AUDIENCE=mem0-rag-api
OAUTH_ALGORITHMS=RS256,ES256
OAUTH_USER_ID_CLAIM=sub
OAUTH_TENANT_ID_CLAIM=tenant_id
OAUTH_ROLE_CLAIM=role
OAUTH_USER_PROFILE_ENDPOINT=https://auth.example.com/userinfo

# API Key Configuration
API_KEY_ENABLED=true
API_KEY_HEADER=X-API-Key
API_KEY_HASH_ALGORITHM=bcrypt

# Performance Configuration
AUTH_TIMEOUT_MS=50
JWKS_CACHE_TTL=3600
```

## Usage in Code

The authentication settings are automatically loaded and available via the global `auth_settings` instance:

```python
from app.config.auth import auth_settings

# Access OAuth settings
if auth_settings.oauth_enabled:
    issuer = auth_settings.oauth_issuer
    jwks_uri = auth_settings.oauth_jwks_uri

# Access API key settings
if auth_settings.api_key_enabled:
    header_name = auth_settings.api_key_header
    hash_algorithm = auth_settings.api_key_hash_algorithm
```

## Performance Requirements

- **FR-AUTH-001**: OAuth 2.0 authentication must complete within 50ms
- **FR-AUTH-002**: API key authentication must complete within 50ms

The system monitors authentication performance and logs warnings if the threshold is exceeded.

## Security Considerations

1. **JWKS Caching**: JWKS keys are cached for 1 hour (3600 seconds) to reduce OAuth provider requests
2. **API Key Hashing**: API keys are hashed using SHA256 + bcrypt to prevent plaintext storage
3. **Token Validation**: JWT tokens are validated for signature, expiration, issuer, and audience
4. **Audit Logging**: All authentication attempts (successful and failed) are logged to the audit log

## Troubleshooting

### OAuth Authentication Fails

1. Verify `OAUTH_ISSUER` and `OAUTH_JWKS_URI` are correctly configured
2. Check that the OAuth provider is accessible from the application
3. Verify JWT tokens include required claims (`sub`, `tenant_id`)
4. Check that the token audience matches `OAUTH_AUDIENCE` (if configured)

### API Key Authentication Fails

1. Verify API key is correctly hashed and stored in `tenant_api_keys` table
2. Check that the API key is not expired
3. Verify the API key header name matches `API_KEY_HEADER`
4. Ensure the tenant associated with the API key exists and is active

### Performance Issues

1. Check `AUTH_TIMEOUT_MS` is set appropriately (default: 50ms)
2. Monitor JWKS cache hit rate (should be high after initial load)
3. For API keys, consider implementing a fast hash prefix lookup for better performance
4. Review database query performance for API key validation

## Related Documentation

- `app/config/auth.py`: Authentication configuration implementation
- `app/mcp/middleware/auth.py`: Authentication middleware implementation
- `app/utils/hashing.py`: API key hashing utilities
- `_bmad-output/implementation-artifacts/1-5-authentication-middleware.md`: Story implementation details





