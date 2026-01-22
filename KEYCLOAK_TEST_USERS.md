# Keycloak Test Users - Bionic-RAG

This document contains the test users created for the Bionic-RAG application with their credentials, roles, and tenant assignments.

## 📋 Test User Credentials

All users have the password: `Test123!`

### Super Administrator
- **Username**: `uber-admin`
- **Password**: `Test123!`
- **Role**: `uber_admin`
- **Tenant ID**: `00000000-0000-0000-0000-000000000001`
- **Description**: Full system access across all tenants

### Tenant Administrators
- **Username**: `tenant-admin-1`
- **Password**: `Test123!`
- **Role**: `tenant_admin`
- **Tenant ID**: `11111111-1111-1111-1111-111111111111`
- **Description**: Admin access for Tenant 1

- **Username**: `tenant-admin-2`
- **Password**: `Test123!`
- **Role**: `tenant_admin`
- **Tenant ID**: `22222222-2222-2222-2222-222222222222`
- **Description**: Admin access for Tenant 2

### Project Administrators
- **Username**: `project-admin-1`
- **Password**: `Test123!`
- **Role**: `project_admin`
- **Tenant ID**: `11111111-1111-1111-1111-111111111111`
- **Description**: Project-level admin for Tenant 1

- **Username**: `project-admin-2`
- **Password**: `Test123!`
- **Role**: `project_admin`
- **Tenant ID**: `22222222-2222-2222-2222-222222222222`
- **Description**: Project-level admin for Tenant 2

### End Users
- **Username**: `end-user-1`
- **Password**: `Test123!`
- **Role**: `end_user`
- **Tenant ID**: `11111111-1111-1111-1111-111111111111`
- **Description**: Regular user for Tenant 1

- **Username**: `end-user-2`
- **Password**: `Test123!`
- **Role**: `end_user`
- **Tenant ID**: `22222222-2222-2222-2222-222222222222`
- **Description**: Regular user for Tenant 2

- **Username**: `end-user-3`
- **Password**: `Test123!`
- **Role**: `end_user`
- **Tenant ID**: `33333333-3333-3333-3333-333333333333`
- **Description**: Regular user for Tenant 3

## 🏢 Tenant Distribution

### Tenant 1 (`11111111-1111-1111-1111-111111111111`)
- tenant-admin-1 (tenant_admin)
- project-admin-1 (project_admin)
- end-user-1 (end_user)

### Tenant 2 (`22222222-2222-2222-2222-222222222222`)
- tenant-admin-2 (tenant_admin)
- project-admin-2 (project_admin)
- end-user-2 (end_user)

### Tenant 3 (`33333333-3333-3333-3333-333333333333`)
- end-user-3 (end_user)

### System Tenant (`00000000-0000-0000-0000-000000000001`)
- uber-admin (uber_admin) - Cross-tenant access

## 🔐 Role Permissions

### uber_admin
- Full system access
- Can manage all tenants
- Can create/modify/delete any resources
- Cross-tenant operations allowed

### tenant_admin
- Full access within their tenant
- Can manage users and projects in their tenant
- Cannot access other tenants' data

### project_admin
- Can manage specific projects within their tenant
- Limited user management capabilities
- Cannot modify tenant-level settings

### end_user
- Basic application access within their tenant
- Can view and modify their own data
- Limited to assigned projects/features

## 🚀 Testing the OAuth Flow

### Start the Application
```bash
# Backend
cd /workspaces/mem0-rag
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm run dev
```

### Test Login
1. Visit `http://localhost:3000`
2. Click "Sign in with OAuth 2.0"
3. Use any of the test user credentials above
4. Verify that the user is logged in with correct role and tenant

### Test Role-Based Access
- Login as `uber-admin` - should have access to all features
- Login as `tenant-admin-1` - should only see Tenant 1 data
- Login as `end-user-1` - should have limited access within Tenant 1

## 🔧 Keycloak Configuration

### Client Configuration
- **Client ID**: `bionic-rag-client`
- **Client Type**: OpenID Connect
- **Access Type**: confidential
- **Valid Redirect URIs**: `http://localhost:3000/auth/callback`

### Protocol Mappers
- `tenant_id`: Maps user attribute to JWT claim
- `realm_roles`: Maps realm roles to JWT claim

### Environment Variables
Backend and frontend are configured with the correct OAuth settings in their respective `.env` files.

## 📞 Support

If you need additional test users or modifications to existing users, use the scripts:
- `scripts/create_keycloak_test_users.py` - Create additional users
- `scripts/setup_keycloak_client.py` - Modify client configuration

All test users are created with verified emails and permanent passwords for easy testing.