# Keycloak OAuth Setup for Bionic-RAG

This guide provides complete instructions for setting up OAuth authentication with Keycloak for the Bionic-RAG multi-tenant application.

## 🚀 Quick Setup (Automated)

### Prerequisites
- Keycloak server running at `https://auth.bionicaisolutions.com`
- Admin credentials: `admin` / `Th1515T0p53cr3t`
- Python 3.8+ with requests library

### Automated Setup

1. **Run the setup script:**
```bash
python scripts/setup_keycloak_client.py \
  https://auth.bionicaisolutions.com \
  admin \
  Th1515T0p53cr3t
```

2. **Test the configuration:**
```bash
python scripts/test_oauth_flow.py \
  https://auth.bionicaisolutions.com \
  <client-secret-from-setup>
```

3. **Start the services:**
```bash
# Backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend && npm run dev
```

## 🔧 Manual Setup (Alternative)

If the automated script doesn't work, follow these manual steps:

### 1. Access Keycloak Admin Console

Navigate to: `https://auth.bionicaisolutions.com/admin/master/console/`

Login with:
- Username: `admin`
- Password: `Th1515T0p53cr3t`

### 2. Switch to Bionic Realm

1. Click the realm dropdown (top-left)
2. Select "Bionic" realm

### 3. Create Client

1. Navigate to "Clients" in the left sidebar
2. Click "Create client"
3. Configure basic settings:
   - **Client ID**: `bionic-rag-client`
   - **Client type**: `OpenID Connect`
   - **Client authentication**: `On`
4. Click "Next"
5. Configure capability config:
   - **Standard flow**: `On`
   - **Direct access grants**: `On` (for development)
   - **Implicit flow**: `Off`
6. Click "Next"
7. Configure login settings:
   - **Valid redirect URIs**:
     - `http://localhost:3000/auth/callback`
     - `https://your-domain.com/auth/callback`
     - `bionic-rag://callback` (for mobile)
   - **Web origins**:
     - `http://localhost:3000`
     - `https://your-domain.com`
8. Click "Save"

### 4. Configure Client Details

After creating the client:

1. Go to "Credentials" tab
2. Copy the "Client secret" (you'll need this for environment variables)

### 5. Add Protocol Mappers

1. Go to "Client scopes" → "bionic-rag-client-dedicated"
2. Click "Add mapper" → "By configuration"

#### Tenant ID Mapper
- **Name**: `tenant_id`
- **Mapper Type**: `User Attribute`
- **User Attribute**: `tenant_id`
- **Token Claim Name**: `tenant_id`
- **Claim JSON Type**: `String`
- Check all token claim options

#### Role Mapper
- **Name**: `realm_roles`
- **Mapper Type**: `User Realm Role`
- **Token Claim Name**: `role`
- **Claim JSON Type**: `String`
- Check all token claim options

### 6. Create Realm Roles

1. Navigate to "Realm roles"
2. Create these roles:
   - `uber_admin`: Super administrator
   - `tenant_admin`: Tenant administrator
   - `project_admin`: Project administrator
   - `end_user`: Regular user

### 7. Create Test Users

1. Navigate to "Users"
2. Click "Create new user"
3. Create test users and assign roles
4. Add custom attributes:
   - Key: `tenant_id`
   - Value: `<tenant-uuid>`

## 📝 Environment Configuration

### Backend (.env)

```bash
# OAuth Configuration
OAUTH_ENABLED=true
OAUTH_ISSUER=https://auth.bionicaisolutions.com/realms/Bionic
OAUTH_JWKS_URI=https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/certs
OAUTH_AUDIENCE=bionic-rag-client
OAUTH_CLIENT_ID=bionic-rag-client
OAUTH_CLIENT_SECRET=<your-client-secret>
OAUTH_USER_ID_CLAIM=sub
OAUTH_TENANT_ID_CLAIM=tenant_id
OAUTH_ROLE_CLAIM=role
OAUTH_USER_PROFILE_ENDPOINT=https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/userinfo
```

### Frontend (.env.local)

```bash
# OAuth Configuration
NEXT_PUBLIC_OAUTH_BASE_URL=https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect
NEXT_PUBLIC_OAUTH_CLIENT_ID=bionic-rag-client
NEXT_PUBLIC_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 🧪 Testing the Setup

### 1. Start Services

```bash
# Backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend && npm run dev
```

### 2. Test OAuth Flow

1. Visit `http://localhost:3000`
2. Click "Sign in with OAuth 2.0"
3. You should be redirected to Keycloak
4. Login with a test user
5. You should be redirected back to the application

### 3. Verify Token Claims

Check the browser developer tools to verify the JWT token contains:
- `sub`: User ID
- `tenant_id`: Tenant identifier
- `role`: User role

## 🔍 Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Ensure redirect URIs in Keycloak match exactly
   - Include/exclude trailing slashes consistently

2. **"Client authentication failed"**
   - Verify client secret is correct
   - Ensure client is confidential (not public)

3. **Token doesn't contain custom claims**
   - Check protocol mappers are configured
   - Verify user attributes are set
   - Ensure mappers are enabled for all token types

4. **CORS errors**
   - Add frontend URL to "Web origins" in client settings
   - Check CORS configuration in Keycloak

### Debug Steps

1. **Check Keycloak logs:**
```bash
docker logs <keycloak-container>
```

2. **Test OpenID configuration:**
```bash
curl https://auth.bionicaisolutions.com/realms/Bionic/.well-known/openid-connect-configuration
```

3. **Test JWKS endpoint:**
```bash
curl https://auth.bionicaisolutions.com/realms/Bionic/protocol/openid-connect/certs
```

4. **Decode JWT token:**
Use https://jwt.io to verify token contents

## 🔐 Security Considerations

### Production Setup

1. **SSL/TLS**: Ensure all URLs use HTTPS
2. **Client Secret**: Store securely (environment variables, secrets manager)
3. **Token Lifespan**: Adjust for production (shorter access tokens)
4. **PKCE**: Enable for additional security
5. **Direct Access Grants**: Disable in production

### Best Practices

1. **Rotate Secrets**: Regularly rotate client secrets
2. **Monitor Logs**: Monitor authentication failures
3. **Rate Limiting**: Implement rate limiting on auth endpoints
4. **Session Management**: Configure proper session timeouts
5. **Audit Logging**: Enable audit logging for security events

## 📚 Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)

## 🎯 What's Configured

This setup provides:

- ✅ Multi-tenant authentication via `tenant_id` claim
- ✅ Role-based access control (uber_admin, tenant_admin, etc.)
- ✅ Secure token validation with JWKS
- ✅ Proper redirect URI configuration
- ✅ Protocol mappers for custom claims
- ✅ Test user setup
- ✅ Environment configuration templates
- ✅ Automated testing scripts

The application now supports complete OAuth 2.0 authentication flow with Keycloak!