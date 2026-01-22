# Keycloak OAuth Setup for Bionic-RAG

This document provides step-by-step instructions for setting up Keycloak as the OAuth provider for the Bionic-RAG multi-tenant application.

## Prerequisites

- Keycloak server running and accessible
- Admin access to Keycloak admin console
- Application URLs and redirect URIs prepared

## 1. Create Keycloak Realm

1. **Access Keycloak Admin Console**
   - Navigate to your Keycloak admin console (typically `https://keycloak.example.com/admin`)

2. **Create New Realm**
   - Click on the dropdown in the top-left corner
   - Click "Create realm"
   - Enter realm name: `bionic-rag`
   - Click "Create"

## 2. Create Client Configuration

1. **Navigate to Clients**
   - Select the "bionic-rag" realm from the dropdown
   - Go to "Clients" in the left sidebar

2. **Create New Client**
   - Click "Create client"
   - Configure client settings:
     ```
     Client ID: bionic-rag-client
     Client type: OpenID Connect
     Client authentication: On (for confidential client)
     ```

3. **Configure Client Details**
   - **Capability config**:
     - Standard flow: ON
     - Direct access grants: ON (for development/testing)
     - Implicit flow: OFF (not recommended for security)

4. **Configure Login Settings**
   - **Login settings**:
     ```
     Valid redirect URIs:
     - http://localhost:3000/auth/callback (development)
     - https://your-domain.com/auth/callback (production)
     - bionic-rag://callback (mobile app)

     Web origins:
     - http://localhost:3000 (development)
     - https://your-domain.com (production)
     ```

5. **Configure Tokens**
   - **Fine-grained OpenID Connect configuration**:
     ```
     Access token lifespan: 5 minutes (300 seconds)
     Refresh token lifespan: 30 days
     ```

## 3. Configure User Attributes and Mappers

### Add Tenant ID Mapper

1. **Go to Client Scopes**
   - Navigate to "Client scopes" in the left sidebar
   - Click on "bionic-rag-client-dedicated" (auto-created scope)

2. **Add Protocol Mapper**
   - Click "Add mapper" → "By configuration"
   - Select "User Attribute"
   - Configure:
     ```
     Name: tenant_id
     User Attribute: tenant_id
     Token Claim Name: tenant_id
     Claim JSON Type: String
     Add to ID token: ON
     Add to access token: ON
     Add to userinfo: ON
     ```

### Add Role Mapper

1. **Add Another Protocol Mapper**
   - Click "Add mapper" → "By configuration"
   - Select "User Realm Role"
   - Configure:
     ```
     Name: realm_roles
     Token Claim Name: role
     Claim JSON Type: String
     Add to ID token: ON
     Add to access token: ON
     Add to userinfo: ON
     ```

## 4. Create User Roles

1. **Navigate to Realm Roles**
   - Go to "Realm roles" in the left sidebar

2. **Create Roles**
   - Create the following roles:
     ```
     uber_admin: Super administrator with full access
     tenant_admin: Tenant administrator
     project_admin: Project-level administrator
     end_user: Regular application user
     ```

## 5. Create Test Users

1. **Navigate to Users**
   - Go to "Users" in the left sidebar

2. **Create Users**
   - Create test users for each role type
   - Set temporary password and require password change on first login

3. **Assign Roles**
   - For each user, go to "Role mapping" tab
   - Assign appropriate realm role

4. **Set User Attributes**
   - For each user, add custom attributes:
     ```
     tenant_id: <tenant-uuid>
     ```

## 6. Configure Environment Variables

### Backend Configuration (.env)

Add the following to your backend `.env` file:

```bash
# OAuth Configuration
OAUTH_ENABLED=true
OAUTH_ISSUER=https://keycloak.example.com/realms/bionic-rag
OAUTH_JWKS_URI=https://keycloak.example.com/realms/bionic-rag/protocol/openid-connect/certs
OAUTH_AUDIENCE=bionic-rag-client
OAUTH_CLIENT_ID=bionic-rag-client
OAUTH_CLIENT_SECRET=<client-secret-from-keycloak>
OAUTH_USER_ID_CLAIM=sub
OAUTH_TENANT_ID_CLAIM=tenant_id
OAUTH_ROLE_CLAIM=role
OAUTH_USER_PROFILE_ENDPOINT=https://keycloak.example.com/realms/bionic-rag/protocol/openid-connect/userinfo
```

### Frontend Configuration (.env.local)

Add the following to your frontend `.env.local` file:

```bash
# OAuth Configuration
NEXT_PUBLIC_OAUTH_BASE_URL=https://keycloak.example.com/realms/bionic-rag/protocol/openid-connect
NEXT_PUBLIC_OAUTH_CLIENT_ID=bionic-rag-client
NEXT_PUBLIC_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 7. Test the Configuration

### Verify Keycloak Endpoints

1. **OpenID Connect Configuration**
   - Visit: `https://keycloak.example.com/realms/bionic-rag/.well-known/openid-connect-configuration`
   - Verify all endpoints are accessible

2. **JWKS Endpoint**
   - Visit: `https://keycloak.example.com/realms/bionic-rag/protocol/openid-connect/certs`
   - Should return valid JWKS

### Test OAuth Flow

1. **Start the Application**
   ```bash
   # Backend
   cd /workspaces/mem0-rag
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

   # Frontend
   cd frontend
   npm run dev
   ```

2. **Test Login Flow**
   - Visit `http://localhost:3000`
   - Click "Sign in with OAuth 2.0"
   - Should redirect to Keycloak login
   - Login with test user
   - Should redirect back to application

3. **Verify Token**
   - Check browser developer tools for stored token
   - Decode token to verify claims (tenant_id, role, etc.)

## 8. Production Deployment Considerations

### SSL/TLS Configuration
- Ensure all Keycloak URLs use HTTPS
- Configure proper SSL certificates
- Set up redirect URIs for production domain

### Client Secret Management
- Store client secret securely (environment variables, secret management)
- Rotate secrets regularly
- Use different secrets for different environments

### Token Configuration
- Adjust token lifespans for production
- Configure proper refresh token policies
- Set up token revocation policies

### Security Hardening
- Disable direct access grants in production
- Enable PKCE for additional security
- Configure CORS properly
- Set up proper session management

## 9. Troubleshooting

### Common Issues

1. **Invalid redirect URI**
   - Check that redirect URIs in Keycloak match exactly
   - Include/exclude trailing slashes consistently

2. **JWKS endpoint not accessible**
   - Verify realm name is correct
   - Check network connectivity
   - Ensure realm is active

3. **Token validation fails**
   - Verify client secret is correct
   - Check token algorithms (RS256/ES256)
   - Validate audience and issuer claims

4. **User attributes not in token**
   - Ensure protocol mappers are configured
   - Check user attribute names
   - Verify mappers are enabled

### Debug Steps

1. **Check Keycloak Logs**
   ```bash
   docker logs <keycloak-container>
   ```

2. **Test Token Introspection**
   ```bash
   curl -X POST https://keycloak.example.com/realms/bionic-rag/protocol/openid-connect/token/introspect \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "token=<access-token>&client_id=bionic-rag-client&client_secret=<client-secret>"
   ```

3. **Decode JWT Token**
   - Use jwt.io or similar tool to decode token
   - Verify all required claims are present

## 10. Keycloak Client Export (Optional)

To export the client configuration for backup or migration:

1. Go to "Clients" → "bionic-rag-client"
2. Click "Export" tab
3. Export as JSON for backup

## Summary

Following this guide will set up Keycloak as the OAuth provider for the Bionic-RAG application with:

- Multi-tenant support via tenant_id claim
- Role-based access control
- Secure token handling
- Proper redirect URI configuration
- Test user setup for development

The setup supports both development and production environments with appropriate security configurations.