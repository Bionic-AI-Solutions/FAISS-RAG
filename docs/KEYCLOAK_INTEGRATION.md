# Keycloak OAuth 2.0 Integration Guide

## Overview

This application uses Keycloak as the OAuth 2.0 / OpenID Connect identity provider for authentication. The integration supports:

- Authorization Code Flow
- JWT token validation
- Role-based access control (RBAC)
- Multi-tenant support via custom claims
- Keycloak logout integration

## Architecture

### Flow Diagram

```
User → Frontend → Keycloak → Frontend → Backend → Keycloak → Backend → Frontend
  ↓       ↓          ↓          ↓         ↓          ↓         ↓         ↓
Login   OAuth     Login      Callback  Exchange   Token    Validate  Store
Button   URL      Page        Page      Code      Response   Token     Token
```

### Components

1. **Frontend (`frontend/`)**
   - OAuth URL generation
   - Keycloak redirect handling
   - Token storage and management
   - User session management

2. **Backend (`app/api/auth.py`)**
   - Token exchange with Keycloak
   - JWT validation
   - User/tenant extraction from claims

3. **Keycloak Server**
   - Identity provider
   - User authentication
   - Token issuance
   - Role management

## Configuration

### Frontend Configuration (`frontend/.env.local`)

```env
# Keycloak OAuth Configuration
NEXT_PUBLIC_OAUTH_BASE_URL=https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect
NEXT_PUBLIC_OAUTH_CLIENT_ID=bionic-rag-client
NEXT_PUBLIC_OAUTH_REDIRECT_URI=http://localhost:3001/auth/callback
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration (`backend.env`)

```env
# Keycloak OAuth Configuration
OAUTH_ENABLED=true
OAUTH_ISSUER=https://auth.bionicaisolutions.com/realms/Bionic
OAUTH_JWKS_URI=https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/certs
OAUTH_AUDIENCE=bionic-rag-client
OAUTH_CLIENT_ID=bionic-rag-client
OAUTH_CLIENT_SECRET=<your-client-secret>
OAUTH_REDIRECT_URI=http://localhost:3001/auth/callback

# Keycloak Claim Mapping
OAUTH_USER_ID_CLAIM=sub
OAUTH_TENANT_ID_CLAIM=tenant_id
OAUTH_ROLE_CLAIM=role
OAUTH_USER_PROFILE_ENDPOINT=https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/userinfo
```

## Keycloak Setup

### Client Configuration

1. **Create Client**
   - Client ID: `bionic-rag-client`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `http://localhost:3001/auth/callback`

2. **Protocol Mappers**
   - `tenant_id`: Custom claim mapper for tenant ID
   - `role`: Custom claim mapper for user role

3. **Roles**
   - `uber_admin`: Full system access
   - `tenant_admin`: Tenant-level access
   - `project_admin`: Project-level access
   - `end_user`: Basic user access

### User Attributes

Users in Keycloak should have:
- `tenant_id`: UUID of the tenant
- Role assignment: One of the roles above

## Token Structure

### Keycloak JWT Claims

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "preferred_username": "username",
  "tenant_id": "tenant-uuid",
  "role": "tenant_admin",
  "realm_access": {
    "roles": ["offline_access", "uma_authorization"]
  },
  "resource_access": {
    "bionic-rag-client": {
      "roles": ["tenant_admin"]
    }
  },
  "iss": "https://auth.bionicaisolutions.com/realms/Bionic",
  "aud": "bionic-rag-client",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Token Extraction

The frontend extracts user information from Keycloak tokens:

1. **User ID**: From `sub` claim
2. **Email**: From `email` or `preferred_username` claim
3. **Role**: From custom `role` claim, or from `resource_access.{client_id}.roles`
4. **Tenant ID**: From custom `tenant_id` claim

## OAuth Flow

### 1. Login Initiation

```typescript
// Frontend: User clicks "Sign in with OAuth 2.0"
const login = () => {
  window.location.href = getOAuthUrl();
};

// Generates Keycloak authorization URL:
// https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/auth?
//   response_type=code&
//   client_id=bionic-rag-client&
//   redirect_uri=http://localhost:3001/auth/callback&
//   scope=openid profile email offline_access&
//   state=<random-state>
```

### 2. Keycloak Authentication

- User is redirected to Keycloak login page
- User enters credentials
- Keycloak validates credentials
- Keycloak redirects back with authorization code

### 3. Token Exchange

```typescript
// Frontend callback page receives code
// Exchanges code for token via backend

POST /api/auth/callback
{
  "code": "authorization-code",
  "state": "state-parameter"
}

// Backend exchanges code with Keycloak
POST https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/token
{
  "grant_type": "authorization_code",
  "code": "authorization-code",
  "redirect_uri": "http://localhost:3001/auth/callback",
  "client_id": "bionic-rag-client",
  "client_secret": "<secret>"
}

// Keycloak responds with tokens
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### 4. Token Storage

- Access token stored in `localStorage`
- Token used for API authentication
- Token validated on each request

### 5. Logout

```typescript
// Frontend logout
const logout = () => {
  removeToken();
  // Redirect to Keycloak logout
  window.location.href = getKeycloakLogoutUrl();
};

// Keycloak logout URL:
// https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/logout?
//   redirect_uri=http://localhost:3001/auth/login
```

## Security Features

### CSRF Protection

- State parameter generated and stored in `sessionStorage`
- State validated in callback to prevent CSRF attacks
- State removed after validation

### Token Validation

- Backend validates JWT signature using JWKS
- Token issuer validated against configured issuer
- Token audience validated against client ID
- Token expiration checked

### Secure Storage

- Tokens stored in `localStorage` (consider httpOnly cookies for production)
- Refresh tokens handled securely
- Token expiration managed automatically

## Error Handling

### Common Errors

1. **Invalid Authorization Code**
   - Error: `400 Bad Request`
   - Solution: Re-initiate login flow

2. **Token Exchange Failed**
   - Error: `400 Bad Request`
   - Solution: Check Keycloak configuration and client secret

3. **Invalid State Parameter**
   - Error: Frontend validation error
   - Solution: Re-initiate login flow

4. **Token Expired**
   - Error: Token validation fails
   - Solution: Refresh token or re-login

### Keycloak-Specific Errors

- `invalid_client`: Client ID or secret incorrect
- `invalid_grant`: Authorization code invalid or expired
- `unauthorized_client`: Client not authorized for this flow
- `invalid_redirect_uri`: Redirect URI mismatch

## Testing

### Manual Testing

1. **Start Services**
   ```bash
   # Backend
   uvicorn app.main:app --reload --port 8000
   
   # Frontend
   cd frontend && npm run dev -- -p 3001
   ```

2. **Test Login Flow**
   - Navigate to `http://localhost:3001/auth/login`
   - Click "Sign in with OAuth 2.0"
   - Login with Keycloak credentials
   - Verify redirect back to app
   - Check token in browser DevTools → Application → Local Storage

3. **Test Logout**
   - Click logout button
   - Verify redirect to Keycloak logout
   - Verify redirect back to login page
   - Verify token removed from storage

### Automated Testing

Run the OAuth test suite:

```bash
python3 scripts/test_oauth_login.py
```

## Troubleshooting

### Token Not Stored

- Check browser console for errors
- Verify callback URL matches Keycloak configuration
- Check network tab for API responses

### Role Not Extracted

- Verify protocol mapper configured in Keycloak
- Check token claims in browser DevTools
- Verify role mapping in `extractUserFromToken()`

### Logout Not Working

- Verify Keycloak logout URL is correct
- Check redirect URI configuration
- Verify token is removed from storage

## Production Considerations

1. **HTTPS Only**: Use HTTPS for all OAuth endpoints
2. **Secure Cookies**: Consider httpOnly cookies for token storage
3. **Token Refresh**: Implement automatic token refresh
4. **Error Monitoring**: Monitor OAuth errors and failures
5. **Rate Limiting**: Implement rate limiting on auth endpoints
6. **Session Management**: Implement proper session timeout

## References

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth 2.0 Specification](https://oauth.net/2/)
