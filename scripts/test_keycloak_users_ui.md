# Keycloak User Testing Guide - UI Testing

## Test Users
All users have password: `Test123!`

1. **uber-admin** - uber_admin role
2. **tenant-admin-1** - tenant_admin role  
3. **tenant-admin-2** - tenant_admin role
4. **project-admin-1** - project_admin role
5. **end-user-1** - end_user role
6. **end-user-2** - end_user role
7. **end-user-3** - end_user role

## Testing Steps for Each User

### Step 1: Navigate to Login
- Go to: `http://localhost:3001/auth/login`

### Step 2: Click OAuth Button
- Click "Sign in with OAuth 2.0" button
- This generates a proper state parameter

### Step 3: Access Keycloak Native Login
- If redirected to Google, navigate directly to:
  `https://auth.bionicaisolutions.com/realms/Bionic/login-actions/authenticate?client_id=bionic-rag-client&redirect_uri=http%3A%2F%2Flocalhost%3A3001%2Fauth%2Fcallback&response_type=code&scope=openid+profile+email+offline_access&state=<state-from-frontend>`

### Step 4: Login
- Enter username: `<username>`
- Enter password: `Test123!`
- Click "Sign In" or press Enter

### Step 5: Complete Profile (if required)
- Fill in Email, First name, Last name
- Click Submit

### Step 6: Verify Success
- Should redirect to app dashboard
- Check user role and tenant_id are correct
- Verify UI shows appropriate access level

### Step 7: Logout
- Click Logout button
- Should redirect to Keycloak logout, then back to login

## Test Results Template

For each user, record:
- ✅ Login successful
- ✅ Role extracted correctly
- ✅ Tenant ID extracted correctly
- ✅ UI access level appropriate
- ✅ Logout works
- ❌ Any errors encountered
